import os
import subprocess
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

INPUT_FILE = "projfiles.txt"


def ask_common_metadata():
    print(Fore.CYAN + Style.BRIGHT + "Enter EXE metadata (used for all files):")
    return {
        "description": input("File Description: ").strip(),
        "product": input("Product Name: ").strip(),
        "company": input("Company Name: ").strip(),
        "copyright": input("Copyright: ").strip()
    }


def create_version_file(py_name, version, meta):
    exe_name = os.path.splitext(py_name)[0]

    version_tuple = tuple(int(x) for x in version.split(".")) + (0, 0, 0, 0)
    version_tuple = version_tuple[:4]

    content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
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
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', '{exe_name}'),
          StringStruct('OriginalFilename', '{exe_name}.exe'),
          StringStruct('ProductName', '{meta["product"]}'),
          StringStruct('ProductVersion', '{version}'),
          StringStruct('LegalCopyright', '{meta["copyright"]}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    filename = f"version_{exe_name}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content.strip())

    return filename


def main():
    if not os.path.exists(INPUT_FILE):
        print(Fore.RED + f"Error: '{INPUT_FILE}' not found.")
        return

    with open(INPUT_FILE, encoding="utf-8") as f:
        entries = [line.split() for line in f if len(line.split()) >= 2]

    if not entries:
        print(Fore.YELLOW + "No valid entries found.")
        return

    metadata = ask_common_metadata()

    print(Fore.CYAN + Style.BRIGHT + "\nStarting Build Process...\n")
    report = []

    for py_file, version in tqdm(entries, desc="Overall Progress", unit="file"):
        if not os.path.exists(py_file):
            report.append(Fore.RED + f"Missing: {py_file}")
            continue

        version_file = create_version_file(py_file, version, metadata)

        cmd = [
            "python", "-m", "PyInstaller",
            "--onefile",
            "--noconfirm",
            "--clean",
            "--version-file", version_file,
            py_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            report.append(Fore.GREEN + f"Success: {py_file} ({version})")
            os.remove(version_file)
        else:
            report.append(Fore.RED + f"Failed: {py_file}")
            with open(f"error_{py_file}.log", "w", encoding="utf-8") as log:
                log.write(result.stderr)

    print(Fore.MAGENTA + Style.BRIGHT + "\n=== FINAL BUILD REPORT ===")
    print("-" * 40)
    for r in report:
        print(r)
    print("-" * 40)
    print(Fore.CYAN + "Check the 'dist' folder for EXE files.")


if __name__ == "__main__":
    main()
