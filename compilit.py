import os
import subprocess
from tqdm import tqdm
from colorama import init, Fore, Style

# Initialize colorama for colored Latin output
init(autoreset=True)

def main():
    input_file = "projfiles.txt"
    
    # Check if the list file exists [cite: 1]
    if not os.path.exists(input_file):
        print(f"{Fore.RED}Error: '{input_file}' not found in the current directory.")
        return

    # Read filenames from projfiles.txt
    with open(input_file, "r", encoding="utf-8") as f:
        # Get only the first word (filename) from each line
        files_to_build = [line.split()[0] for line in f if line.strip()]

    if not files_to_build:
        print(f"{Fore.YELLOW}No files found in {input_file} to process.")
        return

    print(f"{Fore.CYAN}{Style.BRIGHT}Starting Build Process...")
    print(f"{Fore.WHITE}Target Files: {len(files_to_build)}\n")
    
    report = []

    # Main progress bar
    for py_script in tqdm(files_to_build, desc="Overall Progress", unit="file"):
        
        # Verify if the .py file actually exists on disk [cite: 1, 8]
        if not os.path.exists(py_script):
            report.append(f"{Fore.RED}Missing: {py_script}")
            continue

        # Construct the minimal PyInstaller command [cite: 3, 11]
        # --onefile: Create a single executable
        # --noconfirm: Replace output directory without asking
        # --clean: Clean PyInstaller cache before building
        cmd = [
            "python", "-m", "PyInstaller",
            "--onefile",
            "--noconfirm",
            "--clean",
            py_script
        ]

        try:
            # Execute the build [cite: 5, 11]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                report.append(f"{Fore.GREEN}Success: {py_script}")
            else:
                report.append(f"{Fore.RED}Failed: {py_script}")
                # Log the error for the specific file if it fails [cite: 1, 4]
                with open(f"error_{py_script}.log", "w") as error_log:
                    error_log.write(result.stderr)
        
        except Exception as e:
            report.append(f"{Fore.RED}Exception in {py_script}: {str(e)}")

    # Final Summary Report
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== FINAL BUILD REPORT ===")
    print(f"{Fore.WHITE}{'-' * 30}")
    for status in report:
        print(status)
    print(f"{Fore.WHITE}{'-' * 30}")
    print(f"{Fore.CYAN}Check the 'dist' folder for your EXE files.")

if __name__ == "__main__":
    main()