"""Visuelle Autorenprüfung mit Einstieg in die gemeinsame Kurswerkstatt."""

from insi.training.backends import get_authoring_backend
from insi.training.registry import exercise_names, get_exercise

from .components import section_heading
from .library import task_assignment, task_document


def render_authoring_view(ui) -> None:
    """Zeige Aufgaben-Audit und den Einstieg in den gemeinsamen Kurseditor."""
    authoring = get_authoring_backend("pykim")
    with ui.expansion("Trainer-Autorenwerkzeuge", icon="rule").classes(
        "w-full border rounded mt-6"
    ):
        section_heading(
            ui,
            "Aufgabenprüfung",
            "Hier siehst du, aus welchen Testbausteinen jede Aufgabe besteht, "
            "welches Feedback Lernende erhalten und ob Autorenangaben fehlen.",
            level=3,
        )

        for name in exercise_names():
            exercise = get_exercise(name)
            assignment = task_assignment(name)
            document = task_document(name)
            audit = authoring.audit(exercise)
            warnings = [issue for issue in audit.issues if issue.level == "warning"]
            with ui.expansion(
                f"{exercise.title} · {len(exercise.rules)} Tests",
                icon="check_circle" if audit.valid else "error",
            ).classes("w-full"):
                ui.label(f"Kennung: {exercise.name}").classes("text-grey-7")
                ui.label(
                    f"Aufgabentext: {assignment.difficulty} · "
                    f"{document.paradigm if document else 'unbekannt'}"
                ).classes("text-grey-7")
                ui.label(f"Definitions-Hash: {exercise.definition_hash[:16]}…").classes(
                    "font-mono text-grey-7"
                )
                if warnings:
                    for issue in warnings:
                        ui.label(f"Hinweis: {issue.message}").classes("text-orange")
                for index, rule in enumerate(exercise.rules, start=1):
                    with ui.card().classes("w-full shadow-none border"):
                        ui.label(
                            f"Test {index}: "
                            f"{authoring.rule_labels.get(rule.kind, rule.kind)}"
                        ).classes("font-bold")
                        ui.label(f"✓ {rule.success}").classes("text-positive")
                        ui.label(f"✗ {rule.failure}").classes("text-negative")
                        if rule.hint:
                            ui.label(f"Tipp: {rule.hint}").classes("text-orange")

        ui.separator()
        section_heading(
            ui,
            "Kurswerkstatt",
            "Neue Aufgaben, Trainerdefinitionen und vollständige Kursarchive "
            "werden im gemeinsamen Kurseditor erstellt.",
            level=3,
        )
        ui.button(
            "Kurswerkstatt öffnen",
            icon="edit_note",
            on_click=lambda: ui.navigate.to("/course-builder"),
        )


__all__ = ["render_authoring_view"]
