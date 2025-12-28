import os
import argparse
import stat
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

# Attempt to load Windows security module to display file owner
try:
    import win32security
except ImportError:
    win32security = None

def get_owner(path):
    if win32security:
        try:
            sd = win32security.GetFileSecurity(str(path), win32security.OWNER_SECURITY_INFORMATION)
            sid = sd.GetSecurityDescriptorOwner()
            name, domain, _ = win32security.LookupAccountSid(None, sid)
            return f"{domain}\\{name}"
        except: return "Unknown"
    return "N/A"

def clean_path_input(args_list):
    """Smart path cleaning from unwanted quotes"""
    # Join all components
    full_str = " ".join(args_list)
    # Remove quotes from start and end
    clean = full_str.strip().strip('"').strip("'")
    # Remove any remaining quotes that may be escaped
    clean = clean.replace('"', '').replace("'", "")
    return clean

def list_files():
    console = Console()
    
    parser = argparse.ArgumentParser(description="Professional Dir Tool", add_help=True)
    parser.add_argument("-H", "--hidden", action="store_true", help="Show Hidden")
    parser.add_argument("-s", "--system", action="store_true", help="Show System")
    parser.add_argument("-a", "--all", action="store_true", help="Show Owner/Permissions")
    parser.add_argument("--sort", choices=['name', 'size', 'date'], default='name')
    parser.add_argument("path", nargs="*", help="Target path")
    
    args = parser.parse_args()

    # Clean the input path
    target_str = clean_path_input(args.path)
    
    if not target_str:
        target_str = "."
    
    # Normalize path for Windows
    root = Path(os.path.normpath(target_str)).absolute()

    if not root.exists():
        console.print(f"[bold red]Error:[/bold red] [yellow]Path not found: '{root}'[/yellow]")
        return

    # Professional table design
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
        
        # Sorting logic
        if args.sort == 'size': 
            items.sort(key=lambda x: x.stat().st_size if x.is_file() else 0, reverse=True)
        elif args.sort == 'date': 
            items.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        else: 
            items.sort(key=lambda x: x.name.lower())

        for item in items:
            try:
                f_attrs = os.stat(item).st_file_attributes
                is_h = f_attrs & 2
                is_s = f_attrs & 4
                attr_str = f"{'H' if is_h else '-'}{'S' if is_s else '-'}{'R' if f_attrs & 1 else '-'}"
            except:
                attr_str, is_h, is_s = "---", False, False

            # Filter hidden and system files
            if is_h and not args.hidden: continue
            if is_s and not args.system: continue

            icon = "📁" if item.is_dir() else "📄"
            name_style = "bold blue" if item.is_dir() else "white"
            
            try:
                size_val = item.stat().st_size
                size_str = f"{size_val / 1024:,.1f} KB" if item.is_file() else "DIR"
                mtime = datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            except:
                size_str, mtime = "Error", "Unknown"
            
            row = [attr_str, f"[{name_style}]{icon} {item.name}[/]", size_str, mtime]
            
            if args.all:
                row.append(get_owner(item))
                row.append(stat.filemode(item.stat().st_mode))
            
            table.add_row(*row)

        console.print(table)

    except PermissionError:
        console.print("[bold red]Access denied![/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")

if __name__ == "__main__":
    list_files()
