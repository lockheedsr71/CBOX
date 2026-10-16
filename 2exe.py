"""Build every CBOX tool into a standalone EXE with PyInstaller.

Replaces the old pair of near-identical scripts (2exe.py / compilit.py).
The tool list and version number come from cbox_core, so there is a single
source of truth instead of a hand-maintained projfiles.txt.

Usage:
    python 2exe.py                 # build every tool found in cbox_core.TOOLS
    python 2exe.py cpi cro         # build only the named tools
    python 2exe.py --no-metadata   # skip the version-info resource
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import TOOLS, __version__

ROOT = os.path.dirname(os.path.abspath(__file__))
# Generated artefacts belong here, not in the repository root.
WORK_DIR = os.path.join(ROOT, "build", "version")
DIST_DIR = os.path.join(ROOT, "dist")


def ask_metadata():
    """Prompt for the resource metadata shared by every EXE."""
    print("Enter EXE metadata (used for all tools):")
    return {
        "description": input("File Description: ").strip() or "CBOX CLI Tool",
        "product": input("Product Name: ").strip() or "CBOX",
        "company": input("Company Name: ").strip() or "FOXNET Group",
        "copyright": input("Copyright: ").strip(),
    }


def create_version_file(exe_name, meta):
    """Write a PyInstaller version resource and return its path."""
    os.makedirs(WORK_DIR, exist_ok=True)
    path = os.path.join(WORK_DIR, f"{exe_name}_version_info.txt")

    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={_tuple(__version__)},
    prodvers={_tuple(__version__)},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{meta["company"]}'),
          StringStruct('FileDescription', '{meta["description"]}'),
          StringStruct('FileVersion', '{__version__}'),
          StringStruct('InternalName', '{exe_name}'),
          StringStruct('OriginalFilename', '{exe_name}.exe'),
          StringStruct('ProductName', '{meta["product"]}'),
          StringStruct('ProductVersion', '{__version__}'),
          StringStruct('LegalCopyright', '{meta["copyright"]}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


def _tuple(version):
    parts = [int(p) for p in version.split(".") if p.isdigit()]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def ensure_pyinstaller():
    if subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                      capture_output=True).returncode == 0:
        return True
    print("PyInstaller is not installed in this environment. Installing...")
    return subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"]).returncode == 0


def build_tool(exe_name, script_path, meta=None, windowed=False):
    """Build one EXE. Returns True on success."""
    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--name", exe_name,
        "--distpath", DIST_DIR,
        "--workpath", os.path.join(ROOT, "build", exe_name),
        "--specpath", os.path.join(ROOT, "build"),
        # cbox_core must ship inside the EXE.
        "--paths", ROOT,
        "--hidden-import", "cbox_core",
    ]

    if windowed:
        # Console tools are useless without a console, but a double-click
        # user wants the window suppressed.
        command.append("--windowed")

    version_file = None
    if meta:
        version_file = create_version_file(exe_name, meta)
        command += ["--version-file", version_file]

    command.append(script_path)

    try:
        result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
        if result.returncode == 0:
            return True
        log_path = os.path.join(ROOT, "build", f"error_{exe_name}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write(result.stdout + "\n" + result.stderr)
        print(f"  log: {log_path}")
        return False
    finally:
        if version_file and os.path.isfile(version_file):
            os.remove(version_file)


def main():
    parser = argparse.ArgumentParser(description="Build CBOX tools into EXE files")
    parser.add_argument("tools", nargs="*", help="Tool names to build (default: all)")
    parser.add_argument("--no-metadata", action="store_true", help="Skip the version-info resource")
    parser.add_argument("--no-confirm", action="store_true", help="Do not prompt for EXE metadata")
    parser.add_argument("--windowed", action="store_true", help="Build without a console window")
    args = parser.parse_args()

    names = [n.strip().lower() for n in args.tools if n.strip()] or sorted(TOOLS)

    unknown = [n for n in names if n not in TOOLS]
    if unknown:
        parser.error(f"Unknown tool(s): {', '.join(unknown)}. Known: {', '.join(sorted(TOOLS))}")

    if not ensure_pyinstaller():
        print("PyInstaller could not be installed; aborting.")
        return 3

    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)

    meta = None if args.no_metadata or args.no_confirm else ask_metadata()

    print(f"\nCBOX {__version__} - building {len(names)} tool(s) into {DIST_DIR}\n")

    report = []
    for name in names:
        script = os.path.join(ROOT, TOOLS[name])
        if not os.path.isfile(script):
            report.append((name, False, "source file missing"))
            print(f"[ {name:<10} ] SKIP  (missing {TOOLS[name]})")
            continue

        print(f"[ {name:<10} ] building...")
        ok = build_tool(name, script, meta, windowed=args.windowed)
        report.append((name, ok, "ok" if ok else "failed"))
        print(f"[ {name:<10} ] {'done' if ok else 'FAILED'}")

    print("\n=== BUILD REPORT ===")
    for name, ok, note in report:
        marker = "OK  " if ok else "FAIL"
        print(f"  {marker} {name:<10} {note}")
    print(f"\nOutput folder: {DIST_DIR}")
    return 0 if all(ok for _, ok, _ in report) else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
