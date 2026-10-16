"""Optional-dependency handling.

Most CBOX tools render with `rich`. Rather than letting a missing package
surface as an ImportError traceback, we detect it up front and print the
one-line install command.
"""

import importlib
import sys

from cbox_core.colors import Colors

__all__ = ["MissingDependency", "fail_fast", "have", "require", "rich_toolkit", "safe_glyphs"]

_INSTALL_HINTS = {
    "rich": "python -m pip install rich",
    "scapy": "python -m pip install scapy",
    "colorama": "python -m pip install colorama",
    "requests": "python -m pip install requests",
    "psutil": "python -m pip install psutil",
    "whois": "python -m pip install python-whois",
    "win32security": "python -m pip install pywin32",
}

_EXTRA_HINTS = {
    "scapy": "Npcap (https://npcap.com) is required on Windows for raw sockets.",
    "win32security": "Only needed for the file owner column in cdir.py.",
}


class MissingDependency(Exception):
    """Raised when a tool cannot run because an optional package is absent."""

    def __init__(self, module, feature=None):
        self.module = module
        self.feature = feature
        super().__init__(str(self))

    def __str__(self):
        lines = []
        subject = self.feature or f"'{self.module}' is required for this feature"
        lines.append(f"{Colors.RED}[CBOX] Missing dependency:{Colors.RESET} {subject}")
        hint = _INSTALL_HINTS.get(self.module)
        if hint:
            lines.append(f"  Install it with: {Colors.CYAN}{hint}{Colors.RESET}")
        extra = _EXTRA_HINTS.get(self.module)
        if extra:
            lines.append(f"  {Colors.YELLOW}Note: {extra}{Colors.RESET}")
        return "\n".join(lines)


def have(module):
    """True when `module` can be imported."""
    try:
        importlib.import_module(module)
    except Exception:
        return False
    return True


def require(module, feature=None):
    """Import `module` or raise MissingDependency with a helpful message."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingDependency(module, feature) from exc


def rich_toolkit():
    """Import every rich symbol the dashboards need.

    Returns the same tuple shape the tools historically unpacked, so call
    sites stay unchanged. Raises MissingDependency when rich is absent.
    """
    try:
        from rich import box as rich_box
        from rich.align import Align
        from rich.columns import Columns
        from rich.console import Console
        from rich.layout import Layout
        from rich.live import Live
        from rich.panel import Panel
        from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
        from rich.table import Table
        from rich.text import Text
    except ImportError as exc:
        raise MissingDependency("rich") from exc

    return (
        Console, Table, rich_box, Panel, Text, Align, Live,
        Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn,
        Layout, Columns,
    )


def fail_fast(module, feature=None):
    """Print the missing-dependency guidance and exit with status 1."""
    print(str(MissingDependency(module, feature)))
    sys.exit(1)


#: Unicode glyphs the tools like to use, with an ASCII fallback for consoles
#: running a legacy code page (cp437/cp1252), where printing them raises
#: UnicodeEncodeError and takes the whole command down.
_GLYPHS = {
    "folder": ("\U0001f4c1", "[D]"),
    "file": ("\U0001f4c4", "--"),
    "arrow": ("\u2192", "->"),
    "bullet": ("\u2022", "*"),
    "up": ("\u2191", "up"),
    "down": ("\u2193", "dn"),
}


def safe_glyphs():
    """Resolve the glyph table against what stdout can actually encode."""
    encoding = (getattr(sys.stdout, "encoding", None) or "ascii").lower()
    resolved = {}
    for name, (pretty, fallback) in _GLYPHS.items():
        try:
            pretty.encode(encoding)
            resolved[name] = pretty
        except (UnicodeEncodeError, LookupError):
            resolved[name] = fallback
    return resolved
