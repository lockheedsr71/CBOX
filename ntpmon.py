"""ntpmon - per-process network monitor dashboard."""

import argparse
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import msvcrt
except ImportError:  # pragma: no cover - the dashboard is Windows-only
    print("[CBOX] ntpmon requires Windows (msvcrt).")
    sys.exit(1)

from cbox_core import __version__
from cbox_core.colors import init_color
from cbox_core.console import MissingDependency, rich_toolkit, safe_glyphs
from cbox_core.netutil import geo_label

# CTRL+C is suppressed so the Live dashboard is not torn down mid-frame.
# ESC remains the documented exit key.
signal.signal(signal.SIGINT, lambda sig, frame: None)

conn_start_times = {}
closed_connections = {}

#: Cumulative counters, keyed by process, taken at the first successful sample.
#: psutil reports lifetime totals, so a delta is needed to show real throughput.
_io_baseline = {}


def monitor_process(target, interval=0.5):
    # rich_toolkit() returns:
    # Console, Table, box, Panel, Text, Align, Live, Progress,
    # SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Layout, Columns
    _, _, _, Panel, _, Align, Live, _, _, _, _, _, Layout, _ = rich_toolkit()

    start_time = time.time()
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="resources", size=9),
        Layout(name="footer", size=3),
    )

    with Live(layout, refresh_per_second=4, screen=True, transient=True):
        while True:
            if msvcrt.kbhit() and ord(msvcrt.getch()) == 27:  # ESC
                break

            target_procs = _find_processes(target)

            if not target_procs:
                layout["main"].update(
                    Align.center(f"[bold red]Process '{target}' not found.[/]")
                )
                layout["header"].update(Panel("", border_style="bright_blue"))
                layout["resources"].update(Panel("", border_style="yellow"))
                layout["footer"].update(Panel("", border_style="bright_magenta"))
                time.sleep(1)
                continue

            try:
                _render(layout, target, target_procs, start_time)
            except Exception:
                # A single bad refresh must not kill the dashboard; ESC still
                # works because it is checked before this block.
                pass

            time.sleep(interval)


def _find_processes(target):
    """Processes whose name or PID matches `target` (case-insensitive)."""
    import psutil

    wanted = target.lower()
    matches = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info.get("name") or ""
            if wanted in name.lower() or str(proc.info.get("pid")) == target:
                matches.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return matches


def _io_delta(proc):
    """Bytes written and read since the previous sample.

    `psutil.io_counters()` is a lifetime total, so the dashboard kept
    re-printing the same cumulative number instead of a rate. Take a delta
    against the first sample instead.
    """
    try:
        counters = proc.io_counters()
    except Exception:
        return 0, 0

    key = proc.pid
    current = (counters.write_bytes, counters.read_bytes)

    baseline = _io_baseline.get(key)
    if baseline is None or current < baseline:
        # First sample, or the process restarted (counters went backwards).
        _io_baseline[key] = current
        return 0, 0

    return current[0] - baseline[0], current[1] - baseline[1]


def _advance_io_baseline(proc):
    try:
        counters = proc.io_counters()
        _io_baseline[proc.pid] = (counters.write_bytes, counters.read_bytes)
    except Exception:
        _io_baseline.pop(proc.pid, None)


def _system_resources():
    """Host CPU, memory and disk usage for the dashboard footer panel."""
    import psutil

    memory = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage(psutil.disk_partitions(all=False)[0].mountpoint)
        disk_line = f"Disk  {disk.used / (1024 ** 3):>6.1f} / {disk.total / (1024 ** 3):>6.1f} GB  ({disk.percent:.0f}%)"
    except (IndexError, OSError, PermissionError):
        disk_line = "Disk  unavailable"

    # cpu_percent is stateful: the first call returns 0.0, so prime it once.
    psutil.cpu_percent(interval=None)

    return (
        f"CPU   {psutil.cpu_percent(interval=None):>5.1f}%   "
        f"RAM   {memory.percent:>5.1f}%  ({memory.used / (1024 ** 3):.1f} / "
        f"{memory.total / (1024 ** 3):.1f} GB)\n"
        f"{disk_line}"
    )


