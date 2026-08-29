"""NiceGUI-Zeitleiste für benannte und automatische Projektstände."""

from datetime import datetime

from .project_history import (
    project_states,
    restore_project_state,
    save_project_state,
)


def render_project_history(
    ui,
    nicegui_run,
    project,
    course,
    save_code,
    save_documentation,
    refresh,
) -> None:
    ui.separator()
    with ui.expansion("Projektstände", icon="history").classes("w-full"):
        ui.label(
            "Speichere einen verständlich benannten Stand oder kehre zu "
            "einer früheren Sicherung zurück. Vor dem Zurückspringen wird "
            "der aktuelle Stand automatisch gesichert. Vor einer Ausführung "
            "merkt sich in:si geänderte Projekte automatisch; die letzten "
            "zehn dieser Stände bleiben erhalten."
        ).classes("text-sm text-grey-7")
        state_list = ui.column().classes("w-full gap-2")
    
        def state_time(value: str) -> str:
            try:
                return datetime.fromisoformat(value).astimezone().strftime(
                    "%d.%m.%Y · %H:%M:%S"
                )
            except ValueError:
                return value
    
        selected_state = {"value": None}
    
        def open_restore_dialog(state) -> None:
            selected_state["value"] = state
            restore_title.set_text(state.title or "Automatische Sicherung")
            restore_detail.set_text(
                f"{state_time(state.created_at)} · {len(state.files)} Dateien"
            )
            restore_dialog.open()
    
        def render_states() -> None:
            state_list.clear()
            states = project_states(project.directory, course)
            with state_list:
                if not states:
                    ui.label("Noch keine Projektstände gespeichert.").classes(
                        "text-grey-7"
                    )
                    return
                for state in states:
                    with ui.card().classes("w-full q-pa-sm"):
                        with ui.row().classes("w-full items-center gap-2"):
                            ui.badge(
                                "Benannt"
                                if state.named
                                else "Automatisch"
                                if state.restorable
                                else "Beschädigt",
                                color=(
                                    "primary"
                                    if state.named
                                    else "secondary"
                                    if state.restorable
                                    else "negative"
                                ),
                            )
                            ui.label(
                                state.title or "Automatische Sicherung"
                            ).classes("font-bold")
                            ui.space()
                            ui.label(state_time(state.created_at)).classes(
                                "text-xs text-grey-7"
                            )
                        if state.comment:
                            ui.label(state.comment).classes("text-sm")
                        if state.error:
                            ui.label(state.error).classes("text-xs text-negative")
                        with ui.row().classes("w-full items-center gap-2"):
                            ui.label(f"{len(state.files)} Dateien").classes(
                                "text-xs text-grey-7"
                            )
                            ui.space()
                            restore_button = ui.button(
                                "Diesen Stand wiederherstellen",
                                on_click=lambda selected=state: open_restore_dialog(
                                    selected
                                ),
                                icon="restore",
                            ).props("flat")
                            if not state.restorable:
                                restore_button.disable()
    
        async def save_named_state() -> None:
            if not save_code(notify=False) or not save_documentation(notify=False):
                return
            save_state_button.disable()
            state_activity.set_visibility(True)
            try:
                state = await nicegui_run.io_bound(
                    save_project_state,
                    project.directory,
                    course,
                    state_title.value or "",
                    state_comment.value or "",
                )
                if state is None:
                    raise RuntimeError("Das Speichern wurde abgebrochen.")
                state_dialog.close()
                state_title.set_value("")
                state_comment.set_value("")
                render_states()
                ui.notify(
                    f"Projektstand „{state.title}“ wurde gespeichert.",
                    type="positive",
                )
            except (OSError, RuntimeError, ValueError) as error:
                ui.notify(str(error), type="negative")
            finally:
                state_activity.set_visibility(False)
                save_state_button.enable()
    
        async def restore_selected_state() -> None:
            state = selected_state["value"]
            if state is None:
                return
            if not save_code(notify=False) or not save_documentation(notify=False):
                return
            restore_state_button.disable()
            restore_activity.set_visibility(True)
            try:
                restored = await nicegui_run.io_bound(
                    restore_project_state,
                    project.directory,
                    course,
                    state.id,
                )
                if restored is None:
                    raise RuntimeError("Die Wiederherstellung wurde abgebrochen.")
            except (OSError, RuntimeError, ValueError) as error:
                ui.notify(str(error), type="negative")
                restore_activity.set_visibility(False)
                restore_state_button.enable()
                return
            restore_activity.set_visibility(False)
            restore_state_button.enable()
            restore_dialog.close()
            ui.notify(
                f"Projektstand „{state.title or 'Automatische Sicherung'}“ "
                "wurde wiederhergestellt.",
                type="positive",
            )
            refresh()
    
        with ui.dialog() as state_dialog, ui.card().classes("w-full max-w-xl"):
            ui.label("Neuen Projektstand speichern").classes("text-xl font-bold")
            state_title = ui.input(
                "Titel", placeholder="z. B. Spielfigur kann sich bewegen"
            ).classes("w-full").mark("project-state-title")
            state_comment = ui.textarea(
                "Was hast du verändert?",
                placeholder="Kurz beschreiben, was funktioniert oder noch offen ist.",
            ).classes("w-full")
            with ui.row().classes("w-full justify-end"):
                ui.button("Abbrechen", on_click=state_dialog.close).props("flat")
                save_state_button = ui.button(
                    "Projektstand speichern",
                    on_click=save_named_state,
                    icon="bookmark_add",
                ).mark("save-project-state")
                state_activity = ui.spinner(size="sm", color="primary")
                state_activity.set_visibility(False)
    
        with ui.dialog() as restore_dialog, ui.card().classes("w-full max-w-lg"):
            ui.label("Projektstand wiederherstellen?").classes(
                "text-xl font-bold"
            )
            restore_title = ui.label().classes("font-bold")
            restore_detail = ui.label().classes("text-sm text-grey-7")
            ui.label(
                "Ungespeicherte Editorinhalte werden zuerst gespeichert. "
                "Danach legt in:si automatisch einen Sicherheitsstand des "
                "aktuellen Projekts an."
            )
            with ui.row().classes("w-full justify-end"):
                ui.button("Abbrechen", on_click=restore_dialog.close).props("flat")
                restore_state_button = ui.button(
                    "Wiederherstellen",
                    on_click=restore_selected_state,
                    icon="restore",
                )
                restore_activity = ui.spinner(size="sm", color="primary")
                restore_activity.set_visibility(False)
    
        ui.button(
            "Neuen Projektstand speichern",
            on_click=state_dialog.open,
            icon="bookmark_add",
        ).props("outline")
        render_states()


__all__ = ["render_project_history"]
