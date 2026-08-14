"""Kursgebundene Registry für Prüfungen und interaktive Aktivitäten."""

from __future__ import annotations

import os
from pathlib import Path

from pykim.trainer.definitions import load_exercises
from pykim.trainer.models import Exercise

from .activities import Activity, load_activities


TRAINER_PROVIDER_ENV = "PYKIM_TRAINER_PROVIDER"
TRAINER_PROVIDER_SPEC = "insi.training.provider:provider"

_EXERCISES: dict[str, Exercise] = {}
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
    exercises = load_exercises(trainers) if trainers.is_dir() else {}
    activities = (
        load_activities(trainers, assignments) if trainers.is_dir() else {}
    )
    global _EXERCISES, _ACTIVITIES, _ACTIVE_ROOT
    _EXERCISES = exercises
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


def get_exercise(name: str) -> Exercise:
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


__all__ = [
    "TRAINER_PROVIDER_ENV",
    "TRAINER_PROVIDER_SPEC",
    "activate",
    "activity_names",
    "exercise_names",
    "get_activity",
    "get_exercise",
]
