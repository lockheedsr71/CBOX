"""Tests for the shell itself: alias table, dispatch and help text."""

import os

import pytest

import cbox


def test_alias_table_targets_real_files(repo_root):
    """Every None-template alias must resolve to a bundled tool."""
    from cbox_core.tools import resolve_tool

    for command, (_, handler) in cbox.ALIASES.items():
        if handler is None:
            assert resolve_tool(command) is not None, f"'{command}' has no runnable tool"


def test_native_handlers_are_callable():
    """df and cl run in-process rather than shelling out."""
    for command in ("df", "cl"):
        handler = cbox.ALIASES[command][1]
        assert callable(handler), f"'{command}' should be a native handler"


def test_df_does_not_shell_out_to_wmic(monkeypatch, capsys):
    """`wmic` was removed in Windows 11 24H2, so `df` failed outright."""
    monkeypatch.setattr(cbox.executor, "run", lambda cmd: pytest.fail("df must not shell out"))

    cbox.execute_command("df")

    out = capsys.readouterr().out
    assert "Drive" in out
    assert "wmic" not in out.lower()


def test_dead_aliases_are_gone():
    """'cnetw' had no implementation behind it."""
    assert "cnetw" not in cbox.ALIASES


def test_netdetail_alias_is_resolvable(repo_root):
    assert "netdetail" in cbox.ALIASES


def test_show_help_lists_every_alias(capsys):
    cbox.show_help(cbox.ALIASES)
    out = capsys.readouterr().out
    for command in cbox.ALIASES:
        assert command in out


def test_show_help_lists_navigation_helpers(capsys):
    cbox.show_help(cbox.ALIASES)
    out = capsys.readouterr().out
    assert "cd [path]" in out
    assert "cd -" in out


def test_cd_changes_directory(tmp_path, capsys):
    original = os.getcwd()
    try:
        cbox.execute_command(f"cd {tmp_path}")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(tmp_path))
        assert "Directory Changed" in capsys.readouterr().out
    finally:
        os.chdir(original)


def test_cd_expands_user_and_vars(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CBOX_TEST_DIR", str(tmp_path))
    original = os.getcwd()
    try:
        cbox.execute_command("cd %CBOX_TEST_DIR%")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(str(tmp_path))
    finally:
        os.chdir(original)


def test_cd_reports_errors(capsys):
    cbox.execute_command("cd Z:\\definitely\\not\\here")
    assert "Error:" in capsys.readouterr().out


def test_cd_dotdot_goes_up_one_level(capsys):
    original = os.getcwd()
    nested = os.path.join(original, "a", "b")
    os.makedirs(nested, exist_ok=True)
    try:
        os.chdir(nested)
        cbox.execute_command("cd..")
        assert os.path.realpath(os.getcwd()) == os.path.realpath(os.path.join(original, "a"))
    finally:
        os.chdir(original)


def test_empty_input_is_ignored(capsys):
    cbox.execute_command("")
    cbox.execute_command("   ")
    assert capsys.readouterr().out == ""


def test_run_tool_reports_unknown_tools(capsys, monkeypatch):
    monkeypatch.setattr(cbox, "resolve_tool", lambda name, allow_path=True: None)
    assert cbox.run_tool("nope", []) == 9009
    assert "not found" in capsys.readouterr().out


def test_run_tool_forwards_arguments(monkeypatch):
    seen = {}

    def fake_run(argv, shell=False):
        seen["argv"] = argv
        seen["shell"] = shell
        return type("Completed", (), {"returncode": 0})()

    monkeypatch.setattr(cbox.subprocess, "run", fake_run)
    monkeypatch.setattr(cbox, "resolve_tool", lambda name, allow_path=True: ["cpi.exe"])

    assert cbox.run_tool("cpi", ["8.8.8.8", "-g"]) == 0
    assert seen["argv"] == ["cpi.exe", "8.8.8.8", "-g"]
    # Bundled tools are launched directly, never through a shell, so their
    # arguments are not re-parsed by cmd.exe.
    assert seen["shell"] is False


def _record(seen):
    def run(cmd):
        seen["cmd"] = cmd
        return 0
    return run


def test_alias_arguments_are_passed_through(monkeypatch):
    seen = {}
    monkeypatch.setattr(cbox.executor, "run", _record(seen))

    cbox.execute_command("pi 8.8.8.8")
    assert seen["cmd"] == "ping 8.8.8.8"

    cbox.execute_command("tr 8.8.8.8")
    assert seen["cmd"] == "tracert -d 8.8.8.8"

    cbox.execute_command("kill 4321")
    assert seen["cmd"] == "taskkill /PID 4321 /F"


def test_quoted_paths_survive_the_alias(monkeypatch):
    seen = {}
    monkeypatch.setattr(cbox.executor, "run", _record(seen))

    cbox.execute_command('ls "C:\\Program Files"')
    assert '"C:\\Program Files"' in seen["cmd"]


def test_commands_without_arguments_are_passed_verbatim(monkeypatch):
    seen = {}
    monkeypatch.setattr(cbox.executor, "run", _record(seen))

    cbox.execute_command("ip")
    assert seen["cmd"] == "ipconfig"


def test_logical_drives_reports_real_geometry():
    drives = list(cbox.logical_drives())
    assert drives, "at least one drive should be readable"
    for letter, total, free in drives:
        assert len(letter) >= 1
        assert total > 0
        assert 0 <= free <= total


@pytest.mark.parametrize("size,expected", [
    (0, "0 B"),
    (512, "512 B"),
    (2048, "2.0 KB"),
    (1024 ** 3, "1.0 GB"),
    (1024 ** 4, "1.0 TB"),
])
def test_format_size(size, expected):
    assert cbox._format_size(size) == expected


def test_missing_alias_target_is_reported_accurately(monkeypatch, capsys):
    """The old message said 'unknown command' when the alias itself was fine."""
    monkeypatch.setattr(cbox.executor, "run", lambda cmd: 9009)

    cbox.execute_command("ver")
    out = capsys.readouterr().out
    assert "systeminfo" in out
    assert "not a recognized CBOX" not in out


def test_unknown_command_falls_through_to_the_shell(monkeypatch):
    seen = {}
    monkeypatch.setattr(cbox.executor, "run", lambda cmd: seen.update(cmd=cmd) or 9009)

    cbox.execute_command("mkdir testdir")
    assert seen["cmd"] == "mkdir testdir"


def test_bundled_tool_routes_through_run_tool(monkeypatch):
    seen = {}
    monkeypatch.setattr(cbox, "run_tool", lambda name, args: seen.setdefault("tool", (name, args)))
    monkeypatch.setattr(cbox.executor, "run", lambda cmd: pytest.fail("should not hit the shell"))

    cbox.execute_command("cwho example.com")
    assert seen["tool"] == ("cwho", ["example.com"])


def test_version_is_a_release_string():
    from cbox_core import __version__

    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(part.isdigit() for part in parts)
