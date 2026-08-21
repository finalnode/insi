"""Generische Trainingsinfrastruktur der in:si-Lernumgebung."""

from .activities import Activity, CodeBlock, MatchingPair
from .backends import backend_names, register_backend
from .contracts import CheckReport, CheckResult, StarterFile, Submission
from .registry import (
    activity_names,
    evaluate_submission,
    exercise_names,
    get_activity,
    get_exercise,
    trainable_names,
)

__all__ = [
    "Activity",
    "CheckReport",
    "CheckResult",
    "CodeBlock",
    "MatchingPair",
    "StarterFile",
    "Submission",
    "activity_names",
    "backend_names",
    "evaluate_submission",
    "exercise_names",
    "get_activity",
    "get_exercise",
    "register_backend",
    "trainable_names",
]
