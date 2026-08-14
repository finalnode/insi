"""Projektartige Kurswerkstatt mit Inhaltsnavigation und echter Kursvorschau."""

from __future__ import annotations

from pathlib import Path

import yaml

from pykim.trainer.authoring import RULE_LABELS, RULE_TEMPLATES, generate_exercise_source
from pykim.trainer.definitions import exercise_from_data

from .author_workspace import AuthorDraft, assignment_markdown, validate_author_draft
from .course_builder_view import (
    analyze_course_directory,
    course_documents,
    course_source_counts,
    create_portable_course,
    ensure_course_source,
    import_course_candidates,
    load_course_document,
    save_course_assignment,
    save_course_markdown,
)
from .library import (
    render_script_markdown,
    render_task_markdown,
    task_hints,
    task_sources,
    task_tags,
)
from .markedown import validate_markedown
from .theme import configure_theme


def _title(markdown: str, fallback: str) -> str:
    return next(
        (
            line.removeprefix("# ").strip()
            for line in markdown.splitlines()
            if line.startswith("# ")
        ),
        fallback,
    )


def _trainer_exercise(source: str):
    payload = yaml.safe_load(source)
    definitions = payload.get("exercises") if isinstance(payload, dict) else None
    if not isinstance(definitions, list) or len(definitions) != 1:
        raise ValueError("Die Vorschau benötigt genau eine Trainingsdefinition.")
    return exercise_from_data(definitions[0])


