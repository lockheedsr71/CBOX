"""Tests for cbox_core.tools - resolving tools to runnable commands."""

import os
import sys

from cbox_core import TOOLS, tools


def test_every_registered_tool_script_exists(repo_root):
    missing = tools.missing_tools()
    assert missing == [], f"TOOLS lists scripts that are not on disk: {missing}"


def test_resolve_tool_falls_back_to_the_python_script(monkeypatch, repo_root):
    monkeypatch.setattr(tools.shutil, "which", lambda name: None)
    argv = tools.resolve_tool("cdir")
    assert argv is not None
    assert argv[0] == sys.executable
    assert argv[1].endswith("cdir.py")
    assert os.path.isfile(argv[1])


def test_resolve_tool_prefers_a_local_built_exe(monkeypatch, tmp_path):
    built = tmp_path / "dist"
    built.mkdir()
    (built / "cpi.exe").write_bytes(b"MZ")
    monkeypatch.setattr(tools, "_repo_root", lambda: str(tmp_path))

    argv = tools.resolve_tool("cpi")
    assert argv == [str(built / "cpi.exe")]


def test_an_installed_exe_never_shadows_the_source(monkeypatch, repo_root):
    """A stale EXE on PATH used to win, silently running old code."""
    monkeypatch.setattr(tools.shutil, "which", lambda name: r"D:\MyPrograms\cbox\cpi.EXE")

    argv = tools.resolve_tool("cpi")
    assert argv is not None
    assert argv[0] == sys.executable
    assert argv[1].endswith("cpi.py")


def test_installed_exe_is_used_when_no_script_exists(monkeypatch, tmp_path):
    monkeypatch.setattr(tools, "_repo_root", lambda: str(tmp_path))
    monkeypatch.setattr(tools.shutil, "which", lambda name: r"C:\Tools\cro.exe")

    assert tools.resolve_tool("cro") == [r"C:\Tools\cro.exe"]


def test_find_installed_ignores_the_working_directory(monkeypatch, repo_root):
    """shutil.which probes the CWD on Windows; a same-named file there wins."""
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(tools.shutil, "which", lambda name: os.path.join(os.getcwd(), f"{name}.exe"))
    assert tools._find_installed("cpi") is None


def test_find_installed_rejects_non_executables(monkeypatch, tmp_path):
    script = tmp_path / "cro.py"
    script.write_text("# not a tool", encoding="utf-8")
    monkeypatch.setattr(tools.shutil, "which", lambda name: str(script))

    if os.name == "nt":
        assert tools._find_installed("cro") is None
    else:
        assert tools._find_installed("cro") == str(script)


def test_resolve_tool_returns_none_for_unknown(monkeypatch):
    monkeypatch.setattr(tools.shutil, "which", lambda name: None)
    assert tools.resolve_tool("definitely-not-a-tool") is None


def test_netdetail_maps_to_netinf(monkeypatch, repo_root):
    """The alias used to point at 'net_info.py', a file that never existed."""
    monkeypatch.setattr(tools.shutil, "which", lambda name: None)
    argv = tools.resolve_tool("netdetail")
    assert argv is not None
    assert argv[1].endswith("netinf.py")
    assert os.path.isfile(argv[1])


def test_tool_script_path_is_absolute(repo_root):
    path = tools.tool_script("ntpmon")
    assert os.path.isabs(path)
    assert os.path.isfile(path)


def test_tool_names_are_unique():
    assert len(TOOLS) == len(set(TOOLS))
    assert len(set(TOOLS.values())) == len(TOOLS)
