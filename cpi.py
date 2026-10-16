import argparse
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import Fore, Style, init

from cbox_core import __version__
from cbox_core.colors import init_color

init(autoreset=True)


def get_ping_data(target, ttl=None, buffer_size=None):
    """اجرای پینگ با تنظیمات TTL و Buffer Size"""
    param_n = "-n" if platform.system().lower() == "windows" else "-c"

    command = ["ping", param_n, "1"]

    # TTL در ویندوز با سوییچ -i تنظیم می‌شود
    if ttl:
        command.extend(["-i", str(ttl)])

    # اندازه بسته در ویندوز با سوییچ -l
    if buffer_size:
        command.extend(["-l", str(buffer_size)])

    command.append(target)

    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace",
        )
        output = completed.stdout or ""
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "text": "Request Timed Out!"}
    except FileNotFoundError:
        return {"status": "ERROR", "text": "ping executable not found on this system"}

    time_match = re.search(r"time[=<]\s*(\d+)\s*ms", output, re.IGNORECASE)
    if time_match:
        ms = int(time_match.group(1))
        ttl_match = re.search(r"TTL=(\d+)", output, re.IGNORECASE)
        res_ttl = ttl_match.group(1) if ttl_match else "N/A"
        color = Fore.GREEN if ms < 50 else Fore.YELLOW if ms < 150 else Fore.RED
        return {
            "status": "OK", "ms": ms, "ttl": res_ttl, "color": color,
            "text": f"{ms:>3}ms (TTL={res_ttl})",
        }

    if re.search(r"transmit failed|could not find host|unreachable", output, re.IGNORECASE):
        return {"status": "TIMEOUT", "text": "Request Timed Out!"}

    return {"status": "TIMEOUT", "text": "No Reply!"}


def main():
    parser = argparse.ArgumentParser(description=f"cpi {__version__} - Advanced ping by FOXNET")
    parser.add_argument("targets", nargs='*', help="One or two targets to compare")
    parser.add_argument("-n", "--count", type=int, default=None, help="Number of pings")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Interval (sec) between pings")
    parser.add_argument("-t", "--ttl", type=int, default=None, help="Set Time To Live (TTL)")
    parser.add_argument("-l", "--size", type=int, default=None, help="Send buffer size (bytes)")

    args = parser.parse_args()

    if not args.targets:
        parser.print_help()
        return 1

    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    if args.count is not None and args.count <= 0:
        parser.error("--count must be greater than zero")

    targets = args.targets
    is_multi = len(targets) >= 2
    col_width = 38

    print(f"\n{Fore.LIGHTBLUE_EX}cpi {__version__} - {datetime.now().strftime('%Y-%m-%d')}{Style.RESET_ALL}")
    if args.ttl:
        print(f"{Fore.WHITE}Custom TTL: {args.ttl}")
    if args.size:
        print(f"{Fore.WHITE}Buffer Size: {args.size} bytes")

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
                print(f"{now:<10} | {_cell(res1).center(col_width + 9)} | {_cell(res2).center(col_width + 9)} |")
            else:
                res = get_ping_data(targets[0], args.ttl, args.size)
                print(f"{counter:<4} | {now:<10} | {targets[0]:<15} | {_cell(res)}")

            counter += 1
            if args.count is None or counter <= args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Stopping...{Style.RESET_ALL}")

    return 0


def _cell(result):
    if result["status"] == "OK":
        return f"{result['color']}{result['text']}{Style.RESET_ALL}"
    return f"{Fore.RED}{result['text']}{Style.RESET_ALL}"


if __name__ == "__main__":
    init_color()
    sys.exit(main() or 0)
