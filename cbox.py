import os
import subprocess
import sys
import signal

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
    print(f"{Colors.BLUE_BG}CBOX v1.0.1  Secure CLI for Windows                     {Colors.RESET}")
    print(f"{Colors.BLUE_BG}Advanced Command-Line Interface (Python Refactor)     {Colors.RESET}")
    print(f"{Colors.BLUE_BG}FOXNET Group | https://software.foxnet.ir              {Colors.RESET}")
    print(f"{Colors.BLUE_BG}#######################################################{Colors.RESET}")
    print(f"{Colors.GREEN}Type '?' for command list. Use 'exit' to quit.{Colors.RESET}")

def show_help():
    print(f"\n{Colors.WHITE}================== CBOX HELP =================={Colors.RESET}")
    cmds = [
        ("ls [path]", "List directory"),
        ("pi host", "Ping host"),
        ("tr host", "Trace route"),
        ("ip / ipa", "Network info"),
        ("df", "Disk free"),
        ("task / ps", "Process list"),
        ("kill PID", "Kill process"),
        ("who", "Current user"),
        ("ver", "System version"),
        ("cl", "Clear screen"),
        ("exit / quit", "Exit CBOX")
    ]
    for c, d in cmds:
        print(f"{Colors.GREEN}{c.ljust(15)}{Colors.RESET} - {d}")
    print()

# ================== SECURE COMMAND EXECUTOR ==================
class CommandExecutor:
    def __init__(self):
        self.current_process = None

    def run(self, command, shell=True):
        try:
            self.current_process = subprocess.Popen(
                command,
                shell=shell
            )
            self.current_process.wait()

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupt received. Stopping command...{Colors.RESET}")
            self.terminate()

        finally:
            self.current_process = None

    def terminate(self):
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()

# ================== COMMAND DISPATCHER ==================
executor = CommandExecutor()

def execute_command(user_input):
    parts = user_input.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "cl":
        clear_screen()

    elif cmd == "ls":
        path = args[0] if args else "."
        executor.run(f'dir "{path}"')

    elif cmd == "pi":
        if not args:
            print(f"{Colors.RED}Host required.{Colors.RESET}")
            return
        executor.run(f'ping {args[0]}')

    elif cmd == "tr":
        if not args:
            print(f"{Colors.RED}Host required.{Colors.RESET}")
            return
        executor.run(f'tracert -d {args[0]}')

    elif cmd in ("ip", "ipa"):
        executor.run("ipconfig")

    elif cmd in ("df", "dirfree"):
        executor.run("wmic logicaldisk get caption,freespace,size")

    elif cmd in ("task", "ps"):
        executor.run("tasklist")

    elif cmd == "kill" and args:
        executor.run(f"taskkill /PID {args[0]} /F")

    elif cmd == "who":
        executor.run("whoami")

    elif cmd == "ver":
        executor.run('systeminfo | findstr /B /C:"OS Version"')

    else:
        print(f"{Colors.YELLOW}Passing command to system...{Colors.RESET}")
        executor.run(user_input)

# ================== MAIN LOOP ==================
def main():
    clear_screen()
    show_banner()

    while True:
        try:
            cwd = os.getcwd()
            print(f"\n{Colors.CYAN_BG} {cwd} {Colors.RESET}")
            user_input = input(f"{Colors.BRIGHT_BLUE}CBOX > {Colors.RESET}").strip()

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}CTRL+C pressed.{Colors.RESET}")
            confirm = input(f"{Colors.RED}Exit CBOX? (y/N): {Colors.RESET}").lower()
            if confirm == "y":
                print(f"{Colors.WHITE}Exiting CBOX...{Colors.RESET}")
                break
            else:
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

# ================== ENTRY ==================
if __name__ == "__main__":
    main()
