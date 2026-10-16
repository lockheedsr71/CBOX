"""netinf - deep network diagnostics for Windows (IPv4/IPv6/DNS/DHCP)."""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.colors import Colors, init_color

# ipconfig output is localised, so we cannot rely on English labels alone.
# `errors="replace"` keeps us from dying on a console codepage we cannot map.
DECODE_FALLBACKS = ("utf-8", "cp1252", "latin-1")


def decode_windows_output(raw):
    """Decode a byte string from a Windows console tool."""
    for encoding in DECODE_FALLBACKS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def get_net_config():
    init_color()
    try:
        raw = subprocess.check_output(
            "ipconfig /all", shell=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as exc:
        print(f"{Colors.RED}Error: 'ipconfig /all' failed (exit {exc.returncode}).{Colors.RESET}")
        return 1
    except OSError as exc:
        print(f"{Colors.RED}Error: could not run ipconfig ({exc}).{Colors.RESET}")
        return 1

    output = decode_windows_output(raw)

    print(f"\n{Colors.MAGENTA}{'=' * 65}")
    print(f"{f'CBOX NETWORK DIAGNOSTICS v{__version__} (IPv4/IPv6)':^65}")
    print(f"{'=' * 65}{Colors.RESET}\n")

    adapters = split_adapters(output)
    shown = 0

    for adapter_name, adapter in adapters:
        rows = []

        for label, value_pattern in ADAPTER_FIELDS.items():
            found = re.search(_field(label, value_pattern), adapter)
            if found and found.group(1).strip():
                rows.append((label, found.group(1).strip()))

        primary_dns = _primary_dns(adapter)
        for extra in _secondary_dns(adapter):
            if extra != primary_dns:
                rows.append(("Secondary DNS", extra))

        # Skip the "Windows IP Configuration" preamble and virtual adapters
        # that carry no address at all.
        if not rows:
            continue

        print(f"{Colors.BOLD_WHITE_ON_BLUE} INTERFACE: {adapter_name.upper():<53} {Colors.RESET}")
        print(f"{Colors.YELLOW}{'-' * 65}{Colors.RESET}")
        print(f"{Colors.WHITE}{'Property':<25} | {'Value'}{Colors.RESET}")
        print(f"{Colors.YELLOW}{'-' * 65}{Colors.RESET}")

        for label, value in rows:
            print(f"{label:<25} | {Colors.GREEN}{value}{Colors.RESET}")

        print(f"{Colors.YELLOW}{'-' * 65}{Colors.RESET}\n")
        shown += 1

    if not shown:
        print(f"{Colors.YELLOW}No adapters with an address were found.{Colors.RESET}")
    return 0


def split_adapters(output):
    """Split `ipconfig /all` into (adapter name, body) pairs.

    ipconfig puts each adapter name in column 0 on its own line, with every
    property indented underneath. Anything in column 0 therefore starts a new
    block, and the block's first line is the name.
    """
    adapters = []
    name = None
    body = []

    for line in output.splitlines():
        if line[:1].isalnum():
            if name is not None:
                adapters.append((name, "\n".join(body)))
            # Adapter names are printed as "Ethernet:", "VPN - VPN Client:".
            name = line.strip().rstrip(":").strip()
            body = []
        elif name is not None:
            body.append(line)

    if name is not None:
        adapters.append((name, "\n".join(body)))

    return adapters


_SPACE = "[ \t]*"
_DOT_RUN = r"(?:\.[ \t]*)+"
_COLON_VALUE = ":[ \t]*("


def _field(label, value_pattern):
    """Regex for one `ipconfig /all` row.

    ipconfig pads the label column with a run of dots whose length depends on
    the label width, so the exact number of dots is not fixed across Windows
    versions or locales. Match the run instead of hard-coding it.

    Only horizontal whitespace is used. A bare `\\s` also matches newlines,
    which let a missing field run on and swallow the value of the next row.
    """
    return re.escape(label) + _SPACE + _DOT_RUN + _SPACE + _COLON_VALUE + value_pattern + ")"


#: ipconfig value shapes: IPv4, IPv6, MAC/other free text, DHCP flag.
_IPV4 = r"[\d\.]+"
_IPV6 = r"[a-fA-F0-9:]+%?\d*"
_ANY = r".*"

ADAPTER_FIELDS = {
    "Physical Address": _ANY,
    "IPv4 Address": _IPV4,
    "IPv6 Address": _IPV6,
    "Link-local IPv6 Address": _IPV6,
    "Subnet Mask": _IPV4,
    "Default Gateway": r"[\d\.:a-fA-F]+%?\d*",
    "DHCP Server": r"[\d\.:a-fA-F]+%?\d*",
    "DHCP Enabled": _ANY,
    "DNS Servers": r"[\d\.:a-fA-F]+%?\d*",
}


def _primary_dns(adapter):
    found = re.search(_field("DNS Servers", r"[\d\.:a-fA-F]+%?\d*"), adapter)
    return found.group(1).strip() if found else None


def _secondary_dns(adapter):
    """Extra DNS lines listed on their own lines below the DNS Servers row."""
    found = re.search(_field("DNS Servers", r"[\d\.:a-fA-F]+%?\d*"), adapter)
    if not found:
        return []

    # Only the lines immediately after the header, up to the next labelled field.
    tail = adapter[found.end():]
    tail = re.split(r"\n\s*\S[^:\n]*\s(?:\.\s*)+:", tail, maxsplit=1)[0]
    return re.findall(r"^\s+([a-fA-F0-9:]*:[\d\.:a-fA-F%]+|[\d\.]+)\s*$", tail, re.MULTILINE)


if __name__ == "__main__":
    sys.exit(get_net_config() or 0)
