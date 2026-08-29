"""Lokale Werkzeuge, Kursabgleich und Updateverwaltung."""

from insi.author_view import render_authoring_view
from .branding import APP_DISPLAY_NAME
from insi.course import get_course_directory, set_runtime_preference
from insi.course_setup import course_setup_info, sync_installed_course_content
from insi.library import PACKAGED_CONTENT_ROOT
from insi.local_data_view import render_local_data_management
from insi.system import open_in_preferred_ide, open_path, system_status
from insi.runtime import course_runtime_preflight
from insi.updates import check_updates, format_content_version, install_content_update
from insi.workspace_files import (
    FileScope,
    MAX_IMPORTED_FILE_BYTES,
    course_files_directory,
    global_files_directory,
    import_workspace_bytes,
)


def render_tools_panel(
    context,
    update_badge,
    header_setup,
    tabs,
    projects_tab,
) -> None:
    """Rendere lokale Werkzeuge und alle Updateaktionen."""
    ui = context.ui
    nicegui_run = context.run
    course_sync_state = context.course_sync
    course_selection_state = context.course_selection
    ui.label("IDE, Dateien und Updates").classes("text-2xl font-bold")
    ui.markdown(
        "Diese Werkzeuge werden lokal gestartet und öffnen sich in einem "
        f"**eigenen Fenster** neben {APP_DISPLAY_NAME}."
    )
    course = get_course_directory()
    if course is None:
        ui.label("Richte zuerst im Setup einen Kursordner ein.").classes("text-orange")
    else:
        tool_status = system_status()

        def start_local(action, success: str) -> None:
            try:
                action()
                ui.notify(success, type="positive")
            except (OSError, RuntimeError, ValueError) as error:
                ui.notify(f"Start fehlgeschlagen: {error}", type="negative")

        with ui.row():
            ui.button(
                "Kursordner öffnen",
                on_click=lambda: start_local(
                    lambda: open_path(course), "Kursordner wurde geöffnet."
                ),
                icon="folder_open",
            )
            ui.button(
                "In bevorzugter IDE öffnen",
                on_click=lambda: start_local(
                    lambda: open_in_preferred_ide(course),
                    "Bevorzugte IDE wurde gestartet.",
                ),
                icon="terminal",
            )
            if tool_status.thonny:
                ui.button(
                    "In Thonny öffnen",
                    on_click=lambda: start_local(
                        lambda: open_path(course, "thonny"), "Thonny wurde gestartet."
                    ),
                    icon="school",
                )
            if tool_status.vscode:
                ui.button(
                    "In VS Code öffnen",
                    on_click=lambda: start_local(
                        lambda: open_path(course, "vscode"), "VS Code wurde gestartet."
                    ),
                    icon="code",
                )

        ui.separator()
        ui.label("Dateien im in:si-Workspace").classes("text-xl font-bold")
        ui.label(
            "Importierte Dateien werden in den Workspace kopiert. Lerncode kann "
            "globale und kursweite Dateien lesen, aber nicht verändern."
        ).classes("text-sm text-grey-7")

        async def import_file(event, scope: FileScope) -> None:
            try:
                imported = import_workspace_bytes(
                    await event.file.read(),
                    event.file.name,
                    scope,
                    course=course,
                )
                ui.notify(
                    f"{imported.path.name} wurde in {imported.path.parent} abgelegt.",
                    type="positive",
                )
            except (OSError, RuntimeError, ValueError) as error:
                ui.notify(f"Dateiimport fehlgeschlagen: {error}", type="negative")

        with ui.row().classes("items-start gap-4"):
            with ui.card().classes("shadow-none border"):
                ui.label("Für alle Kurse").classes("font-bold")
                ui.label(str(global_files_directory())).classes("text-xs text-grey-7")
                ui.upload(
                    label="Globale Datei hinzufügen",
                    on_upload=lambda event: import_file(event, FileScope.GLOBAL),
                    auto_upload=True,
                    max_file_size=MAX_IMPORTED_FILE_BYTES,
                ).props("flat")
            with ui.card().classes("shadow-none border"):
                ui.label("Für diesen Kurs").classes("font-bold")
                ui.label(str(course_files_directory(course))).classes("text-xs text-grey-7")
                ui.upload(
                    label="Kursdatei hinzufügen",
                    on_upload=lambda event: import_file(event, FileScope.COURSE),
                    auto_upload=True,
                    max_file_size=MAX_IMPORTED_FILE_BYTES,
                ).props("flat")

        ui.separator()
        ui.label("Pyxel-Ressourceneditor").classes("text-xl font-bold")
        ui.markdown(
            "Ressourcendateien gehören immer zu einem Projekt. Lege unter "
            "**Meine Projekte** ein Pyxel-Spiel an und öffne dort den "
            "Spriteeditor oder Musikeditor."
        )
        ui.button(
            "Zu meinen Projekten",
            on_click=lambda: tabs.set_value(projects_tab),
            icon="folder_special",
        )

    render_local_data_management(context)

    ui.separator()
    ui.label("Updates").classes("text-xl font-bold").props("id=pykim-updates")
    ui.label(
        "App und Lerninhalte werden nur nach einem Klick auf „Jetzt prüfen“ "
        "über GitHub abgefragt. Schülerlösungen und Lernstand werden dabei "
        "niemals verändert."
    ).classes("text-grey-7")
    startup_sync = course_sync_state["result"]
    startup_sync_error = str(course_sync_state["error"])
    if startup_sync_error:
        course_sync_text = (
            "Kursrepository beim Start nicht erreichbar: "
            f"{startup_sync_error}"
        )
        course_sync_class = "text-warning"
    elif startup_sync is not None and startup_sync.checked_online:
        course_sync_text = (
            "Kursrepository zuletzt manuell abgeglichen: "
            + startup_sync.message
        )
        course_sync_class = "text-positive"
    else:
        course_sync_text = (
            startup_sync.message
            if startup_sync is not None
            else (
                "Kursrepository wurde noch nicht abgeglichen. Der Abgleich "
                "startet nur über den Button."
            )
        )
        course_sync_class = "text-grey-7"
    course_sync_label = ui.label(course_sync_text).classes(course_sync_class)
    app_update_label = ui.label("App-Version wurde noch nicht geprüft.")
    content_update_label = ui.label("Inhaltsversion wurde noch nicht geprüft.")
    update_state: dict[str, object] = {"status": None}

    async def refresh_course_content() -> None:
        course_sync_button.disable()
        course_sync_label.text = "Kursrepository wird abgeglichen …"
        update_badge.text = "Kursabgleich läuft …"
        update_badge.props("color=positive")
        try:
            result = await nicegui_run.io_bound(
                sync_installed_course_content
            )
            course_sync_state["result"] = result
            course_sync_state["error"] = ""
            course_sync_label.text = result.message
            if course is not None:
                preflight = await nicegui_run.io_bound(
                    course_runtime_preflight, course
                )
                if not preflight.ready:
                    course_selection_state["confirmed"] = False
                    ui.notify(
                        "Die aktualisierten Kursinhalte benötigen eine andere "
                        "Laufzeit. Der Kursstart wird erneut geprüft.",
                        type="warning",
                        timeout=7000,
                    )
                    ui.navigate.reload()
                    return
                if preflight.candidate is not None:
                    set_runtime_preference(preflight.candidate.executable)
            if not result.checked_online:
                ui.notify(result.message, type="warning")
            elif result.updated:
                ui.notify(
                    "Neue Kursinhalte wurden aktiviert.",
                    type="positive",
                )
                ui.navigate.reload()
            else:
                ui.notify("Die Kursinhalte sind aktuell.", type="positive")
        except Exception as error:
            course_sync_state["error"] = str(error)
            course_sync_label.text = f"Kursabgleich fehlgeschlagen: {error}"
            ui.notify(
                f"Kursabgleich fehlgeschlagen: {error}",
                type="negative",
            )
        finally:
            course_sync_state["pending"] = False
            status = update_state["status"]
            if course_sync_state["error"]:
                update_badge.text = "Kursabgleich offline"
                update_badge.props("color=warning")
            elif (
                status is not None
                and status.app is not None
                and status.app.newer
            ):
                update_badge.text = "Update verfügbar"
                update_badge.props("color=orange")
            else:
                update_badge.text = "Aktuell"
                update_badge.props("color=positive")
            course_sync_button.enable()

    def open_app_download() -> None:
        status = update_state["status"]
        if status is None or status.app is None:
            return
        target = status.app.download_url or status.app.release_url
        if target:
            ui.navigate.to(target, new_tab=True)

    async def activate_content_update() -> None:
        status = update_state["status"]
        if status is None or status.content is None:
            return
        try:
            await nicegui_run.io_bound(
                install_content_update, status.content.manifest
            )
            content_update_label.text = (
                f"Inhalte {status.content.available} wurden aktiviert."
            )
            content_button.disable()
            ui.notify(
                f"Neue Lerninhalte aktiviert. Bitte {APP_DISPLAY_NAME} neu starten.",
                type="positive",
            )
        except Exception as error:
            ui.notify(f"Inhaltsupdate fehlgeschlagen: {error}", type="negative")

    with ui.row().classes("items-center"):
        course_sync_button = ui.button(
            "Kursinhalte abgleichen",
            on_click=refresh_course_content,
            icon="sync",
        ).props("outline")
        app_button = ui.button(
            "App-Update öffnen", on_click=open_app_download, icon="download"
        )
        content_button = ui.button(
            "Lerninhalte aktualisieren",
            on_click=activate_content_update,
            icon="library_books",
        )
        refresh_button = ui.button(
            "Jetzt prüfen", icon="refresh"
        ).props("outline")
    app_button.disable()
    content_button.disable()

    async def refresh_updates() -> None:
        refresh_button.disable()
        update_badge.text = "Updates werden geprüft …"
        try:
            status = await nicegui_run.io_bound(
                check_updates, PACKAGED_CONTENT_ROOT, include_content=header_setup is None
            )
            update_state["status"] = status
            if status.app is None:
                app_update_label.text = "App-Prüfung nicht verfügbar."
                app_button.disable()
            elif status.app.newer:
                app_update_label.text = (
                    f"Neue App: {status.app.available} · installiert: "
                    f"{status.app.installed}"
                )
                app_button.enable()
            else:
                app_update_label.text = (
                    f"App {status.app.installed} ist aktuell."
                )
                app_button.disable()
            if header_setup is not None:
                content_update_label.text = (
                    "Kursinhalte werden über das Repository des ausgewählten "
                    "Kurses aktualisiert."
                )
                content_button.disable()
            elif status.content is None:
                content_update_label.text = "Inhaltsprüfung nicht verfügbar."
                content_button.disable()
            elif status.content.newer and status.content.compatible:
                content_update_label.text = (
                    "Neue Lerninhalte: "
                    f"{format_content_version(status.content.available)} · aktiv: "
                    f"{format_content_version(status.content.installed)}"
                )
                content_button.enable()
            elif not status.content.compatible:
                content_update_label.text = (
                    "Die neuen Inhalte benötigen zuerst ein App-Update."
                )
                content_button.disable()
            else:
                content_update_label.text = (
                    "Lerninhalte "
                    f"{format_content_version(status.content.installed)} sind aktuell."
                )
                content_button.disable()
            if status.error:
                update_badge.text = "Updateprüfung teilweise offline"
                update_badge.props("color=warning")
            elif (
                (status.app is not None and status.app.newer)
                or (
                    header_setup is None
                    and status.content is not None
                    and status.content.newer
                )
            ):
                update_badge.text = "Update verfügbar"
                update_badge.props("color=orange")
            else:
                update_badge.text = "Aktuell"
                update_badge.props("color=positive")
        finally:
            refresh_button.enable()

    refresh_button.on("click", refresh_updates)

    author_course = get_course_directory()
    if author_course is not None and course_setup_info(author_course) is not None:
        render_authoring_view(ui)



__all__ = ["render_tools_panel"]
