"""Line editing for the CBOX shell: history and tab completion.

Python's `readline` module does not exist on Windows, so the usual
`import readline` recipe for an interactive shell raises
ModuleNotFoundError there. The alternatives are `pyreadline3` (unmaintained)
or `prompt_toolkit` (a heavy dependency for a project that prides itself on
being dependency-light).

This module reads keys through `msvcrt.getwch()` on Windows and falls back to
plain `input()` elsewhere, which gives history and completion with nothing
beyond the standard library.
"""

import os
import sys

__all__ = ["Completer", "EditResult", "History", "LineEditor"]

#: Control characters
CTRL_C = "\x03"
CTRL_D = "\x04"
CTRL_A = "\x01"  # home
CTRL_E = "\x05"  # end
CTRL_K = "\x0b"  # kill to end of line
CTRL_U = "\x15"  # kill to start of line
CTRL_W = "\x17"  # kill previous word
CTRL_L = "\x0c"  # clear screen
TAB = "\t"
BACKSPACE = "\x08"
DELETE = "\x7f"
ESC = "\x1b"

#: Arrow keys arrive as a NUL/0xE0 prefix followed by a scan code.
UP = ("\x00", "H")
DOWN = ("\x00", "P")
LEFT = ("\x00", "K")
RIGHT = ("\x00", "M")
HOME = ("\x00", "G")
END = ("\x00", "O")
DELETE_KEY = ("\x00", "S")

MAX_HISTORY = 500


class EditResult:
    """Outcome of one `read_line` call."""

    def __init__(self, text, interrupted=False):
        self.text = text
        self.interrupted = interrupted

    def __bool__(self):
        return not self.interrupted


class History:
    """Persisted command history with duplicate collapsing."""

    def __init__(self, path=None, limit=MAX_HISTORY):
        self.path = path
        self.limit = limit
        self.entries = []
        self.load()

    def load(self):
        if not self.path or not os.path.isfile(self.path):
            return
        try:
            with open(self.path, encoding="utf-8", errors="replace") as handle:
                for raw in handle:
                    entry = raw.rstrip("\n")
                    if entry:
                        self.entries.append(entry)
        except OSError:
            # A corrupt or locked history file must not stop the shell.
            self.entries = []
        self.trim()

    def save(self):
        if not self.path:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(self.entries) + "\n")
        except OSError:
            pass

    def add(self, text):
        text = text.strip()
        if not text:
            return
        # Collapse a repeat of the previous entry rather than storing it twice.
        if self.entries and self.entries[-1] == text:
            return
        self.entries.append(text)
        self.trim()
        self.save()

    def trim(self):
        if len(self.entries) > self.limit:
            del self.entries[:len(self.entries) - self.limit]

    def search(self, prefix):
        """Entries starting with `prefix`, most recent last."""
        return [entry for entry in self.entries if entry.startswith(prefix)]

    def __len__(self):
        return len(self.entries)


class Completer:
    """Tab completion over command names and filesystem paths."""

    def __init__(self, commands=(), path_commands=()):
        self.commands = sorted({c.lower() for c in commands})
        self.path_commands = {c.lower() for c in path_commands}

    def complete(self, buffer):
        """Return (completions, replace_from) for `buffer`.

        `replace_from` is the index in `buffer` where the chosen completion
        starts, so the caller can splice it in without re-typing.
        """
        stripped = buffer.rstrip()
        # A trailing space means the previous token is complete.
        trailing_space = len(buffer) > len(stripped)

        if trailing_space:
            # Completing a new argument: offer paths when the command takes one.
            head, _, _ = stripped.partition(" ")
            if head.lower() in self.path_commands:
                return self._complete_path(""), len(head) + 1
            return [], 0

        head, sep, tail = stripped.partition(" ")

        if not sep:
            matches = [c for c in self.commands if c.startswith(head.lower())]
            return matches, 0

        if head.lower() in self.path_commands:
            return self._complete_path(tail), len(head) + 1
        return [], 0

    def _complete_path(self, fragment):
        """Complete a filesystem path fragment."""
        try:
            directory, _, prefix = fragment.rpartition("\\")
            directory = directory + "\\" if directory else ""
            search_dir = os.path.join(os.getcwd(), directory) if directory else os.getcwd()
            entries = os.listdir(search_dir)
        except OSError:
            return []

        matches = [name for name in entries if name.lower().startswith(prefix.lower())]
        matches.sort(key=str.lower)

        expanded = []
        for name in matches:
            full = directory + name
            if os.path.isdir(os.path.join(search_dir, name)):
                # Directories get a trailing separator so the next tab
                # continues inside them.
                full += "\\"
            expanded.append(full)
        return expanded


def has_tty():
    """True when stdin is an interactive terminal.

    Checking `hasattr(stdin, "fileno")` is not enough: pytest's capture object
    and some stream wrappers expose the attribute but raise when it is called.
    Raw key handling needs a real console, and a shell fed from a pipe is not
    one, so any failure here must mean "no raw mode".
    """
    try:
        return os.isatty(sys.stdin.fileno())
    except Exception:
        return False


