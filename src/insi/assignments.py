"""Kompatible Aufgaben-API, erzeugt aus den Markdown-Quelldateien."""

from .library import TaskAssignment as Assignment
from .library import PARADIGMS, assignment_from_document, task_documents
from insi.training.registry import trainable_names


ASSIGNMENTS: dict[str, Assignment] = {}


def refresh_assignments(
    content_root=None,
    assignments_path: str = "Aufgaben",
) -> tuple[str, ...]:
    """Lade Aufgabenmetadaten nach einer Inhaltssynchronisation neu."""
    names = trainable_names()
    documents = {}
    for paradigm in PARADIGMS if names else ():
        for document in task_documents(
            paradigm, content_root=content_root, assignments_path=assignments_path
        ):
            # Gleiche Priorität wie task_document: imperativ vor oop.
            documents.setdefault(document.name, document)
    refreshed = {}
    for name in names:
        if name not in documents:
            raise ValueError(f"Für {name!r} fehlt die Aufgabenstellung.")
        refreshed[name] = assignment_from_document(documents[name])
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


refresh_assignments()
