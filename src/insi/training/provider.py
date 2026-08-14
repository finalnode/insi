"""Optionale Trainingsanbindung für Schülerprogramme mit PyKIM."""

from __future__ import annotations

from .registry import get_exercise
from .runner import check_exercise


class InsiTrainerProvider:
    """Verbinde PyKIMs neutrale Host-Schnittstelle mit dem aktiven in:si-Kurs."""

    @staticmethod
    def get_world_setup(exercise_name: str):
        return get_exercise(exercise_name).world_setup

    @staticmethod
    def check_exercise(
        name: str,
        source: str,
        namespace: dict[str, object] | None = None,
    ):
        return check_exercise(name, source, namespace)


provider = InsiTrainerProvider()

__all__ = ["InsiTrainerProvider", "provider"]
