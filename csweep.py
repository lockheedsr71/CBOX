"""csweep - parallel host and port discovery over a network."""

import argparse
import ipaddress
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.console import MissingDependency, rich_toolkit
from cbox_core.jsonout import add_json_flag, emit_json, json_requested

#: Concurrency is bounded so a sweep cannot saturate the link or trip a
#: firewall's SYN-flood threshold. 128 parallel probes is well inside that.
DEFAULT_WORKERS = 128
DEFAULT_PORT_TIMEOUT = 0.4
DEFAULT_HOST_TIMEOUT = 1.0


def parse_subnet(spec):
    """Accept '192.168.1', '192.168.1.0/24' or '192.168.1.10-50'."""
    try:
        if "/" in spec:
            return ipaddress.ip_network(spec, strict=False)

        if "-" in spec:
            base_text, _, last_text = spec.rpartition(".")
            if not base_text or not last_text:
                raise ValueError
            base = ipaddress.ip_address(base_text)
            first, last = int(spec.split(".")[-1].split("-")[0]), int(last_text)
            if not (0 <= first <= last <= 255):
                raise ValueError
            return ipaddress.ip_network(f"{base}/{base.prefixlen}")

        address = ipaddress.ip_address(spec)
        # A bare address scans just that host.
        return ipaddress.ip_network(f"{address}/{address.max_prefixlen}")

    except ValueError as exc:
        raise ValueError(
            f"Invalid subnet: '{spec}' (use 192.168.1, 192.168.1.0/24 or 192.168.1.10-50)"
        ) from exc


def host_addresses(network):
    """Usable host addresses, excluding the network and broadcast addresses."""
    if network.num_addresses == 2:  # /31: both addresses are usable
        return [str(addr) for addr in network]
    if network.num_addresses <= 2:
        return [str(addr) for addr in network if not (addr.is_network_address or addr.is_reserved)]

    return [
        str(addr) for addr in network
        if addr not in (network.network_address, network.broadcast_address)
    ]


def _reverse(address):
    """PTR lookup. Best-effort: a slow or unreachable resolver must not
    stretch the scan, so failures collapse to an empty string."""
    try:
        return socket.gethostbyaddr(address)[0]
    except (OSError, socket.herror):
        return ""


def probe_host(address, timeout=DEFAULT_HOST_TIMEOUT):
    """Return (address, rtt_ms, hostname) if the host answers ICMP.

    The hostname is resolved later, off the probe path - see
    resolve_hostnames.
    """
    import subprocess

    start = time.perf_counter()
    flag = "-n" if os.name == "nt" else "-c"
    timeout_flag = "-w" if os.name == "nt" else "-W"
    timeout_value = str(int(timeout * 1000)) if os.name == "nt" else "1"

    try:
        completed = subprocess.run(
            ["ping", flag, "1", timeout_flag, timeout_value, address],
            capture_output=True, timeout=timeout + 1,
        )
        if completed.returncode == 0:
            return address, (time.perf_counter() - start) * 1000, ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def probe_port(address, port, timeout=DEFAULT_PORT_TIMEOUT):
    """Return (address, port, service) when the TCP port accepts a connection."""
    if timeout is None:
        # A blocking socket would hang on every filtered packet.
        timeout = DEFAULT_PORT_TIMEOUT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        if sock.connect_ex((address, port)) == 0:
            try:
                service = socket.getservbyport(port)
            except OSError:
                service = "-"
            return address, port, service
    except OSError:
        pass
    finally:
        sock.close()
    return None


def resolve_hostnames(rows, key="ip", workers=16, timeout=2.0):
    """Fill in hostnames after the scan, off the critical path.

    PTR lookups are sequential-blocking and can take seconds each when the
    resolver is slow. Doing them inline made a small sweep take 20x longer
    than the probes themselves.
    """
    pending = list({row[key] for row in rows if not row.get("hostname")})
    if not pending:
        return rows

    resolved = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_reverse, addr): addr for addr in pending}
        try:
            for future in as_completed(futures, timeout=timeout):
                name = future.result()
                resolved[futures[future]] = name
        except TimeoutError:
            # Whatever is still outstanding gets no hostname; do not block on it.
            for future in futures:
                future.cancel()

    for row in rows:
        row["hostname"] = row.get("hostname") or resolved.get(row[key], "")
    return rows


def sweep_hosts(network, workers, timeout):
    """Ping every host in `network` concurrently, preserving input order.

    Each probe shells out to `ping.exe`, so a /24 costs 256 process launches
    and takes a few seconds. The fast alternative - one batched raw ICMP echo
    via scapy - was tried and removed: it needs Npcap, returns nothing at all
    without it, and spews driver errors on cleanup.
    """
    addresses = host_addresses(network)
    found = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(probe_host, addr, timeout): addr for addr in addresses}
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append({"ip": result[0], "rtt_ms": round(result[1], 1), "hostname": ""})

    found.sort(key=lambda row: ipaddress.ip_address(row["ip"]))
    return found


def sweep_ports(network, ports, workers, timeout, live=True):
    """Scan `ports` on every host in `network` concurrently."""
    addresses = host_addresses(network)

    if live:
        rich = rich_toolkit()
        Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn = (
            rich[7], rich[8], rich[9], rich[10], rich[11]
        )
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            transient=True,
        )
        task = progress.add_task(f"[cyan]Scanning {network}...", total=len(addresses) * len(ports))
        progress_context = progress
    else:
        progress = None
        progress_context = None

    rows = []
    if progress is None:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(probe_port, addr, port, timeout): (addr, port)
                for addr in addresses for port in ports
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    rows.append(_port_row(result))
    else:
        with progress_context, ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(probe_port, addr, port, timeout): (addr, port)
                for addr in addresses for port in ports
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    rows.append(_port_row(result))
                progress.update(task, advance=1)

    rows.sort(key=lambda row: (ipaddress.ip_address(row["ip"]), row["port"]))
    return rows


