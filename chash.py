"""chash - file and directory hashing."""

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.console import MissingDependency, rich_toolkit
from cbox_core.jsonout import add_json_flag, emit_json, json_requested

ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}

#: 8 MiB reads large files without thrashing the page cache.
CHUNK = 8 * 1024 * 1024


def hash_file(path, algorithms, progress=False):
    """Hash `path` with every named algorithm in a single pass over the file."""
    digests = {name: factory() for name, factory in algorithms.items()}
    size = os.path.getsize(path)
    read = 0

    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            read += len(chunk)
            for digest in digests.values():
                digest.update(chunk)
            if progress:
                pct = read / size * 100 if size else 100.0
                sys.stderr.write(f"\r  hashing... {pct:5.1f}%")
                sys.stderr.flush()

    if progress:
        sys.stderr.write("\r" + " " * 30 + "\r")
        sys.stderr.flush()

    return {name: digest.hexdigest() for name, digest in digests.items()}, size


def walk_files(root, recursive, follow_links=False):
    """Yield (path, relative_display) for the files under `root`."""
    if os.path.isfile(root):
        yield root, os.path.basename(root)
        return

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_links):
            dirnames.sort()
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                yield full, os.path.relpath(full, root)
    else:
        for name in sorted(os.listdir(root)):
            full = os.path.join(root, name)
            if os.path.isfile(full):
                yield full, name


def main():
    parser = argparse.ArgumentParser(
        description=f"CBOX chash {__version__} - Hash files and verify checksums",
    )
    parser.add_argument("paths", nargs="+", help="Files, or directories with -r")
    parser.add_argument("-a", "--algo", action="append", choices=sorted(ALGORITHMS),
                        help="Algorithm (repeatable, default: sha256)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Walk directories")
    parser.add_argument("-c", "--check", action="store_true",
                        help="Verify: treat each path as '<file> <expected-digest>'")
    parser.add_argument("--no-follow-links", action="store_false", dest="follow_links",
                        help="Do not follow symlinks while recursing")
    add_json_flag(parser)
    args = parser.parse_args()

    names = args.algo or ["sha256"]
    algorithms = {name: ALGORITHMS[name] for name in dict.fromkeys(names)}

    if args.check:
        return run_check(args, names)
    return run_hash(args, algorithms)


def run_hash(args, algorithms):
    results = []
    failures = []

    for root in args.paths:
        if not os.path.exists(root):
            failures.append({"path": root, "error": "not found"})
            continue

        try:
            files = list(walk_files(root, args.recursive, args.follow_links))
        except OSError as exc:
            failures.append({"path": root, "error": str(exc)})
            continue

        for full, display in files:
            try:
                digests, size = hash_file(full, algorithms)
            except (OSError, PermissionError) as exc:
                failures.append({"path": display, "error": str(exc)})
                continue
            results.append({"path": full, "display": display, "size": size, "digests": digests})

    if json_requested(args):
        emit_json({
            "tool": "chash", "version": __version__,
            "algorithms": sorted(algorithms), "count": len(results),
            "files": results, "errors": failures,
        })
        return 1 if failures and not results else 0

    if failures:
        print_failed(failures)
    if not results:
        if not failures:
            print("No files matched.")
        return 1 if failures else 0

    Console, Table, box, *_ = rich_toolkit()
    console = Console()

    width = max(len(row["display"]) for row in results)
    width = min(width, 40)
    table = Table(title="CBOX Hashes", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("File", width=width, style="white")
    table.add_column("Size", justify="right", style="dim")
    for name in sorted(algorithms):
        table.add_column(name.upper(), style="bold yellow", overflow="fold")

    for row in results:
        table.add_row(row["display"], _format_size(row["size"]),
                      *[row["digests"][name] for name in sorted(algorithms)])

    console.print(table)
    return 0


def run_check(args, names):
    """Compare a file's digest against the one supplied on the command line."""
    Console, Table, box, *_ = rich_toolkit()
    console = Console()

    table = Table(title="CBOX Checksum Verification", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("File", style="white")
    table.add_column("Algorithm", style="cyan")
    table.add_column("Result", justify="center")

    failures = []
    checked = 0

    for spec in args.paths:
        # Split on the last whitespace group so paths containing spaces survive.
        parts = spec.rsplit(None, 1)
        if len(parts) != 2:
            console.print(f"[red]Expected '<file> <digest>', got '{spec}'[/red]")
            failures.append(spec)
            continue

        path, expected = parts
        expected = expected.strip().lower()

        if not os.path.isfile(path):
            table.add_row(path, "-", "[red]MISSING[/red]")
            failures.append(path)
            continue

        name = _match_algorithm(expected, names)
        if name is None:
            table.add_row(os.path.basename(path), "-", "[red]UNKNOWN LENGTH[/red]")
            failures.append(path)
            continue

        digests, _ = hash_file(path, {name: ALGORITHMS[name]})
        actual = digests[name]
        checked += 1

        if actual == expected:
            table.add_row(os.path.basename(path), name.upper(), "[green]OK[/green]")
        else:
            table.add_row(os.path.basename(path), name.upper(), "[red]MISMATCH[/red]")
            console.print(f"[red]  expected {expected}[/red]")
            console.print(f"[red]  actual   {actual}[/red]")
            failures.append(path)

    if json_requested(args):
        emit_json({
            "tool": "chash", "version": __version__, "mode": "check",
            "checked": checked, "failed": failures, "ok": not failures,
        })
        return 1 if failures else 0

    console.print(table)
    if failures:
        console.print(f"[red]{len(failures)} file(s) failed verification.[/red]")
        return 1
    console.print("[green]All files verified.[/green]")
    return 0


def _match_algorithm(digest, preferred):
    """Pick an algorithm from the digest length, preferring the requested ones."""
    lengths = {"md5": 32, "sha1": 40, "sha256": 64, "sha512": 128}
    for name in preferred:
        if lengths[name] == len(digest):
            return name
    for name, length in lengths.items():
        if length == len(digest):
            return name
    return None


def _format_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} B" if unit == "B" else f"{size:,.1f} {unit}"
        size /= 1024


def print_failed(failures):
    Console, *_ = rich_toolkit()
    console = Console()
    for item in failures:
        console.print(f"[red]{item['path']}: {item['error']}[/red]")


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
