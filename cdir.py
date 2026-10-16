"""cdir - directory lister with rich table output."""

import argparse
import os
import stat
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.console import MissingDependency, rich_toolkit, safe_glyphs
from cbox_core.jsonout import add_json_flag, emit_json, json_requested
from cbox_core.tools import unquote_path

# pywin32 is optional: without it the owner column shows "N/A".
win32security = None
try:
    import win32security
except ImportError:
    pass


def get_owner(path):
    """Windows owner of `path`, or a short placeholder."""
    if win32security is None:
        return "N/A"
    try:
        sd = win32security.GetFileSecurity(str(path), win32security.OWNER_SECURITY_INFORMATION)
        sid = sd.GetSecurityDescriptorOwner()
        name, domain, _ = win32security.LookupAccountSid(None, sid)
        return f"{domain}\\{name}"
    except Exception:
        # AccessDenied, unsupported filesystem, deleted mid-scan - none of
        # these should abort the listing.
        return "Unknown"


def clean_path_input(args_list):
    """Join path fragments and strip stray quotes from the shell layer."""
    return unquote_path(args_list)


def list_files():
    Console, Table, box, *_ = rich_toolkit()
    console = Console()
    glyphs = safe_glyphs()

    parser = argparse.ArgumentParser(description="CBOX cdir - Professional Dir Tool")
    parser.add_argument("-H", "--hidden", action="store_true", help="Show Hidden")
    parser.add_argument("-s", "--system", action="store_true", help="Show System")
    parser.add_argument("-a", "--all", action="store_true", help="Show Owner/Permissions")
    parser.add_argument("--sort", choices=["name", "size", "date"], default="name")
    parser.add_argument("path", nargs="*", help="Target path")
    add_json_flag(parser, "Emit machine-readable JSON instead of a table")

    args = parser.parse_args()

    target_str = clean_path_input(args.path) or "."
    root = Path(os.path.expanduser(os.path.expandvars(target_str))).absolute()

    if not root.exists():
        message = f"Path not found: {root}"
        if json_requested(args):
            emit_json({"tool": "cdir", "version": __version__, "path": str(root),
                       "error": message, "entries": []})
        else:
            Console, *_ = rich_toolkit()
            Console().print(f"[bold red]Error:[/bold red] [yellow]{message}[/yellow]")
        return 1

    Console, Table, box, *_ = rich_toolkit()
    console = Console()

    table = Table(title=f"Listing: {root}", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Attr", justify="center")
    table.add_column("Name")
    table.add_column("Size", justify="right")
    table.add_column("Last Modified", justify="center")

    if args.all:
        table.add_column("Owner", style="blue")
        table.add_column("Permissions", style="magenta")

    try:
        items = list(root.iterdir())
    except PermissionError:
        if json_requested(args):
            emit_json({"tool": "cdir", "version": __version__, "path": str(root),
                       "error": "access denied", "entries": []})
        else:
            console.print("[bold red]Access denied![/]")
        return 1
    except OSError as exc:
        if json_requested(args):
            emit_json({"tool": "cdir", "version": __version__, "path": str(root),
                       "error": str(exc), "entries": []})
        else:
            console.print(f"[bold red]Error:[/] {exc}")
        return 1

    if args.sort == "size":
        items.sort(key=_size_key, reverse=True)
    elif args.sort == "date":
        items.sort(key=_mtime_key, reverse=True)
    else:
        items.sort(key=lambda item: item.name.lower())

    entries = []
    for item in items:
        attr_str, is_h, is_s = _read_attributes(item)

        if is_h and not args.hidden:
            continue
        if is_s and not args.system:
            continue

        is_dir = item.is_dir()
        icon = glyphs["folder"] if is_dir else glyphs["file"]
        name_style = "bold blue" if is_dir else "white"
        size_str, mtime = _size_and_mtime(item, is_dir)
        size_bytes = _size_bytes(item, is_dir)

        row = [attr_str, f"[{name_style}]{icon} {item.name}[/]", size_str, mtime]
        entry = {
            "name": item.name,
            "path": str(item),
            "type": "directory" if is_dir else "file",
            "size": size_bytes,
            "size_human": size_str,
            "modified": mtime,
            "attributes": {"hidden": is_h, "system": is_s},
        }

        if args.all:
            owner = get_owner(item)
            mode = stat.filemode(_safe_stat_mode(item))
            row.append(owner)
            row.append(mode)
            entry["owner"] = owner
            entry["permissions"] = mode

        table.add_row(*row)
        entries.append(entry)

    if json_requested(args):
        emit_json({
            "tool": "cdir", "version": __version__, "path": str(root),
            "count": len(entries), "entries": entries,
        })
        return 0

    console.print(table)
    return 0


def _safe_stat_mode(item):
    try:
        return item.stat().st_mode
    except OSError:
        return 0


def _size_key(item):
    try:
        return item.stat().st_size if item.is_file() else 0
    except OSError:
        return 0


def _mtime_key(item):
    try:
        return item.stat().st_mtime
    except OSError:
        return 0.0


def _read_attributes(item):
    """Windows attribute letters (Hidden/System/ReadOnly), or '---'."""
    try:
        attrs = os.stat(item).st_file_attributes
    except (AttributeError, OSError):
        # Non-Windows platforms have no st_file_attributes.
        return "---", False, False

    is_hidden = bool(attrs & 2)
    is_system = bool(attrs & 4)
    is_readonly = bool(attrs & 1)
    letter = f"{'H' if is_hidden else '-'}{'S' if is_system else '-'}{'R' if is_readonly else '-'}"
    return letter, is_hidden, is_system


def _size_and_mtime(item, is_dir):
    try:
        info = item.stat()
    except OSError:
        return "Error", "Unknown"

    size_str = "DIR" if is_dir else f"{info.st_size / 1024:,.1f} KB"
    mtime = datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M")
    return size_str, mtime


def _size_bytes(item, is_dir):
    if is_dir:
        return None
    try:
        return item.stat().st_size
    except OSError:
        return None


if __name__ == "__main__":
    try:
        sys.exit(list_files() or 0)
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
