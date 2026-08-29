"""Lernstand, Dokubuch und Traineraufzeichnungen im Kursordner."""

import pykim

from insi.progress import (
    load_progress,
    record_attempt,
    revealed_hint_count,
    save_journal_entry,
    save_revealed_hint_count,
    save_task_answer,
)
from pykim.trainer.models import CheckReport, CheckResult, OptimizationResult


def test_progress_and_journal_travel_inside_the_course_folder(tmp_path):
    course = tmp_path / "mounted-drive"
    course.mkdir()
    report = CheckReport(
        "Testaufgabe",
        (
            CheckResult(True, "Position stimmt.", "Position falsch."),
            CheckResult(False, "Schleife stimmt.", "Schleife fehlt.", "Nutze for."),
        ),
        OptimizationResult(50, maximum=100),
    )

    assert record_attempt("test", report, "right()", course=course)
    save_journal_entry("test", "Ich brauche noch eine Schleife.", course=course)
    save_task_answer(
        "imperativ/erste-schritte",
        "Meine freie Antwort.",
        course=course,
    )
    save_revealed_hint_count("imperativ/test", 2, course=course)
    progress = load_progress(course)

    attempt = progress["attempts"][0]
    assert attempt["source"] == "right()"
    assert attempt["tests"][1]["hint"] == "Nutze for."
    assert attempt["optimization"]["score"] == 50
    assert progress["journal"]["test"]["text"].startswith("Ich brauche")
    assert progress["answers"]["imperativ/erste-schritte"]["text"] == (
        "Meine freie Antwort."
    )
    assert revealed_hint_count("imperativ/test", course=course) == 2
    assert (course / ".pykim" / "progress.json").exists()


def test_trainer_records_an_attempt_when_course_is_configured(
    tmp_path, monkeypatch, capsys
):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.delenv("PYKIM_PROGRESS_MODE")
    monkeypatch.setenv("PYKIM_COURSE_DIR", str(course))
    pykim.set_position(50, 50)
    pykim.paint_start("purple")
    pykim.right(5)
    pykim.down(5)
    pykim.left(5)
    pykim.up(5)

    from insi.training.runner import check_exercise

    check_exercise("quadrat-5", "right(5)")
    capsys.readouterr()
    progress = load_progress(course)

    assert len(progress["attempts"]) == 1
    assert progress["attempts"][0]["exercise"] == "quadrat-5"
    assert progress["attempts"][0]["successful"]


def test_record_attempt_is_disabled_without_a_configured_course(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "empty-config"))
    monkeypatch.delenv("PYKIM_COURSE_DIR", raising=False)
    report = CheckReport("Leer", ())

    assert not record_attempt("leer", report)


def test_trainer_does_not_record_progress_in_example_mode(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.setenv("PYKIM_COURSE_DIR", str(course))
    monkeypatch.setenv("PYKIM_PROGRESS_MODE", "disabled")

    from insi.training.runner import check_exercise

    check_exercise("quadrat-5", "")

    assert load_progress(course)["attempts"] == []
