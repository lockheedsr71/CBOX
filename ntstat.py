import psutil
import socket
import os
import sys
import argparse

def get_rich_tools():
    from rich.console import Console
    from rich.table import Table
    from rich import box
    return Console, Table, box

def get_port_stats():
    # تنظیم پارامترها و راهنمای لاتین
    parser = argparse.ArgumentParser(description="CBOX Network Statistics Tool", add_help=True)
    parser.add_argument("-p", "--proto", choices=['tcp', 'udp'], help="Filter by protocol (tcp/udp)")
    parser.add_argument("-s", "--status", help="Filter by status (e.g., ESTABLISHED, LISTEN, CLOSE_WAIT)")
    parser.add_argument("-src", "--source", help="Filter by source (local) IP")
    parser.add_argument("-dst", "--dest", help="Filter by destination (remote) IP")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show more details (Family, Type)")
    
    args = parser.parse_args()

    # دریافت تمامی اتصالات
    kind = 'inet'
    if args.proto == 'tcp': kind = 'tcp'
    elif args.proto == 'udp': kind = 'udp'
    
    connections = psutil.net_connections(kind=kind)
    
    # بارگذاری ابزارهای گرافیکی
    Console, Table, box = get_rich_tools()
    console = Console()
    
    table = Table(title="CBOX Advanced Network Monitor", box=box.SIMPLE_HEAVY, header_style="bold magenta")
    
    table.add_column("Proto", justify="center", style="cyan")
    table.add_column("Local Address", style="white")
    table.add_column("Remote Address", style="yellow")
    table.add_column("Status", justify="center")
    
    if args.verbose:
        table.add_column("Family", justify="center", style="dim")
        table.add_column("Interface", style="dim")

    table.add_column("PID", justify="right", style="green")
    table.add_column("Process Name", style="bold blue")

    for conn in connections:
        # فیلتر بر اساس وضعیت
        if args.status and args.status.upper() != conn.status:
            continue
            
        # فیلتر بر اساس IP مبدا و مقصد
        l_ip = conn.laddr.ip
        r_ip = conn.raddr.ip if conn.raddr else None
        
        if args.source and args.source not in l_ip: continue
        if args.dest and (not r_ip or args.dest not in r_ip): continue

        # تعیین پروتکل
        proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
        
        # فرمت‌دهی آدرس‌ها
        l_addr = f"{l_ip}:{conn.laddr.port}"
        r_addr = f"{r_ip}:{conn.raddr.port}" if r_ip else "*-*-*"
        
        # رنگ‌بندی وضعیت
        status = conn.status
        status_color = "green" if status == "ESTABLISHED" else "yellow"
        if status == "LISTEN": status_color = "bright_blue"
        if status == "CLOSE_WAIT" or status == "TIME_WAIT": status_color = "red"
        
        # اطلاعات پردازش
        try:
            process = psutil.Process(conn.pid)
            p_name = process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            p_name = "N/A"

        # ساخت ردیف بر اساس سوئیچ verbose
        row_data = [
            proto,
            l_addr,
            r_addr,
            f"[{status_color}]{status}[/]"
        ]
        
        if args.verbose:
            row_data.append("IPv4" if conn.family == socket.AF_INET else "IPv6")
            row_data.append(str(conn.fd) if hasattr(conn, 'fd') else "-")

        row_data.extend([str(conn.pid) if conn.pid else "0", p_name])
        table.add_row(*row_data)

    console.print(table)

if __name__ == "__main__":
    os.system('') # فعال‌سازی رنگ در ویندوز
    get_port_stats()