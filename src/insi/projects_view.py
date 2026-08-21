"""NiceGUI-Arbeitsbereich für persönliche Schülerprojekte."""

from .course import get_course_directory
from .markdown_editor import MarkdownEditor
from .projects import (
    create_project,
    launch_project,
    launch_project_editor,
    project_text,
    project_text_hash,
    save_project_text,
    student_projects,
)
from .system import open_in_preferred_ide, open_path
from .sandbox import sandbox_status
from .workspace_files import (
    FileScope,
    MAX_IMPORTED_FILE_BYTES,
    import_workspace_bytes,
    project_files_directory,
)


TEMPLATE_LABELS = {
    "pykim": "PyKIM-Projekt",
    "pyxel": "Pyxel-Spiel mit Ressourcen",
    "empty": "Leeres Python-Projekt",
}


def render_projects_view(ui, preferred_ide_label: str, ide_open_buttons: list):
    ui.label("Meine Projekte").classes("text-2xl font-bold")
    ui.markdown(
        "Wähle links ein Projekt und bearbeite rechts den Code oder seine "
        "Dokumentation. Alle Dateien liegen portabel unter `Projekte/`."
    )
    course = get_course_directory()
    if course is None:
        ui.label("Richte zuerst im Setup einen Kursordner ein.").classes("text-orange")
        return None
    protection = sandbox_status()
    if not protection.available:
        ui.label(
            "Die geschützte Ausführung ist auf diesem System nicht verfügbar. "
            "Projekte können weiterhin in der gewählten IDE gestartet werden."
        ).classes("text-sm text-orange-8")
    elif not protection.gui_available:
        ui.label(
            "Konsolenprojekte können geschützt gestartet werden. PyKIM- und "
            "Pyxel-Fenster benötigen eine Wayland-Sitzung oder die externe IDE."
        ).classes("text-sm text-orange-8")

    workspace = ui.column().classes("w-full")

    def action(callback, success: str) -> None:
        try:
            callback()
            ui.notify(success, type="positive")
        except (OSError, RuntimeError, ValueError) as error:
            ui.notify(str(error), type="negative")

    def render_project(project) -> None:
        graphical = project.kind in {"pykim", "pyxel"}
        with ui.row().classes("w-full items-center gap-2"):
            ui.label(project.name).classes("text-xl font-bold")
            ui.badge(TEMPLATE_LABELS.get(project.kind, project.kind), color="secondary")
            ui.space()
            ui.label(str(project.directory.relative_to(course))).classes(
                "text-xs text-grey-7"
            )

        if project.resources is not None and not project.resources.exists():
            ui.label(
                "Ressourcen noch nicht gespeichert – öffne zuerst den Sprite- und "
                "Musikeditor."
            ).classes("text-sm text-orange")

        with ui.row().classes("items-center gap-2"):
            start_button = ui.button(
                "Starten",
                on_click=lambda selected=project: action(
                    lambda: launch_project(selected, course),
                    "Projekt wurde gestartet.",
                ),
                icon="play_arrow",
            )
            if not protection.available or (graphical and not protection.gui_available):
                start_button.disable()
            ide_button = ui.button(
                f"In {preferred_ide_label} öffnen",
                on_click=lambda selected=project: action(
                    lambda: open_in_preferred_ide(selected.directory),
                    "Projekt wurde in der IDE geöffnet.",
                ),
                icon="open_in_new",
            ).props("outline")
            ide_open_buttons.append(ide_button)
            ui.button(
                "Ordner öffnen",
                on_click=lambda selected=project: action(
                    lambda: open_path(selected.directory),
                    "Projektordner wurde geöffnet.",
                ),
                icon="folder_open",
            ).props("outline")
            if project.resources is not None:
                ui.button(
                    "Sprite- und Musikeditor",
                    on_click=lambda selected=project: action(
                        lambda: launch_project_editor(selected, course),
                        "Pyxel-Ressourceneditor wurde gestartet.",
                    ),
                    icon="palette",
                ).props("outline")

        async def import_project_file(event) -> None:
            try:
                imported = import_workspace_bytes(
                    await event.file.read(),
                    event.file.name,
                    FileScope.PROJECT,
                    course=course,
                    project=project.directory,
                )
                ui.notify(
                    f"{imported.path.name} wurde dem Projekt hinzugefügt.",
                    type="positive",
                )
            except (OSError, RuntimeError, ValueError) as error:
                ui.notify(f"Dateiimport fehlgeschlagen: {error}", type="negative")

        with ui.row().classes("w-full items-center gap-3"):
            ui.upload(
                label="Datei zum Projekt hinzufügen",
                on_upload=import_project_file,
                auto_upload=True,
                max_file_size=MAX_IMPORTED_FILE_BYTES,
            ).props("flat")
            ui.label(
                f"Ablage: {project_files_directory(project.directory).relative_to(course)}"
            ).classes("text-xs text-grey-7")

        with ui.tabs().classes("w-full") as editor_tabs:
            code_tab = ui.tab("Code", icon="code")
            docs_tab = ui.tab("Dokumentation", icon="description")

        with ui.tab_panels(editor_tabs, value=code_tab).classes("w-full"):
            with ui.tab_panel(code_tab):
                code_source = project_text(project, project.entrypoint)
                code_editor = ui.codemirror(
                    value=code_source,
                    language="Python",
                    line_wrapping=False,
                ).classes("w-full").style("height: 34rem")
                code_state = {"hash": project_text_hash(code_source)}
                code_status = ui.label("Gespeichert").classes("text-xs text-grey-7")

                def save_code(notify=True) -> bool:
                    try:
                        save_project_text(
                            project,
                            project.entrypoint,
                            code_editor.value,
                            expected_hash=code_state["hash"],
                        )
                        code_state["hash"] = project_text_hash(code_editor.value)
                        code_status.set_text("Gespeichert")
                        code_status.classes(replace="text-xs text-grey-7")
                        if notify:
                            ui.notify("Projektcode gespeichert.", type="positive")
                        return True
                    except (OSError, RuntimeError, ValueError) as error:
                        code_status.set_text("Speichern nicht möglich")
                        code_status.classes(replace="text-xs text-negative")
                        ui.notify(str(error), type="warning")
                        return False

                def save_and_start() -> None:
                    if save_code(notify=False):
                        action(
                            lambda: launch_project(project, course),
                            "Projekt wurde gespeichert und gestartet.",
                        )

                code_editor.on(
                    "change",
                    lambda _: (
                        code_status.set_text("Ungespeicherte Änderungen"),
                        code_status.classes(replace="text-xs text-orange-8"),
                    ),
                )
                with ui.row().classes("items-center"):
                    ui.button("Speichern", on_click=lambda: save_code(), icon="save")
                    start_saved_button = ui.button(
                        "Speichern und starten", on_click=save_and_start, icon="play_arrow"
                    )
                    if not protection.available or (
                        graphical and not protection.gui_available
                    ):
                        start_saved_button.disable()
                    ui.button(
                        "Kopieren",
                        on_click=lambda: ui.clipboard.write(code_editor.value),
                        icon="content_copy",
                    ).props("outline")

            with ui.tab_panel(docs_tab):
                documentation = project_text(project, project.documentation)
                ui.label(
                    "Die Dokumentation wird als portable Markdown-Datei gespeichert. "
                    "Du kannst jederzeit zwischen visueller und direkter Bearbeitung wechseln."
                ).classes("text-sm text-grey-7 mb-2")
                docs_editor = MarkdownEditor(
                    value=documentation,
                    height="32rem",
                    initial_mode="wysiwyg",
                )
                docs_state = {"hash": project_text_hash(documentation)}
                docs_status = ui.label("Gespeichert").classes("text-xs text-grey-7")

                def update_documentation_preview(_) -> None:
                    docs_status.set_text("Ungespeicherte Änderungen")
                    docs_status.classes(replace="text-xs text-orange-8")

                docs_editor.on_value_change(update_documentation_preview)

                def save_documentation() -> None:
                    try:
                        save_project_text(
                            project,
                            project.documentation,
                            docs_editor.value,
                            expected_hash=docs_state["hash"],
                        )
                        docs_state["hash"] = project_text_hash(docs_editor.value)
                        docs_status.set_text("Gespeichert")
                        docs_status.classes(replace="text-xs text-grey-7")
                        ui.notify("Dokumentation gespeichert.", type="positive")
                    except (OSError, RuntimeError, ValueError) as error:
                        docs_status.set_text("Speichern nicht möglich")
                        docs_status.classes(replace="text-xs text-negative")
                        ui.notify(str(error), type="warning")

                with ui.row().classes("items-center"):
                    ui.button(
                        "Dokumentation speichern",
                        on_click=save_documentation,
                        icon="save",
                    )
                    ui.button(
                        "Markdown kopieren",
                        on_click=lambda: ui.clipboard.write(docs_editor.value),
                        icon="content_copy",
                    ).props("outline")

    def refresh() -> None:
        workspace.clear()
        projects = student_projects(course)
        with workspace:
            if not projects:
                ui.label("Du hast noch kein eigenes Projekt angelegt.").classes(
                    "text-grey-7"
                )
                return
            with ui.splitter(value=20).classes("pykim-project-workspace w-full") as splitter:
                with splitter.before:
                    ui.label("Projekte").classes("font-bold px-3 pt-3")
                    with ui.tabs().props("vertical").classes(
                        "pykim-project-selector w-full"
                    ) as project_tabs:
                        project_tab_pairs = [
                            (project, ui.tab(project.name, icon="folder"))
                            for project in projects
                        ]
                with splitter.after:
                    with ui.tab_panels(
                        project_tabs, value=project_tab_pairs[0][1]
                    ).props("vertical").classes("w-full"):
                        for project, project_tab in project_tab_pairs:
                            with ui.tab_panel(project_tab):
                                render_project(project)

    with ui.dialog() as create_dialog, ui.card().classes("w-full max-w-xl"):
        ui.label("Neues Projekt").classes("text-xl font-bold")
        project_name = ui.input(
            "Projektname", placeholder="z. B. Mein Labyrinth"
        ).classes("w-full")
        project_kind = ui.select(
            TEMPLATE_LABELS, value="pykim", label="Vorlage"
        ).classes("w-full")

        def submit() -> None:
            try:
                project = create_project(
                    course, project_name.value or "", project_kind.value
                )
                create_dialog.close()
                project_name.set_value("")
                refresh()
                ui.notify(f"Projekt „{project.name}“ wurde angelegt.", type="positive")
            except (OSError, ValueError) as error:
                ui.notify(str(error), type="negative")

        with ui.row().classes("w-full justify-end"):
            ui.button("Abbrechen", on_click=create_dialog.close).props("flat")
            ui.button("Projekt anlegen", on_click=submit, icon="create_new_folder")

    ui.button("Neues Projekt", on_click=create_dialog.open, icon="add")
    refresh()
    return refresh


__all__ = ["render_projects_view"]
