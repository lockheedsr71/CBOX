"""Tests for the shell's navigation, safety guard, config and script mode."""

import os

import pytest

import cbox
from cbox_core.config import Config, parse_config


def make_shell(**settings):
    config = Config(path=os.path.join("nonexistent-dir", ".cboxrc"))
    config.settings.update(Config.DEFAULTS)
    config.settings.update(settings)
    return cbox.Shell(config)


# ================== cd and cd - ==================


def test_cd_changes_directory(tmp_path, capsys):
    shell = make_shell()
    shell.execute(f"cd {tmp_path}")
    assert os.path.realpath(os.getcwd()) == os.path.realpath(str(tmp_path))
    assert "Directory Changed" in capsys.readouterr().out


def test_cd_minus_returns_to_the_previous_directory(tmp_path, capsys):
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir()
    second.mkdir()

    original = os.getcwd()
    try:
        shell = make_shell()
        shell.execute(f"cd {first}")
        shell.execute(f"cd {second}")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(second))

        shell.execute("cd -")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(first))
        assert "Directory Changed" in capsys.readouterr().out
    finally:
        os.chdir(original)


def test_cd_minus_toggles_back_and_forth(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    first.mkdir()
    second.mkdir()

    original = os.getcwd()
    try:
        shell = make_shell()
        shell.execute(f"cd {first}")
        shell.execute(f"cd {second}")

        shell.execute("cd -")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(first))
        shell.execute("cd -")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(second))
    finally:
        os.chdir(original)


def test_cd_minus_without_history_reports_instead_of_crashing(capsys):
    shell = make_shell()
    shell.execute("cd -")
    assert "No previous directory" in capsys.readouterr().out


def test_cd_handles_a_quoted_path_with_spaces(tmp_path):
    """`cd "C:\\Program Files"` reached os.chdir with the quotes still on."""
    target = tmp_path / "a folder"
    target.mkdir()

    original = os.getcwd()
    try:
        shell = make_shell()
        shell.execute(f'cd "{target}"')
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(target))
    finally:
        os.chdir(original)


def test_unquote_path_strips_matching_quotes():
    from cbox_core.tools import unquote_path

    assert unquote_path(['"C:\\Program', 'Files"']) == "C:\\Program Files"
    assert unquote_path(["'single'"]) == "single"
    assert unquote_path([]) == ""
    # Unbalanced quotes still yield a usable path.
    assert unquote_path(['"C:\\x']) == "C:\\x"


def test_cd_minus_ignores_extra_arguments(tmp_path, capsys):
    """`cd - somewhere` is a path named '-', not the history shortcut."""
    target = tmp_path / "-"
    target.mkdir()

    original = os.getcwd()
    try:
        shell = make_shell()
        shell.execute(f'cd "{target}"')
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(target))

        shell.execute("cd - extra")
        # The command failed, so we stayed where we were.
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(target))
        assert "Error:" in capsys.readouterr().out
    finally:
        os.chdir(original)


def test_cd_dotdot_records_the_previous_directory(tmp_path):
    nested = tmp_path / "x" / "y"
    nested.mkdir(parents=True)

    original = os.getcwd()
    try:
        os.chdir(nested)
        shell = make_shell()
        shell.execute("cd..")
        assert shell.previous_dir is not None
    finally:
        os.chdir(original)


# ================== destructive-command guard ==================


@pytest.mark.parametrize("command,args,expected", [
    ("del", ["C:\\"], True),
    ("del", ["c:/"], True),
    ("rmdir", ["D:\\"], True),
    ("del", [""], True),
    ("kill", ["4321"], False),
    ("del", ["testfile.txt"], False),
    ("del", [], False),
    ("mkdir", ["C:\\Windows"], False),
    ("ls", [], False),
])
def test_is_destructive(command, args, expected):
    assert cbox.is_destructive(command, args) is expected


def test_destructive_passthrough_asks_first(monkeypatch, capsys):
    shell = make_shell(confirm_destructive=True)
    monkeypatch.setattr(cbox, "confirm", lambda text: False)
    monkeypatch.setattr(cbox.executor, "run",
                        lambda cmd: pytest.fail("must not run without confirmation"))

    shell.execute("del C:\\")
    assert "Refusing" in capsys.readouterr().out


