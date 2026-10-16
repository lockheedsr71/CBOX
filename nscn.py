"""nscn - LAN and port scanner (ARP discovery + TCP port scan)."""

import argparse
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.colors import Colors, init_color
from cbox_core.console import MissingDependency, rich_toolkit
from cbox_core.jsonout import add_json_flag, emit_json, json_requested

# scapy touches the packet driver at import time, so it has to be imported
# lazily and only after we know Npcap is present.
ARP = Ether = srp = IP = ICMP = sr1 = conf = None


def _load_scapy():
    global ARP, Ether, srp, IP, ICMP, sr1, conf
    if ARP is not None:
        return True
    try:
        from scapy.all import ARP as _ARP
        from scapy.all import ICMP as _ICMP
        from scapy.all import IP as _IP
        from scapy.all import Ether as _Ether
        from scapy.all import conf as _conf
        from scapy.all import sr1 as _sr1
        from scapy.all import srp as _srp
    except ImportError as exc:
        raise MissingDependency("scapy") from exc
    except Exception as exc:
        # ImportError is not the only failure: a missing Npcap driver makes
        # scapy raise a RuntimeError/Scapy_Exception on import.
        print(
            f"{Colors.RED}[CBOX] scapy could not start: {exc}{Colors.RESET}\n"
            f"  On Windows, raw sockets need Npcap: https://npcap.com\n"
            f"  Install it, then run 'pip install scapy' and try again."
        )
        sys.exit(1)

    ARP, Ether, srp, IP, ICMP, sr1, conf = _ARP, _Ether, _srp, _IP, _ICMP, _sr1, _conf
    return True


def is_admin():
    """True when the process holds elevated privileges."""
    try:
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception:
        return hasattr(os, "geteuid") and os.geteuid() == 0


def preflight():
    """Abort with an actionable message when the scanner cannot run."""
    init_color()
    _load_scapy()

    if os.name == "nt" and not is_admin():
        print(
            f"{Colors.RED}[CBOX] Administrator privileges are required.{Colors.RESET}\n"
            f"  ARP discovery and raw ICMP need an elevated shell.\n"
            f"  Right-click the terminal and choose 'Run as administrator'."
        )
        sys.exit(1)


def get_main_lan_info():
    """Local IP, default /24 subnet and interface name."""
    import psutil

    try:
        _route = conf.route.route("0.0.0.0")
        ip, iface = _route[1], _route[0]
        if ip and ip != "0.0.0.0":
            return ip, f"{_prefix(ip)}.0/24", iface
    except Exception:
        pass

    for interface, addresses in psutil.net_if_addrs().items():
        for addr in addresses:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                return addr.address, f"{_prefix(addr.address)}.0/24", interface

    return "127.0.0.1", "127.0.0.0/24", "Unknown"


def _prefix(ip):
    return ".".join(ip.split(".")[:-1])


def get_mac_vendor(mac):
    """Best-effort OUI lookup; falls back to a generic label when offline."""
    try:
        import requests

        response = requests.get(f"https://api.macvendors.com/{mac}", timeout=0.8)
        if response.status_code == 200:
            return response.text.strip()
    except Exception:
        pass
    return "Generic Hardware"


def get_os_and_latency(ip):
    """Guess the remote OS from the reply TTL and measure the RTT."""
    try:
        start = time.time()
        packet = sr1(IP(dst=ip) / ICMP(), timeout=0.7, verbose=0)
        rtt = f"{(time.time() - start) * 1000:.1f}ms"
        if packet:
            ttl = packet.ttl
            if ttl <= 64:
                os_name = "Linux/IoT"
            elif ttl <= 128:
                os_name = "Windows"
            else:
                os_name = "Router/Switch"
            return os_name, rtt
    except Exception:
        pass
    return "Unknown", "Timed Out"


DEFAULT_WORKERS = 128
DEFAULT_PORT_TIMEOUT = 0.4


