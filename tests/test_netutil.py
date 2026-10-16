"""Tests for cbox_core.netutil - IP classification and geo caching."""


import pytest

from cbox_core import netutil


@pytest.mark.parametrize("ip", [
    "127.0.0.1",
    "10.0.0.1",
    "192.168.1.10",
    "172.16.0.1",
    "172.31.255.254",
    "169.254.10.1",      # link-local: missed by the old regex list
    "100.64.0.1",        # CGNAT: missed by the old regex list
    "224.0.0.1",         # multicast
    "0.0.0.0",           # unspecified
    "::1",
    "fe80::1",
    "fd00::1",
])
def test_private_addresses_are_detected(ip):
    assert netutil.is_private_ip(ip) is True


@pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1", "172.15.0.1", "172.32.0.1", "2606:4700::1111"])
def test_public_addresses_are_not_private(ip):
    assert netutil.is_private_ip(ip) is False


@pytest.mark.parametrize("value,expected", [
    ("8.8.8.8", True),
    ("::1", True),
    ("999.1.1.1", False),
    ("not-an-ip", False),
    ("", False),
    (None, False),
])
def test_is_valid_ip(value, expected):
    assert netutil.is_valid_ip(value) is expected


def test_geo_lookup_skips_private_addresses(monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("private addresses must never hit the network")

    monkeypatch.setattr("requests.get", explode)
    netutil.clear_cache()
    assert netutil.get_ip_info("192.168.1.1") is None


def test_geo_lookup_uses_https_and_caches(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "success": True,
                "country": "United States",
                "city": "Mountain View",
                "connection": {"asn": 15169, "isp": "Google LLC"},
            }

    def fake_get(url, timeout=None):
        calls.append(url)
        return Response()

    monkeypatch.setattr("requests.get", fake_get)
    netutil.clear_cache()

    first = netutil.get_ip_info("8.8.8.8")
    second = netutil.get_ip_info("8.8.8.8")

    assert first == second
    assert first["asn"] == 15169
    assert first["isp"] == "Google LLC"
    # One network call: the second lookup was served from the cache.
    assert len(calls) == 1
    assert calls[0].startswith("https://")
    assert "8.8.8.8" in calls[0]


def test_geo_failures_are_cached_to_avoid_a_request_storm(monkeypatch):
    calls = []

    def failing_get(url, timeout=None):
        calls.append(url)
        raise OSError("network unreachable")

    monkeypatch.setattr("requests.get", failing_get)
    netutil.clear_cache()

    for _ in range(5):
        assert netutil.get_ip_info("1.2.3.4") is None

    assert len(calls) == 1


def test_geo_rejects_malformed_addresses(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **k: pytest.fail("no request expected"))
    netutil.clear_cache()
    assert netutil.get_ip_info("definitely-not-an-ip") is None


def test_isp_label_includes_asn(monkeypatch):
    netutil.clear_cache()
    monkeypatch.setattr(netutil, "get_ip_info", lambda ip, timeout=None: {
        "country": "DE", "city": "Berlin", "isp": "Example ISP", "asn": 64500,
    })
    assert netutil.isp_label("8.8.8.8") == "Example ISP (AS64500)"


def test_labels_fall_back_when_lookup_is_unavailable(monkeypatch):
    netutil.clear_cache()
    monkeypatch.setattr(netutil, "get_ip_info", lambda ip, timeout=None: None)
    assert netutil.geo_label("192.168.0.5") == "-"
    assert netutil.geo_label("8.8.8.8") == "Unknown"
