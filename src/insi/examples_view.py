"""Beispielgalerie mit Starten, Kopieren und persönlichen Projektkopien."""

from .course import get_course_directory
from .examples import copy_example_to_course, example_programs, start_example
from .execution import script_example_manager
from .system import open_in_preferred_ide


def render_examples_view(ui, preferred_ide_label: str, ide_open_buttons: list) -> None:
    ui.label("PyKIM-Beispiele").classes("text-2xl font-bold")
    ui.markdown(
        "Die Originale gehören zum Paket und bleiben unverändert. Zum Bearbeiten "
        "wird automatisch ein persönliches Projekt unter "
        "`Projekte/beispiele` angelegt."
    )
    for example in example_programs():
        with ui.expansion(example.title, icon="code").classes("w-full"):
            with ui.row().classes("w-full items-center"):
                ui.label(example.description).classes("text-base")
                ui.space()
                ui.badge(example.category, color="secondary")
            editor = ui.codemirror(
                value=example.source, language="Python", line_wrapping=False,
            ).classes("w-full").style("height: 24rem")
            editor.disable()

            with ui.expansion("Programmausgabe", icon="terminal").classes(
                "w-full border rounded"
            ):
                output = ui.code(
                    "Noch kein Programmlauf in dieser Sitzung.", language="text"
                ).classes("w-full")

            state = {"job_id": None, "run_button": None, "stop_button": None, "timer": None}
            status_badge = ui.badge("BEREIT", color="grey")

            def copy_source(source_editor=editor) -> None:
                ui.clipboard.write(source_editor.value)
                ui.notify("Beispielcode wurde kopiert.", type="positive")

            def poll_run(
                output_view=output,
                state_ref=state,
                badge=status_badge,
            ) -> None:
                job_id = state_ref["job_id"]
                if not isinstance(job_id, str):
                    return
                result = script_example_manager.status(job_id)
                if result is None:
                    output_view.set_content("Der Programmlauf wurde nicht gefunden.")
                    state_ref["job_id"] = None
                    state_ref["timer"].deactivate()
                    state_ref["run_button"].enable()
                    state_ref["stop_button"].disable()
                    badge.set_text("FEHLER")
                    badge.props("color=negative")
                    return
                text = "\n".join(
                    part.rstrip()
                    for part in (str(result["stdout"]), str(result["stderr"]))
                    if part
                ).strip()
                output_view.set_content(
                    text
                    or (
                        "Das Beispiel läuft in einem eigenen Grafikfenster. "
                        "Schließe das Fenster oder klicke auf Stoppen."
                        if result["running"]
                        else "Grafikfenster geschlossen; das Programm wurde ohne "
                        f"Textausgabe beendet (Code {result['returncode']})."
                    )
                )
                if result["running"]:
                    return
                state_ref["job_id"] = None
                state_ref["timer"].deactivate()
                state_ref["run_button"].enable()
                state_ref["stop_button"].disable()
                successful = result["returncode"] == 0
                badge.set_text("BEENDET" if successful else "FEHLER")
                badge.props(f"color={'positive' if successful else 'negative'}")

            def start(
                example_name=example.name,
                output_view=output,
                state_ref=state,
                badge=status_badge,
            ) -> None:
                if state_ref["job_id"] is not None:
                    ui.notify("Dieses Beispiel läuft bereits.", type="warning")
                    return
                try:
                    state_ref["job_id"] = start_example(example_name)
                    output_view.set_content(
                        "Das Beispiel startet in einem eigenen Grafikfenster …"
                    )
                    state_ref["run_button"].disable()
                    state_ref["stop_button"].enable()
                    badge.set_text("LÄUFT")
                    badge.props("color=warning")
                    state_ref["timer"].activate()
                except (OSError, RuntimeError, ValueError) as error:
                    ui.notify(f"Start fehlgeschlagen: {error}", type="negative")

            def stop(state_ref=state, output_view=output) -> None:
                job_id = state_ref["job_id"]
                if isinstance(job_id, str) and script_example_manager.stop(job_id):
                    output_view.set_content("Beispiel wird beendet …")
                else:
                    ui.notify("Dieses Beispiel läuft gerade nicht.", type="info")

            def personal_copy(example_name=example.name):
                course = get_course_directory()
                if course is None:
                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                    return None
                try:
                    return course, copy_example_to_course(example_name, course)
                except (OSError, ValueError) as error:
                    ui.notify(str(error), type="negative")
                    return None

            def save(example_name=example.name) -> None:
                result = personal_copy(example_name)
                if result is None:
                    return
                course, (target, created) = result
                ui.notify(
                    f"Kopie angelegt: {target.relative_to(course)}"
                    if created else "Die persönliche Kopie ist bereits vorhanden.",
                    type="positive",
                )

            def open_in_ide(example_name=example.name) -> None:
                result = personal_copy(example_name)
                if result is None:
                    return
                _course, (target, _created) = result
                try:
                    open_in_preferred_ide(target)
                    ui.notify("Beispiel wurde in der IDE geöffnet.", type="positive")
                except (OSError, RuntimeError, ValueError) as error:
                    ui.notify(str(error), type="negative")

            with ui.row().classes("items-center"):
                run_button = ui.button("Ausführen", on_click=start, icon="play_arrow")
                stop_button = ui.button("Stoppen", on_click=stop, icon="stop").props(
                    "outline color=negative"
                )
                stop_button.disable()
                ui.button("Kopieren", on_click=copy_source, icon="content_copy").props(
                    "outline"
                )
                ide_button = ui.button(
                    f"In {preferred_ide_label} öffnen",
                    on_click=open_in_ide,
                    icon="open_in_new",
                ).props("outline")
                ide_open_buttons.append(ide_button)
                ui.button(
                    "Als eigenes Projekt speichern",
                    on_click=save,
                    icon="content_copy",
                ).props("outline")
            state["run_button"] = run_button
            state["stop_button"] = stop_button
            state["timer"] = ui.timer(0.15, poll_run, active=False)


__all__ = ["render_examples_view"]
