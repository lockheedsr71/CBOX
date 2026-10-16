"""User configuration for the CBOX shell, read from `~/.cboxrc`.

The file is a plain `key = value` list, one per line, so it stays editable by
hand and needs no parser beyond a split:

    # comment
    theme = dark
    history_size = 200
    confirm_destructive = yes
    alias lg = cdir -a --sort size
    alias net = cwho

Aliases extend or override the built-in command table; anything unparseable
is reported with its line number and skipped rather than aborting startup.
"""

import os
from typing import ClassVar

__all__ = ["BOOLEAN_KEYS", "DEFAULT_PATH", "INTEGER_KEYS", "Config", "parse_config"]

DEFAULT_PATH = os.path.join("~", ".cboxrc")

BOOLEAN_KEYS = {"confirm_destructive", "history", "completion", "banner", "color"}
INTEGER_KEYS = {"history_size", "tab_cycle_limit"}
THEMES = ("dark", "light", "plain")


def parse_config(text):
    """Parse rc text into (settings, aliases, errors)."""
    settings = {}
    aliases = {}
    errors = []

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        if line.lower().startswith("alias "):
            body = line[6:].strip()
            name, _, target = body.partition(" ")
            # Both `alias name = cmd` and `alias name cmd` are accepted; the
            # '=' is what save() writes, so it has to parse too.
            target = target.strip().lstrip("=").strip()
            if not name or not target:
                errors.append((number, f"alias needs a name and a command: {line!r}"))
                continue
            aliases[name.strip().lower()] = target
            continue

        key, sep, value = line.partition("=")
        if not sep:
            errors.append((number, f"expected 'key = value': {line!r}"))
            continue

        key = key.strip().lower()
        value = value.strip()

        if key in BOOLEAN_KEYS:
            settings[key] = value.lower() in ("1", "yes", "true", "on")
        elif key in INTEGER_KEYS:
            try:
                settings[key] = int(value)
            except ValueError:
                errors.append((number, f"{key} expects a whole number, got {value!r}"))
        elif key == "theme":
            if value.lower() not in THEMES:
                errors.append((number, f"unknown theme {value!r}; try {', '.join(THEMES)}"))
            else:
                settings[key] = value.lower()
        else:
            errors.append((number, f"unknown setting {key!r}"))

    return settings, aliases, errors


class Config:
    """Settings and user aliases, with defaults applied."""

    #: Class-level because it documents the full setting set; each instance
    #: copies it, so mutating Config.DEFAULTS never leaks between sessions.
    DEFAULTS: ClassVar[dict] = {
        "theme": "dark",
        "history": True,
        "history_size": 500,
        "completion": True,
        "banner": True,
        "color": True,
        "confirm_destructive": True,
    }

    def __init__(self, path=DEFAULT_PATH):
        self.path = os.path.expanduser(path) if path else None
        self.settings = dict(self.DEFAULTS)
        self.aliases = {}
        self.errors = []
        self.loaded = False

    @property
    def exists(self):
        return bool(self.path) and os.path.isfile(self.path)

    def load(self):
        """Read the rc file. A missing file is not an error."""
        if not self.exists:
            self.loaded = True
            return self

        try:
            # utf-8-sig, not utf-8: Notepad and PowerShell 5.1 write a BOM,
            # which would otherwise turn the first setting into '﻿theme'.
            with open(self.path, encoding="utf-8-sig") as handle:
                text = handle.read()
        except OSError as exc:
            self.errors.append((0, f"could not read {self.path}: {exc}"))
            self.loaded = True
            return self

        settings, aliases, errors = parse_config(text)
        self.settings.update(settings)
        self.aliases.update(aliases)
        self.errors.extend(errors)
        self.loaded = True
        return self

    def save(self):
        """Write the current settings and aliases back out."""
        lines = [
            "# CBOX shell configuration",
            "# Aliases extend or override the built-in command table.",
            "",
        ]
        for key in ("theme", "banner", "color", "history", "history_size",
                    "completion", "confirm_destructive"):
            if key in self.settings:
                lines.append(f"{key} = {_render(self.settings[key])}")
        if self.aliases:
            lines.append("")
            for name in sorted(self.aliases):
                lines.append(f"alias {name} = {self.aliases[name]}")

        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
        except OSError as exc:
            self.errors.append((0, f"could not write {self.path}: {exc}"))
            return False
        return True

    def get(self, key, fallback=None):
        return self.settings.get(key, self.DEFAULTS.get(key, fallback))

    def __contains__(self, key):
        return key in self.settings or key in self.aliases

    def __repr__(self):
        return f"Config(path={self.path!r}, aliases={len(self.aliases)}, errors={len(self.errors)})"


def _render(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)
