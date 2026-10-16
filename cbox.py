"""CBOX interactive shell (Python)."""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.colors import Colors, init_color
from cbox_core.config import Config
from cbox_core.lineedit import Completer, History, LineEditor
from cbox_core.tools import logical_drives, resolve_tool, unquote_path

# ================== UI ==================


def clear_screen(*_args):
    os.system("cls" if os.name == "nt" else "clear")


def _format_size(num_bytes):
    """Human-readable byte count."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{int(size)} B" if unit == "B" else f"{size:,.1f} {unit}"
        size /= 1024


def show_disk_free(*_args):
    """`df`, implemented in-process.

    The shell used to shell out to `wmic logicaldisk`, which no longer ships
    with Windows 11 24H2, so `df` failed with a bare cmd.exe error on current
    Windows builds.
    """
    header = f"{'Drive':<8} {'Total':>12} {'Used':>12} {'Free':>12} {'Free%':>7}"
    print(f"{Colors.CYAN}{header}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'-' * len(header)}{Colors.RESET}")

    drives = list(logical_drives())
    if not drives:
        print(f"{Colors.RED}No readable drives were found.{Colors.RESET}")
        return

    for letter, total, free in drives:
        used = max(total - free, 0)
        free_pct = (free / total * 100) if total else 0.0
        colour = Colors.RED if free_pct < 10 else Colors.YELLOW if free_pct < 20 else Colors.GREEN
        print(
            f"{letter:<8} {_format_size(total):>12} {_format_size(used):>12} "
            f"{colour}{_format_size(free):>12} {free_pct:>6.1f}%{Colors.RESET}"
        )


def show_banner():
    print(f"{Colors.BLUE_BG}#######################################################{Colors.RESET}")
    print(f"{Colors.BLUE_BG}CBOX v{__version__}  Secure CLI for Windows                      {Colors.RESET}")
    print(f"{Colors.BLUE_BG}Advanced Command-Line Interface (Dynamic Logic)        {Colors.RESET}")
    print(f"{Colors.BLUE_BG}FOXNET Group | https://software.foxnet.ir              {Colors.RESET}")
    print(f"{Colors.BLUE_BG}#######################################################{Colors.RESET}")
    print(f"{Colors.GREEN}Type '?' for command list. Use 'exit' to quit.{Colors.RESET}")



def show_help(aliases):
    print(f"\n{Colors.WHITE}================== CBOX HELP =================={Colors.RESET}")
    print(f"{Colors.GREEN}{'cd [path]'.ljust(20)}{Colors.RESET} - Change directory (supports .. and \\)")
    print(f"{Colors.GREEN}{'cd -'.ljust(20)}{Colors.RESET} - Return to the previous directory")
    for command, (description, _) in aliases.items():
        print(f"{Colors.GREEN}{command.ljust(20)}{Colors.RESET} - {description}")
    print(f"\n{Colors.YELLOW}Note: You can also run any system command (e.g. mkdir, python, etc.){Colors.RESET}")
    print(f"{Colors.YELLOW}Example: cpi 8.8.8.8 1.1.1.1   |   cro 8.8.8.8 -g -a{Colors.RESET}")
    print(f"{Colors.YELLOW}Up/Down recall history, Tab completes commands and paths.{Colors.RESET}\n")


# ================== SECURE COMMAND EXECUTOR ==================


class CommandExecutor:
    def __init__(self):
        self.current_process = None

    def run(self, command):
        try:
            # shell=True lets internal and external Windows commands work as-is
            self.current_process = subprocess.Popen(command, shell=True)
            self.current_process.wait()
            return self.current_process.returncode
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupt received. Stopping command...{Colors.RESET}")
            self.terminate()
            return 1
        except Exception as exc:
            print(f"{Colors.RED}Execution Error: {exc}{Colors.RESET}")
            return 1
        finally:
            self.current_process = None

    def terminate(self):
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()


executor = CommandExecutor()


def run_tool(name, args):
    """Launch a bundled CBOX tool, preferring a compiled EXE when present."""
    argv = resolve_tool(name)
    if argv is None:
        print(
            f"{Colors.RED}Error: tool '{name}' was not found.{Colors.RESET}"
            f"\n{Colors.YELLOW}Expected {name}.py next to cbox.py, or an installed '{name}' EXE.{Colors.RESET}"
        )
        return 9009

    try:
        completed = subprocess.run(argv + args, shell=False)
        return completed.returncode
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupt received.{Colors.RESET}")
        return 1
    except Exception as exc:
        print(f"{Colors.RED}Execution Error: {exc}{Colors.RESET}")
        return 1


# ================== CBOX COMMAND TABLE ==================

#: CBOX command -> (description, handler).
#:
#: A handler is one of:
#:   str   - passed to cmd.exe verbatim; `{args}` is replaced by the caller's
#:           argument string, so quoting survives
#:   None  - a bundled tool, resolved by cbox_core.tools (dist EXE, then the
#:           .py next to this file)
#:   func  - a native handler, called as handler(args)
ALIASES = {
    "ls": ("List directory content", "dir {args}"),
    "pi": ("Ping host", "ping {args}"),
    "tr": ("Trace route to host", "tracert -d {args}"),
    "ip": ("Standard network config", "ipconfig"),
    "ipa": ("Full network config", "ipconfig /all"),
    "df": ("Disk free space", show_disk_free),
    "task": ("Process list", "tasklist"),
    "ps": ("Process list", "tasklist"),
    "kill": ("Kill process by ID", "taskkill /PID {args} /F"),
    "who": ("Current user info", "whoami"),
    "ver": ("OS version info", 'systeminfo | findstr /B /C:"OS Version"'),
    "cl": ("Clear screen", clear_screen),
    # CBOX tools
    "cdir": ("Directory lister (rich table)", None),
    "cpi": ("Colour-coded ping", None),
    "cro": ("Traceroute with Geo-IP/ASN", None),
    "cwho": ("WHOIS lookup", None),
    "netdetail": ("Deep network info (IPv4/IPv6/DNS/DHCP)", None),
    "ntstat": ("Socket table with process owner", None),
    "ntpmon": ("Per-process network monitor", None),
    "nscn": ("LAN / port scanner", None),
    "cport": ("Listening ports and owning process", None),
    "csweep": ("Parallel host / port discovery", None),
    "chash": ("File hashing and checksum verification", None),
    "cwlan": ("Wireless interface status", None),
}

#: Commands whose first argument names a file or directory. Tab completion
#: offers paths for these rather than command names.
PATH_COMMANDS = {"ls", "cdir", "chash"}

#: Passthrough commands that destroy something. These ask before running,
#: unless ~/.cboxrc turns confirm_destructive off.
DESTRUCTIVE = {"del", "erase", "rmdir", "rd", "format", "diskpart", "kill"}

#: Paths that must never be handed to a destructive command without a very
#: loud warning, whatever the user's own command was.
CRITICAL_PATHS = {
    "c:\\", "c:/", "d:\\", "d:/", "e:\\", "e:/",
    os.path.expanduser("~"),
    os.path.expanduser("~").rstrip("\\") + "\\",
}


def confirm(text):
    """Ask a yes/no question. Default is no."""
    try:
        answer = input(f"{Colors.YELLOW}{text} [y/N]: {Colors.RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("y", "yes")


def is_destructive(command, args):
    """True when `command` targets something critical.

    Matches the command name and the specific argument rather than a bare
    keyword list, so `kill 1234` is not treated like `del C:\\`.
    """
    command = command.lower().lstrip("/")
    if command not in DESTRUCTIVE and command not in ("del", "erase"):
        return False

    if not args:
        return False

    target = args[0].strip().strip('"').rstrip("\\/")
    normalised = target.lower().replace("/", "\\")

    if normalised in {p.lower().replace("/", "\\").rstrip("\\") for p in CRITICAL_PATHS}:
        return True
    # `del` with no target, or `del \` - the argument is the drive root.
    return not normalised


# ================== COMMAND DISPATCHER ==================


class Shell:
    """Holds the mutable session state: aliases, cwd history, settings."""

    def __init__(self, config=None):
        self.config = config or Config().load()
        self.aliases = dict(ALIASES)
        self.apply_user_aliases()
        self.previous_dir = None

    def apply_user_aliases(self):
        for name, target in self.config.aliases.items():
            description = f"user alias -> {target}"
            if target.strip().lower() in ALIASES:
                self.aliases[name] = (description, ALIASES[target.strip().lower()][1])
            else:
                self.aliases[name] = (description, target.strip())

    # ---- navigation ----

    def change_directory(self, args):
        if not args:
            target = unquote_path(args) if args else os.path.expanduser("~")
        elif args[0] == "-" and len(args) == 1:
            if self.previous_dir is None:
                print(f"{Colors.YELLOW}No previous directory yet.{Colors.RESET}")
                return
            target = self.previous_dir
        else:
            target = unquote_path(args)

        target = os.path.expandvars(os.path.expanduser(target))
        current = os.getcwd()
        try:
            os.chdir(target)
        except Exception as exc:
            print(f"{Colors.RED}Error: {exc}{Colors.RESET}")
            return

        if os.path.realpath(os.getcwd()) != os.path.realpath(current):
            self.previous_dir = current
        print(f"{Colors.CYAN}[Directory Changed]{Colors.RESET}")

    # ---- dispatch ----

    def execute(self, user_input):
        parts = user_input.split()
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "cd":
            self.change_directory(args)
            return

        if cmd in ("cd..", "cd\\"):
            os.chdir(".." if cmd == "cd.." else "\\")
            self.previous_dir = os.path.dirname(os.getcwd())
            print(f"{Colors.CYAN}[Directory Changed]{Colors.RESET}")
            return

        if cmd not in self.aliases:
            if self.guard(cmd, args, user_input):
                return
            exit_code = executor.run(user_input)
            if exit_code == 9009:
                # 9009 is cmd.exe's "command not found".
                print(
                    f"{Colors.RED}Error: '{cmd}' is not a recognized CBOX or System command.{Colors.RESET}"
                    f"\n{Colors.YELLOW}Type '?' for help and list of commands.{Colors.RESET}"
                )
            return

        handler = self.aliases[cmd][1]

        if callable(handler):
            # Native handler: runs in-process, no shell involved.
            handler(args)
            return

        if handler is None:
            # Bundled tool: invoked through cbox_core.tools so a fresh clone
            # works without any EXE being built.
            run_tool(cmd, args)
            return

        # Passthrough alias: keep the caller's argument string verbatim.
        exit_code = executor.run(handler.format(args=" ".join(args)))

        if exit_code == 9009:
            # cmd.exe could not find the program the alias wraps. Saying
            # "unknown command" here would be wrong: the alias resolved fine,
            # its target is what is missing.
            print(
                f"{Colors.RED}Error: '{cmd}' needs '{handler.split()[0]}', "
                f"which is not available on this system.{Colors.RESET}"
                f"\n{Colors.YELLOW}Some of these tools were removed in recent Windows releases."
                f"{Colors.RESET}"
            )

    def guard(self, cmd, args, user_input):
        """Return True when a destructive passthrough command was refused."""
        if not self.config.get("confirm_destructive"):
            return False
        if not is_destructive(cmd, args):
            return False

        print(f"{Colors.RED}Refusing to run a destructive command:{Colors.RESET}")
        print(f"  {user_input}")
        if not confirm("Run it anyway?"):
            print(f"{Colors.YELLOW}Cancelled.{Colors.RESET}")
            return True
        return False


# ================== SCRIPT MODE ==================


def run_script(path, shell):
    """Execute a file of shell commands, one per line.

    Blank lines and `#` comments are skipped. `exit` stops the script. Every
    other line goes through the same dispatcher as interactive input, so
    scripts behave exactly like typing the commands.
    """
    try:
        # utf-8-sig: a BOM would otherwise make the first comment line look
        # like a command.
        with open(path, encoding="utf-8-sig") as handle:
            lines = handle.readlines()
    except OSError as exc:
        print(f"{Colors.RED}Cannot read script '{path}': {exc}{Colors.RESET}")
        return 1

    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower() in ("exit", "quit"):
            break

        print(f"{Colors.DIM}{_printable(path)}:{number}{Colors.RESET} {_printable(line)}")
        try:
            shell.execute(line)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Script stopped at line {number}.{Colors.RESET}")
            break

    return 0


def _printable(text):
    """Strip characters the console cannot encode.

    Scripts may be UTF-8 while the console is cp1252; echoing the source line
    would otherwise raise UnicodeEncodeError before the command even runs.
    """
    encoding = (getattr(sys.stdout, "encoding", None) or "ascii").lower()
    try:
        text.encode(encoding)
        return text
    except (UnicodeEncodeError, LookupError):
        return text.encode("ascii", "backslashreplace").decode("ascii")


# ================== MAIN LOOP ==================


def build_editor(config):
    """Wire up the line editor according to the user's settings."""
    history = History(
        path=os.path.expanduser("~/.cbox_history") if config.get("history") else None,
        limit=config.get("history_size", 500),
    )
    if not config.get("history"):
        history.path = None

    completer = None
    if config.get("completion"):
        completer = Completer(commands=list(ALIASES), path_commands=PATH_COMMANDS)

    return LineEditor(history=history, completer=completer, clear=clear_screen)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="cbox", description=f"CBOX {__version__} - Secure CLI for Windows",
        epilog="Settings and aliases are read from ~/.cboxrc.",
    )
    parser.add_argument("-f", "--file", metavar="SCRIPT",
                        help="Run the shell commands in SCRIPT, then exit")
    parser.add_argument("-c", "--command", metavar="CMD",
                        help="Run one shell command, then exit")
    parser.add_argument("--no-config", action="store_true",
                        help="Ignore ~/.cboxrc for this session")
    parser.add_argument("--rc", metavar="PATH",
                        help="Use this rc file instead of ~/.cboxrc")
    args = parser.parse_args(argv)

    init_color()

    config = Config(args.rc) if args.rc else Config()

    if args.no_config:
        # Defaults only: no file is read, so aliases and settings stay empty.
        config.path = None
        config.settings = dict(Config.DEFAULTS)
        config.aliases = {}
        config.errors = []
        config.loaded = True
    else:
        config.load()

    shell = Shell(config)

    for number, message in config.errors:
        where = f"line {number}: " if number else ""
        print(f"{Colors.YELLOW}[cboxrc] {where}{message}{Colors.RESET}")

    if args.command:
        shell.execute(args.command)
        return 0

    if args.file:
        return run_script(args.file, shell)

    if config.get("banner"):
        clear_screen()
        show_banner()
    if config.aliases:
        names = ", ".join(sorted(config.aliases))
        print(f"{Colors.DIM}Loaded {len(config.aliases)} "
              f"alias(es) from {config.path}: {names}{Colors.RESET}")

    editor = build_editor(config)
    interactive(config, shell, editor)
    return 0


