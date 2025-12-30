import subprocess
import re
import os

# تنظیمات رنگ و استایل
class Colors:
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RESET = '\033[0m'
    MAGENTA = '\033[35m'
    WHITE = '\033[37m'
    BOLD_WHITE_ON_BLUE = '\033[1;37;44m' # متن سفید ضخیم روی پس‌زمینه آبی

def get_net_config():
    try:
        # دریافت خروجی از سیستم با انکودینگ مناسب ویندوز
        output = subprocess.check_output("ipconfig /all", shell=True).decode('cp1252')
        
        print(f"\n{Colors.MAGENTA}{'='*65}")
        print(f"{'CBOX ADVANCED NETWORK DIAGNOSTICS (IPv4/IPv6)':^65}")
        print(f"{'='*65}{Colors.RESET}\n")

        # جدا کردن آداپتورها
        adapters = re.split(r'\n(?=[a-zA-Z0-9])', output)

        for adapter in adapters:
            # بررسی اینکه آیا آداپتور فعال است (دارای آدرس IP است یا خیر)
            if "Address" not in adapter:
                continue

            # استخراج نام آداپتور
            adapter_name_match = re.match(r'^([^:]+):', adapter.strip())
            adapter_name = adapter_name_match.group(1) if adapter_name_match else "Unknown Adapter"
            
            # تیتر کارت شبکه: متن سفید روی بک‌گراند آبی
            print(f"{Colors.BOLD_WHITE_ON_BLUE} INTERFACE: {adapter_name.upper():<53} {Colors.RESET}")
            print(f"{Colors.YELLOW}{'-'*65}{Colors.RESET}")
            print(f"{Colors.WHITE}{'Property':<25} | {'Value'}{Colors.RESET}")
            print(f"{Colors.YELLOW}{'-'*65}{Colors.RESET}")

            # الگوهای جستجو شامل IPv6
            patterns = {
                "Physical Address": r"Physical Address. . . . . . . . . : (.*)",
                "IPv4 Address": r"IPv4 Address. . . . . . . . . . . : ([\d\.]+)",
                "IPv6 Address": r"IPv6 Address. . . . . . . . . . . : ([a-fA-F0-9:]+)",
                "Link-local IPv6": r"Link-local IPv6 Address . . . . . : ([a-fA-F0-9:]+)",
                "Subnet Mask": r"Subnet Mask . . . . . . . . . . . : ([\d\.]+)",
                "Default Gateway": r"Default Gateway . . . . . . . . . : ([\d\.:a-fA-F]+)",
                "DHCP Server": r"DHCP Server . . . . . . . . . . . : ([\d\.]+)",
                "DNS Servers": r"DNS Servers . . . . . . . . . . . : ([\d\.:a-fA-F]+)",
                "DHCP Enabled": r"DHCP Enabled. . . . . . . . . . . : (.*)"
            }

            for label, pattern in patterns.items():
                match = re.search(pattern, adapter)
                if match:
                    value = match.group(1).strip()
                    # رنگ سبز برای مقادیر پیدا شده
                    print(f"{label:<25} | {Colors.GREEN}{value}{Colors.RESET}")
                else:
                    # عدم نمایش ردیف اگر مقدار وجود ندارد (مثلاً اگر IPv6 ندارد)
                    continue

            # پیدا کردن DNSهای اضافی که در خطوط بعدی لیست می‌شوند
            dns_extra = re.findall(r'^\s+([a-fA-F0-9:]+[:][a-fA-F0-9:]+|[\d\.]+)\s*$', adapter, re.MULTILINE)
            for extra in dns_extra:
                # جلوگیری از تکرار آدرسی که قبلاً در بخش DNS Servers چاپ شده
                if extra not in adapter.split("DNS Servers")[1].split("\n")[0]:
                    print(f"{'Secondary DNS':<25} | {Colors.GREEN}{extra}{Colors.RESET}")

            print(f"{Colors.YELLOW}{'-'*65}{Colors.RESET}\n")

    except Exception as e:
        print(f"{Colors.RED}Error processing network data: {e}{Colors.RESET}")

if __name__ == "__main__":
    # فعال‌سازی کدهای ANSI در کنسول ویندوز
    os.system('') 
    get_net_config()