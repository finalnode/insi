"""Aufräumen von Aufgabenläufen auch bei Fehlern und überlappenden Starts."""

import threading
from io import StringIO
from types import SimpleNamespace

import pytest

from insi import execution


@pytest.fixture
def task(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    program = course / "task.py"
    program.write_text("print('ok')", encoding="utf-8")
    run_root = tmp_path / "run"

    def create_run(**kwargs):
        run_root.mkdir()
        return str(run_root)

    monkeypatch.setattr(execution.tempfile, "mkdtemp", create_run)
    return course, program, run_root


@pytest.mark.parametrize("stage", ["prepare_sandbox_progress", "student_policy", "sandbox_popen", "merge_sandbox_progress"])
def test_run_cleanup_survives_preparation_and_merge_errors(task, monkeypatch, stage):
    course, program, run_root = task
    manager = execution.ExecutionManager()

    def fail(*args, **kwargs):
        raise OSError("Datenträger getrennt")

    monkeypatch.setattr(execution, stage, fail)
    with pytest.raises(OSError, match="Datenträger getrennt"):
        manager.execute(program, course)
    assert not run_root.exists()
    assert not manager._processes


def test_duplicate_launch_does_not_prepare_another_workspace(task):
    course, program, run_root = task
    manager = execution.ExecutionManager()
    manager._processes[program] = SimpleNamespace(poll=lambda: None)
    with pytest.raises(RuntimeError, match="läuft bereits"):
        manager.execute(program, course)
    assert not run_root.exists()


def test_old_run_cleanup_preserves_new_process_registration(task, monkeypatch):
    course, program, run_root = task
    manager = execution.ExecutionManager()
    newer = SimpleNamespace(poll=lambda: None)

    def register_new_run(*args, **kwargs):
        manager._processes[program] = newer
        manager._stopped.add(program)

    monkeypatch.setattr(execution, "merge_sandbox_progress", register_new_run)
    assert manager.execute(program, course).returncode == 0
    assert manager._processes[program] is newer
    assert program in manager._stopped
    assert not run_root.exists()


def test_preview_finishes_and_cleans_up(task, monkeypatch):
    course, program, run_root = task
    manager = execution.ExecutionManager()
    finished = threading.Event()
    finish = manager._finish

    def finish_and_notify(*args):
        try:
            finish(*args)
        finally:
            finished.set()

    monkeypatch.setattr(manager, "_finish", finish_and_notify)
    manager.launch_preview(program, course)
    assert finished.wait(timeout=5)
    assert not run_root.exists()
    assert not manager._processes


def test_unbroken_script_output_is_read_in_bounded_chunks(monkeypatch):
    stdout = StringIO("x" * 100_000)
    sizes = []
    readline = stdout.readline

    def read_chunk(size=-1):
        sizes.append(size)
        return readline(size)

    stdout.readline = read_chunk
    process = SimpleNamespace(
        stdout=stdout, stderr=StringIO(), wait=lambda **kwargs: 0,
        poll=lambda: 0, violation_reason=None,
    )
    monkeypatch.setattr(execution, "sandbox_popen", lambda *args, **kwargs: process)
    manager = execution.ScriptExampleManager()
    job_id = manager.start("", max_output_chars=128)
    assert manager._jobs[job_id].finished_event.wait(timeout=5)
    status = manager.status(job_id)
    assert status["output_truncated"]
    assert status["stdout"] == "x" * 128
    assert sizes and all(0 < size <= 65536 for size in sizes)


def test_finished_job_retention_preserves_running_jobs_and_completion_order():
    manager = execution.ScriptExampleManager(max_finished_jobs=2)
    slow = manager.start("import time; time.sleep(30)")
    slow_job = manager._jobs[slow]
    try:
        finished = []
        for _ in range(3):
            job_id = manager.start("print('done')")
            job = manager._jobs[job_id]
            assert job.finished_event.wait(timeout=5)
            assert not job.path.exists()
            finished.append(job_id)
        assert manager.status(slow)["running"]
        assert manager.status(finished[0]) is None
        assert manager.status(finished[1])["stdout"].strip() == "done"
        assert len(manager._jobs) == 3
        assert manager.stop(slow)
        assert slow_job.finished_event.wait(timeout=5)
        assert manager.status(finished[1]) is None
        assert manager.status(slow) is not None
        assert len(manager._jobs) == 2
    finally:
        manager.stop_all()


def test_finished_job_limit_must_be_positive():
    with pytest.raises(ValueError, match="Mindestens ein"):
        execution.ScriptExampleManager(max_finished_jobs=0)
