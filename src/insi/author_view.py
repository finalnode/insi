"""Visuelle Autorenprüfung und Builder-Entwürfe für Traineraufgaben."""

import json

from pykim.trainer.authoring import (
    RULE_LABELS,
    RULE_TEMPLATES,
    audit_exercise,
    generate_exercise_source,
)
from insi.training.registry import exercise_names, get_exercise

from .components import section_heading
from .library import task_assignment, task_document
from .course import get_course_directory
from .author_workspace import (
    AuthorDraft,
    assignment_markdown,
    load_published_draft,
    save_author_draft,
    validate_author_draft,
)


def render_authoring_view(ui) -> None:
    """Zeige Aufgaben-Audit, Feedbackvorschau und einen kleinen Bausteineditor."""
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
            audit = audit_exercise(exercise)
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
                            f"Test {index}: {RULE_LABELS.get(rule.kind, rule.kind)}"
                        ).classes("font-bold")
                        ui.label(f"✓ {rule.success}").classes("text-positive")
                        ui.label(f"✗ {rule.failure}").classes("text-negative")
                        if rule.hint:
                            ui.label(f"Tipp: {rule.hint}").classes("text-orange")

        ui.separator()
        section_heading(
            ui,
            "Neue Trainingsdefinition entwerfen",
            "Der Entwurf ist sicheres YAML. Positionen, Farben, Feedback und erlaubte "
            "Prüfbausteine können ohne eigenen Python-Trainer angepasst werden.",
            level=3,
        )
        published = ui.select(
            {name: get_exercise(name).title for name in exercise_names()},
            label="Vorhandene Aufgabe als Ausgangspunkt laden",
        ).classes("w-full")
        name = ui.input("Eindeutige Kennung", placeholder="meine-aufgabe")
        title = ui.input("Titel", placeholder="Meine Aufgabe")
        paradigm = ui.select(
            {"imperativ": "Imperativer Lernweg", "oop": "OOP-Lernweg"},
            value="imperativ",
            label="Lernweg",
        )
        difficulty = ui.select(
            {"einfach": "Einfach", "mittel": "Mittel", "fortgeschritten": "Fortgeschritten"},
            value="mittel",
            label="Schwierigkeit",
        )
        summary = ui.input(
            "Kurze Aufgabenstellung", placeholder="Zeichne ..."
        ).classes("w-full")
        requirements = ui.textarea(
            "Anforderungen – eine pro Zeile",
            placeholder="Beginne bei ...\nVerwende eine Schleife ...",
        ).props("outlined autogrow").classes("w-full")
        rules = ui.select(
            {key: RULE_LABELS[key] for key in RULE_TEMPLATES},
            multiple=True,
            label="Prüfbausteine",
        ).classes("w-full")
        optimal = ui.number("Optimale relevante Codezeilen (optional)", min=1)
        trainer_output = ui.codemirror(
            value="", language="YAML", line_wrapping=False,
        ).classes("w-full").style("height: 24rem")
        markdown_output = ui.textarea("Vollständiges Aufgaben-Markdown").props(
            "outlined autogrow"
        ).classes("w-full font-mono")
        validation = ui.label("Noch kein Entwurf erzeugt.").classes("text-grey-7")
        preview = ui.column().classes("w-full")

        def current_draft() -> AuthorDraft:
            return AuthorDraft(
                name.value or "",
                trainer_output.value or "",
                markdown_output.value or "",
            )

        def validate() -> tuple[str, ...]:
            issues = validate_author_draft(current_draft())
            validation.text = (
                "✓ Entwurf ist technisch vollständig."
                if not issues else "✗ " + " · ".join(issues)
            )
            validation.classes(
                remove="text-grey-7 text-positive text-negative",
                add="text-positive" if not issues else "text-negative",
            )
            return issues

        def render_preview() -> None:
            preview.clear()
            with preview:
                ui.label("Feedbackvorschau").classes("font-bold")
                for index, kind in enumerate(tuple(rules.value or ()), start=1):
                    with ui.card().classes("w-full shadow-none border"):
                        ui.label(f"Test {index}: {RULE_LABELS[kind]}").classes("font-bold")
                        ui.label("✓ So sieht eine bestandene Prüfung aus.").classes("text-positive")
                        ui.label("✗ So sieht eine fehlgeschlagene Prüfung aus.").classes("text-negative")
                        ui.label("Tipp: Hier erscheint die konkrete Hilfestellung.").classes("text-orange")

        def generate() -> None:
            try:
                trainer = generate_exercise_source(
                    name.value or "",
                    title.value or "",
                    tuple(rules.value or ()),
                    optimal_lines=int(optimal.value) if optimal.value else None,
                )
                markdown = assignment_markdown(
                    title.value or "",
                    summary.value or "",
                    requirements.value or "",
                    difficulty.value or "mittel",
                )
                trainer_output.value = trainer
                markdown_output.value = markdown
                render_preview()
                validate()
                ui.notify("Gültiger Builder-Entwurf erzeugt.", type="positive")
            except ValueError as error:
                ui.notify(str(error), type="warning")

        def copy() -> None:
            if not trainer_output.value:
                ui.notify("Erzeuge zuerst einen Entwurf.", type="warning")
                return
            ui.run_javascript(
                f"navigator.clipboard.writeText({json.dumps(trainer_output.value)})"
            )
            ui.notify("Trainings-YAML kopiert.", type="positive")

        def load_published() -> None:
            if not published.value:
                return
            try:
                draft = load_published_draft(published.value)
                exercise = get_exercise(published.value)
                assignment = task_assignment(published.value)
                document = task_document(published.value)
                name.value = draft.name
                title.value = exercise.title
                paradigm.value = document.paradigm if document else "imperativ"
                difficulty.value = assignment.difficulty
                summary.value = assignment.summary
                requirements.value = "\n".join(assignment.requirements)
                rules.value = [rule.kind for rule in exercise.rules if rule.kind in RULE_TEMPLATES]
                trainer_output.value = draft.trainer_source
                markdown_output.value = draft.assignment_markdown
                render_preview()
                validate()
                ui.notify("Aufgabe wurde in den Entwurf geladen.", type="positive")
            except (OSError, ValueError) as error:
                ui.notify(str(error), type="negative")

        overwrite = ui.checkbox("Vorhandenen Entwurf bewusst überschreiben")

        def save() -> None:
            issues = validate()
            if issues:
                ui.notify("Der Entwurf ist noch nicht speicherbar.", type="warning")
                return
            course = get_course_directory()
            if course is None:
                ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                return
            try:
                trainer_path, markdown_path = save_author_draft(
                    course,
                    current_draft(),
                    paradigm=paradigm.value or "imperativ",
                    overwrite=bool(overwrite.value),
                )
                ui.notify(
                    f"Beide Entwürfe gespeichert unter {trainer_path.parent.parent}",
                    type="positive",
                )
            except (OSError, ValueError) as error:
                ui.notify(str(error), type="negative")

        published.on("update:model-value", lambda: load_published())
        trainer_output.on("update:model-value", lambda: validate())
        markdown_output.on("update:model-value", lambda: validate())

        with ui.row():
            ui.button("Entwurf erzeugen", on_click=generate, icon="auto_fix_high")
            ui.button("Kopieren", on_click=copy, icon="content_copy").props("outline")
            ui.button("Beide Dateien speichern", on_click=save, icon="save").props("outline")


__all__ = ["render_authoring_view"]
