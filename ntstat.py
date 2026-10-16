"""ntstat - socket table with owning process details."""

import argparse
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.console import MissingDependency, rich_toolkit
from cbox_core.jsonout import add_json_flag, emit_json, json_requested

STATUS_COLORS = {
    "ESTABLISHED": "green",
    "LISTEN": "bright_blue",
    "CLOSE_WAIT": "red",
    "TIME_WAIT": "red",
    "SYN_SENT": "yellow",
}


def get_port_stats():
    import psutil

    parser = argparse.ArgumentParser(description="CBOX ntstat - Network Socket Statistics")
    parser.add_argument("-p", "--proto", choices=["tcp", "udp"], help="Filter by protocol")
    parser.add_argument("-s", "--status", help="Filter by status (e.g. ESTABLISHED, LISTEN)")
    parser.add_argument("-src", "--source", help="Filter by local IP substring")
    parser.add_argument("-dst", "--dest", help="Filter by remote IP substring")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show family and socket handle")
    add_json_flag(parser, "Emit machine-readable JSON instead of a table")

    args = parser.parse_args()

    kind = {"tcp": "tcp", "udp": "udp"}.get(args.proto, "inet")

    try:
        connections = psutil.net_connections(kind=kind)
    except psutil.AccessDenied:
        message = "Access denied. Run as Administrator to see other users' sockets."
        if json_requested(args):
            emit_json({"tool": "ntstat", "version": __version__,
                       "error": message, "count": 0, "connections": []})
        else:
            print(message)
        return 1

    Console, Table, box, *_ = rich_toolkit()
    console = Console()

    table = Table(title="CBOX Advanced Network Monitor", box=box.SIMPLE_HEAVY, header_style="bold magenta")
    table.add_column("Proto", justify="center", style="cyan")
    table.add_column("Local Address", style="white")
    table.add_column("Remote Address", style="yellow")
    table.add_column("Status", justify="center")

    if args.verbose:
        table.add_column("Family", justify="center", style="dim")
        table.add_column("Handle", style="dim")

    table.add_column("PID", justify="right", style="green")
    table.add_column("Process Name", style="bold blue")

    matched = 0
    rows = []
    for conn in connections:
        if args.status and args.status.upper() != conn.status:
            continue

        # UDP sockets are unbound until they are used, so laddr can be None
        # and conn.fd can be -1. Both used to raise AttributeError here.
        l_addr = _format_addr(conn.laddr)
        r_addr = _format_addr(conn.raddr) or "*-*-*"

        if args.source and args.source not in l_addr:
            continue
        if args.dest and args.dest not in r_addr:
            continue

        proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
        color = STATUS_COLORS.get(conn.status, "yellow")
        p_name = _process_name(conn.pid)

        row = [proto, l_addr, r_addr, f"[{color}]{conn.status}[/]"]

        entry = {
            "proto": proto,
            "status": conn.status,
            "local": l_addr,
            "remote": r_addr if r_addr != "*-*-*" else None,
            "pid": conn.pid or 0,
            "process": p_name,
        }

        if args.verbose:
            family = "IPv4" if conn.family == socket.AF_INET else "IPv6"
            handle = str(conn.fd) if conn.fd not in (None, -1) else None
            row.append(family)
            row.append(handle if handle else "-")
            entry["family"] = family
            entry["handle"] = handle

        row.extend([str(conn.pid) if conn.pid else "0", p_name])
        table.add_row(*row)
        rows.append(entry)
        matched += 1

    if json_requested(args):
        emit_json({
            "tool": "ntstat", "version": __version__, "filters": {
                "proto": args.proto, "status": args.status,
                "source": args.source, "dest": args.dest,
            },
            "count": matched, "connections": rows,
        })
        return 0

    console.print(table)

    if matched == 0:
        console.print("[yellow]No sockets matched the given filters.[/]")
    return 0


def _format_addr(addr):
    """`ip:port` for a bound address, '-' when the socket is unbound."""
    if addr is None:
        return "-"
    ip = getattr(addr, "ip", None)
    port = getattr(addr, "port", None)
    if ip is None and port is None:
        return "-"
    if port is None:
        return str(ip)
    return f"{ip}:{port}"


def _process_name(pid):
    import psutil

    if not pid:
        return "-"
    try:
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return "N/A"


if __name__ == "__main__":
    try:
        sys.exit(get_port_stats() or 0)
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