def scan_ports(ip, ports, workers=DEFAULT_WORKERS, timeout=DEFAULT_PORT_TIMEOUT, live=True):
    """TCP connect scan of `ports` on `ip`, run concurrently.

    The original walked the range one socket at a time with a 50 ms timeout,
    so a 1-65535 scan took well over an hour. Concurrency turns the same work
    into a few seconds; the per-probe timeout stays small so closed ports
    still cost little.
    """
    (
        Console, Table, box, Panel, Text, Align, Live, Progress,
        SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Layout, Columns,
    ) = rich_toolkit()

    table = Table(box=box.DOUBLE_EDGE, expand=True, border_style="light_sky_blue1")
    table.add_column("Port", style="bold light_sky_blue1")
    table.add_column("Service", style="white")
    table.add_column("Status", style="bold green")

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        console=Console(),
        transient=True,
    )

    # One layout holding both the table and the bar avoids flicker.
    layout = Layout()
    layout.split_column(Layout(name="table", ratio=4), Layout(name="prog", size=3))

    task = progress.add_task(f"[cyan]Scanning {ip}...", total=len(ports))
    open_ports = []

    def record(port):
        open_ports.append(port)
        try:
            service = socket.getservbyport(port)
        except OSError:
            service = "Unknown"
        table.add_row(str(port), service, "[bold green]OPEN[/]")

    if live:
        with Live(layout, refresh_per_second=10, screen=False), \
                ThreadPoolExecutor(max_workers=min(workers, max(len(ports), 1))) as pool:
            futures = {pool.submit(_probe_port, ip, port, timeout): port for port in ports}
            for future in as_completed(futures):
                if future.result():
                    record(futures[future])

                progress.update(task, advance=1)
                layout["table"].update(Panel(table, title=f"Port Scan: {ip}",
                                             border_style="light_sky_blue1"))
                layout["prog"].update(Panel(progress, border_style="light_sky_blue1"))
    else:
        with ThreadPoolExecutor(max_workers=min(workers, max(len(ports), 1))) as pool:
            futures = {pool.submit(_probe_port, ip, port, timeout): port for port in ports}
            for future in as_completed(futures):
                if future.result():
                    record(futures[future])
                progress.update(task, advance=1)

    open_ports.sort()
    return open_ports


def _probe_port(ip, port, timeout):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((ip, port)) == 0
    except OSError:
        return False
    finally:
        sock.close()


def parse_port_range(spec):
    """'80', '80-443' -> (start, end), with validation."""
    try:
        if "-" in spec:
            start_text, end_text = spec.split("-", 1)
            start, end = int(start_text), int(end_text)
        else:
            start = end = int(spec)
    except ValueError as exc:
        raise ValueError(f"Invalid port specification: '{spec}' (use '80' or '80-443')") from exc

    if not (1 <= start <= 65535 and 1 <= end <= 65535):
        raise ValueError("Ports must be between 1 and 65535")
    if start > end:
        start, end = end, start
    return start, end


def scan_ports_live(ip, port_range, workers=DEFAULT_WORKERS, timeout=DEFAULT_PORT_TIMEOUT):
    start_port, end_port = parse_port_range(port_range)
    return scan_ports(ip, range(start_port, end_port + 1), workers, timeout)


