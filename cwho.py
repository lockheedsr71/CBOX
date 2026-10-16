"""cwho - WHOIS lookup for domains and IP addresses."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import Fore, Style, init

from cbox_core import __version__

init(autoreset=True)

FIELDS = (
    ("Domain Name", "domain_name"),
    ("Registrar", "registrar"),
    ("Whois Server", "whois_server"),
    ("Creation Date", "creation_date"),
    ("Expiration Date", "expiration_date"),
    ("Name Servers", "name_servers"),
    ("Status", "status"),
    ("Emails", "emails"),
    ("Country", "country"),
)


def _stringify(value):
    """python-whois returns lists for most fields and bare strings for others."""
    if value is None:
        return "N/A"
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item) for item in value) or "N/A"
    return str(value)


def get_domain_info(target, output_file=None):
    try:
        import whois
    except ImportError:
        print(
            f"{Fore.RED}Error: 'python-whois' is not installed.{Style.RESET_ALL}\n"
            f"  Install it with: {Fore.CYAN}python -m pip install python-whois{Style.RESET_ALL}"
        )
        return 1

    print(f"{Fore.CYAN}Fetching WHOIS information for: {target}...")

    try:
        record = whois.whois(target)
    except Exception as exc:
        print(f"{Fore.RED}Error: Could not retrieve information. ({exc})")
        return 1

    report = [f"\n=== WHOIS REPORT BY FOXNET === (cwho {__version__})"]

    for label, attribute in FIELDS:
        value = _stringify(getattr(record, attribute, None))
        print(f"{Fore.YELLOW}{label:<16}: {Fore.WHITE}{value}")
        report.append(f"{label:<16}: {value}")

    if output_file:
        try:
            with open(output_file, "a", encoding="utf-8") as handle:
                handle.write("\n".join(report) + "\n" + ("-" * 30) + "\n")
            print(f"\n{Fore.GREEN}Report saved to: {output_file}")
        except OSError as exc:
            print(f"{Fore.RED}Could not write '{output_file}': {exc}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Domain/IP Ownership Information (WHOIS)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", nargs="?", help="Domain name or IP address (e.g. google.com)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to save the report")

    args = parser.parse_args()

    if not args.target:
        parser.print_help()
        return 1

    return get_domain_info(args.target, args.output)


if __name__ == "__main__":
    sys.exit(main() or 0)
