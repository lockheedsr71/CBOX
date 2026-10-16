"""cro - traceroute with optional Geo-IP and ASN annotations."""

import argparse
import os
import platform
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import Fore, Style, init

from cbox_core import __version__
from cbox_core.colors import init_color
from cbox_core.netutil import get_ip_info, is_private_ip

init(autoreset=True)

IPV4_RE = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def annotate_hop(ip, show_geo=False, show_asn=False):
    """Annotation suffix for one hop, or an empty string."""
    if not ip or not (show_geo or show_asn):
        return ""
    if is_private_ip(ip):
        return f" {Fore.LIGHTBLACK_EX}[Internal Network]{Style.RESET_ALL}"

    info = get_ip_info(ip)
    if not info:
        return f" {Fore.LIGHTBLACK_EX}[geo unavailable]{Style.RESET_ALL}"

    parts = []
    if show_geo:
        location = ", ".join(p for p in (info["country"], info["city"]) if p)
        if location:
            parts.append(location)
    if show_asn:
        isp = info["isp"]
        asn = f"AS{info['asn']}" if info["asn"] else ""
        if isp and asn:
            parts.append(f"{isp} ({asn})")
        elif isp:
            parts.append(isp)

    if not parts:
        return ""
    return f" {Fore.YELLOW}[{' | '.join(parts)}]{Style.RESET_ALL}"


def main():
    print(f"{Fore.LIGHTBLUE_EX}cro {__version__} - Croute Pro by FOXNET (CBOX Tools) {Style.RESET_ALL}")

    parser = argparse.ArgumentParser(
        description="Professional Fast Traceroute with Optional Geo-IP & ASN Info",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  cro 8.8.8.8 -g -a -o log.txt",
    )
    parser.add_argument("target", nargs="?", default=None, help="Target IP or Domain")
    parser.add_argument("-m", "--max-hops", type=int, default=20, help="Maximum hops (default: 20)")
    parser.add_argument("-g", "--geo", action="store_true", help="Show geographic info (country, city)")
    parser.add_argument("-a", "--asn", action="store_true", help="Show ISP and AS number")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to save the log file")

    args = parser.parse_args()

    if args.target is None:
        parser.print_help()
        return 1

    if platform.system().lower() == "windows":
        command = ["tracert", "-d", "-h", str(args.max_hops), args.target]
    else:
        command = ["traceroute", "-n", "-m", str(args.max_hops), args.target]

    print(f"{Fore.CYAN}Tracing route to {args.target}...")
    print(f"{Fore.WHITE}Settings: Geo={args.geo}, ASN={args.asn}, MaxHops={args.max_hops}{Style.RESET_ALL}\n")

    output_file = None
    try:
        # The log handle stays open for the whole trace so each hop can be
        # appended as it arrives rather than buffered until the end.
        if args.output:
            # Held open for the whole trace so each hop is appended as it
            # arrives; closed in the finally block below.
            output_file = open(args.output, "a", encoding="utf-8")  # noqa: SIM115

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace",
        )

        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith(("Tracing", "Over")):
                continue

            match = IPV4_RE.search(clean_line)
            info = annotate_hop(match.group(), args.geo, args.asn) if match else ""

            if "*" in clean_line:
                print(f"{Fore.RED}{clean_line}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}{clean_line}{info}{Style.RESET_ALL}")

            if output_file:
                # Strip ANSI codes so the log stays readable in an editor.
                output_file.write(f"{_strip_ansi(clean_line)}{info}\n")

        return process.wait()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Trace stopped by user.{Style.RESET_ALL}")
        return 1
    except FileNotFoundError:
        tool = "tracert" if platform.system().lower() == "windows" else "traceroute"
        print(f"{Fore.RED}Error: '{tool}' was not found on this system.{Style.RESET_ALL}")
        return 1
    finally:
        if output_file:
            output_file.close()


def _strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


if __name__ == "__main__":
    init_color()
    sys.exit(main() or 0)
