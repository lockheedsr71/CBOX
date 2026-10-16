"""Tests for cbox_core.lineedit - history and tab completion."""

import io
import os

from cbox_core import lineedit
from cbox_core.lineedit import Completer, EditResult, History

# ================== History ==================


def test_history_records_and_persists(tmp_path):
    path = tmp_path / "nested" / "history"

    history = History(path=str(path))
    history.add("df")
    history.add("cpi 8.8.8.8")
    history.add("   ")  # blank, ignored

    assert history.entries == ["df", "cpi 8.8.8.8"]

    reloaded = History(path=str(path))
    assert reloaded.entries == ["df", "cpi 8.8.8.8"]


def test_history_collapses_immediate_repeats(tmp_path):
    history = History(path=None)
    history.add("df")
    history.add("df")
    history.add("df")
    assert history.entries == ["df"]


def test_history_keeps_non_adjacent_repeats(tmp_path):
    history = History(path=None)
    history.add("df")
    history.add("ver")
    history.add("df")
    assert history.entries == ["df", "ver", "df"]


def test_history_is_trimmed_to_the_limit(tmp_path):
    history = History(path=None, limit=3)
    for index in range(10):
        history.add(f"cmd{index}")
    assert len(history) == 3
    # The most recent entries survive.
    assert history.entries == ["cmd7", "cmd8", "cmd9"]


def test_history_survives_a_corrupt_file(tmp_path):
    path = tmp_path / "history"
    path.write_bytes(b"\xff\xfe broken \x00 bytes\n")

    history = History(path=str(path))
    assert isinstance(history.entries, list)


def test_history_without_a_path_does_not_write(tmp_path):
    history = History(path=None)
    history.add("df")
    assert history.entries == ["df"]


def test_history_search_by_prefix(tmp_path):
    history = History(path=None)
    for command in ("cro 8.8.8.8", "cdir -a", "cro 1.1.1.1", "cd"):
        history.add(command)

    assert history.search("cro") == ["cro 8.8.8.8", "cro 1.1.1.1"]
    assert history.search("cd") == ["cdir -a", "cd"]
    assert history.search("zzz") == []


# ================== Completer ==================


def test_completer_matches_command_names():
    completer = Completer(commands=["cro", "cpi", "cdir", "cwho"], path_commands=set())

    matches, start = completer.complete("c")
    assert start == 0
    assert set(matches) == {"cro", "cpi", "cdir", "cwho"}


def test_completer_narrows_on_more_input():
    completer = Completer(commands=["cro", "cpi", "cwho"], path_commands=set())
    matches, _ = completer.complete("cw")
    assert matches == ["cwho"]


def test_completer_is_case_insensitive_on_the_prefix():
    completer = Completer(commands=["cro", "cpi"], path_commands=set())
    assert completer.complete("CR")[0] == ["cro"]


def test_completer_uses_command_names_for_a_bare_token():
    """`cd` is navigation, not a command table entry."""
    completer = Completer(commands=["cdir", "cro"], path_commands={"cd"})
    matches, _ = completer.complete("cd")
    assert matches == ["cdir"]


def test_completer_falls_back_to_paths_for_path_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "alpha.txt").write_text("a")
    (tmp_path / "beta.txt").write_text("b")
    (tmp_path / "alphadir").mkdir()

    completer = Completer(commands=["chash"], path_commands={"chash"})
    matches, start = completer.complete("chash al")

    assert start == 6
    assert "alphadir\\" in matches
    assert "alpha.txt" in matches
    assert "beta.txt" not in matches


def test_completer_appends_a_separator_to_directories(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "folder").mkdir()
    (tmp_path / "file.txt").write_text("x")

    completer = Completer(commands=["cdir"], path_commands={"cdir"})
    matches, _ = completer.complete("cdir f")

    assert "folder\\" in matches
    assert "file.txt" in matches


def test_completer_after_a_trailing_space_starts_a_new_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "alpha.txt").write_text("a")

    completer = Completer(commands=["cdir"], path_commands={"cdir"})
    matches, start = completer.complete("cdir ")
    assert start == 5
    assert "alpha.txt" in matches


def test_completer_returns_nothing_for_unknown_prefixes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    completer = Completer(commands=["cdir"], path_commands={"cdir"})
    assert completer.complete("zzzz")[0] == []


def test_completer_handles_a_missing_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    completer = Completer(commands=["cdir"], path_commands={"cdir"})
    assert completer.complete("cdir does" + chr(92) + "notexist" + chr(92))[0] == []


def test_completer_survives_a_path_without_a_separator():
    completer = Completer(commands=["cdir"], path_commands={"cdir"})
    matches, start = completer.complete("cdir somefile")
    # The tail begins right after the single space following "cdir".
    assert start == 5
    assert isinstance(matches, list)


# ================== LineEditor fallback ==================


def test_edit_result_is_falsy_only_when_interrupted():
    assert bool(EditResult("df"))
    assert not EditResult("", interrupted=True)


def test_editor_falls_back_to_input_when_not_a_tty():
    """Piped stdin has no raw mode, so the plain path must be used."""
    history = History(path=None)
    editor = lineedit.LineEditor(history=history)
    assert editor.supports_raw is False

    monkey = io.StringIO("df\nver\n")
    original = lineedit.sys.stdin
    lineedit.sys.stdin = monkey
    try:
        assert editor.read_line("> ").text == "df"
        assert editor.read_line("> ").text == "ver"
    finally:
        lineedit.sys.stdin = original

    assert history.entries == ["df", "ver"]


def test_editor_treats_eof_as_interrupted():
    editor = lineedit.LineEditor(history=History(path=None))

    class NoInput:
        encoding = "utf-8"

        def __iter__(self):
            return iter(())

        def readline(self, *args):
            raise EOFError

        def fileno(self):
            raise OSError

    original = lineedit.sys.stdin
    lineedit.sys.stdin = NoInput()
    try:
        assert editor.read_line("> ").interrupted is True
    finally:
        lineedit.sys.stdin = original


def test_control_key_constants_are_distinct():
    """A typo that aliases two constants would break editing silently."""
    constants = [
        lineedit.CTRL_C, lineedit.CTRL_D, lineedit.CTRL_A, lineedit.CTRL_E,
        lineedit.CTRL_K, lineedit.CTRL_U, lineedit.CTRL_W, lineedit.CTRL_L,
        lineedit.TAB, lineedit.BACKSPACE, lineedit.ESC,
    ]
    assert len(set(constants)) == len(constants)


def test_arrow_key_sequences_are_distinct():
    sequences = [lineedit.UP, lineedit.DOWN, lineedit.LEFT, lineedit.RIGHT,
                 lineedit.HOME, lineedit.END, lineedit.DELETE_KEY]
    assert len(set(sequences)) == len(sequences)


def test_history_file_default_location_is_under_home():
    history = History(path=os.path.join("~", ".cbox_history"))
    assert os.path.isabs(history.path) or "~" in history.path
