"""Atomare Aktivierung zusammengehöriger Kurs- und Trainerregistrys."""

from __future__ import annotations

from pathlib import Path

from .assignments import refresh_assignments


def activate_content_registries(
    content_root: str | Path,
    *,
    trainers_path: str = "Trainer",
    assignments_path: str = "Aufgaben",
) -> None:
    """Richte Trainer, Aktivitäten und Aufgaben auf denselben Inhaltsstand."""
    from pykim.trainer.activities import refresh_activities
    from pykim.trainer.exercises import refresh_exercises

    root = Path(content_root).expanduser().resolve()
    refresh_exercises(root, trainers_path)
    refresh_activities(root, trainers_path, assignments_path)
    refresh_assignments(root, assignments_path)


__all__ = ["activate_content_registries"]
