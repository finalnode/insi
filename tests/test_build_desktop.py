"""Plattformübergreifender Buildablauf ohne Compiler- oder Netzwerkaufrufe."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import build_desktop_app as build
from tools import build_macos_app as macos


@pytest.fixture(params=["Windows", "Linux", "Darwin"])
def build_target(request, tmp_path, monkeypatch):
    system = request.param
    name = "macos" if system == "Darwin" else system.lower()
    flag = "INSI_MACOS_BUILD_ENV" if system == "Darwin" else "INSI_DESKTOP_BUILD_ENV"
    monkeypatch.setattr(build.platform, "system", lambda: system)
    monkeypatch.setattr(build, "__file__", str(tmp_path / "tools" / "build_desktop_app.py"))
    monkeypatch.setattr(build, "dependency_lock", lambda project, **kw: project / "locked.txt")
    monkeypatch.delenv(flag, raising=False)
    return tmp_path, name, flag


def test_bootstrap_preserves_arguments_pins_and_child_exit_code(build_target, monkeypatch):
    project, name, flag = build_target
    calls = []

    def run(command, **options):
        calls.append((command, options))
        return SimpleNamespace(returncode=7 if "env" in options else 0)

    monkeypatch.setattr(build.subprocess, "run", run)
    monkeypatch.setattr(build.sys, "argv", ["unrelated.py", "--wrong-option"])
    assert build.main(["--skip-clean", "--skip-wheelhouse"]) == 7
    assert calls[0][0][-1] == str(project / "build" / f"{name}-venv")
    installs = [command for command, _ in calls if "pip" in command]
    assert len(installs) == 3
    assert installs[0][-1] == str(project / "requirements" / "build-bootstrap.txt")
    assert all("--constraint" in command for command in installs[1:])
    assert installs[1][-1] == str(project / "requirements" / "pykim-0.6.0.txt")
    assert installs[2][-1] == f"{project}[build]"
    command, options = calls[-1]
    assert command[-2:] == ["--skip-clean", "--skip-wheelhouse"]
    assert options["env"][flag] == "1"
    assert options["cwd"] == project


@pytest.mark.parametrize("skip", [False, True])
def test_build_keeps_audit_cleanup_and_platform_steps(build_target, monkeypatch, skip):
    project, name, flag = build_target
    monkeypatch.setenv(flag, "1")
    work = project / "build" / name
    work.mkdir(parents=True)
    obsolete = work / "obsolete"
    obsolete.touch()
    calls = []
    signed = []

    def run(command, **options):
        calls.append(command)
        if "PyInstaller" in command:
            destination = Path(command[command.index("--distpath") + 1])
            (destination / ("insi.app" if name == "macos" else "insi")).mkdir(parents=True)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(build.subprocess, "run", run)
    monkeypatch.setattr(macos, "apply_adhoc_signature", signed.append)
    main = macos.main if name == "macos" else build.main
    assert main(["--skip-clean", "--skip-wheelhouse"] if skip else []) == 0
    scripts = [Path(command[1]).name for command in calls if command[1] != "-m"]
    assert ("build_wheelhouse.py" in scripts) is not skip
    assert "audit_runtime_licenses.py" in scripts
    audit = next(command for command in calls if any("audit_runtime_licenses.py" in arg for arg in command))
    assert "--strict" in audit
    assert ("build_macos_icon.py" in scripts) is (name == "macos")
    compiler = calls[-1]
    assert "PyInstaller" in compiler
    assert ("--clean" in compiler) is not skip
    assert obsolete.exists() is skip
    assert compiler[-1] == str(project / "packaging" / ("macos" if name == "macos" else "desktop") / "insi.spec")
    assert signed == ([project / "dist" / "macos" / "insi.app"] if name == "macos" else [])
