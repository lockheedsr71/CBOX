"""ANSI colour definitions shared by every CBOX tool."""

import os
import sys

__all__ = ["Colors", "init_color", "supports_color"]


class Colors:
    """Raw ANSI escape codes.

    The tools colourise their own output, so these stay as plain escape
    strings rather than colorama constants: they are embedded in f-strings
    that get written to log files as well as the terminal.
    """

    BLUE_BG = "\033[97;44m"
    CYAN_BG = "\033[30;46m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    DIM = "\033[2m"
    BRIGHT_BLUE = "\033[94m"
    BOLD_WHITE_ON_BLUE = "\033[1;37;44m"


def supports_color():
    """True when ANSI escapes should be emitted."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("CBOX_FORCE_COLOR"):
        return True
    return os.environ.get("TERM") != "dumb"


def init_color():
    """Enable ANSI processing on legacy Windows consoles.

    Modern terminals (Windows Terminal, ConEmu, VS Code) already interpret
    escape sequences. Old conhost.exe only starts doing so after it has seen
    a 0x1A byte on stdout, which is what `os.system("")` used to trigger.
    """
    if not supports_color():
        return
    if sys.platform != "win32":
        return

    if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
        return  # Windows Terminal / VS Code handle ANSI natively

    try:
        import colorama  # noqa: F401
    except ImportError:
        os.system("")  # pragma: no cover - best effort side effect