def interactive(config, shell, editor):
    while True:
        cwd = os.getcwd()
        prompt = f"{Colors.CYAN_BG} {cwd} {Colors.RESET}{Colors.BRIGHT_BLUE}CBOX > {Colors.RESET}"

        if editor.supports_raw:
            result = editor.read_line(prompt)
            if result.interrupted:
                print(f"\n{Colors.YELLOW}CTRL+C pressed.{Colors.RESET}")
                if confirm("Exit CBOX?"):
                    break
                continue
            user_input = result.text.strip()
        else:
            try:
                print(f"\n{Colors.CYAN_BG} {cwd} {Colors.RESET}")
                user_input = input(f"{Colors.BRIGHT_BLUE}CBOX > {Colors.RESET}").strip()
            except EOFError:
                break
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}CTRL+C pressed.{Colors.RESET}")
                if confirm("Exit CBOX?"):
                    break
                continue

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print(f"{Colors.WHITE}Exiting CBOX...{Colors.RESET}")
            break

        if user_input in ("?", "help", "-h", "--help"):
            show_help(shell.aliases)
            continue

        shell.execute(user_input)


# Backwards-compatible module-level entry points. The test suite and any
# external caller use these names.
def show_help_default():
    show_help(ALIASES)


def execute_command(user_input):
    Shell().execute(user_input)


if __name__ == "__main__":
    sys.exit(main() or 0)
