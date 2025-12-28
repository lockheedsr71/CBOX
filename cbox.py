import os
import subprocess
import sys

# ================== COLORS ==================
class Colors:
    BLUE_BG = '\033[97;44m'
    CYAN_BG = '\033[30;46m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'
    BRIGHT_BLUE = '\033[94m'

# ================== UI ==================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    print(f"{Colors.BLUE_BG}#######################################################{Colors.RESET}")
    print(f"{Colors.BLUE_BG}CBOX v1.1.0  Secure CLI for Windows                    {Colors.RESET}")
    print(f"{Colors.BLUE_BG}Advanced Command-Line Interface (Dynamic Logic)        {Colors.RESET}")
    print(f"{Colors.BLUE_BG}FOXNET Group | https://software.foxnet.ir              {Colors.RESET}")
    print(f"{Colors.BLUE_BG}#######################################################{Colors.RESET}")
    print(f"{Colors.GREEN}Type '?' for command list. Use 'exit' to quit.{Colors.RESET}")

def show_help():
    print(f"\n{Colors.WHITE}================== CBOX HELP =================={Colors.RESET}")
    cmds = [
        ("ls [path]", "List directory content"),
        ("cd [path]", "Change directory (supports .. and \\)"),
        ("pi [host]", "Ping host"),
        ("tr [host]", "Trace route to host"),
        ("netdetail", "Deep network info (IPv4/IPv6/DNS/DHCP)"),
        ("ip / ipa", "Standard network config"),
        ("df", "Disk free space"),
        ("task / ps", "Process list"),
        ("kill [PID]", "Kill process by ID"),
        ("who", "Current user info"),
        ("ver", "OS version info"),
        ("cdir / cro", "Execute custom external tools"),
        ("cl", "Clear screen"),
        ("exit / quit", "Exit CBOX")
    ]
    for c, d in cmds:
        print(f"{Colors.GREEN}{c.ljust(20)}{Colors.RESET} - {d}")
    print(f"\n{Colors.YELLOW}Note: You can also run any system command (e.g. mkdir, python, etc.){Colors.RESET}\n")

# ================== SECURE COMMAND EXECUTOR ==================
class CommandExecutor:
    def __init__(self):
        self.current_process = None

    def run(self, command):
        try:
            # shell=True اجازه می‌دهد دستورات داخلی و خارجی ویندوز به درستی هندل شوند
            self.current_process = subprocess.Popen(command, shell=True)
            self.current_process.wait()
            return self.current_process.returncode
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupt received. Stopping command...{Colors.RESET}")
            self.terminate()
            return 1
        except Exception as e:
            print(f"{Colors.RED}Execution Error: {e}{Colors.RESET}")
            return 1
        finally:
            self.current_process = None

    def terminate(self):
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()

# ================== COMMAND DISPATCHER ==================
executor = CommandExecutor()

def execute_command(user_input):
    parts = user_input.split()
    if not parts:
        return
        
    cmd = parts[0].lower()
    args = parts[1:]
    full_args = " ".join(args)

    # 1. مدیریت اختصاصی دستورات ناوبری (Navigation)
    if cmd == "cd":
        try:
            path = full_args if args else os.path.expanduser("~")
            os.chdir(path)
            print(f"{Colors.CYAN}[Directory Changed]{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return

    elif cmd == "cd.." or cmd == "cd\\":
        os.chdir(".." if cmd == "cd.." else "\\")
        print(f"{Colors.CYAN}[Directory Changed]{Colors.RESET}")
        return

    # 2. سیستم الیاس (Aliases) برای دستورات اختصاصی CBOX
    # این بخش پارامترها را به صورت داینامیک به دستور نهایی منتقل می‌کند
    aliases = {
        "ls": f"dir {full_args}",
        "pi": f"ping {full_args}",
        "tr": f"tracert -d {full_args}",
        "ip": "ipconfig",
        "ipa": "ipconfig",
        "df": "wmic logicaldisk get caption,freespace,size",
        "task": "tasklist",
        "ps": "tasklist",
        "kill": f"taskkill /PID {full_args} /F",
        "who": "whoami",
        "ver": 'systeminfo | findstr /B /C:"OS Version"',
        "cl": "cls",
        "netdetail": f"python net_info.py {full_args}",
        "cdir": f"cdir {full_args}",
        "cnetw": f"cnetw {full_args}",
        "cro": f"cro {full_args}",
        "cpi": f"cpi {full_args}"
    }

    # 3. منطق اجرا و تشخیص
    if cmd in aliases:
        # اگر دستور جزو میانبرهای CBOX بود
        executor.run(aliases[cmd])
    else:
        # اگر دستور در CBOX نبود، تلاش برای اجرای مستقیم در سیستم
        # کد خروج 9009 در ویندوز یعنی دستور پیدا نشد
        exit_code = executor.run(user_input)
        
        if exit_code == 9009:
            print(f"{Colors.RED}Error: '{cmd}' is not a recognized CBOX or System command.{Colors.RESET}")
            print(f"{Colors.YELLOW}Type '?' for help and list of commands.{Colors.RESET}")

# ================== MAIN LOOP ==================
def main():
    # فعال سازی کدهای رنگی ANSI در کنسول ویندوز
    os.system('') 
    clear_screen()
    show_banner()

    while True:
        try:
            cwd = os.getcwd()
            # نمایش مسیر جاری با پس‌زمینه رنگی
            print(f"\n{Colors.CYAN_BG} {cwd} {Colors.RESET}")
            user_input = input(f"{Colors.BRIGHT_BLUE}CBOX > {Colors.RESET}").strip()

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}CTRL+C pressed.{Colors.RESET}")
            confirm = input(f"{Colors.RED}Exit CBOX? (y/N): {Colors.RESET}").lower()
            if confirm == "y":
                break
            continue

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print(f"{Colors.WHITE}Exiting CBOX...{Colors.RESET}")
            break

        if user_input == "?":
            show_help()
            continue

        execute_command(user_input)

if __name__ == "__main__":
    main()