def scan_network_live(subnet, workers=DEFAULT_WORKERS, timeout=DEFAULT_PORT_TIMEOUT):
    (
        Console, Table, box, Panel, Text, Align, Live, Progress,
        SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Layout, Columns,
    ) = rich_toolkit()
    console = Console()

    start_time = time.time()
    found = []

    table = Table(title=f"NetMAP Live Scan: {subnet}", box=box.DOUBLE_EDGE, expand=True,
                  border_style="light_sky_blue1")
    table.add_column("IP Address", style="bold light_sky_blue1")
    table.add_column("MAC Address", style="white")
    table.add_column("System / OS", style="bold green")
    table.add_column("Latency", style="bold yellow", justify="right")
    table.add_column("Hardware / Vendor", style="bold white")

    prefix = subnet.split("/")[0].rsplit(".", 1)[0]

    with Live(table, refresh_per_second=4):
        # Probe the whole subnet concurrently, then enrich each hit. The
        # serial version took 0.15s x 254 = ~38s of pure ARP waiting even
        # when every host answered immediately.
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_arp_probe, f"{prefix}.{host}", timeout): host
                for host in range(1, 255)
            }
            hits = []
            for future in as_completed(futures):
                result = future.result()
                if result:
                    hits.append(result)

        for target_ip, mac in sorted(hits):
            os_info, rtt = get_os_and_latency(target_ip)
            found.append({
                "ip": target_ip, "mac": mac, "os": os_info,
                "rtt": rtt, "vendor": get_mac_vendor(mac),
            })
            table.add_row(target_ip, mac, os_info, rtt, found[-1]["vendor"])

    duration = time.time() - start_time
    console.print(Panel(
        Text.assemble(
            ("\n NETMAP SCAN COMPLETED", "bold light_sky_blue1"),
            ("\n Devices Identified: ", "white"), (str(len(found)), "bold green"),
            ("\n Scan Time:         ", "white"), (f"{duration:.2f}s", "bold yellow"),
        ),
        title="Statistics", border_style="light_sky_blue1",
    ))
    return found


def _arp_probe(target_ip, timeout):
    """Return (ip, mac) when the host answers ARP, else None."""
    try:
        answered, _ = srp(
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_ip),
            timeout=timeout, verbose=0, retry=0,
        )
    except Exception:
        return None

    for _, received in answered:
        return received.psrc, received.hwsrc
    return None


def main():
    preflight()

    Console, Table, box, Panel, Text, Align, Live, Progress, SpinnerColumn, TextColumn, \
        BarColumn, TaskProgressColumn, Layout, Columns = rich_toolkit()
    console = Console()

    parser = argparse.ArgumentParser(
        description="CBOX NetMAP - Advanced Network Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nscn -s                        Scan the current local subnet.
  nscn -t 192.168.1.5 -p 80-90   Scan ports 80 to 90 on a target.
  nscn -t 192.168.1.1 -p 445     Check a single port on the target.

Requires Administrator and Npcap on Windows.
""",
    )
    parser.add_argument("-s", "--scan", action="store_true", help="Scan the current subnet live")
    parser.add_argument("-t", "--target", help="Target IP address for port scanning")
    parser.add_argument("-p", "--port", help="Port range (e.g. '80-443') or a single port (e.g. '22')")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"Concurrent probes (default: {DEFAULT_WORKERS})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_PORT_TIMEOUT,
                        help="Per-probe timeout in seconds")
    add_json_flag(parser, "Emit machine-readable JSON instead of a table")
    args = parser.parse_args()

    local_ip, default_subnet, iface = get_main_lan_info()

    if not json_requested(args):
        console.print(Panel(
            Align.center(Text.assemble(
                ("CBOX NETSCAN tool by FOXNET ", "bold white on blue"),
                (f" Ver {__version__} ", "bold white"),
                (f"\nActive LAN: {iface} | IP: {local_ip}", "bold red"),
            )),
            border_style="bold white",
        ))

    if args.scan:
        if json_requested(args):
            subnet = args.target or default_subnet
        else:
            custom = console.input(
                f"\n[bold light_sky_blue1]Enter Subnet (Default {default_subnet}): [/]"
            ).strip()
            subnet = custom or default_subnet

        found = scan_network_live(subnet, args.workers, args.timeout)
        if json_requested(args):
            emit_json({
                "tool": "nscn", "version": __version__, "mode": "subnet",
                "subnet": subnet, "interface": iface, "local_ip": local_ip,
                "count": len(found), "devices": found,
            })
        return 0

    if args.target and args.port:
        open_ports = scan_ports_live(args.target, args.port, args.workers, args.timeout)
        if json_requested(args):
            emit_json({
                "tool": "nscn", "version": __version__, "mode": "ports",
                "target": args.target, "count": len(open_ports),
                "open_ports": open_ports,
            })
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled.")
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
