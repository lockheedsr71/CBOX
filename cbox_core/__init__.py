"""Shared helpers for the CBOX toolkit.

This package holds the pieces that used to be copy-pasted into every tool:
colour definitions, tool discovery, IP/geo lookups and optional-dependency
handling. Keeping them here means a fix lands in one place only.
"""

__version__ = "1.2.0"

#: Canonical tool name -> script filename. cbox.py uses this to build its
#: alias table and the release builder uses it to build every EXE.
TOOLS = {
    "cdir": "cdir.py",
    "cpi": "cpi.py",
    "cro": "cro.py",
    "cwho": "cwho.py",
    "cport": "cport.py",
    "csweep": "csweep.py",
    "chash": "chash.py",
    "cwlan": "cwlan.py",
    "netdetail": "netinf.py",
    "ntstat": "ntstat.py",
    "ntpmon": "ntpmon.py",
    "nscn": "nscn.py",
}

__all__ = ["TOOLS", "__version__"]
