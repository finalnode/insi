"""Projektartige Kurswerkstatt mit Inhaltsnavigation und echter Kursvorschau."""

from __future__ import annotations

from pathlib import Path

import yaml

from insi.training.backends import get_authoring_backend

from .author_workspace import (
    AuthorDraft,
    assignment_markdown,
    compose_task_fields,
    split_task_markdown,
    validate_author_draft,
)
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
from .course_runtime import (
    RUNTIME_FILENAME,
    RUNTIME_PYTHON,
    parse_runtime_manifest,
    suggested_runtime_requirements,
)
from .library import (
    render_script_markdown,
    render_task_markdown,
    task_hints,
    task_sources,
    task_tags,
)
from .markedown import validate_markedown
from .markdown_editor import MarkdownEditor
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


def _show_validation(label, issues: tuple[str, ...], success: str) -> None:
    label.set_text(success if not issues else "✗ " + " · ".join(issues))
    label.classes(
        remove="text-grey-7 text-positive text-negative",
        add="text-positive" if not issues else "text-negative",
    )


def register_course_studio_page(ui, nicegui_app, nicegui_run, *, desktop: bool) -> None:
    authoring = get_authoring_backend("pykim")

    @ui.page("/course-builder")
    def course_studio() -> None:
        configure_theme(ui)

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
            ).props("dense").classes("w-full").mark("course-source")

            async def choose_source() -> None:
                if not desktop or nicegui_app.native.main_window is None:
                    return
                import webview

                selected = await nicegui_app.native.main_window.create_file_dialog(
                    dialog_type=webview.FileDialog.FOLDER,
                    directory=str(Path.home()),
                )
                if selected:
                    selected_path = Path(selected[0]).resolve()
                    source.set_value(str(selected_path))
                    ensure_course_source(selected_path)
                    load_runtime_contract(selected_path)
                    refresh_navigation()
                    show_welcome()

            def use_source_path() -> None:
                if not source.value:
                    ui.notify("Gib zuerst einen Kursordner an.", type="warning")
                    return
                try:
                    selected = Path(source.value).expanduser().resolve()
                    ensure_course_source(selected)
                except (OSError, ValueError) as error:
                    ui.notify(f"Kursordner nicht verwendbar: {error}", type="negative")
                    return
                source.set_value(str(selected))
                load_runtime_contract(selected)
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
            else:
                ui.button(
                    "Pfad verwenden", icon="folder_open", on_click=use_source_path
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
                runtime_python = ui.input(
                    "Python-Version des Kurses", value=RUNTIME_PYTHON
                ).props("dense").classes("w-full")
                runtime_requirements = ui.textarea(
                    "Kurspakete mit exakter Version – eines pro Zeile",
                    value="\n".join(suggested_runtime_requirements()),
                ).props("outlined autogrow").classes("w-full")
                ui.label(
                    "Diese Angaben gehören zum Kursvertrag. in:si prüft und "
                    "installiert sie, legt die Versionen aber nicht fest."
                ).classes("text-xs text-grey-7")

            def load_runtime_contract(root: Path) -> None:
                manifest_path = root / RUNTIME_FILENAME
                if not manifest_path.is_file():
                    return
                try:
                    manifest = parse_runtime_manifest(manifest_path)
                except (OSError, ValueError) as error:
                    ui.notify(f"Runtime-Vertrag ungültig: {error}", type="negative")
                    return
                runtime_python.set_value(manifest.python)
                runtime_requirements.set_value("\n".join(manifest.requirements))

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
                with ui.button(icon="add").props("flat round dense").tooltip(
                    "Neue Aufgabe"
                ).mark("new-task-menu"):
                    with ui.menu():
                        ui.menu_item(
                            "Freie Aufgabe mit Hinweisen",
                            on_click=lambda: show_free_task(),
                        ).mark("new-free-task")
                        ui.menu_item(
                            "Geprüfte PyKIM-Aufgabe mit Hinweisen",
                            on_click=lambda: show_task(),
                        ).mark("new-checked-task")
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

        def save_content(operation, success_message) -> None:
            try:
                result = operation()
            except (OSError, ValueError) as error:
                ui.notify(str(error), type="negative")
                return
            refresh_navigation()
            ui.notify(success_message(result), type="positive")

        def task_metadata_fields(parts, *, checked: bool = False):
            with ui.row().classes("w-full gap-3 items-start flex-wrap"):
                difficulty = ui.select(
                    {
                        "einfach": "Einfach",
                        "mittel": "Mittel",
                        "fortgeschritten": "Fortgeschritten",
                    },
                    value=parts.difficulty,
                    label="Schwierigkeit",
                ).classes("w-48")
                tags = ui.input(
                    "Tags (kommagetrennt)", value=", ".join(parts.tags)
                ).classes("grow min-w-64")
            hints = ui.textarea(
                "Gestufte Hinweise (Hints) – einer pro Zeile",
                value="\n".join(parts.hints),
            ).props("outlined autogrow").classes("w-full")
            ui.label(
                "Hinweise werden schrittweise angeboten; regelbezogene Tipps "
                "stehen zusätzlich in der Trainer-YAML."
                if checked else
                "Die Hinweise werden Lernenden schrittweise angeboten."
            ).classes("text-xs text-grey-7")
            sources = ui.textarea(
                "Quellen – eine pro Zeile: Name | URL",
                value="\n".join(parts.sources),
            ).props("outlined autogrow").classes("w-full")
            return difficulty, tags, hints, sources
            with task_navigation:
                trainer_names = set(course_documents(source.value, "trainer"))
                for paradigm in ("imperativ", "oop"):
                    names = course_documents(source.value, "Aufgaben", paradigm=paradigm)
                    if names:
                        ui.label("Imperativ" if paradigm == "imperativ" else "OOP").classes(
                            "text-xs text-grey-6 mt-1 px-2"
                        )
                    for name in names:
                        has_trainer = name in trainer_names
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
                ui.label(
                    "Visuell schreiben oder unten auf Markdown wechseln. "
                    "Kursaktionen werden sicher über das Annotationsmenü eingefügt."
                ).classes("text-sm text-grey-7 mb-2")
                markdown = MarkdownEditor(
                    value=content,
                    height="34rem",
                    initial_mode="markdown",
                    course_kind="script",
                )
                with ui.expansion(
                    "Kursvorschau", icon="visibility", value=False
                ).classes("w-full") as preview_expansion:
                    preview = ui.markdown(render_script_markdown(content)).classes(
                        "pykim-chapter-markdown w-full"
                    )
                validation = ui.label("M@rkdown noch nicht geprüft.").classes(
                    "text-grey-7"
                )

                def validate() -> tuple:
                    issues = validate_markedown(markdown.value or "", kind="script")
                    _show_validation(
                        validation,
                        tuple(f"Zeile {issue.line}: {issue.message}" for issue in issues),
                        "✓ M@rkdown ist gültig.",
                    )
                    return issues

                def update_preview() -> None:
                    validate()
                    preview.set_content(render_script_markdown(markdown.value or ""))

                def save() -> None:
                    if validate():
                        ui.notify("Behebe zuerst die M@rkdown-Fehler.", type="warning")
                        return
                    save_content(
                        lambda: save_course_markdown(
                            source.value,
                            "Skripte",
                            chapter_name.value or "",
                            markdown.value or "",
                            paradigm=chapter_paradigm.value or "imperativ",
                        ),
                        lambda target: f"Gespeichert: {target.name}",
                    )

                preview_expansion.on_value_change(
                    lambda event: update_preview() if event.value else None
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
                    exercise = authoring.parse_source(trainer)
                    ui.label("Automatische Tests").classes("text-lg font-bold mt-4")
                    for index, rule in enumerate(exercise.rules, start=1):
                        with ui.card().classes("w-full shadow-none border"):
                            ui.label(
                                f"Test {index}: {authoring.rule_labels.get(rule.kind, rule.kind)}"
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
            parts = split_task_markdown(content)
            editor.clear()
            with editor:
                with ui.row().classes("w-full items-end gap-3 flex-wrap"):
                    ui.label("Freie Aufgabe").classes("text-xl font-bold")
                    task_name = ui.input(
                        "Dateiname", value=name, placeholder="reflexion-schleifen"
                    ).classes("grow min-w-48")
                    task_title = ui.input("Titel", value=parts.title).classes(
                        "grow min-w-48"
                    )
                    task_paradigm = ui.select(
                        {"imperativ": "Imperativ", "oop": "OOP"},
                        value=paradigm,
                        label="Lernweg",
                    ).classes("w-40")
                ui.label(
                    "Ohne Trainerdatei erhalten Lernende ein freies Antwortfeld. "
                    "Hinweise, Tags und Quellen sind weiterhin möglich."
                ).classes("text-sm text-grey-7")
                with ui.expansion(
                    "Aufgabenangaben und gestufte Hilfen", icon="tune", value=True
                ).classes("w-full"):
                    difficulty, tags, hints, sources = task_metadata_fields(parts)
                markdown = MarkdownEditor(
                    value=parts.body,
                    height="32rem",
                    initial_mode="wysiwyg",
                    course_kind="task-body",
                )
                with ui.expansion(
                    "Aufgabenvorschau", icon="visibility", value=False
                ).classes("w-full") as preview_expansion:
                    preview = ui.column().classes("w-full gap-2")
                validation = ui.label("M@rkdown noch nicht geprüft.").classes("text-grey-7")

                def current_markdown() -> str:
                    return compose_task_fields(
                        task_title.value or "Aufgabe",
                        markdown.value or "",
                        difficulty.value or "mittel",
                        hints=hints.value or "",
                        tags=tags.value or "",
                        sources=sources.value or "",
                    )

                def validate() -> tuple:
                    issues = validate_markedown(current_markdown(), kind="task")
                    _show_validation(
                        validation,
                        tuple(f"Zeile {issue.line}: {issue.message}" for issue in issues),
                        "✓ M@rkdown ist gültig.",
                    )
                    return issues

                def save() -> None:
                    if validate():
                        return
                    save_content(
                        lambda: save_course_markdown(
                            source.value,
                            "Aufgaben",
                            task_name.value or "",
                            current_markdown(),
                            paradigm=task_paradigm.value or "imperativ",
                        ),
                        lambda target: f"Freie Aufgabe gespeichert: {target.name}",
                    )

                preview_expansion.on_value_change(
                    lambda event: render_task_preview(
                        preview, current_markdown(), ""
                    )
                    if event.value
                    else None
                )
                with ui.row().classes("w-full justify-end"):
                    ui.button("Speichern", icon="save", on_click=save)

        def show_task(paradigm: str = "imperativ", name: str = "") -> None:
            if require_source() is None:
                return
            markdown_content = (
                load_course_document(source.value, "Aufgaben", name, paradigm=paradigm)
                if name
                else assignment_markdown(
                    "Neue Aufgabe",
                    "Beschreibe hier die Aufgabe.",
                    "Formuliere mindestens eine Anforderung.",
                    "mittel",
                )
            )
            parts = split_task_markdown(markdown_content)
            body_lines = parts.body.splitlines()
            initial_summary = next(
                (
                    line.strip() for line in body_lines
                    if line.strip() and not line.startswith(("#", "- ", "@"))
                ),
                "",
            )
            initial_requirements = "\n".join(
                line.removeprefix("- ").strip()
                for line in body_lines if line.startswith("- ")
            )
            trainer_content = (
                load_course_document(source.value, "trainer", name) if name else ""
            )
            initial_rules: list[str] = []
            initial_optimal = None
            if trainer_content.strip():
                try:
                    existing_exercise = authoring.parse_source(trainer_content)
                    initial_rules = [
                        rule.kind for rule in existing_exercise.rules
                        if rule.kind in authoring.rule_kinds
                    ]
                    payload = yaml.safe_load(trainer_content)
                    optimization = payload["exercises"][0].get("optimization", {})
                    initial_optimal = optimization.get("optimal_lines")
                except (AttributeError, KeyError, TypeError, ValueError, yaml.YAMLError):
                    pass
            editor.clear()
            with editor:
                ui.label("PyKIM-Aufgabe").classes("text-xl font-bold")
                with ui.row().classes("w-full gap-3 items-start flex-wrap"):
                    task_name = ui.input(
                        "Kennung", value=name, placeholder="meine-aufgabe"
                    ).classes("grow min-w-44")
                    task_title = ui.input(
                        "Titel", value=parts.title
                    ).classes("grow min-w-52")
                    task_paradigm = ui.select(
                        {"imperativ": "Imperativ", "oop": "OOP"},
                        value=paradigm,
                        label="Lernweg",
                    ).classes("w-40")
                with ui.expansion("Aufgabenangaben und Prüfbausteine", icon="auto_fix_high", value=True).classes("w-full"):
                    summary = ui.input(
                        "Kurze Aufgabenstellung", value=initial_summary
                    ).classes("w-full")
                    requirements = ui.textarea(
                        "Anforderungen – eine pro Zeile", value=initial_requirements
                    ).props(
                        "outlined autogrow"
                    ).classes("w-full")
                    difficulty, tags, hints, sources = task_metadata_fields(
                        parts, checked=True
                    )
                    with ui.row().classes("w-full gap-3 items-start flex-wrap"):
                        rules = ui.select(
                            {
                                key: authoring.rule_labels[key]
                                for key in authoring.rule_kinds
                            },
                            value=initial_rules,
                            multiple=True,
                            label="Prüfbausteine",
                        ).classes("grow min-w-64")
                        optimal = ui.number(
                            "Optimale Codezeilen", min=1, value=initial_optimal
                        ).props(
                            "hint='optional' persistent-hint"
                        ).classes("w-full sm:w-52")

                    def generate() -> None:
                        try:
                            trainer_editor.set_value(
                                authoring.generate_source(
                                    task_name.value or "",
                                    task_title.value or "",
                                    tuple(rules.value or ()),
                                    optimal_lines=int(optimal.value) if optimal.value else None,
                                )
                            )
                            generated = split_task_markdown(assignment_markdown(
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
                                ))
                            markdown_editor.set_value(generated.body)
                            validate()
                        except ValueError as error:
                            ui.notify(str(error), type="warning")

                    ui.button("Entwurf erzeugen", icon="auto_fix_high", on_click=generate)

                ui.label(
                    "Aufgabentext visuell bearbeiten; Metadaten und Hinweise "
                    "werden aus den Formularfeldern als Annotationen erzeugt."
                ).classes("text-sm text-grey-7 mb-2")
                markdown_editor = MarkdownEditor(
                    value=parts.body,
                    height="32rem",
                    initial_mode=(
                        "markdown" if "@block:" in parts.body else "wysiwyg"
                    ),
                    course_kind="task-body",
                )
                with ui.expansion(
                    "Trainer.yml – Expertenansicht", icon="rule", value=False
                ).classes("w-full"):
                    trainer_editor = ui.codemirror(
                        value=trainer_content, language="YAML", line_wrapping=False
                    ).classes("w-full").style("height: 32rem")
                with ui.expansion(
                    "Aufgabenvorschau", icon="visibility", value=False
                ).classes("w-full") as preview_expansion:
                    preview = ui.column().classes("w-full gap-2")
                validation = ui.label("Noch nicht geprüft.").classes("text-grey-7")

                def current_markdown() -> str:
                    return compose_task_fields(
                        task_title.value or "Aufgabe",
                        markdown_editor.value or "",
                        difficulty.value or "mittel",
                        hints=hints.value or "",
                        tags=tags.value or "",
                        sources=sources.value or "",
                    )

                def draft() -> AuthorDraft:
                    return AuthorDraft(
                        task_name.value or "",
                        trainer_editor.value or "",
                        current_markdown(),
                    )

                def validate() -> tuple[str, ...]:
                    issues = validate_author_draft(draft())
                    _show_validation(
                        validation,
                        issues,
                        "✓ Aufgabe und Trainer sind vollständig.",
                    )
                    return issues

                def save() -> None:
                    if validate():
                        return
                    save_content(
                        lambda: save_course_assignment(
                            source.value,
                            draft(),
                            paradigm=task_paradigm.value or "imperativ",
                        ),
                        lambda saved: (
                            f"{saved[0].name} und {saved[1].name} gespeichert."
                        ),
                    )

                preview_expansion.on_value_change(
                    lambda event: render_task_preview(
                        preview, current_markdown(), trainer_editor.value or ""
                    )
                    if event.value
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
                    runtime_python=runtime_python.value,
                    runtime_requirements=runtime_requirements.value or "",
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