def register_course_studio_page(ui, nicegui_app, nicegui_run, *, desktop: bool) -> None:
    @ui.page("/course-builder")
    def course_studio() -> None:
        configure_theme(ui)
        state = {"selection": None}

        with ui.column().classes("w-full max-w-7xl mx-auto gap-3 p-5"):
            with ui.row().classes("w-full items-center gap-2"):
                ui.button(
                    icon="arrow_back", on_click=lambda: ui.navigate.to("/")
                ).props("flat round")
                with ui.column().classes("gap-0"):
                    ui.label("PyKIM Kurswerkstatt").classes(
                        "text-2xl font-bold text-primary"
                    )
                    workspace_status = ui.label("Lokaler Kurseditor").classes(
                        "text-xs text-grey-7"
                    )
                ui.space()
                export_button = ui.button("ZIP exportieren", icon="inventory_2")

            with ui.element("div").classes("pykim-script-layout w-full items-start"):
                menu = ui.card().classes("pykim-script-menu shadow-none gap-2")
                editor = ui.column().classes("pykim-script-page w-full min-w-0 gap-3")

        with menu:
            ui.label("Kursprojekt").classes("text-lg font-bold")
            source = ui.input(
                "Kursordner", placeholder=str(Path.home() / "Mein-PyKIM-Kurs")
            ).props("dense").classes("w-full")

            async def choose_source() -> None:
                if not desktop or nicegui_app.native.main_window is None:
                    return
                import webview

                selected = await nicegui_app.native.main_window.create_file_dialog(
                    dialog_type=webview.FileDialog.FOLDER,
                    directory=str(Path.home()),
                )
                if selected:
                    source.set_value(str(Path(selected[0]).resolve()))
                    ensure_course_source(source.value)
                    refresh_navigation()
                    show_welcome()

            async def analyze_existing_files() -> None:
                if not source.value:
                    ui.notify("Wähle zuerst einen Kursordner.", type="warning")
                    return
                try:
                    candidates = await nicegui_run.io_bound(
                        analyze_course_directory, source.value
                    )
                except (OSError, ValueError) as error:
                    ui.notify(f"Analyse fehlgeschlagen: {error}", type="negative")
                    return
                if not candidates:
                    ui.notify(
                        "Keine unzugeordneten Markdown-, Text- oder YAML-Dateien gefunden.",
                        type="info",
                    )
                    return
                with ui.dialog() as mapping_dialog, ui.card().classes(
                    "w-full max-w-4xl"
                ):
                    ui.label("Vorhandene Dateien zuordnen").classes("text-xl font-bold")
                    ui.label(
                        "Passe die Vorschläge an. Die Originaldateien bleiben erhalten."
                    ).classes("text-sm text-grey-7")
                    paradigm = ui.select(
                        {"imperativ": "Imperativer Lernweg", "oop": "OOP-Lernweg"},
                        value="imperativ",
                        label="Ziel-Lernweg für Markdown",
                    ).classes("w-64")
                    fields = {}
                    with ui.scroll_area().classes("w-full").style("max-height: 28rem"):
                        for candidate in candidates:
                            with ui.row().classes("w-full items-center gap-3 no-wrap"):
                                with ui.column().classes("grow min-w-0 gap-0"):
                                    ui.label(candidate.relative_path).classes(
                                        "font-mono text-sm break-all"
                                    )
                                    ui.label(candidate.reason).classes(
                                        "text-xs text-grey-7"
                                    )
                                fields[candidate.relative_path] = ui.select(
                                    {
                                        "script": "Skript",
                                        "task": "Freie Aufgabe",
                                        "trainer": "Trainer",
                                        "ignore": "Ignorieren",
                                    },
                                    value=candidate.suggested_kind,
                                ).classes("w-48")

                    def apply_mapping() -> None:
                        try:
                            imported = import_course_candidates(
                                source.value,
                                {name: field.value or "ignore" for name, field in fields.items()},
                                paradigm=paradigm.value or "imperativ",
                            )
                            mapping_dialog.close()
                            refresh_navigation()
                            ui.notify(
                                f"{len(imported)} Dateien wurden als Kopien einsortiert.",
                                type="positive",
                            )
                        except (OSError, ValueError) as error:
                            ui.notify(f"Zuordnung fehlgeschlagen: {error}", type="negative")

                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button("Abbrechen", on_click=mapping_dialog.close).props("flat")
                        ui.button(
                            "Zuordnung übernehmen", icon="rule", on_click=apply_mapping
                        )
                mapping_dialog.open()

            if desktop:
                ui.button(
                    "Ordner wählen", icon="folder_open", on_click=choose_source
                ).props("flat dense no-caps").classes("w-full")
            ui.button(
                "Dateien analysieren",
                icon="manage_search",
                on_click=analyze_existing_files,
            ).props("flat dense no-caps").classes("w-full")

            with ui.expansion("Kursangaben", icon="settings").classes("w-full"):
                course_name = ui.input("Kursname").props("dense").classes("w-full")
                teacher = ui.input("Lehrkraft/Herausgeber").props("dense").classes(
                    "w-full"
                )
                school = ui.input("Schule/Organisation").props("dense").classes(
                    "w-full"
                )
                repository = ui.input("Repository (optional)").props("dense").classes(
                    "w-full"
                )
                branch = ui.input("Branch", value="main").props("dense").classes(
                    "w-full"
                )

            ui.separator()
            with ui.row().classes("w-full items-center"):
                ui.label("Skripte").classes("font-bold text-primary")
                ui.space()
                ui.button(icon="add", on_click=lambda: show_script()).props(
                    "flat round dense"
                )
            script_navigation = ui.column().classes("w-full gap-0")

            with ui.row().classes("w-full items-center mt-2"):
                ui.label("Aufgaben").classes("font-bold text-primary")
                ui.space()
                ui.button(icon="add", on_click=lambda: show_free_task()).props(
                    "flat round dense"
                )
            task_navigation = ui.column().classes("w-full gap-0")

        def require_source() -> Path | None:
            if not source.value:
                ui.notify("Wähle zuerst einen Kursordner.", type="warning")
                return None
            return ensure_course_source(source.value)

        def document_label(kind: str, paradigm: str, name: str) -> str:
            try:
                markdown = load_course_document(
                    source.value, kind, name, paradigm=paradigm
                )
                return _title(markdown, name)
            except (OSError, ValueError):
                return name

        def refresh_navigation() -> None:
            script_navigation.clear()
            task_navigation.clear()
            if not source.value:
                workspace_status.set_text("Noch kein Kursordner gewählt")
                return
            counts = course_source_counts(source.value)
            workspace_status.set_text(
                f"{counts['scripts']} Skripte · {counts['assignments']} Aufgaben · "
                f"{counts['trainers']} Trainer"
            )
            with script_navigation:
                for paradigm in ("imperativ", "oop"):
                    names = course_documents(source.value, "Skripte", paradigm=paradigm)
                    if names:
                        ui.label("Imperativ" if paradigm == "imperativ" else "OOP").classes(
                            "text-xs text-grey-6 mt-1 px-2"
                        )
                    for name in names:
                        ui.button(
                            document_label("Skripte", paradigm, name),
                            icon="description",
                            on_click=lambda p=paradigm, n=name: show_script(p, n),
                        ).props("flat dense no-caps align=left").classes(
                            "pykim-script-menu-button w-full"
                        )
            with task_navigation:
                for paradigm in ("imperativ", "oop"):
                    names = course_documents(source.value, "Aufgaben", paradigm=paradigm)
                    if names:
                        ui.label("Imperativ" if paradigm == "imperativ" else "OOP").classes(
                            "text-xs text-grey-6 mt-1 px-2"
                        )
                    for name in names:
                        has_trainer = name in set(
                            course_documents(source.value, "trainer")
                        )
                        ui.button(
                            document_label("Aufgaben", paradigm, name),
                            icon="task_alt" if has_trainer else "description",
                            on_click=(
                                (lambda p=paradigm, n=name: show_task(p, n))
                                if has_trainer
                                else (lambda p=paradigm, n=name: show_free_task(p, n))
                            ),
                        ).props("flat dense no-caps align=left").classes(
                            "pykim-script-menu-button w-full"
                        )

        def show_welcome() -> None:
            state["selection"] = None
            editor.clear()
            with editor:
                ui.label("Kursinhalt bearbeiten").classes("text-2xl font-bold")
                ui.label(
                    "Wähle links ein Kapitel oder eine Aufgabe – oder lege über + "
                    "einen neuen Inhalt an. Bearbeitung und Vorschau bleiben dabei "
                    "direkt nebeneinander erreichbar."
                ).classes("text-grey-7")
                with ui.row().classes("w-full gap-3 flex-wrap"):
                    ui.button(
                        "Neues Skriptkapitel", icon="menu_book", on_click=lambda: show_script()
                    )
                    ui.button(
                        "Neue freie Aufgabe",
                        icon="description",
                        on_click=lambda: show_free_task(),
                    ).props("outline")
                    ui.button(
                        "Neue geprüfte PyKIM-Aufgabe",
                        icon="rule",
                        on_click=lambda: show_task(),
                    ).props("outline")

        def show_script(paradigm: str = "imperativ", name: str = "") -> None:
            if require_source() is None:
                return
            state["selection"] = ("script", paradigm, name)
            content = (
                load_course_document(source.value, "Skripte", name, paradigm=paradigm)
                if name
                else "# Neues Kapitel\n\nErkläre hier das Thema.\n\n```python\nfrom pykim import *\n```\n"
            )
            editor.clear()
            with editor:
                with ui.row().classes("w-full items-end gap-3 flex-wrap"):
                    ui.label("Skriptkapitel").classes("text-xl font-bold")
                    chapter_name = ui.input(
                        "Dateiname", value=name, placeholder="01-erste-schritte"
                    ).classes("grow min-w-48")
                    chapter_paradigm = ui.select(
                        {"imperativ": "Imperativ", "oop": "OOP"},
                        value=paradigm,
                        label="Lernweg",
                    ).classes("w-40")
                with ui.tabs().classes("w-full") as tabs:
                    edit_tab = ui.tab("Bearbeiten", icon="edit")
                    preview_tab = ui.tab("Vorschau", icon="visibility")
                with ui.tab_panels(tabs, value=edit_tab).classes("w-full"):
                    with ui.tab_panel(edit_tab):
                        markdown = ui.codemirror(
                            value=content, language="Markdown", line_wrapping=True
                        ).classes("w-full").style("height: 34rem")
                    with ui.tab_panel(preview_tab):
                        preview = ui.markdown(render_script_markdown(content)).classes(
                            "pykim-chapter-markdown w-full"
                        )
                validation = ui.label("M@rkdown noch nicht geprüft.").classes(
                    "text-grey-7"
                )

                def validate() -> tuple:
                    issues = validate_markedown(markdown.value or "", kind="script")
                    validation.set_text(
                        "✓ M@rkdown ist gültig."
                        if not issues
                        else "✗ " + " · ".join(
                            f"Zeile {issue.line}: {issue.message}" for issue in issues
                        )
                    )
                    validation.classes(
                        remove="text-grey-7 text-positive text-negative",
                        add="text-positive" if not issues else "text-negative",
                    )
                    return issues

                def update_preview() -> None:
                    validate()
                    preview.set_content(render_script_markdown(markdown.value or ""))

                def save() -> None:
                    if validate():
                        ui.notify("Behebe zuerst die M@rkdown-Fehler.", type="warning")
                        return
                    try:
                        target = save_course_markdown(
                            source.value,
                            "Skripte",
                            chapter_name.value or "",
                            markdown.value or "",
                            paradigm=chapter_paradigm.value or "imperativ",
                        )
                        refresh_navigation()
                        ui.notify(f"Gespeichert: {target.name}", type="positive")
                    except (OSError, ValueError) as error:
                        ui.notify(str(error), type="negative")

                tabs.on_value_change(
                    lambda event: update_preview()
                    if event.value == "Vorschau"
                    else None
                )
                with ui.row().classes("w-full justify-end"):
                    ui.button("M@rkdown prüfen", icon="fact_check", on_click=validate).props(
                        "outline"
                    )
                    ui.button("Speichern", icon="save", on_click=save)

        def render_task_preview(container, markdown: str, trainer: str) -> None:
            container.clear()
            with container:
                title = _title(markdown, "Aufgabe")
                ui.label(title).classes("text-2xl font-bold")
                tags = task_tags(markdown)
                if tags:
                    with ui.row().classes("items-center gap-1"):
                        for tag in tags:
                            ui.badge(tag, color="grey-7")
                ui.markdown(render_task_markdown(markdown)).classes(
                    "pykim-chapter-markdown w-full"
                )
                hints = task_hints(markdown)
                if hints:
                    ui.label("Hinweise").classes("text-lg font-bold mt-3")
                    for index, hint in enumerate(hints, start=1):
                        with ui.card().classes("w-full shadow-none bg-orange-1 border-l-4 border-primary"):
                            ui.label(f"Hinweis {index}").classes("font-bold text-primary")
                            ui.markdown(hint)
                sources = task_sources(markdown)
                if sources:
                    with ui.row().classes("items-center gap-1 text-sm text-grey-7"):
                        ui.icon("source", size="xs")
                        ui.label("Quellen:")
                        for item in sources:
                            ui.link(item.label, item.url, new_tab=True) if item.url else ui.label(item.label)
                if not trainer.strip():
                    ui.label("Freie Antwort – keine automatische Prüfung").classes(
                        "text-sm text-grey-7 mt-3"
                    )
                    return
                try:
                    exercise = _trainer_exercise(trainer)
                    ui.label("Automatische Tests").classes("text-lg font-bold mt-4")
                    for index, rule in enumerate(exercise.rules, start=1):
                        with ui.card().classes("w-full shadow-none border"):
                            ui.label(
                                f"Test {index}: {RULE_LABELS.get(rule.kind, rule.kind)}"
                            ).classes("font-bold")
                            ui.label(f"✓ {rule.success}").classes("text-positive")
                            ui.label(f"✗ {rule.failure}").classes("text-negative")
                            if rule.hint:
                                ui.label(f"Tipp: {rule.hint}").classes("text-orange")
                except (AttributeError, TypeError, ValueError, yaml.YAMLError) as error:
                    ui.label(f"Trainervorschau nicht möglich: {error}").classes("text-negative")

        def show_free_task(paradigm: str = "imperativ", name: str = "") -> None:
            if require_source() is None:
                return
            content = (
                load_course_document(source.value, "Aufgaben", name, paradigm=paradigm)
                if name
                else assignment_markdown(
                    "Neue Aufgabe",
                    "Beschreibe hier die Aufgabe.",
                    "Formuliere mindestens eine Anforderung.",
                    "mittel",
                )
            )
            editor.clear()
            with editor:
                with ui.row().classes("w-full items-end gap-3 flex-wrap"):
                    ui.label("Freie Aufgabe").classes("text-xl font-bold")
                    task_name = ui.input(
                        "Dateiname", value=name, placeholder="reflexion-schleifen"
                    ).classes("grow min-w-48")
                    task_paradigm = ui.select(
                        {"imperativ": "Imperativ", "oop": "OOP"},
                        value=paradigm,
                        label="Lernweg",
                    ).classes("w-40")
                ui.label(
                    "Ohne Trainerdatei erhalten Lernende ein freies Antwortfeld. "
                    "Hinweise, Tags und Quellen sind weiterhin möglich."
                ).classes("text-sm text-grey-7")
                with ui.tabs().classes("w-full") as tabs:
                    edit_tab = ui.tab("Bearbeiten", icon="edit")
                    preview_tab = ui.tab("Vorschau", icon="visibility")
                with ui.tab_panels(tabs, value=edit_tab).classes("w-full"):
                    with ui.tab_panel(edit_tab):
                        markdown = ui.codemirror(
                            value=content, language="Markdown", line_wrapping=True
                        ).classes("w-full").style("height: 34rem")
                    with ui.tab_panel(preview_tab):
                        preview = ui.column().classes("w-full gap-2")
                validation = ui.label("M@rkdown noch nicht geprüft.").classes("text-grey-7")

                def validate() -> tuple:
                    issues = validate_markedown(markdown.value or "", kind="task")
                    validation.set_text(
                        "✓ M@rkdown ist gültig."
                        if not issues
                        else "✗ " + " · ".join(
                            f"Zeile {issue.line}: {issue.message}" for issue in issues
                        )
                    )
                    validation.classes(
                        remove="text-grey-7 text-positive text-negative",
                        add="text-positive" if not issues else "text-negative",
                    )
                    return issues

                def save() -> None:
                    if validate():
                        return
                    try:
                        target = save_course_markdown(
                            source.value,
                            "Aufgaben",
                            task_name.value or "",
                            markdown.value or "",
                            paradigm=task_paradigm.value or "imperativ",
                        )
                        refresh_navigation()
                        ui.notify(f"Freie Aufgabe gespeichert: {target.name}", type="positive")
                    except (OSError, ValueError) as error:
                        ui.notify(str(error), type="negative")

                tabs.on_value_change(
                    lambda event: render_task_preview(
                        preview, markdown.value or "", ""
                    )
                    if event.value == "Vorschau"
                    else None
                )
                with ui.row().classes("w-full justify-end"):
                    ui.button("Speichern", icon="save", on_click=save)

        def show_task(paradigm: str = "imperativ", name: str = "") -> None:
            if require_source() is None:
                return
            state["selection"] = ("task", paradigm, name)
            markdown_content = (
                load_course_document(source.value, "Aufgaben", name, paradigm=paradigm)
                if name
                else ""
            )
            trainer_content = (
                load_course_document(source.value, "trainer", name) if name else ""
            )
            editor.clear()
            with editor:
                ui.label("PyKIM-Aufgabe").classes("text-xl font-bold")
                with ui.row().classes("w-full gap-3 items-start flex-wrap"):
                    task_name = ui.input(
                        "Kennung", value=name, placeholder="meine-aufgabe"
                    ).classes("grow min-w-44")
                    task_title = ui.input(
                        "Titel", value=_title(markdown_content, "")
                    ).classes("grow min-w-52")
                    task_paradigm = ui.select(
                        {"imperativ": "Imperativ", "oop": "OOP"},
                        value=paradigm,
                        label="Lernweg",
                    ).classes("w-40")
                with ui.expansion("Entwurf aus Prüfbausteinen erzeugen", icon="auto_fix_high").classes("w-full"):
                    summary = ui.input("Kurze Aufgabenstellung").classes("w-full")
                    requirements = ui.textarea("Anforderungen – eine pro Zeile").props(
                        "outlined autogrow"
                    ).classes("w-full")
                    hints = ui.textarea(
                        "Hinweise – einer pro Zeile",
                        placeholder="Prüfe zuerst deine Startposition.\nWelche Schleife passt?",
                    ).props("outlined autogrow").classes("w-full")
                    tags = ui.input(
                        "Tags (kommagetrennt)",
                        placeholder="schleifen, pixel, einstieg",
                    ).classes("w-full")
                    with ui.row().classes("w-full gap-3 items-start flex-wrap"):
                        difficulty = ui.select(
                            {"einfach": "Einfach", "mittel": "Mittel", "fortgeschritten": "Fortgeschritten"},
                            value="mittel",
                            label="Schwierigkeit",
                        ).classes("w-full sm:w-48")
                        rules = ui.select(
                            {key: RULE_LABELS[key] for key in RULE_TEMPLATES},
                            multiple=True,
                            label="Prüfbausteine",
                        ).classes("grow min-w-64")
                        optimal = ui.number("Optimale Codezeilen", min=1).props(
                            "hint='optional' persistent-hint"
                        ).classes("w-full sm:w-52")

                    def generate() -> None:
                        try:
                            trainer_editor.set_value(
                                generate_exercise_source(
                                    task_name.value or "",
                                    task_title.value or "",
                                    tuple(rules.value or ()),
                                    optimal_lines=int(optimal.value) if optimal.value else None,
                                )
                            )
                            markdown_editor.set_value(
                                assignment_markdown(
                                    task_title.value or "",
                                    summary.value or "",
                                    requirements.value or "",
                                    difficulty.value or "mittel",
                                    hints=tuple(
                                        line.strip()
                                        for line in (hints.value or "").splitlines()
                                        if line.strip()
                                    ),
                                    tags=tuple(
                                        tag.strip()
                                        for tag in (tags.value or "").split(",")
                                        if tag.strip()
                                    ),
                                )
                            )
                            validate()
                        except ValueError as error:
                            ui.notify(str(error), type="warning")

                    ui.button("Entwurf erzeugen", icon="auto_fix_high", on_click=generate)

                with ui.tabs().classes("w-full") as tabs:
                    markdown_tab = ui.tab("Aufgabe.md", icon="description")
                    trainer_tab = ui.tab("Trainer.yml", icon="rule")
                    preview_tab = ui.tab("Vorschau", icon="visibility")
                with ui.tab_panels(tabs, value=markdown_tab).classes("w-full"):
                    with ui.tab_panel(markdown_tab):
                        markdown_editor = ui.codemirror(
                            value=markdown_content, language="Markdown", line_wrapping=True
                        ).classes("w-full").style("height: 32rem")
                    with ui.tab_panel(trainer_tab):
                        trainer_editor = ui.codemirror(
                            value=trainer_content, language="YAML", line_wrapping=False
                        ).classes("w-full").style("height: 32rem")
                    with ui.tab_panel(preview_tab):
                        preview = ui.column().classes("w-full gap-2")
                validation = ui.label("Noch nicht geprüft.").classes("text-grey-7")

                def draft() -> AuthorDraft:
                    return AuthorDraft(
                        task_name.value or "",
                        trainer_editor.value or "",
                        markdown_editor.value or "",
                    )

                def validate() -> tuple[str, ...]:
                    issues = validate_author_draft(draft())
                    validation.set_text(
                        "✓ Aufgabe und Trainer sind vollständig."
                        if not issues
                        else "✗ " + " · ".join(issues)
                    )
                    validation.classes(
                        remove="text-grey-7 text-positive text-negative",
                        add="text-positive" if not issues else "text-negative",
                    )
                    return issues

                def save() -> None:
                    if validate():
                        return
                    try:
                        markdown, trainer = save_course_assignment(
                            source.value,
                            draft(),
                            paradigm=task_paradigm.value or "imperativ",
                        )
                        refresh_navigation()
                        ui.notify(f"{markdown.name} und {trainer.name} gespeichert.", type="positive")
                    except (OSError, ValueError) as error:
                        ui.notify(str(error), type="negative")

                tabs.on_value_change(
                    lambda event: render_task_preview(
                        preview, markdown_editor.value or "", trainer_editor.value or ""
                    )
                    if event.value == "Vorschau"
                    else None
                )
                with ui.row().classes("w-full justify-end"):
                    ui.button("Aufgabe speichern", icon="save", on_click=save)

        async def export_course() -> None:
            if require_source() is None:
                return
            required = (course_name.value, teacher.value, school.value, branch.value)
            if not all(str(value or "").strip() for value in required):
                ui.notify("Fülle zuerst die Kursangaben aus.", type="warning")
                return
            export_button.disable()
            try:
                setup, archive = await nicegui_run.io_bound(
                    create_portable_course,
                    source.value,
                    teacher=teacher.value,
                    school=school.value,
                    course=course_name.value,
                    repository=repository.value or "",
                    branch=branch.value,
                )
                ui.notify(f"Offline-ZIP erstellt: {archive}", type="positive", timeout=7000)
                refresh_navigation()
            except Exception as error:
                ui.notify(f"Export fehlgeschlagen: {error}", type="negative")
            finally:
                export_button.enable()

        export_button.on("click", export_course)
        source.on_value_change(lambda _: refresh_navigation())
        refresh_navigation()
        show_welcome()


__all__ = ["register_course_studio_page"]
