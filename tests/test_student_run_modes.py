"""Unterschiede der Kurs- und Suite-Läufe bleiben beim gemeinsamen Setup erhalten."""

import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from insi import execution, system


@pytest.mark.parametrize("mode", ["course-sync", "course-background", "suite", "headless", "preview"])
def test_student_run_preserves_interpreter_gui_environment_and_output(mode, tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    program = course / "task.py"
    program.write_text("print('ok')", encoding="utf-8")
    custom = str(tmp_path / "course-python")
    monkeypatch.setattr("insi.runtime.selected_runtime", lambda course: SimpleNamespace(executable=custom))
    monkeypatch.setattr(execution, "python_command", lambda: ["suite-python"])
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-be-inherited")
    finished = threading.Event()
    calls = []
    threads = []
    original_thread = threading.Thread

    def track_thread(*args, **kwargs):
        thread = original_thread(*args, **kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr(threading, "Thread", track_thread)

    def launch(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(
            returncode=0, stdout="ok\n", stderr="", violation_reason=None,
            wait=lambda **kw: finished.set(), poll=lambda: 0,
            communicate_bounded=lambda **kw: ("ok\n", "", False, False),
        )

    monkeypatch.setattr(system, "sandbox_run", launch)
    monkeypatch.setattr(system, "sandbox_popen", launch)
    monkeypatch.setattr(execution, "sandbox_popen", launch)
    manager = execution.ExecutionManager()
    if mode == "course-sync":
        assert system.execute_student_program(program, course).stdout == "ok\n"
    elif mode == "course-background":
        assert system.run_student_program(program, course) == program
        assert finished.wait(timeout=5)
    elif mode == "preview":
        manager.launch_preview(program, course)
        assert finished.wait(timeout=5)
    else:
        assert manager.execute(program, course, headless=mode == "headless").stdout == "ok\n"
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()
    command, options = calls[0]
    policy, env = options["policy"], options["env"]
    assert command == [custom if mode.startswith("course-") else "suite-python", str(program)]
    assert policy.allow_gui is (mode in {"course-background", "suite", "preview"})
    assert (env.get("PYKIM_HEADLESS") == "1") is (mode == "headless")
    assert "GITHUB_TOKEN" not in env
    assert str(course) in env["PYTHONPATH"].split(os.pathsep)
    assert policy.workspace != course
    assert policy.writable_roots == (policy.workspace,)
    assert Path(env["INSI_PROGRESS_FILE"]).resolve() == policy.workspace / "progress.json"
    assert Path(env["INSI_RUN_FILES"]).resolve() == policy.workspace
    if mode == "course-sync":
        assert options["capture_output"] and options["text"]
    elif mode == "course-background":
        assert "stdout" not in options and "stderr" not in options


@pytest.mark.parametrize("background,stage", [
    (background, stage)
    for background in (False, True)
    for stage in ("runtime", "prepare", "launch", "merge")
] + [(True, "wait")])
def test_course_run_cleans_workspace_on_failure(background, stage, tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    program = course / "task.py"
    program.write_text("print('ok')", encoding="utf-8")
    workspaces = []
    original_mkdtemp = execution.tempfile.mkdtemp

    def fail(*args, **kwargs):
        raise RuntimeError(stage)

    def allocate(**kwargs):
        workspace = original_mkdtemp(dir=tmp_path, **kwargs)
        workspaces.append(Path(workspace))
        return workspace

    monkeypatch.setattr(execution.tempfile, "mkdtemp", allocate)
    monkeypatch.setattr("insi.runtime.selected_runtime", fail if stage == "runtime" else
                        lambda course: SimpleNamespace(executable="course-python"))
    monkeypatch.setattr(execution, "prepare_sandbox_progress", fail if stage == "prepare" else
                        lambda *args: 0)
    monkeypatch.setattr(execution, "merge_sandbox_progress", fail if stage == "merge" else
                        lambda *args, **kwargs: None)
    completed = SimpleNamespace(returncode=0, stdout="ok", stderr="", violation_reason=None,
                                wait=fail if stage == "wait" else lambda: None)
    launch = fail if stage == "launch" else lambda *args, **kwargs: completed
    monkeypatch.setattr(system, "sandbox_run", launch)
    monkeypatch.setattr(system, "sandbox_popen", launch)
    # Run cleanup inline so background failures and cleanup are fully observable.
    monkeypatch.setattr(system.threading, "Thread", lambda *, target, daemon:
                        SimpleNamespace(start=target))

    run = system.run_student_program if background else system.execute_student_program
    with pytest.raises(RuntimeError, match=stage):
        run(program, course)
    assert len(workspaces) == (0 if stage == "runtime" else 1)
    assert all(not workspace.exists() for workspace in workspaces)