def _port_row(result):
    address, port, service = result
    # The hostname is resolved later, off the probe path.
    return {"ip": address, "port": port, "service": service, "hostname": ""}


def parse_ports(spec):
    if not spec:
        return []
    ports = []
    for raw in spec.split(","):
        chunk = raw.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_text, end_text = chunk.split("-", 1)
            try:
                start, end = int(start_text), int(end_text)
            except ValueError as exc:
                raise ValueError(f"Invalid port range: '{chunk}'") from exc
            if not (1 <= start <= 65535 and 1 <= end <= 65535):
                raise ValueError("Ports must be between 1 and 65535")
            ports.extend(range(min(start, end), max(start, end) + 1))
        else:
            try:
                ports.append(int(chunk))
            except ValueError as exc:
                raise ValueError(f"Invalid port: '{chunk}'") from exc
    return list(dict.fromkeys(ports))


def default_subnet():
    """The /24 this machine sits on, or None when it cannot be determined."""
    try:
        import psutil

        for addresses in psutil.net_if_addrs().values():
            for addr in addresses:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return ipaddress.ip_network(f"{addr.address}/24", strict=False)
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description=f"CBOX csweep {__version__} - Parallel host and port discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  csweep                              Sweep this machine's /24 for live hosts.
  csweep 192.168.1.0/24               Sweep an explicit subnet.
  csweep 192.168.1.10-50              Sweep a host range.
  csweep 192.168.1.0/24 -p 22,80,443  Scan ports across the subnet.
  csweep -p 1-1024 --target 10.0.0.5  Scan a port range on one host.

Only scan networks you are authorized to test.
""",
    )
    parser.add_argument("subnet", nargs="?", help="Subnet, range or single host")
    parser.add_argument("-t", "--target", help="Scan only this host")
    parser.add_argument("-p", "--ports", help="Ports to scan, e.g. '22,80,443' or '1-1024'")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"Concurrent probes (default: {DEFAULT_WORKERS})")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Per-probe timeout in seconds")
    parser.add_argument("--no-resolve", action="store_true",
                        help="Skip reverse-DNS lookups for hostnames")
    add_json_flag(parser)
    args = parser.parse_args()

    try:
        ports = parse_ports(args.ports)
    except ValueError as exc:
        parser.error(str(exc))

    target = args.target or args.subnet
    if not target:
        detected = default_subnet()
        if detected is None:
            parser.error("No subnet given and this machine's subnet could not be detected.")
        target = str(detected)

    try:
        network = parse_subnet(target)
    except ValueError as exc:
        parser.error(str(exc))

    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if args.workers > 1024:
        parser.error("--workers above 1024 is unlikely to help and may be dropped by firewalls")

    if network.num_addresses > 8192:
        parser.error(f"{network} is too large; narrow the range or use a subnet mask")

    # A None timeout would make the probe sockets blocking, so an unreachable
    # host would hang until the OS gave up (~21s) instead of the 0.4s budget.
    # Never let None reach settimeout.
    if args.timeout is not None:
        port_timeout = args.timeout
    else:
        port_timeout = DEFAULT_PORT_TIMEOUT if ports else DEFAULT_HOST_TIMEOUT

    started = time.perf_counter()

    if ports:
        rows = sweep_ports(network, ports, args.workers, port_timeout, live=not json_requested(args))
        if not args.no_resolve:
            rows = resolve_hostnames(rows)
        duration = time.perf_counter() - started

        if json_requested(args):
            emit_json({
                "tool": "csweep", "version": __version__, "mode": "ports",
                "subnet": str(network), "ports": ports, "duration_s": round(duration, 2),
                "count": len(rows), "results": rows,
            })
            return 0

        if not rows:
            print(f"No open ports found on {network}.")
            return 0

        Console, Table, box, *_ = rich_toolkit()
        console = Console()
        table = Table(title=f"CBOX Port Sweep: {network}", box=box.SIMPLE_HEAVY, header_style="bold cyan")
        table.add_column("IP", style="bold bright_cyan")
        table.add_column("Port", justify="right", style="bold yellow")
        table.add_column("Service", style="green")
        table.add_column("Hostname", style="white")

        for row in rows:
            table.add_row(row["ip"], str(row["port"]), row["service"], row["hostname"] or "-")

        console.print(table)
        console.print(f"[dim]{len(rows)} open port(s) in {duration:.2f}s "
                      f"across {network.num_addresses} address(es).[/dim]")
        return 0

    rows = sweep_hosts(network, args.workers, port_timeout)
    if not args.no_resolve:
        rows = resolve_hostnames(rows)
    duration = time.perf_counter() - started

    if json_requested(args):
        emit_json({
            "tool": "csweep", "version": __version__, "mode": "hosts",
            "subnet": str(network), "duration_s": round(duration, 2),
            "count": len(rows), "hosts": rows,
        })
        return 0

    Console, Table, box, *_ = rich_toolkit()
    console = Console()

    table = Table(title=f"CBOX Host Sweep: {network}", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("IP Address", style="bold bright_cyan")
    table.add_column("Latency", justify="right", style="bold yellow")
    table.add_column("Hostname", style="white")

    for row in rows:
        table.add_row(row["ip"], f"{row['rtt_ms']:.1f} ms", row["hostname"] or "-")

    if rows:
        console.print(table)
    else:
        console.print("[yellow]No hosts responded. They may block ICMP; try a port sweep.[/yellow]")

    console.print(f"[dim]{len(rows)} live host(s) of {network.num_addresses} address(es) "
                  f"in {duration:.2f}s with {args.workers} workers.[/dim]")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
