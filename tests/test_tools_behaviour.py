"""Tests for the pure helpers inside the individual tools."""

import os
import re
import sys

import pytest

import cro
import netinf
import nscn


@pytest.mark.parametrize("spec,expected", [
    ("80", (80, 80)),
    ("80-443", (80, 443)),
    ("443-80", (80, 443)),      # reversed ranges are normalised
    ("1-65535", (1, 65535)),
])
def test_parse_port_range(spec, expected):
    assert nscn.parse_port_range(spec) == expected


@pytest.mark.parametrize("spec", ["0", "65536", "abc", "80-", "-", "80-abc", "80..90"])
def test_parse_port_range_rejects_bad_input(spec):
    with pytest.raises(ValueError):
        nscn.parse_port_range(spec)


def test_is_private_ip_still_importable_from_cro():
    """cro used to define this itself; it now re-exports the shared version."""
    assert cro.is_private_ip("192.168.1.1") is True
    assert cro.is_private_ip("8.8.8.8") is False


def test_decode_windows_output_handles_latin_and_utf8():
    assert netinf.decode_windows_output("caf\xe9".encode("cp1252")) == "caf\xe9"
    assert netinf.decode_windows_output("caf\xe9".encode()) == "caf\xe9"


def test_decode_windows_output_never_raises():
    # Undecodable bytes must degrade, not crash the whole report.
    assert isinstance(netinf.decode_windows_output(b"\xff\xfe\x00\x81"), str)


def test_primary_dns_is_extracted():
    adapter = "DNS Servers . . . . . . . . . . . . : 192.168.1.1\n   8.8.8.8\n"
    assert netinf._primary_dns(adapter) == "192.168.1.1"


def test_secondary_dns_is_extracted():
    adapter = (
        "   DNS Servers . . . . . . . . . . . . : 192.168.1.1\n"
        "   1.1.1.1\n"
        "   Link-local IPv6 Address . . . . . : fe80::1\n"
    )
    assert "1.1.1.1" in netinf._secondary_dns(adapter)


def test_secondary_dns_handles_a_missing_dns_block():
    """The old code did adapter.split('DNS Servers')[1] and could IndexError."""
    assert netinf._secondary_dns("Some Adapter with no DNS block") == []


def test_a_missing_field_does_not_swallow_the_next_row():
    """`\\s` in the field regex matched newlines, so an absent row read the next."""
    adapter = (
        "   Description . . . . . . . : WireGuard Tunnel\n"
        "   DHCP Enabled. . . . . . . . . . . . . : No\n"
    )
    pattern = netinf._field("Physical Address", ".*")
    assert re.search(pattern, adapter) is None


def test_split_adapters_names_each_block():
    output = (
        "Windows IP Configuration\r\n"
        "\r\n"
        "Ethernet adapter Ethernet:\r\n"
        "   Physical Address. . . . . . . . . : AA-BB-CC-DD-EE-FF\r\n"
        "   IPv4 Address. . . . . . . . . . . : 192.168.1.10\r\n"
        "\r\n"
        "Wireless LAN adapter Wi-Fi:\r\n"
        "   IPv4 Address. . . . . . . . . . . : 10.0.0.5\r\n"
    )
    adapters = netinf.split_adapters(output)
    names = [name for name, _ in adapters]
    assert "Windows IP Configuration" in names
    assert "Ethernet adapter Ethernet" in names      # trailing ':' stripped
    assert "Wireless LAN adapter Wi-Fi" in names

    ethernet = dict(adapters)["Ethernet adapter Ethernet"]
    assert "192.168.1.10" in ethernet
    assert "10.0.0.5" not in ethernet                # blocks stay separate


def test_field_pattern_accepts_any_dot_run_length():
    """ipconfig's padding width varies between Windows versions."""
    for dots in (" . . . .", " . . . . . . . . . . . . . ."):
        row = f"   DNS Servers{dots} : 8.8.8.8\n"
        found = re.search(netinf._field("DNS Servers", r"[\d\.]+"), row)
        assert found and found.group(1) == "8.8.8.8"


def test_colors_define_red():
    """netinf referenced Colors.RED in its error path but never defined it."""
    from cbox_core.colors import Colors

    for name in ("RED", "GREEN", "YELLOW", "CYAN", "MAGENTA", "WHITE", "RESET"):
        assert getattr(Colors, name).startswith("\033")


def test_clean_path_input_strips_quotes():
    import cdir

    assert cdir.clean_path_input(['"C:\\Program', 'Files"']) == "C:\\Program Files"
    assert cdir.clean_path_input([]) == ""


def test_glyphs_fall_back_on_a_legacy_console(monkeypatch):
    """Emoji used to crash cdir on a cp1252 console with UnicodeEncodeError."""
    import io

    from cbox_core.console import safe_glyphs

    class LegacyStdout(io.TextIOWrapper):
        pass

    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))
    for glyph in safe_glyphs().values():
        glyph.encode("cp1252")  # must not raise

    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="utf-8"))
    pretty = safe_glyphs()
    assert pretty["folder"] == "\U0001f4c1"


def test_cdir_renders_on_a_cp1252_console(monkeypatch, tmp_path, capsys):
    """End-to-end: a legacy code page must not kill the listing."""
    import io

    import cdir

    monkeypatch.setattr(sys, "argv", ["cdir.py", "-a", str(tmp_path)])
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))

    assert cdir.list_files() == 0


def test_get_owner_degrades_without_pywin32():
    import cdir

    # Never raises, regardless of whether pywin32 is installed.
    assert isinstance(cdir.get_owner(os.getcwd()), str)


def test_format_addr_handles_unbound_sockets():
    """ntstat crashed on UDP rows where laddr is None."""
    import ntstat

    class Addr:
        ip = "10.0.0.5"
        port = 443

    assert ntstat._format_addr(None) == "-"
    assert ntstat._format_addr(Addr()) == "10.0.0.5:443"
    assert ntstat._format_addr(type("A", (), {"ip": None, "port": None})()) == "-"
