"""Kursgebundene Registry für Prüfungen und interaktive Aktivitäten."""

from __future__ import annotations

import os
from pathlib import Path

from .activities import Activity, load_activities
from .backends import (
    evaluate as backend_evaluate,
    load_backend_exercises,
    register_backend,
    starter_files as backend_starter_files,
)
from .contracts import CheckReportLike, ExerciseLike, StarterFile, Submission
from .pykim_backend import backend as pykim_backend


TRAINER_PROVIDER_ENV = "PYKIM_TRAINER_PROVIDER"
TRAINER_PROVIDER_SPEC = "insi.training.provider:provider"

_EXERCISES: dict[str, ExerciseLike] = {}
_EXERCISE_ENGINES: dict[str, str] = {}
_ACTIVITIES: dict[str, Activity] = {}
_ACTIVE_ROOT: Path | None = None


def activate(
    content_root: str | Path,
    *,
    trainers_path: str = "Trainer",
    assignments_path: str = "Aufgaben",
) -> None:
    """Aktiviere Trainer und Aktivitäten atomar für genau einen Kursstand."""
    root = Path(content_root).expanduser().resolve()
    trainers = root / trainers_path
    assignments = root / assignments_path
    exercises, engines = load_backend_exercises(trainers)
    activities = (
        load_activities(trainers, assignments) if trainers.is_dir() else {}
    )
    global _EXERCISES, _EXERCISE_ENGINES, _ACTIVITIES, _ACTIVE_ROOT
    _EXERCISES = exercises
    _EXERCISE_ENGINES = engines
    _ACTIVITIES = activities
    _ACTIVE_ROOT = root
    # Schülerprozesse und aus in:si gestartete IDEs erben die optionale
    # Provideradresse. PyKIM importiert in:si dadurch nicht fest.
    os.environ[TRAINER_PROVIDER_ENV] = TRAINER_PROVIDER_SPEC


def _ensure_active() -> None:
    """Lade den von in:si übergebenen Kurs auch in einem neuen Kindprozess."""
    if _ACTIVE_ROOT is not None:
        return
    configured = os.environ.get("PYKIM_CONTENT_DIR", "").strip()
    if configured:
        activate(configured)


def exercise_names() -> tuple[str, ...]:
    _ensure_active()
    return tuple(sorted(_EXERCISES))


def get_exercise(name: str) -> ExerciseLike:
    _ensure_active()
    try:
        return _EXERCISES[name]
    except KeyError:
        available = " und ".join(repr(item) for item in exercise_names())
        raise ValueError(
            f"Die Aufgabe {name!r} gibt es nicht. Verfügbar sind: {available}."
        ) from None


def activity_names() -> tuple[str, ...]:
    _ensure_active()
    return tuple(sorted(_ACTIVITIES))


def get_activity(name: str) -> Activity | None:
    _ensure_active()
    return _ACTIVITIES.get(name)


def exercise_engine(name: str) -> str:
    get_exercise(name)
    return _EXERCISE_ENGINES[name]


def exercise_starter_files(name: str) -> tuple[StarterFile, ...]:
    exercise = get_exercise(name)
    return backend_starter_files(exercise_engine(name), exercise)


def evaluate_submission(name: str, submission: Submission) -> CheckReportLike:
    """Prüfe eine Abgabe über die für die Aufgabe registrierte Engine."""
    exercise = get_exercise(name)
    return backend_evaluate(exercise_engine(name), exercise, submission)


def trainable_names() -> tuple[str, ...]:
    _ensure_active()
    return tuple(sorted(set(_EXERCISES) | set(_ACTIVITIES)))


def validate_training_directory(
    trainers: str | Path,
    assignments: str | Path | None = None,
) -> None:
    """Validiere alle Engines und Core-Aktivitäten ohne Registry-Aktivierung."""
    directory = Path(trainers)
    load_backend_exercises(directory)
    load_activities(directory, assignments)


register_backend(pykim_backend)


__all__ = [
    "TRAINER_PROVIDER_ENV",
    "TRAINER_PROVIDER_SPEC",
    "activate",
    "activity_names",
    "exercise_names",
    "exercise_engine",
    "exercise_starter_files",
    "evaluate_submission",
    "get_activity",
    "get_exercise",
    "trainable_names",
    "validate_training_directory",
]
