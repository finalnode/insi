"""Kompatibler Einstieg für zusammengehörige Kurs- und Trainerregistrys."""

from __future__ import annotations

from pathlib import Path

from .assignments import refresh_assignments
from .training.registry import activate


def activate_content_registries(
    content_root: str | Path,
    *,
    trainers_path: str = "Trainer",
    assignments_path: str = "Aufgaben",
) -> None:
    """Richte Trainer, Aktivitäten und Aufgaben auf denselben Inhaltsstand."""
    root = Path(content_root).expanduser().resolve()
    activate(
        root,
        trainers_path=trainers_path,
        assignments_path=assignments_path,
    )
    refresh_assignments(root, assignments_path)


__all__ = ["activate_content_registries"]
