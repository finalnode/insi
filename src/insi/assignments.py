"""Kompatible Aufgaben-API, erzeugt aus den Markdown-Quelldateien."""

from .library import TaskAssignment as Assignment
from .library import task_assignment
from insi.training.registry import exercise_names


ASSIGNMENTS = {name: task_assignment(name) for name in exercise_names()}


def refresh_assignments(
    content_root=None,
    assignments_path: str = "Aufgaben",
) -> tuple[str, ...]:
    """Lade Aufgabenmetadaten nach einer Inhaltssynchronisation neu."""
    refreshed = {
        name: task_assignment(
            name,
            content_root=content_root,
            assignments_path=assignments_path,
        )
        for name in exercise_names()
    }
    # Bereits importierte Referenzen müssen denselben Kursstand sehen. Ein
    # Rebinding würde unter anderem Views und Erweiterungen auf dem alten
    # Dictionary zurücklassen.
    ASSIGNMENTS.clear()
    ASSIGNMENTS.update(refreshed)
    return tuple(sorted(ASSIGNMENTS))


def get_assignment(name: str) -> Assignment:
    try:
        return ASSIGNMENTS[name]
    except KeyError:
        raise ValueError(f"Für {name!r} fehlt die Aufgabenstellung.") from None
