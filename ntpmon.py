import psutil
import time
import os
import sys
import argparse
import requests
import msvcrt
import signal

def get_rich_tools():
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    return Console, Table, box, Live, Panel, Layout, Text, Align, Columns

# مسدود کردن CTRL+C
signal.signal(signal.SIGINT, lambda sig, frame: None)

geo_cache = {}
conn_start_times = {}
closed_connections = {}

def get_location(ip, cache):
    if ip in ["127.0.0.1", "::1"] or ip.startswith("192.168."):
        return "Local Network"
    if ip in cache:
        return cache[ip]
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city", timeout=0.5).json()
        location = f"{response.get('country', 'Unknown')}, {response.get('city', '')}"
        cache[ip] = location
        return location
    except: return "Unknown"

def monitor_process(target, interval):
    Console, Table, box, Live, Panel, Layout, Text, Align, Columns = get_rich_tools()
    console = Console()
    start_time = time.time()
    
    # تنظیمات لایه‌بندی داشبورد
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )

    with Live(layout, refresh_per_second=4, screen=True, transient=True) as live:
        while True:
            # خروج با ESC
            if msvcrt.kbhit():
                if ord(msvcrt.getch()) == 27: break

            # پیدا کردن تمام زیرپروسه‌ها
            target_procs = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if target.lower() in proc.info['name'].lower() or str(proc.info['pid']) == target:
                        target_procs.append(proc)
                except: continue

            if not target_procs:
                layout["main"].update(Align.center(f"[bold red]Process '{target}' not found.[/]"))
                time.sleep(1)
                continue

            try:
                # 1. بخش هدر (Header)
                uptime = time.strftime('%H:%M:%S', time.gmtime(int(time.time() - start_time)))
                header_text = Text.assemble(
                    (f" CBOX NETWORK PROCESS MONITOR ", "bold white on blue"),
                    (f"                  Monitoring: {target.upper()} ", "bold bright_yellow"),
                    (f" | Uptime: {uptime} ", "bold bright_yellow")
                )
                # ورژن در گوشه سمت راست
                version_text = Text(f"                     Ver 1.0.0", style="bold white")
                layout["header"].update(Panel(
                    Columns([header_text, Align.right(version_text)]),
                    border_style="bright_blue"
                ))

                # 2. بخش اصلی (Table)
                table = Table(box=box.SIMPLE_HEAVY, expand=True, header_style="bold cyan")
                table.add_column("PID", width=8, style="dim")
                table.add_column("Proto", width=6, justify="center")
                table.add_column("Remote Address", width=25, style="yellow")
                table.add_column("Location", width=25, style="cyan")
                table.add_column("Status", width=12)
                table.add_column("Duration", width=10, justify="right")

                total_sent, total_recv, active_ids = 0, 0, []
                now = time.time()

                for p in target_procs:
                    try:
                        io = p.io_counters()
                        total_sent += io.write_bytes
                        total_recv += io.read_bytes
                        for conn in p.connections(kind='inet'):
                            if not conn.raddr: continue
                            cid = f"{conn.raddr.ip}:{conn.raddr.port}"
                            active_ids.append(cid)
                            if cid not in conn_start_times: conn_start_times[cid] = now
                            if cid in closed_connections: del closed_connections[cid]
                            
                            table.add_row(
                                str(p.pid), "TCP" if conn.type == 1 else "UDP",
                                cid, get_location(conn.raddr.ip, geo_cache),
                                f"[green]{conn.status}[/]", f"{int(now - conn_start_times[cid])}s"
                            )
                    except: continue

                # مدیریت قطع شده‌ها (قرمز)
                for cid in list(conn_start_times.keys()):
                    if cid not in active_ids:
                        closed_connections[cid] = now
                        del conn_start_times[cid]
                for cid, c_time in list(closed_connections.items()):
                    if now - c_time < 5:
                        table.add_row("---", "---", cid, "Disconnected", "[bold red]CLOSED[/]", "-", style="red")
                    else: del closed_connections[cid]

                layout["main"].update(Panel(table, border_style="dim"))

                # 3. بخش فوتر (Footer)
                # آدرس سایت سمت چپ، آمار وسط، کلید خروج سمت راست
                site_text = Text("https://software.foxnet.ir", style="bold link blue")
                stats_text = Text.assemble(
                    ("                     SENT: ", "bold white"), (f"{total_sent/(1024*1024):.2f}MB ", "red"),
                    (" RECV: ", "bold white"), (f"{total_recv/(1024*1024):.2f}MB ", "blue")
                )
                exit_hint = Text("                       [ESC] Exit", style="bold white")
                
                layout["footer"].update(Panel(
                    Columns([site_text, Align.center(stats_text), Align.right(exit_hint)]),
                    border_style="bright_magenta"
                ))

                time.sleep(interval)
            except: break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("-i", "--interval", type=float, default=0.5)
    args = parser.parse_args()
    os.system('') 
    monitor_process(args.target, args.interval)