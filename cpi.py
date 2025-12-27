import subprocess
import platform
import re
import time
import argparse
import sys
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

def main():
    print(f"{Fore.LIGHTBLUE_EX}Tping by FOXNET (CBOX Tools).For more help use -h or --help{Style.RESET_ALL}\n")
    
    parser = argparse.ArgumentParser(
        description="Professional Network Ping Tool with Color Coding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"{Fore.LIGHTBLUE_EX}Tping by FOXNET (CBOX Tools) {Style.RESET_ALL}"
    )
    parser.add_argument("target", nargs='?', default=None, help="Target IP address or Domain (e.g. google.com)")
    parser.add_argument("-n", "--count", type=int, default=None, help="Number of echo requests to send (default: infinite)")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="Wait interval between pings in seconds (default: 1s)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to save the log file (default: no logging)")
    
    args = parser.parse_args()
    
    # Display help if no target provided
    if args.target is None:
        parser.print_help()
        sys.exit(1)

    print(f"\n{Fore.CYAN}Row | Date       | Time     | Target         | Latency  | TTL{Style.RESET_ALL}")
    print("-" * 75)

    counter = 1
    try:
        while args.count is None or counter <= args.count:
            now = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", args.target]
            
            try:
                output = subprocess.run(command, capture_output=True, text=True, timeout=5).stdout
                time_match = re.search(r"time[=<](\d+)ms", output)
                ttl_match = re.search(r"TTL=(\d+)", output, re.IGNORECASE)

                if time_match:
                    ms = int(time_match.group(1))
                    ttl = ttl_match.group(1) if ttl_match else "N/A"
                    
                    # رنگ‌بندی ۴ مرحله‌ای
                    if ms < 50: color = Fore.GREEN
                    elif ms < 150: color = Fore.YELLOW
                    elif ms < 300: color = Fore.LIGHTRED_EX # Orange-like
                    else: color = Fore.RED
                    
                    result = f"{counter:<3} | {now} | {args.target:<14} | {ms:>3}ms    | TTL={ttl}"
                    print(f"{color}{result}{Style.RESET_ALL}")
                else:
                    result = f"{counter:<3} | {now} | {args.target:<14} | Request Timed Out!"
                    print(f"{Fore.RED}{result}{Style.RESET_ALL}")

                if args.output:
                    with open(args.output, "a", encoding="utf-8") as f:
                        f.write(result + "\n")

            except subprocess.TimeoutExpired:
                print(f"{Fore.RED}Process timeout for hop {counter}")

            counter += 1
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()