def _top_processes(target_procs, limit=5):
    """The heaviest of the monitored processes by resident memory."""
    import psutil

    rows = []
    for proc in target_procs:
        try:
            with proc.oneshot():
                rows.append({
                    "pid": proc.pid,
                    "name": proc.name(),
                    "rss_mb": proc.memory_info().rss / (1024 ** 2),
                    "threads": proc.num_threads(),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
            continue

    rows.sort(key=lambda row: row["rss_mb"], reverse=True)
    return rows[:limit]


def _render(layout, target, processes, start_time):
    _, Table, box, Panel, Text, Align, _, _, _, _, _, _, _, Columns = rich_toolkit()

    uptime = time.strftime("%H:%M:%S", time.gmtime(int(time.time() - start_time)))
    header_text = Text.assemble(
        (" CBOX NETWORK PROCESS MONITOR ", "bold white on blue"),
        (f"                  Monitoring: {target.upper()} ", "bold bright_yellow"),
        (f" | Uptime: {uptime} ", "bold bright_yellow"),
    )
    version_text = Text(f"                     Ver {__version__}", style="bold white")
    layout["header"].update(
        Panel(Columns([header_text, Align.right(version_text)]), border_style="bright_blue")
    )

    table = Table(box=box.SIMPLE_HEAVY, expand=True, header_style="bold cyan")
    table.add_column("PID", width=8, style="dim")
    table.add_column("Proto", width=6, justify="center")
    table.add_column("Remote Address", width=25, style="yellow")
    table.add_column("Location", width=25, style="cyan")
    table.add_column("Status", width=12)
    table.add_column("Duration", width=10, justify="right")

    window_sent = window_recv = 0
    active_ids = []
    now = time.time()

    for proc in processes:
        written, read = _io_delta(proc)
        window_sent += written
        window_recv += read

        try:
            connections = proc.net_connections(kind="inet")
        except Exception:
            # AccessDenied on other users' processes is expected without admin.
            connections = []

        for conn in connections:
            if not conn.raddr:
                continue
            cid = f"{conn.raddr.ip}:{conn.raddr.port}"
            active_ids.append(cid)
            conn_start_times.setdefault(cid, now)
            closed_connections.pop(cid, None)

            table.add_row(
                str(proc.pid),
                "TCP" if conn.type == 1 else "UDP",
                cid,
                geo_label(conn.raddr.ip),
                f"[green]{conn.status}[/]",
                f"{int(now - conn_start_times[cid])}s",
            )

    # Recently closed connections stay visible for a few seconds.
    for cid in [c for c in conn_start_times if c not in active_ids]:
        closed_connections[cid] = now
        del conn_start_times[cid]
    for cid, closed_at in list(closed_connections.items()):
        if now - closed_at < 5:
            table.add_row("---", "---", cid, "Disconnected", "[bold red]CLOSED[/]", "-", style="red")
        else:
            del closed_connections[cid]

    layout["main"].update(Panel(table, border_style="dim"))

    resources = Table.grid(padding=(0, 2))
    resources.add_column(justify="left", ratio=3)
    resources.add_column(justify="left", ratio=2)
    resources.add_row(
        _system_resources(),
        _resource_table(_top_processes(processes), box, Panel),
    )
    layout["resources"].update(Panel(resources, title="Resources", border_style="yellow"))

    site_text = Text("https://software.foxnet.ir", style="bold link blue")
    # Arrows are not encodable on a legacy code page console.
    glyphs = safe_glyphs()
    stats_text = Text.assemble(
        ("                     NET I/O: ", "bold white"),
        (f"{glyphs['up']} {window_sent / 1024:.1f}KB ", "red"),
        ("  ", ""), (f"{glyphs['down']} {window_recv / 1024:.1f}KB ", "blue"),
        (" (last interval)", "dim"),
    )
    layout["footer"].update(
        Panel(
            Columns([
                site_text,
                Align.center(stats_text),
                Align.right(Text("[ESC] Exit", style="bold white")),
            ]),
            border_style="bright_magenta",
        )
    )

    # Advance the baseline last, so this frame reports the delta across the
    # whole interval rather than a partial one.
    for proc in processes:
        _advance_io_baseline(proc)


def _resource_table(rows, box, Panel):
    Table = rich_toolkit()[1]

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow",
                  expand=True, padding=(0, 1))
    table.add_column("PID", justify="right", style="dim", width=7)
    table.add_column("Process", style="white")
    table.add_column("RSS", justify="right", style="bright_cyan", width=9)
    table.add_column("Thr", justify="right", style="dim", width=5)

    if not rows:
        table.add_row("-", "no data", "-", "-")
        return table

    for row in rows:
        table.add_row(str(row["pid"]), row["name"],
                      f"{row['rss_mb']:.0f}M", str(row["threads"]))
    return table


def main():
    parser = argparse.ArgumentParser(description="CBOX ntpmon - Network Process Monitor")
    parser.add_argument("target", help="Process name or PID to monitor")
    parser.add_argument("-i", "--interval", type=float, default=0.5,
                        help="Refresh interval in seconds")
    args = parser.parse_args()

    init_color()
    monitor_process(args.target, max(args.interval, 0.05))


if __name__ == "__main__":
    try:
        main()
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
