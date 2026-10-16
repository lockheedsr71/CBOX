"""IP classification and cached Geo-IP lookups.

Two things this centralises:

* `is_private_ip` now uses :mod:`ipaddress` instead of hand-written regexes,
  which fixes the ranges the regexes missed (link-local 169.254/16, CGNAT
  100.64/10, IPv6 unique-local and link-local).
* Geo lookups go over HTTPS to `ipwho.is`, which needs no API key. The old
  code used `ip-api.com` over plain HTTP: that endpoint is HTTP-only on the
  free tier (HTTPS answers 403) and rate-limits to 45 requests/minute, which
  ntpmon blew through immediately by querying once per connection.
"""

import ipaddress
import threading
import time

__all__ = [
    "GEO_ENDPOINT",
    "clear_cache",
    "geo_label",
    "get_ip_info",
    "is_private_ip",
    "is_valid_ip",
    "isp_label",
]

GEO_ENDPOINT = "https://ipwho.is/{ip}"

DEFAULT_TIMEOUT = 2.0
#: Negative results are cached briefly too, so a slow or blocked endpoint
#: cannot turn into a request storm on every refresh tick.
FAILURE_TTL = 60.0

_cache = {}
_lock = threading.Lock()


def is_valid_ip(value):
    """True when `value` parses as an IPv4/IPv6 address."""
    try:
        ipaddress.ip_address(value.strip())
    except (ValueError, AttributeError):
        return False
    return True


def is_private_ip(ip):
    """True for loopback, RFC1918, link-local, CGNAT, multicast and reserved."""
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False

    if addr.is_private or addr.is_loopback or addr.is_link_local:
        return True
    if addr.is_multicast or addr.is_reserved or addr.is_unspecified:
        return True
    # Carrier-grade NAT (100.64.0.0/10) is neither private nor global.
    return addr.version == 4 and addr in ipaddress.ip_network("100.64.0.0/10")


def clear_cache():
    with _lock:
        _cache.clear()


def get_ip_info(ip, timeout=DEFAULT_TIMEOUT):
    """Geo/ASN details for `ip`.

    Returns a dict with `country`, `city`, `isp` and `asn` on success, or
    None when the address is local, malformed or the lookup failed. Results
    are cached; failures are cached for :data:`FAILURE_TTL` seconds.
    """
    if not ip or not is_valid_ip(ip):
        return None
    if is_private_ip(ip):
        return None

    ip = ip.strip()
    now = _monotonic()
    with _lock:
        cached = _cache.get(ip)
        if cached is not None:
            value, expires_at = cached
            if now < expires_at:
                return value

    try:
        import requests

        response = requests.get(GEO_ENDPOINT.format(ip=ip), timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except Exception:
        # Offline, timed out, DNS blocked, rate limited - all non-fatal.
        # The caller shows a placeholder instead of a hard error.
        _store(ip, None, FAILURE_TTL)
        return None

    if not data.get("success"):
        _store(ip, None, FAILURE_TTL)
        return None

    connection = data.get("connection") or {}
    info = {
        "country": data.get("country") or "",
        "city": data.get("city") or "",
        "isp": connection.get("isp") or connection.get("org") or "",
        "asn": connection.get("asn"),
    }
    _store(ip, info, 3600.0)
    return info


def geo_label(ip):
    """Short human-readable location for `ip`, or '-' when unavailable."""
    info = get_ip_info(ip)
    if not info:
        return "-" if is_private_ip(ip) else "Unknown"
    parts = [p for p in (info["country"], info["city"]) if p]
    return ", ".join(parts) if parts else "Unknown"


def isp_label(ip):
    """`ISP (AS12345)` for `ip`, or '-' when unavailable."""
    info = get_ip_info(ip)
    if not info:
        return "-"
    isp = info["isp"]
    asn = info["asn"]
    if not isp:
        return "-"
    return f"{isp} (AS{asn})" if asn else isp


def _store(ip, value, ttl):
    with _lock:
        _cache[ip] = (value, _monotonic() + ttl)


def _monotonic():
    return time.monotonic()
