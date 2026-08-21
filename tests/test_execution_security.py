import json
import os
import threading
import time

import pytest

from insi.execution import ExecutionManager, ScriptExampleManager
from insi.execution_security import (
    CodeOrigin,
    ExecutionPolicy,
    execution_environment,
    student_policy,
)
from insi.progress import (
    load_progress,
    merge_sandbox_progress,
    prepare_sandbox_progress,
)


def test_student_policy_reserves_workspace_for_persistent_project_data(tmp_path):
    policy = student_policy(tmp_path)

    assert policy.origin is CodeOrigin.STUDENT
    assert policy.workspace == tmp_path.resolve()
    assert policy.writable_roots == (tmp_path.resolve(),)
    assert not policy.allow_network
    assert policy.max_memory_bytes == 512 * 1024 * 1024
    assert policy.max_processes == 16
    assert policy.max_written_bytes == 100 * 1024 * 1024
    assert policy.max_cpu_seconds == 120


def test_execution_policy_rejects_invalid_limits_and_unrelated_workspace(tmp_path):
    with pytest.raises(ValueError, match="Laufzeitgrenze"):
        student_policy(tmp_path, timeout_seconds=0)
    with pytest.raises(ValueError, match="Ausgabegrenze"):
        student_policy(tmp_path, max_output_chars=0)
    with pytest.raises(ValueError, match="Arbeitsordner"):
        ExecutionPolicy(
            CodeOrigin.STUDENT,
            tmp_path / "workspace",
            (tmp_path / "other",),
        )


def test_execution_environment_removes_credentials_and_unsafe_python_hooks(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("OPENAI_API_KEY", "nicht-an-kindprozesse-weitergeben")
    monkeypatch.setenv("CUSTOM_CLIENT_SECRET", "ebenfalls-geheim")
    monkeypatch.setenv("PYTHONSTARTUP", str(tmp_path / "startup.py"))
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "existing"))
    monkeypatch.setenv("DISPLAY", ":42")
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/tmp/private-bus")

    environment = execution_environment(
        student_policy(tmp_path),
        pythonpath=(tmp_path / "course",),
    )

    assert "OPENAI_API_KEY" not in environment
    assert "CUSTOM_CLIENT_SECRET" not in environment
    assert "PYTHONSTARTUP" not in environment
    assert "DBUS_SESSION_BUS_ADDRESS" not in environment
    assert environment["DISPLAY"] == ":42"
    assert environment["PYKIM_CODE_ORIGIN"] == "student"
    assert environment["PYTHONPATH"].split(os.pathsep)[0] == str(
        (tmp_path / "course").resolve()
    )
    assert str(tmp_path / "existing") not in environment["PYTHONPATH"].split(os.pathsep)


def test_execution_manager_sanitizes_environment_and_labels_origin(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("GITHUB_TOKEN", "geheim")
    course = tmp_path / "course"
    course.mkdir()
    program = course / "environment.py"
    program.write_text(
        "import json, os\n"
        "print(json.dumps({\n"
        "    'token': os.getenv('GITHUB_TOKEN'),\n"
        "    'origin': os.getenv('PYKIM_CODE_ORIGIN'),\n"
        "}))\n",
        encoding="utf-8",
    )

    result = ExecutionManager().execute(program, course)
    output = json.loads(result.stdout)

    assert result.returncode == 0
    assert output == {"token": None, "origin": "student"}


def test_execution_manager_can_run_graphical_tasks_headlessly(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    program = course / "headless.py"
    program.write_text(
        "import os\nprint(os.getenv('PYKIM_HEADLESS', '0'))\n",
        encoding="utf-8",
    )

    normal = ExecutionManager().execute(program, course)
    headless = ExecutionManager().execute(program, course, headless=True)

    assert normal.stdout.strip() == "0"
    assert headless.stdout.strip() == "1"


def test_execution_manager_limits_runtime_and_output(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    slow = course / "slow.py"
    slow.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")

    timed = ExecutionManager().execute(slow, course, timeout_seconds=0.05)

    assert timed.timed_out
    assert "automatisch beendet" in timed.stderr

    noisy = course / "noisy.py"
    noisy.write_text("print('x' * 1000)\n", encoding="utf-8")
    limited = ExecutionManager().execute(noisy, course, max_output_chars=120)

    assert limited.output_truncated
    assert len(limited.stdout) <= 120
    assert "gekürzt" in limited.stdout
    assert limited.limit_reason is not None
    assert "Ausgabegrenze" in limited.limit_reason


def test_script_example_manager_applies_timeout():
    manager = ScriptExampleManager()
    job_id = manager.start(
        "import time\ntime.sleep(30)",
        timeout_seconds=0.05,
    )

    for _ in range(200):
        status = manager.status(job_id)
        if status and not status["running"]:
            break
        time.sleep(0.01)

    assert status is not None
    assert status["timed_out"]
    assert "automatisch beendet" in status["stderr"]


def test_stopping_execution_manager_still_marks_manual_stop(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    slow = course / "slow.py"
    slow.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    manager = ExecutionManager()
    results = []
    worker = threading.Thread(
        target=lambda: results.append(manager.execute(slow, course))
    )

    worker.start()
    for _ in range(100):
        if manager.is_running(slow):
            break
        time.sleep(0.01)
    assert manager.stop(slow)
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert results[0].stopped
    assert not results[0].timed_out


def test_sandbox_progress_merges_only_new_attempts_without_overwriting_host_changes(
    tmp_path
):
    course = tmp_path / "course"
    progress = course / ".pykim" / "progress.json"
    progress.parent.mkdir(parents=True)
    progress.write_text(
        json.dumps({"format": 1, "attempts": [{"exercise": "old"}]}),
        encoding="utf-8",
    )
    sandbox_progress = tmp_path / "run" / "progress.json"
    baseline = prepare_sandbox_progress(sandbox_progress, course)
    sandbox_data = json.loads(sandbox_progress.read_text(encoding="utf-8"))
    sandbox_data["attempts"].append(
        {"exercise": "sandbox", "passed": True, "tests": []}
    )
    sandbox_progress.write_text(json.dumps(sandbox_data), encoding="utf-8")
    progress.write_text(
        json.dumps(
            {
                "format": 1,
                "attempts": [
                    {"exercise": "old"},
                    {"exercise": "parallel-host"},
                ],
            }
        ),
        encoding="utf-8",
    )

    assert merge_sandbox_progress(
        sandbox_progress, course, baseline_attempts=baseline
    ) == 1

    assert [item["exercise"] for item in load_progress(course)["attempts"]] == [
        "old",
        "parallel-host",
        "sandbox",
    ]


def test_sandbox_progress_rejects_forged_or_oversized_attempts(tmp_path):
    course = tmp_path / "course"
    sandbox_progress = tmp_path / "run" / "progress.json"
    baseline = prepare_sandbox_progress(sandbox_progress, course)
    sandbox_progress.write_text(
        json.dumps(
            {
                "format": 1,
                "attempts": [
                    {"exercise": "missing-fields"},
                    {
                        "exercise": "oversized",
                        "passed": False,
                        "tests": [],
                        "source": "x" * (1024 * 1024),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert merge_sandbox_progress(
        sandbox_progress, course, baseline_attempts=baseline
    ) == 0
    assert load_progress(course)["attempts"] == []