def test_destructive_passthrough_runs_after_yes(monkeypatch):
    shell = make_shell(confirm_destructive=True)
    monkeypatch.setattr(cbox, "confirm", lambda text: True)

    seen = {}
    monkeypatch.setattr(cbox.executor, "run", lambda cmd: seen.setdefault("cmd", cmd) or 0)

    shell.execute("del C:\\")
    assert seen["cmd"] == "del C:\\"


def test_guard_can_be_disabled_in_the_rc_file(monkeypatch):
    shell = make_shell(confirm_destructive=False)
    monkeypatch.setattr(cbox, "confirm", lambda text: pytest.fail("must not prompt"))

    seen = {}
    monkeypatch.setattr(cbox.executor, "run", lambda cmd: seen.setdefault("cmd", cmd) or 0)

    shell.execute("del C:\\")
    assert seen["cmd"] == "del C:\\"


def test_ordinary_passthrough_is_never_intercepted(monkeypatch):
    shell = make_shell()
    monkeypatch.setattr(cbox, "confirm", lambda text: pytest.fail("must not prompt"))

    seen = {}
    monkeypatch.setattr(cbox.executor, "run", lambda cmd: seen.setdefault("cmd", cmd) or 0)

    shell.execute("mkdir testdir")
    assert seen["cmd"] == "mkdir testdir"


# ================== ~/.cboxrc ==================


def test_parse_config_reads_settings_and_aliases():
    settings, aliases, errors = parse_config("""
        # a comment
        theme = light
        history = no
        history_size = 42
        confirm_destructive = yes
        alias lg = cdir -a --sort size
        alias net = cwho
        alias plain = chash -a sha256
    """)

    assert settings == {
        "theme": "light", "history": False,
        "history_size": 42, "confirm_destructive": True,
    }
    # Both `alias n = cmd` and `alias n cmd` are accepted; save() writes the
    # '=' form, so it has to parse too.
    assert aliases == {
        "lg": "cdir -a --sort size",
        "net": "cwho",
        "plain": "chash -a sha256",
    }
    assert errors == []


def test_config_survives_a_utf8_bom(tmp_path):
    path = tmp_path / ".cboxrc"
    path.write_bytes("\ufefftheme = plain\n".encode("utf-8"))

    config = Config(path=str(path)).load()
    assert config.errors == []
    assert config.settings["theme"] == "plain"


def test_parse_config_reports_bad_lines_with_numbers():
    settings, aliases, errors = parse_config(
        "theme = neon\nhistory_size = many\nnonsense\nalias lone\n"
    )

    assert settings == {}
    assert aliases == {}
    assert [number for number, _ in errors] == [1, 2, 3, 4]
    assert "neon" in errors[0][1]


def test_parse_config_accepts_several_boolean_spellings():
    for value in ("yes", "1", "true", "on"):
        settings, _, _ = parse_config(f"history = {value}")
        assert settings["history"] is True, value
    for value in ("no", "0", "false", "off"):
        settings, _, _ = parse_config(f"history = {value}")
        assert settings["history"] is False, value


def test_parse_config_ignores_comments_and_blank_lines():
    settings, aliases, errors = parse_config("\n# a\n; b\n\n   \n")
    assert (settings, aliases, errors) == ({}, {}, [])


def test_missing_rc_file_is_not_an_error(tmp_path):
    config = Config(path=str(tmp_path / "absent")).load()
    assert config.errors == []
    assert config.settings["theme"] == "dark"
    assert config.aliases == {}


def test_config_round_trips(tmp_path):
    path = str(tmp_path / ".cboxrc")
    config = Config(path=path)
    config.settings["theme"] = "plain"
    config.settings["history_size"] = 7
    config.aliases["lg"] = "cdir -a"
    assert config.save() is True

    reloaded = Config(path=path).load()
    assert reloaded.settings["theme"] == "plain"
    assert reloaded.settings["history_size"] == 7
    assert reloaded.aliases["lg"] == "cdir -a"


