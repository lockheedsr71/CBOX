import whois
import argparse
import sys
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

def get_domain_info(target, output_file=None):
    print(f"{Fore.CYAN}Fetching WHOIS information for: {target}...")
    
    try:
        # دریافت اطلاعات WHOIS
        w = whois.whois(target)
        
        # سازماندهی داده‌ها
        info = {
            "Domain Name": w.domain_name,
            "Registrar": w.registrar,
            "Whois Server": w.whois_server,
            "Creation Date": w.creation_date,
            "Expiration Date": w.expiration_date,
            "Name Servers": w.name_servers,
            "Status": w.status,
            "Emails": w.emails,
            "Country": w.country
        }

        report = []
        report.append(f"\n{Fore.LIGHTBLUE_EX}=== WHOIS REPORT BY FOXNET ==={Style.RESET_ALL}")
        
        for key, value in info.items():
            # مدیریت نمایش زمان و لیست‌ها
            if isinstance(value, list):
                value = ", ".join([str(v) for v in value])
            
            line = f"{Fore.YELLOW}{key:<16}: {Fore.WHITE}{value}"
            print(line)
            report.append(f"{key:<16}: {value}")

        # ذخیره در فایل در صورت نیاز
        if output_file:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write("\n".join(report) + "\n" + ("-"*30) + "\n")
            print(f"\n{Fore.GREEN}Report saved to: {output_file}")

    except Exception as e:
        print(f"{Fore.RED}Error: Could not retrieve information. ({e})")

def main():
    parser = argparse.ArgumentParser(
        description="Domain/IP Ownership Information (WHOIS)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target", help="Domain name or IP address (e.g., google.com)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to save the report")
    
    args = parser.parse_args()
    
    if args.target:
        get_domain_info(args.target, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()