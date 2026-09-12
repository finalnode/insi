"""Lernstandsänderungen aus UI und Laufthreads bleiben erhalten und kursgebunden."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from insi import progress


@pytest.mark.parametrize("second", ["answer", "merge", "hints", "clear"])
def test_concurrent_updates_preserve_both_changes(tmp_path, monkeypatch, second):
    entered, release, second_started, second_done = (threading.Event() for _ in range(4))
    original = progress.atomic_write_json
    sandbox = tmp_path / "sandbox.json"
    sandbox.write_text(json.dumps({"attempts": [{"exercise": "task", "passed": True, "tests": []}]}))

    def delayed_write(target, data):
        if not entered.is_set():
            entered.set()
            assert release.wait(5)
        original(target, data)

    monkeypatch.setattr(progress, "atomic_write_json", delayed_write)

    def another_update():
        second_started.set()
        if second == "answer":
            progress.save_task_answer("task", "Antwort", course=tmp_path)
        elif second == "merge":
            progress.merge_sandbox_progress(sandbox, tmp_path, baseline_attempts=0)
        elif second == "hints":
            progress.save_revealed_hint_count("task", 2, course=tmp_path)
        else:
            progress.clear_exercise_progress("old", tmp_path)
        second_done.set()

    # A reset has actual work to do and must preserve the parallel journal edit.
    original(tmp_path / ".pykim/progress.json", {"attempts": [{"exercise": "old"}]})
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(progress.save_journal_entry, "task", "Notiz", course=tmp_path)
        try:
            assert entered.wait(5)
            other = pool.submit(another_update)
            assert second_started.wait(5)
            second_done.wait(0.2)
        finally:
            release.set()
        first.result(timeout=5)
        other.result(timeout=5)
    data = progress.load_progress(tmp_path)
    assert data["journal"]["task"]["text"] == "Notiz"
    if second == "answer":
        assert data["answers"]["task"]["text"] == "Antwort"
    elif second == "merge":
        assert [item["exercise"] for item in data["attempts"]] == ["old", "task"]
    elif second == "hints":
        assert data["hints"]["task"] == 2
    else:
        assert data["attempts"] == []


def test_course_selection_is_resolved_once_per_update(tmp_path, monkeypatch):
    first, second = tmp_path / "first", tmp_path / "second"
    calls = []

    def current_course():
        calls.append(True)
        return first if len(calls) == 1 else second

    monkeypatch.setattr(progress, "get_course_directory", current_course)
    progress.save_task_answer("task", "Antwort")
    assert len(calls) == 1
    assert progress.load_progress(first)["answers"]["task"]["text"] == "Antwort"
    assert not (second / ".pykim/progress.json").exists()


def test_failed_write_releases_update_lock(tmp_path, monkeypatch):
    original = progress.atomic_write_json
    monkeypatch.setattr(progress, "atomic_write_json", lambda *args: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError, match="disk"):
        progress.save_task_answer("task", "fehlgeschlagen", course=tmp_path)
    monkeypatch.setattr(progress, "atomic_write_json", original)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(progress.save_task_answer, "task", "gespeichert", course=tmp_path).result(timeout=5)
    assert progress.load_progress(tmp_path)["answers"]["task"]["text"] == "gespeichert"
