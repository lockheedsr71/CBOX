"""JSON output shared by the tools that accept `--json`.

Every tool that can emit machine-readable rows routes through here so that
the output shape is consistent (one JSON document, no ANSI escapes, UTF-8
that survives a Windows console) and so `--json` is a one-line change rather
than a per-tool reimplementation.
"""

import json
import sys

__all__ = ["add_json_flag", "emit_json", "json_requested"]


def add_json_flag(parser, help_text="Emit machine-readable JSON instead of a table"):
    parser.add_argument("--json", action="store_true", help=help_text)
    return parser


def json_requested(namespace):
    return bool(getattr(namespace, "json", False))


def emit_json(payload):
    """Write `payload` as JSON to stdout.

    Errors go to stderr and the exit code stays 0: this is a data format, not
    a control channel, so a consumer parsing stdout should not have to
    distinguish "failed" from "empty result".
    """
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    try:
        sys.stdout.write(text + "\n")
    except UnicodeEncodeError:
        # Legacy console: fall back to escapes rather than losing the payload.
        sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")
    sys.stdout.flush()
