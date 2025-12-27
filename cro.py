import subprocess
import argparse
import platform
import sys
import re
import requests
from colorama import Fore, Style, init

init(autoreset=True)

def is_private_ip(ip):
    """بررسی اینکه آیا آی‌پی داخلی است یا خیر"""
    private_patterns = [
        r'^10\.', 
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.', 
        r'^192\.168\.', 
        r'^127\.'
    ]
    return any(re.match(pattern, ip) for pattern in private_patterns)

def get_ip_info(ip, show_geo=False, show_asn=False):
    """دریافت اطلاعات تکمیلی بر اساس سوئیچ‌های کاربر"""
    if "*" in ip or not ip:
        return ""
    
    if is_private_ip(ip):
        return f" {Fore.LIGHTBLACK_EX}[Internal Network]{Style.RESET_ALL}"

    if not (show_geo or show_asn):
        return ""

    try:
        # ساخت فیلدهای درخواستی بر اساس انتخاب کاربر
        fields = "status,message"
        if show_geo: fields += ",country,city"
        if show_asn: fields += ",isp,as"
        
        response = requests.get(f"http://ip-api.com/json/{ip}?fields={fields}", timeout=2)
        data = response.json()
        
        if data.get("status") == "success":
            info_parts = []
            if show_geo:
                info_parts.append(f"{data.get('country')}, {data.get('city')}")
            if show_asn:
                asn = data.get('as', '').split(' ')[0]
                info_parts.append(f"{data.get('isp')} ({asn})")
            
            return f" {Fore.YELLOW}[{' | '.join(info_parts)}]{Style.RESET_ALL}"
    except:
        return f" {Fore.RED}[Lookup Timeout]{Style.RESET_ALL}"
    return ""

def main():
    print(f"{Fore.LIGHTBLUE_EX}Troute Pro by FOXNET (CBOX Tools) {Style.RESET_ALL}")
    
    parser = argparse.ArgumentParser(
        description="Professional Fast Traceroute with Optional Geo-IP & ASN Info",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Example:\n  python route.py 8.8.8.8 -g -a -o log.txt\n\n{Fore.LIGHTBLUE_EX}Troute by FOXNET{Style.RESET_ALL}"
    )
    parser.add_argument("target", nargs='?', default=None, help="Target IP or Domain")
    parser.add_argument("-m", "--max-hops", type=int, default=20, help="Maximum hops (default: 20)")
    parser.add_argument("-g", "--geo", action="store_true", help="Show Geographic info (Country, City)")
    parser.add_argument("-a", "--asn", action="store_true", help="Show ISP and AS Number")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to save the log file")
    
    args = parser.parse_args()
    
    if args.target is None:
        parser.print_help()
        sys.exit(1)

    # دستور سیستمی بهینه شده
    if platform.system().lower() == "windows":
        command = ["tracert", "-d", "-h", str(args.max_hops), args.target]
    else:
        command = ["traceroute", "-n", "-m", str(args.max_hops), args.target]

    print(f"{Fore.CYAN}Tracing route to {args.target}...")
    print(f"{Fore.WHITE}Settings: Geo={args.geo}, ASN={args.asn}, MaxHops={args.max_hops}{Style.RESET_ALL}\n")

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        output_file = open(args.output, "a", encoding="utf-8") if args.output else None
        
        try:
            for line in process.stdout:
                clean_line = line.strip()
                if not clean_line or any(x in clean_line for x in ["Tracing", "Over"]): continue

                # استخراج IP
                ip_match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', clean_line)
                
                info = ""
                if ip_match:
                    info = get_ip_info(ip_match.group(), show_geo=args.geo, show_asn=args.asn)

                # رنگ‌بندی بر اساس وضعیت بسته
                if "*" in clean_line:
                    display_line = f"{Fore.RED}{clean_line}{Style.RESET_ALL}"
                else:
                    display_line = f"{Fore.GREEN}{clean_line}{info}{Style.RESET_ALL}"

                print(display_line)
                if output_file:
                    output_file.write(f"{clean_line}{info}\n")
        finally:
            if output_file:
                output_file.close()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Trace stopped by user.")

if __name__ == "__main__":
    main()