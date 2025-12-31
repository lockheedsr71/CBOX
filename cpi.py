import subprocess
import platform
import re
import time
import argparse
import sys
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

def get_ping_data(target, ttl=None, buffer_size=None):
    """اجرای پینگ با تنظیمات TTL و Buffer Size"""
    param_n = "-n" if platform.system().lower() == "windows" else "-c"
    
    # ساخت دستور پایه
    command = ["ping", param_n, "1"]
    
    # افزودن TTL (در ویندوز سوییچ -i است اما اینجا برای تداخل نداشتن از ورودی استفاده میکنیم)
    if ttl:
        # در ویندوز پینگ واقعی از -i برای TTL استفاده می‌کند
        command.extend(["-i", str(ttl)])
    
    # افزودن Buffer Size (در ویندوز سوییچ -l است)
    if buffer_size:
        command.extend(["-l", str(buffer_size)])
        
    command.append(target)
    
    try:
        output = subprocess.run(command, capture_output=True, text=True, timeout=5).stdout
        time_match = re.search(r"time[=<](\d+)ms", output)
        ttl_res_match = re.search(r"TTL=(\d+)", output, re.IGNORECASE)
        
        if time_match:
            ms = int(time_match.group(1))
            res_ttl = ttl_res_match.group(1) if ttl_res_match else "N/A"
            color = Fore.GREEN if ms < 50 else Fore.YELLOW if ms < 150 else Fore.RED
            return {"status": "OK", "ms": ms, "ttl": res_ttl, "color": color, "text": f"{ms:>3}ms (TTL={res_ttl})"}
        return {"status": "TIMEOUT", "text": "Request Timed Out!"}
    except Exception as e:
        return {"status": "ERROR", "text": f"Error: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="cpi Advanced ping by FOXNET")
    parser.add_argument("targets", nargs='*', help="One or more targets")
    parser.add_argument("-n", "--count", type=int, default=None, help="Number of pings")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Interval (sec) between pings")
    
    # سوییچ‌های جدید درخواست شده
    parser.add_argument("-t", "--ttl", type=int, default=None, help="Set Time To Live (TTL)")
    parser.add_argument("-l", "--size", type=int, default=None, help="Send buffer size (bytes)")
    
    args = parser.parse_args()

    if not args.targets:
        parser.print_help()
        return

    targets = args.targets
    is_multi = len(targets) >= 2
    col_width = 38

    print(f"\n{Fore.LIGHTBLUE_EX}cpi Advanced Mode - {datetime.now().strftime('%Y-%m-%d')}{Style.RESET_ALL}")
    if args.ttl: print(f"{Fore.WHITE}Custom TTL: {args.ttl}")
    if args.size: print(f"{Fore.WHITE}Buffer Size: {args.size} bytes")

    if is_multi:
        header = f"{'Time':<10} | {targets[0].center(col_width)} | {targets[1].center(col_width)} |"
        print(f"{Fore.CYAN}{'=' * len(header)}\n{header}\n{'=' * len(header)}")
    else:
        print(f"{Fore.CYAN}{'Row':<4} | {'Time':<10} | {'Target':<15} | {'Result'}")
        print("-" * 60)

    counter = 1
    try:
        while args.count is None or counter <= args.count:
            now = datetime.now().strftime("%H:%M:%S")
            
            if is_multi:
                res1 = get_ping_data(targets[0], args.ttl, args.size)
                res2 = get_ping_data(targets[1], args.ttl, args.size)
                
                t1 = f"{res1['color']}{res1['text']}{Style.RESET_ALL}" if res1['status'] == "OK" else f"{Fore.RED}{res1['text']}"
                t2 = f"{res2['color']}{res2['text']}{Style.RESET_ALL}" if res2['status'] == "OK" else f"{Fore.RED}{res2['text']}"
                
                print(f"{now:<10} | {t1.center(col_width + 9)} | {t2.center(col_width + 9)} |")
            else:
                res = get_ping_data(targets[0], args.ttl, args.size)
                color = res.get('color', Fore.RED)
                print(f"{counter:<4} | {now:<10} | {targets[0]:<15} | {color}{res['text']}{Style.RESET_ALL}")

            counter += 1
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()