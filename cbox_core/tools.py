"""Locating CBOX tools.

A tool can exist in three shapes, and the shell has to cope with all of
them: a compiled EXE sitting in `dist/`, the plain `.py` in the repository,
or an EXE already installed on `PATH`.

Order matters more than it looks. An EXE found on `PATH` may well be an
older install, and it would silently shadow the source sitting next to
`cbox.py`. So a tool that ships as a script always resolves to that script;
an installed EXE is only used when there is no script to run.
"""

import os
import shutil
import sys

from cbox_core import TOOLS

__all__ = [
    "iter_tools", "logical_drives", "missing_tools", "resolve_tool",
    "tool_script", "unquote_path",
]


def unquote_path(args_list):
    """Join path fragments and strip the shell's quoting.

    The shell splits a command line on whitespace, so `cd "C:\\Program Files"`
    arrives as ['"C:\\Program', 'Files"']. Handing that straight to
    os.chdir fails with WinError 123, so the quotes have to come off.
    """
    joined = " ".join(args_list).strip()
    if len(joined) >= 2 and joined[0] == joined[-1] and joined[0] in ("'", '"'):
        joined = joined[1:-1]
    return joined.replace('"', "").replace("'", "")


def _repo_root():
    """Directory that holds the CBOX scripts (parent of the cbox_core package)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tool_script(name):
    """Absolute path of a tool's source script, or None if it is absent."""
    filename = TOOLS.get(name)
    if not filename:
        return None
    path = os.path.join(_repo_root(), filename)
    return path if os.path.isfile(path) else None


def resolve_tool(name, allow_path=True):
    """Return an argv list able to run `name`, or None if it cannot be found.

    Resolution order:
      1. `dist/<name>.exe` next to the scripts (freshly built from this checkout)
      2. `python <root>/<name>.py` (running from a clone)
      3. `<name>` on PATH (installed system-wide, no script available)
    """
    filename = TOOLS.get(name)
    if not filename:
        return None

    root = _repo_root()

    built = os.path.join(root, "dist", f"{name}.exe" if os.name == "nt" else name)
    if os.path.isfile(built) and (os.name == "nt" or os.access(built, os.X_OK)):
        return [built]

    script = os.path.join(root, filename)
    if os.path.isfile(script):
        return [sys.executable, script]

    if allow_path:
        found = _find_installed(name)
        if found:
            return [found]

    return None


def _find_installed(name):
    """Locate an installed EXE, ignoring anything the CWD happens to shadow."""
    try:
        found = shutil.which(name)
    except Exception:
        return None
    if not found:
        return None

    # On Windows shutil.which also probes the current directory, and PATHEXT
    # can map it to an unrelated .py/.cmd sitting next to us.
    resolved = os.path.abspath(found)
    if os.path.dirname(resolved) == os.path.abspath(os.getcwd()):
        return None
    if os.name == "nt" and not resolved.lower().endswith((".exe", ".com")):
        return None
    return resolved


def iter_tools():
    """Yield (name, path) pairs for every tool that is actually present."""
    for name in sorted(TOOLS):
        script = tool_script(name)
        if script:
            yield name, script


def missing_tools():
    """Names listed in TOOLS whose source script is not on disk."""
    return [name for name in sorted(TOOLS) if not tool_script(name)]


def logical_drives():
    """Yield (drive letter, total bytes, free bytes) for every mounted volume.

    Uses the Win32 API rather than `wmic logicaldisk`, which was removed from
    Windows 11 24H2 and made the shell's `df` fail outright on current builds.
    """
    import shutil

    if os.name != "nt":
        usage = shutil.disk_usage(os.path.abspath(os.sep))
        yield ("/", usage.total, usage.free)
        return

    import ctypes

    mask = ctypes.windll.kernel32.GetLogicalDrives()
    for index in range(26):
        if not mask & (1 << index):
            continue
        letter = f"{chr(ord('A') + index)}:\\"
        try:
            usage = shutil.disk_usage(letter)
        except OSError:
            continue  # removable drive with no media
        yield (letter, usage.total, usage.free)
