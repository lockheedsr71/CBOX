"""cport - listening ports with the owning process resolved."""

import argparse
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.console import MissingDependency, rich_toolkit
from cbox_core.jsonout import add_json_flag, emit_json, json_requested

#: Ports worth naming up front; everything else shows the numeric service or "-".
WELL_KNOWN = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
    80: "http", 110: "pop3", 111: "rpcbind", 135: "msrpc", 139: "netbios-ssn",
    143: "imap", 389: "ldap", 443: "https", 445: "microsoft-ds",
    465: "smtps", 514: "syslog", 587: "submission", 631: "ipp",
    993: "imaps", 995: "pop3s", 1433: "mssql", 1521: "oracle",
    3306: "mysql", 3389: "rdp", 5432: "postgresql", 5900: "vnc",
    6379: "redis", 8080: "http-alt", 8443: "https-alt", 9200: "elasticsearch",
}

#: Default view: the wildcard binds (reachable from anywhere) plus loopback.
#: Binds to one specific LAN address are the least interesting, so `--all` adds
#: those. `0.0.0.0` and `::` are the ones worth seeing, which is why they are
#: listed here despite not being loopback.
DEFAULT_BINDS = {"127.0.0.1", "::1", "0.0.0.0", "::"}
WILDCARD_BINDS = {"0.0.0.0", "::"}


def service_name(port):
    if port in WELL_KNOWN:
        return WELL_KNOWN[port]
    try:
        return socket.getservbyport(port)
    except OSError:
        return "-"


def collect(proto_filter=None, port_filter=None, include_udp=False):
    """Return every listening socket as a list of row dicts.

    `psutil.net_connections` needs Administrator to see other users' sockets,
    and raises AccessDenied rather than returning a partial list; that is
    reported to the caller instead of silently yielding nothing.
    """
    import psutil

    kind = {"tcp": "tcp", "udp": "udp"}.get(proto_filter, "tcp")
    rows = []

    for conn in psutil.net_connections(kind=kind):
        if conn.status not in ("LISTEN", "NONE"):
            continue
        if kind == "tcp" and conn.status != "LISTEN":
            continue

        port = getattr(conn.laddr, "port", None)
        if port is None:
            continue
        if port_filter and port not in port_filter:
            continue

        bind = getattr(conn.laddr, "ip", None) or "*"
        rows.append({
            "proto": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
            "bind": bind,
            "port": port,
            "service": service_name(port),
            "pid": conn.pid or 0,
            "process": _process_name(psutil, conn.pid),
            # '*' and 0.0.0.0 listen on every interface; anything else is
            # reachable only from that address.
            "exposure": "all" if bind in WILDCARD_BINDS else "specific",
        })

    rows.sort(key=lambda row: (row["proto"], row["port"]))
    return rows


def _process_name(psutil, pid):
    if not pid:
        return "-"
    try:
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "N/A"


def parse_port_filter(spec):
    """'80', '80-443', '80,443,8080' -> set of ports, or None for 'all'."""
    if not spec:
        return None
    wanted = set()
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
            wanted.update(range(min(start, end), max(start, end) + 1))
        else:
            try:
                wanted.add(int(chunk))
            except ValueError as exc:
                raise ValueError(f"Invalid port: '{chunk}'") from exc
    return wanted or None


def main():
    parser = argparse.ArgumentParser(
        description=f"CBOX cport {__version__} - Listening ports and their owning process",
    )
    parser.add_argument("-p", "--proto", choices=["tcp", "udp"], default="tcp",
                        help="Protocol to inspect (default: tcp)")
    parser.add_argument("-P", "--ports", help="Only these ports, e.g. '80', '80-443' or '22,3389'")
    parser.add_argument("-a", "--all", action="store_true",
                        help="Include ports bound to a specific address (default: local only)")
    add_json_flag(parser)
    args = parser.parse_args()

    try:
        port_filter = parse_port_filter(args.ports)
    except ValueError as exc:
        parser.error(str(exc))

    import psutil

    elevated = False
    try:
        psutil.net_connections(kind="tcp")
    except psutil.AccessDenied:
        elevated = True

    try:
        rows = collect(args.proto, port_filter)
    except psutil.AccessDenied:
        print("Access denied. Run as Administrator to see other users' sockets.")
        return 1

    if not args.all:
        rows = [row for row in rows if row["bind"] in DEFAULT_BINDS]

    if json_requested(args):
        emit_json({
            "tool": "cport",
            "version": __version__,
            "elevated": elevated,
            "count": len(rows),
            "ports": rows,
        })
        return 0

    if not rows:
        print("No listening sockets matched the given filters.")
        return 0

    Console, Table, box, *_ = rich_toolkit()
    console = Console()

    table = Table(title="CBOX Listening Ports", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Proto", justify="center", style="cyan")
    table.add_column("Bind Address", style="white")
    table.add_column("Port", justify="right", style="bold yellow")
    table.add_column("Service", style="green")
    table.add_column("PID", justify="right", style="dim")
    table.add_column("Process", style="bold blue")

    for row in rows:
        # A wildcard bind is red: it is reachable from outside this machine.
        wildcard = row["exposure"] == "all"
        style = "red" if wildcard else "white"
        table.add_row(row["proto"], f"[{style}]{row['bind']}[/]", str(row["port"]),
                      row["service"], str(row["pid"]), row["process"])

    console.print(table)

    exposed = [row for row in rows if row["exposure"] == "all"]
    if exposed and not args.all:
        console.print(
            f"[yellow]{len(exposed)} port(s) bind all interfaces; "
            f"use --all to list them.[/]"
        )
    if not elevated:
        console.print("[dim]Run as Administrator to include other users' sockets.[/]")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