def test_user_alias_pointing_at_a_builtin_reuses_its_handler():
    config = Config(path="does-not-exist")
    config.aliases["mine"] = "cdir"
    shell = cbox.Shell(config)
    assert "mine" in shell.aliases


def test_user_alias_for_a_passthrough_command_is_kept_verbatim():
    config = Config(path="does-not-exist")
    config.aliases["open"] = "notepad {args}"
    shell = cbox.Shell(config)
    assert shell.aliases["open"][1] == "notepad {args}"


def test_default_config_has_sane_values():
    config = Config(path="does-not-exist").load()
    assert config.get("confirm_destructive") is True
    assert config.get("history") is True
    assert config.get("completion") is True
    assert config.get("history_size") == 500


# ================== script mode ==================


def test_run_script_handles_a_utf8_bom(tmp_path, monkeypatch):
    """Notepad writes a BOM; without utf-8-sig the first line is unusable."""
    script = tmp_path / "bom.cbox"
    script.write_bytes("\ufeff# comment\nwho\n".encode("utf-8"))

    seen = []
    shell = make_shell()
    monkeypatch.setattr(shell, "execute", _record_line(seen))

    assert cbox.run_script(str(script), shell) == 0
    assert seen == ["who"]


def test_run_script_handles_non_ascii_lines(tmp_path, monkeypatch, capsys):
    """A UTF-8 script on a cp1252 console must not crash the echo."""
    script = tmp_path / "farsi.cbox"
    script.write_text("# کامنت\necho تست\n", encoding="utf-8")

    seen = []
    shell = make_shell()
    monkeypatch.setattr(shell, "execute", _record_line(seen))

    assert cbox.run_script(str(script), shell) == 0
    assert seen == ["echo تست"]


def test_printable_survives_an_unencodable_console(monkeypatch):
    import io

    monkeypatch.setattr(cbox.sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))
    result = cbox._printable("تست")
    result.encode("cp1252")  # must not raise
    assert "\\u" in result


def test_run_script_executes_each_line(tmp_path, monkeypatch):
    script = tmp_path / "run.cbox"
    script.write_text("one\n\n# comment\ntwo\n", encoding="utf-8")

    seen = []
    shell = make_shell()
    monkeypatch.setattr(shell, "execute", _record_line(seen))

    assert cbox.run_script(str(script), shell) == 0
    assert seen == ["one", "two"]


def test_run_script_stops_at_exit(tmp_path, monkeypatch):
    script = tmp_path / "run.cbox"
    script.write_text("one\nexit\ntwo\n", encoding="utf-8")

    seen = []
    shell = make_shell()
    monkeypatch.setattr(shell, "execute", _record_line(seen))

    cbox.run_script(str(script), shell)
    assert seen == ["one"]


def test_run_script_reports_a_missing_file(capsys):
    assert cbox.run_script("no-such-script.cbox", make_shell()) == 1
    assert "Cannot read script" in capsys.readouterr().out


def test_main_with_command_flag_runs_one_command(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(cbox.executor, "run", _record_cmd(seen))

    assert cbox.main(["--no-config", "-c", "echo hello"]) == 0
    assert seen == ["echo hello"]


def test_main_with_file_flag_runs_the_script(monkeypatch, tmp_path):
    script = tmp_path / "s.cbox"
    script.write_text("who\n", encoding="utf-8")

    seen = []
    monkeypatch.setattr(cbox.executor, "run", _record_cmd(seen))

    assert cbox.main(["--no-config", "-f", str(script)]) == 0
    # The script goes through the same dispatcher, so aliases expand.
    assert seen == ["whoami"]


# ================== registration ==================


def test_every_new_tool_is_registered():
    for name in ("cport", "csweep", "chash", "cwlan"):
        assert name in cbox.ALIASES


def _record_cmd(seen):
    """Substitute for CommandExecutor.run that records instead of executing."""
    def run(cmd):
        seen.append(cmd)
        return 0
    return run


def _record_line(seen):
    """Substitute for Shell.execute that records the line instead of running it."""
    def execute(line):
        seen.append(line)
        return 0
    return execute
