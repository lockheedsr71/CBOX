"""cwlan - wireless interface status.

`netsh wlan show interfaces` is the only interface-free way to read Wi-Fi
state, but its output is localised: on a Persian Windows the labels are
Farsi and a naive parse finds nothing. This tool therefore parses by
*position and shape* first and only falls back to English label matching,
and it says so instead of printing an empty report.
"""

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbox_core import __version__
from cbox_core.console import MissingDependency, rich_toolkit
from cbox_core.jsonout import add_json_flag, emit_json, json_requested

#: Label -> English fragment. Matched case-insensitively against the part of
#: each line before the first colon, so a localised build simply misses.
LABELS = {
    "name": ("Name", "نام"),
    "description": ("Description", "شرح"),
    "guid": ("GUID",),
    "physical_address": ("Physical address", "آدرس فیزیکی"),
    "interface_type": ("Interface type", "نوع رابط"),
    "state": ("State", "وضعیت"),
    "radio_status": ("Radio status", "وضعیت رادیو"),
    "ssid": ("SSID", "BSSID", "SSID-BSSID"),
    "band": ("Band", "باند"),
    "channel": ("Channel", "کانال"),
    "radio_type": ("Radio type", "نوع رادیو"),
    "authentication": ("Authentication", "احراز هویت"),
    "encryption": ("Encryption", "رمزگذاری"),
    "connection_mode": ("Connection mode", "حالت اتصال"),
    "signal": ("Signal", "سیگنال"),
    "receive_rate": ("Receive rate", "نرخ دریافت"),
    "transmit_rate": ("Transmit rate", "نرخ ارسال"),
    "profile": ("Profile", "پروفایل"),
}

MAC_RE = re.compile(r"^([0-9A-F]{2}([:-][0-9A-F]{2}){5})$", re.IGNORECASE)
SSID_RE = re.compile(r"^[\x20-\x7e]{1,32}$")


def run_netsh():
    """Return raw `netsh wlan show interfaces` output, or raise."""
    command = ["netsh", "wlan", "show", "interfaces"]
    completed = subprocess.run(command, capture_output=True, timeout=15)
    # netsh exits 1 with a message when there is no wireless interface.
    output = (completed.stdout or b"").decode("utf-8", errors="replace")
    if not output.strip():
        raise OSError("netsh returned no output")
    return output


def has_wireless_interface():
    try:
        output = run_netsh()
    except (OSError, subprocess.SubprocessError):
        return False
    lowered = output.lower()
    return "there is no wireless interface" not in lowered and "no wireless" not in lowered


def parse_interfaces(output):
    """Split netsh output into per-interface dicts.

    Interface blocks start with a count line such as
    'There is 1 interface on the system:'. That marker is localised, so the
    split instead keys off blank-line-separated blocks that contain a MAC
    address, which netsh always prints untranslated.
    """
    blocks = []
    current = []

    for raw in output.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)

    parsed = []
    for block in blocks:
        record = _parse_block(block)
        if record is not None:
            parsed.append(record)
    return parsed


def _parse_block(lines):
    record = {"raw": {}}
    found_mac = False

    for line in lines:
        if ":" not in line:
            continue
        key_text, _, value = line.partition(":")
        key = key_text.strip()
        value = value.strip()
        # netsh nests the per-connection detail one level deeper.
        field = _match_label(key)

        if field is None:
            continue

        if field == "physical_address" and MAC_RE.match(value):
            found_mac = True

        # Some labels repeat (SSID and BSSID share a row); keep the first.
        record.setdefault(field, value)
        record["raw"].setdefault(field, value)

    return record if found_mac else None


def _match_label(key):
    lowered = key.lower()
    for field, fragments in LABELS.items():
        for fragment in fragments:
            if lowered.startswith(fragment.lower()) or fragment.lower() in lowered:
                return field
    return None


