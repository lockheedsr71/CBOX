import os
import sys
import socket
import argparse
import time
import psutil
import requests
from scapy.all import ARP, Ether, srp, IP, ICMP, sr1, conf

def get_rich_tools():
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.layout import Layout
    return Console, Table, box, Panel, Text, Align, Live, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Layout

def get_main_lan_info():
    try:
        default_gw = conf.route.route("0.0.0.0")[2]
        ip = conf.route.route("0.0.0.0")[1]
        iface = conf.route.route("0.0.0.0")[0]
        subnet = ".".join(ip.split('.')[:-1]) + ".0/24"
        return ip, subnet, iface
    except:
        for interface, addresses in psutil.net_if_addrs().items():
            for addr in addresses:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    return addr.address, ".".join(addr.address.split('.')[:-1]) + ".0/24", interface
    return "127.0.0.1", "127.0.0.0/24", "Unknown"

def get_mac_vendor(mac):
    try:
        response = requests.get(f"https://api.macvendors.com/{mac}", timeout=0.8)
        if response.status_code == 200:
            return response.text
    except: pass
    return "Generic Hardware"

def get_os_and_latency(ip):
    try:
        start_t = time.time()
        pkt = sr1(IP(dst=ip)/ICMP(), timeout=0.7, verbose=0)
        rtt = f"{(time.time() - start_t)*1000:.1f}ms"
        if pkt:
            ttl = pkt.ttl
            os_name = "Linux/IoT" if ttl <= 64 else "Windows" if ttl <= 128 else "Router/Switch"
            return os_name, rtt
    except: pass
    return "Unknown", "Timed Out"

def scan_ports_live(ip, port_range):
    Console, Table, box, Panel, Text, Align, Live, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Layout = get_rich_tools()
    console = Console()
    
    table = Table(box=box.DOUBLE_EDGE, expand=True, border_style="light_sky_blue1")
    table.add_column("Port", style="bold light_sky_blue1")
    table.add_column("Service", style="white")
    table.add_column("Status", style="bold green")

    start_port, end_port = map(int, port_range.split('-'))
    ports = range(start_port, end_port + 1)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        console=console,
        transient=True
    )
    
    # ترکیب جدول و پروگرس بار در یک چیدمان واحد برای جلوگیری از چشمک زدن
    layout = Layout()
    layout.split_column(
        Layout(name="table", ratio=4),
        Layout(name="prog", size=3)
    )

    task = progress.add_task(f"[cyan]Scanning {ip}...", total=len(ports))
    
    with Live(layout, refresh_per_second=10, screen=False):
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.05)
            result = sock.connect_ex((ip, port))
            if result == 0:
                try: service = socket.getservbyport(port)
                except: service = "Unknown"
                table.add_row(str(port), service, "[bold green]OPEN[/]")
            sock.close()
            
            progress.update(task, advance=1)
            layout["table"].update(Panel(table, title=f"Port Scan: {ip}", border_style="light_sky_blue1"))
            layout["prog"].update(Panel(progress, border_style="light_sky_blue1"))

def scan_network_live(subnet):
    Console, Table, box, Panel, Text, Align, Live, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Layout = get_rich_tools()
    console = Console()
    start_time = time.time()
    found_devices = 0
    
    table = Table(title=f"NetMAP Live Scan: {subnet}", box=box.DOUBLE_EDGE, expand=True, border_style="light_sky_blue1")
    table.add_column("IP Address", style="bold light_sky_blue1")
    table.add_column("MAC Address", style="white")
    table.add_column("System / OS", style="bold green")
    table.add_column("Latency", style="bold yellow", justify="right")
    table.add_column("Hardware / Vendor", style="bold white")

    prefix = subnet.split('/')[0].rsplit('.', 1)[0]
    
    with Live(table, refresh_per_second=4):
        for i in range(1, 255):
            target_ip = f"{prefix}.{i}"
            ans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=target_ip), timeout=0.15, verbose=0)[0]
            for sent, received in ans:
                found_devices += 1
                os_info, rtt = get_os_and_latency(target_ip)
                vendor = get_mac_vendor(received.hwsrc)
                table.add_row(received.psrc, received.hwsrc, os_info, rtt, vendor)

    duration = time.time() - start_time
    summary = Panel(
        Text.assemble(
            ("\n NETMAP SCAN COMPLETED", "bold light_sky_blue1"),
            (f"\n Devices Identified: ", "white"), (f"{found_devices}", "bold green"),
            (f"\n Scan Time:         ", "white"), (f"{duration:.2f}s", "bold yellow")
        ), title="Statistics", border_style="light_sky_blue1"
    )
    console.print(summary)

def main():
    Console, Table, box, Panel, Text, Align, Live, Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, Layout = get_rich_tools()
    console = Console()
    
    # بهبود بخش Help برای سوئیچ -p
    parser = argparse.ArgumentParser(
        description="CBOX NetMAP - Advanced Network Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nscn -s                      Scan your current local network subnet.
  nscn -t 192.168.1.5 -p 80-90 Scan ports 80 to 90 on a specific target IP.
  nscn -t 192.168.1.1 -p 445   Check if a single port (445) is open on the target.
        """
    )
    parser.add_argument("-s", "--scan", action="store_true", help="Scan current subnet live")
    parser.add_argument("-t", "--target", help="Target IP address for port scanning")
    parser.add_argument("-p", "--port", help="Port range (e.g., '80-443') or a single port (e.g., '22')")
    
    args = parser.parse_class = parser.parse_args()

    local_ip, def_subnet, iface = get_main_lan_info()

    header = Panel(
        Align.center(
            Text.assemble(
                ("CBOX NETSCAN tool by FOXNET ", "bold white on blue"),
                (f" Ver 1.0.0 ", "bold white"),
                (f"\nActive LAN: {iface} | IP: {local_ip}", "bold red")
            )
        ), border_style="bold white "
    )
    console.print(header)

    if args.scan:
        q = f"\n[bold light_sky_blue1]Enter Subnet (Default {def_subnet}): [/]"
        custom_input = console.input(q).strip()
        scan_network_live(custom_input if custom_input else def_subnet)
    elif args.target and args.port:
        # اگر کاربر فقط یک عدد وارد کرد (مثلا 80)، آن را به بازه 80-80 تبدیل کن
        p_range = args.port if "-" in args.port else f"{args.port}-{args.port}"
        scan_ports_live(args.target, p_range)
    else:
        parser.print_help()
 

if __name__ == "__main__":
    os.system('') 
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled.")