class LineEditor:
    """Read one line with history and completion on Windows; plain input elsewhere."""

    def __init__(self, history=None, completer=None, prompt="", clear=None):
        self.history = history if history is not None else History()
        self.completer = completer
        self.prompt = prompt
        self.clear = clear
        self.supports_raw = sys.platform == "win32" and has_tty()

    def read_line(self, prompt=None):
        prompt = self.prompt if prompt is None else prompt
        if self.supports_raw:
            return self._read_raw(prompt)
        return self._read_plain(prompt)

    # ---------- fallback ----------

    def _read_plain(self, prompt):
        try:
            text = input(prompt)
        except EOFError:
            return EditResult("", interrupted=True)
        self.history.add(text)
        return EditResult(text)

    # ---------- raw Windows editing ----------

    def _read_raw(self, prompt):
        import msvcrt

        buffer = ""
        cursor = 0
        # Navigation state for history browsing.
        history_index = len(self.history.entries)
        saved_line = ""
        pending_completions = None
        pending_from = 0
        pending_index = 0

        def redraw():
            # \r clears the line, then re-emit prompt + buffer up to the cursor.
            sys.stdout.write("\r" + " " * (len(prompt) + len(buffer) + 2) + "\r")
            sys.stdout.write(prompt)
            sys.stdout.write(buffer)
            back = len(buffer) - cursor
            if back > 0:
                sys.stdout.write(f"\033[{back}D")
            sys.stdout.flush()

        def insert(text):
            nonlocal buffer, cursor
            buffer = buffer[:cursor] + text + buffer[cursor:]
            cursor += len(text)

        while True:
            key = msvcrt.getwch()

            if key in (CTRL_C,):
                sys.stdout.write("\n")
                return EditResult("", interrupted=True)

            if key in (CTRL_D,):
                if buffer:
                    insert(chr(0))  # force a no-op edit
                    buffer = buffer[:-1]
                    cursor -= 1
                    redraw()
                    continue
                sys.stdout.write("\n")
                return EditResult("", interrupted=True)

            if key in (CTRL_L,):
                if self.clear:
                    self.clear()
                sys.stdout.write("\n" + prompt + buffer)
                sys.stdout.flush()
                continue

            if key in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                self.history.add(buffer)
                return EditResult(buffer)

            if key in (BACKSPACE, DELETE):
                if cursor > 0:
                    buffer = buffer[:cursor - 1] + buffer[cursor:]
                    cursor -= 1
                    redraw()
                continue

            if key == DELETE_KEY:
                if cursor < len(buffer):
                    buffer = buffer[:cursor] + buffer[cursor + 1:]
                    redraw()
                continue

            if key in UP:
                if not self.history.entries:
                    continue
                if history_index == len(self.history.entries):
                    saved_line = buffer
                if history_index > 0:
                    history_index -= 1
                    buffer = self.history.entries[history_index]
                    cursor = len(buffer)
                    pending_completions = None
                    redraw()
                continue

            if key in DOWN:
                if history_index < len(self.history.entries):
                    history_index += 1
                    if history_index == len(self.history.entries):
                        buffer = saved_line
                    else:
                        buffer = self.history.entries[history_index]
                    cursor = len(buffer)
                    pending_completions = None
                    redraw()
                continue

            if key in LEFT:
                if cursor > 0:
                    cursor -= 1
                    redraw()
                continue

            if key in RIGHT:
                if cursor < len(buffer):
                    cursor += 1
                    redraw()
                continue

            if key in HOME:
                cursor = 0
                redraw()
                continue

            if key in END:
                cursor = len(buffer)
                redraw()
                continue

            if key == CTRL_A:
                cursor = 0
                redraw()
                continue

            if key == CTRL_E:
                cursor = len(buffer)
                redraw()
                continue

            if key == CTRL_U:
                buffer = buffer[cursor:]
                cursor = 0
                redraw()
                continue

            if key == CTRL_K:
                buffer = buffer[:cursor]
                redraw()
                continue

            if key == CTRL_W:
                left = buffer[:cursor].rstrip()
                cut = left.rfind(" ") + 1
                buffer = buffer[:cut] + buffer[cursor:]
                cursor = cut
                redraw()
                continue

            if key == TAB:
                if pending_completions:
                    # A second tab cycles through the candidates.
                    pending_index = (pending_index + 1) % len(pending_completions)
                    chosen = pending_completions[pending_index]
                    buffer = buffer[:pending_from] + chosen + buffer[cursor:]
                    cursor = pending_from + len(chosen)
                    redraw()
                    continue

                matches, start = self._completions_for(buffer)
                if not matches:
                    continue
                if len(matches) == 1:
                    chosen = matches[0]
                    buffer = buffer[:start] + chosen + buffer[cursor:]
                    cursor = start + len(chosen)
                    redraw()
                    continue

                # Several candidates: show them, and arm cycling for a second tab.
                pending_completions = matches
                pending_from = start
                pending_index = 0
                sys.stdout.write("\n" + "  ".join(matches) + "\n" + prompt + buffer)
                sys.stdout.flush()
                continue

            if key in (ESC,):
                pending_completions = None
                continue

            if ord(key) < 32:
                # Any other control key: ignore it rather than inserting noise.
                continue

            pending_completions = None
            insert(key)
            redraw()

    def _completions_for(self, buffer):
        if self.completer is None:
            return [], 0
        return self.completer.complete(buffer)
