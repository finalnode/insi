"""Auswahl des privaten Windows-Runners aus dem Onefile-Paket."""

import sys
from pathlib import Path

import pytest

from insi.interpreter import WINDOWS_RUNTIME_NAME, command_for
from insi.sandbox import WindowsAppContainerAdapter
from insi.execution_security import student_policy


@pytest.mark.parametrize("inside_runner", [False, True])
def test_windows_uses_packaged_runtime_without_onefile_bootstrap(
    tmp_path, monkeypatch, inside_runner
):
    runtime = tmp_path / "_MEI12345"
    runtime.mkdir()
    runner = runtime / WINDOWS_RUNTIME_NAME
    runner.touch()
    launcher = tmp_path / "insi.exe"
    launcher.touch()
    executable = runner if inside_runner else launcher
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "_MEIPASS", str(runtime), raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))

    command = command_for(str(executable))
    assert command == [str(runner), "--pykim-python"]
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    private = tmp_path / "private"
    private.mkdir()
    payload = WindowsAppContainerAdapter()._payload(
        [*command, "-c", "print('ok')"],
        cwd=workspace,
        environment={},
        policy=student_policy(workspace),
    )
    assert payload["onefile_bootstrap"] is False
    assert str(runner) in payload["readable_roots"]
    assert str(runtime) in payload["readable_roots"]
    assert all(
        not private.is_relative_to(Path(root))
        for root in payload["readable_roots"]
    )
    external = tmp_path / "python.exe"
    assert command_for(str(external)) == [str(external)]


def test_internal_runner_does_not_regrant_runtime_permissions(tmp_path, monkeypatch):
    from insi import windows_staging

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / WINDOWS_RUNTIME_NAME))
    monkeypatch.delenv("INSI_SANDBOX", raising=False)
    monkeypatch.delenv(windows_staging.PREAUTHORIZED_RUNTIME_ENV, raising=False)

    def reject_grant(*args, **kwargs):
        pytest.fail("Der interne Runner darf die Runtime-ACL nicht verändern.")

    monkeypatch.setattr(windows_staging.subprocess, "run", reject_grant)
    windows_staging.prepare_onefile_runtime_for_appcontainer()