def signal_percent(raw):
    """Convert 'Signal : 97%' style text to an integer, or None."""
    match = re.search(r"(\d+)\s*%", raw or "")
    return int(match.group(1)) if match else None


def link_speed_mbps(raw):
    """Convert 'Receive rate : 780 Mbps' to a float, or None."""
    match = re.search(r"([\d.]+)\s*Mbps", raw or "", re.IGNORECASE)
    return float(match.group(1)) if match else None


def summarise(records):
    """Attach derived, display-ready values to each parsed record."""
    for record in records:
        record["signal_percent"] = signal_percent(record.get("signal", ""))
        record["channel"] = _int_or_none(record.get("channel"))
        record["receive_mbps"] = link_speed_mbps(record.get("receive_rate", ""))
        record["transmit_mbps"] = link_speed_mbps(record.get("transmit_rate", ""))
        record["connected"] = _is_connected(record.get("state", ""))
    return records


def _int_or_none(value):
    match = re.search(r"(\d+)", value or "")
    return int(match.group(1)) if match else None


def _is_connected(state):
    lowered = (state or "").lower()
    return "connected" in lowered and "disconnected" not in lowered


def main():
    parser = argparse.ArgumentParser(
        description=f"CBOX cwlan {__version__} - Wireless interface status",
    )
    add_json_flag(parser)
    args = parser.parse_args()

    try:
        output = run_netsh()
    except FileNotFoundError:
        print("netsh is not available on this system.")
        return 1
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Could not read wireless state: {exc}")
        return 1

    lowered = output.lower()
    if "there is no wireless interface" in lowered or "no wireless" in lowered:
        print("No wireless interface is present on this system.")
        if json_requested(args):
            emit_json({"tool": "cwlan", "version": __version__, "interfaces": []})
        return 0

    records = summarise(parse_interfaces(output))

    if json_requested(args):
        emit_json({
            "tool": "cwlan", "version": __version__,
            "count": len(records), "interfaces": records,
        })
        return 0

    if not records:
        # Do not silently print nothing: this almost always means the output
        # was localised beyond recognition.
        print("Could not parse the wireless report.")
        print("This usually means netsh output is localised beyond recognition.")
        print("Raw output follows:")
        print(output)
        return 1

    Console, Table, box, *_ = rich_toolkit()
    console = Console()

    table = Table(title="CBOX Wireless Interfaces", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Interface", style="bold bright_cyan")
    table.add_column("SSID", style="white")
    table.add_column("State", justify="center")
    table.add_column("Signal", justify="right")
    table.add_column("Channel", justify="right", style="cyan")
    table.add_column("Rx / Tx", justify="right", style="dim")

    for record in records:
        state = record.get("state", "?")
        state_cell = "[green]connected[/]" if record["connected"] else f"[yellow]{state}[/]"

        if record["signal_percent"] is None:
            signal_cell = "-"
        else:
            pct = record["signal_percent"]
            colour = "green" if pct >= 70 else "yellow" if pct >= 50 else "red"
            signal_cell = f"[{colour}]{pct}%[/]"

        rx = f"{record['receive_mbps']:.0f}" if record["receive_mbps"] else "-"
        tx = f"{record['transmit_mbps']:.0f}" if record["transmit_mbps"] else "-"

        table.add_row(
            record.get("name", "?"),
            record.get("ssid", "-"),
            state_cell,
            signal_cell,
            str(record["channel"]) if record["channel"] else "-",
            f"{rx} / {tx}" if rx != "-" or tx != "-" else "-",
        )

    console.print(table)

    for record in records:
        extra = []
        if record.get("authentication"):
            extra.append(f"auth={record['authentication']}")
        if record.get("encryption"):
            extra.append(f"encryption={record['encryption']}")
        if record.get("band"):
            extra.append(f"band={record['band']}")
        if extra:
            console.print(f"[dim]  {record.get('name', '?')}: {'  '.join(extra)}[/dim]")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except MissingDependency as exc:
        print(exc)
        sys.exit(1)
