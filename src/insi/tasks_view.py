"""Aufgabenansicht mit Editor, Aktivitäten, Tests und Dokubuch."""

from __future__ import annotations

import json

from pykim.trainer.activities import get_activity
from insi.assignments import get_assignment
from pykim.trainer.exercises import exercise_names, get_exercise

from insi.activity_view import (
    current_parsons_order,
    parsons_html,
    render_matching_activity,
    saved_activity_value,
)
from insi.course import (
    exercise_file,
    get_course_directory,
    reset_exercise_file,
)
from insi.course_setup import course_setup_info
from insi.execution import execution_manager
from insi.library import (
    PARADIGMS,
    render_task_markdown,
    task_documents,
    task_hints,
    task_sources,
)
from insi.learning_view import (
    friendly_python_error,
    render_task_hints,
    render_task_sources,
    render_test_results as render_exercise_test_results,
)
from insi.progress import (
    clear_exercise_progress,
    load_progress,
    save_journal_entry,
    save_task_answer,
)
from insi.system import (
    SourceConflictError,
    open_in_preferred_ide,
    read_student_source,
    save_student_source,
    source_hash,
)


def render_tasks_panel(
    ui,
    nicegui_run,
    ide_open_buttons: list,
    refresh_overview,
    preferred_ide_label,
) -> None:
    """Rendere Aufgaben und binde ihre lokalen Aktionen."""
    dirty_exercises: set[str] = set()
    progress = load_progress()
    journal = progress.get("journal", {})
    answers = progress.get("answers", {})
    ui.label("Aufgaben und Testfälle").classes("text-2xl font-bold")
    current_paradigm = None
    tasks_course = get_course_directory()
    has_course_setup = (
        tasks_course is not None
        and course_setup_info(tasks_course) is not None
    )
    visible_tasks = tuple(
        document
        for paradigm in PARADIGMS
        for document in task_documents(paradigm)
    ) if has_course_setup else ()
    if not visible_tasks:
        ui.label(
            "Noch kein Kurs eingerichtet. Importiere im Setup die "
            ".pykim-setup-Datei deiner Lehrkraft."
        ).classes("text-grey-7")
    trainable_names = set(exercise_names())
    material_tasks = tuple(
        document for document in visible_tasks
        if document.name not in trainable_names
    )
    if material_tasks:
        ui.separator()
        ui.label("Weitere Aufgaben").classes(
            "text-xl font-bold text-primary"
        )
        ui.label(
            "Freie Antworten und interaktive Zuordnungsaufgaben."
        ).classes("text-grey-7")
        for material in material_tasks:
            with ui.expansion(material.title, icon="description").classes(
                "w-full"
            ):
                hint_key = f"{material.paradigm}/{material.name}"
                ui.markdown(
                    render_task_markdown(material.content)
                ).classes("prose max-w-none")
                render_task_sources(ui, task_sources(material.content))
                render_task_hints(
                    ui, hint_key, task_hints(material.content)
                )
                activity = get_activity(material.name)
                if activity is not None and activity.mode == "matching":
                    render_matching_activity(
                        ui, activity, paradigm=material.paradigm
                    )
                    continue
                answer_key = hint_key
                old_answer = (
                    answers.get(answer_key, {})
                    if isinstance(answers, dict)
                    else {}
                )
                answer = ui.textarea(
                    "Meine Antwort",
                    value=(
                        old_answer.get("text", "")
                        if isinstance(old_answer, dict)
                        else ""
                    ),
                ).props("outlined autogrow").classes("w-full")
                ui.button(
                    "Antwort speichern",
                    on_click=lambda key=answer_key, field=answer: (
                        save_task_answer(key, field.value),
                        ui.notify(
                            "Antwort wurde gespeichert.",
                            type="positive",
                        ),
                    ),
                    icon="save",
                )
    for task_document in (
        document for document in visible_tasks
        if document.name in trainable_names
    ):
        name = task_document.name
        if task_document.paradigm != current_paradigm:
            current_paradigm = task_document.paradigm
            ui.separator()
            ui.label(
                "Imperative Aufgaben"
                if current_paradigm == "imperativ"
                else "Objektorientierte Aufgaben"
            ).classes("text-xl font-bold text-primary")
        exercise = get_exercise(name)
        with ui.expansion(exercise.title, icon="task_alt").classes("w-full"):
            assignment = get_assignment(name)
            with ui.card().classes("w-full bg-orange-1 shadow-none"):
                with ui.row().classes("w-full items-center"):
                    ui.label("Aufgabenstellung").classes("text-lg font-bold")
                    ui.space()
                    ui.badge(assignment.difficulty.upper(), color="primary")
                ui.markdown(render_task_markdown(task_document.content)).classes(
                    "prose max-w-none"
                )
                render_task_sources(
                    ui, task_sources(task_document.content)
                )
            render_task_hints(
                ui,
                f"{task_document.paradigm}/{name}",
                task_hints(task_document.content),
            )
            target = exercise_file(name)
            activity = get_activity(name)
            if (
                activity is not None
                and activity.mode == "parsons"
                and target is not None
            ):
                answer_key = f"{task_document.paradigm}/{name}"
                saved_order = saved_activity_value(answer_key)
                order = (
                    saved_order
                    if isinstance(saved_order, list)
                    and set(saved_order) == {block.id for block in activity.blocks}
                    else [block.id for block in reversed(activity.blocks)]
                )
                ui.label(
                    "Ziehe die Blöcke in die richtige Reihenfolge. Mit den "
                    "Pfeiltasten an jedem Block geht es auch ohne Drag-and-drop."
                ).classes("text-grey-7")
                ui.html(parsons_html(activity, order), sanitize=False).classes("w-full")
                parsons_order_status = ui.label(
                    "Ordne zuerst alle Blöcke und prüfe dann den Code."
                ).classes("text-grey-7")
                parsons_output = ui.code(
                    "Noch nicht ausgeführt.", language="text"
                ).classes("w-full pykim-no-code-actions")
                parsons_output.set_visibility(False)
                parsons_tests = ui.column().classes("w-full gap-2")
                with parsons_tests:
                    ui.label(
                        "Die automatischen Tests starten erst, wenn die "
                        "Blockreihenfolge stimmt."
                    ).classes("text-grey-7")

                def refresh_parsons_tests(
                    exercise_name=name, container=parsons_tests,
                ) -> None:
                    container.clear()
                    with container:
                        render_exercise_test_results(ui, exercise_name)

                parsons_run_state = {"running": False}

                async def execute_parsons(
                    path=target,
                    output=parsons_output,
                    refresh=refresh_parsons_tests,
                ) -> None:
                    """Führe das Puzzle nach Abschluss des Browser-Events aus."""
                    selected_course = get_course_directory()
                    if selected_course is None:
                        ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                        parsons_run_state["running"] = False
                        parsons_run_button.enable()
                        return
                    try:
                        result = await nicegui_run.io_bound(
                            execution_manager.execute,
                            path,
                            selected_course,
                            headless=True,
                        )
                        rendered = result.stdout
                        if result.stderr:
                            rendered += ("\n" if rendered else "") + result.stderr
                        output.set_content(
                            rendered.strip()
                            or f"Programm beendet (Code {result.returncode}), ohne Ausgabe."
                        )
                        refresh()
                        refresh_overview()
                        parsons_preview_button.set_visibility(
                            result.returncode == 0
                        )
                        if result.returncode == 0:
                            ui.notify(
                                "Reihenfolge und Tests wurden geprüft. Du kannst "
                                "die Animation jetzt separat öffnen.",
                                type="positive",
                            )
                    except (OSError, ValueError, RuntimeError) as error:
                        output.set_content(f"Ausführung fehlgeschlagen: {error}")
                        ui.notify(str(error), type="negative")
                    finally:
                        parsons_run_state["running"] = False
                        parsons_run_button.enable()

                async def run_parsons(
                    puzzle=activity,
                    path=target,
                    output=parsons_output,
                    order_status=parsons_order_status,
                    key=answer_key,
                    refresh=refresh_parsons_tests,
                ) -> None:
                    if parsons_run_state["running"]:
                        ui.notify("Diese Aufgabe läuft bereits.", type="warning")
                        return
                    selected_course = get_course_directory()
                    if selected_course is None:
                        ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                        return
                    parsons_run_button.disable()
                    try:
                        current_order = await current_parsons_order(ui, puzzle)
                    except (TimeoutError, RuntimeError):
                        parsons_run_button.enable()
                        ui.notify(
                            "Die Blockreihenfolge konnte nicht gelesen werden. "
                            "Die Verbindung zur Oberfläche wird neu aufgebaut; "
                            "versuche es gleich noch einmal.",
                            type="warning",
                        )
                        return
                    try:
                        source = puzzle.assemble(current_order)
                        save_task_answer(
                            key, json.dumps(current_order, ensure_ascii=False)
                        )
                    except (OSError, ValueError, SourceConflictError) as error:
                        parsons_run_button.enable()
                        ui.notify(f"Puzzle konnte nicht gespeichert werden: {error}", type="negative")
                        return
                    if not puzzle.order_is_correct(current_order):
                        parsons_run_button.enable()
                        order_status.text = (
                            "Die Reihenfolge stimmt noch nicht. Verschiebe mindestens "
                            "einen Block und prüfe erneut."
                        )
                        order_status.classes(
                            add="text-negative", remove="text-grey-7 text-positive"
                        )
                        ui.notify(
                            "Blockreihenfolge noch nicht korrekt – das Programm wurde "
                            "noch nicht ausgeführt.",
                            type="warning",
                        )
                        return
                    order_status.text = (
                        "Reihenfolge korrekt. Programm und Tests werden ausgeführt …"
                    )
                    order_status.classes(
                        add="text-positive", remove="text-grey-7 text-negative"
                    )
                    try:
                        old_source = read_student_source(path, selected_course)
                        save_student_source(
                            path,
                            source,
                            selected_course,
                            expected_hash=source_hash(old_source),
                        )
                    except (OSError, ValueError, SourceConflictError) as error:
                        parsons_run_button.enable()
                        ui.notify(f"Puzzle konnte nicht gespeichert werden: {error}", type="negative")
                        return
                    output.set_visibility(True)
                    output.set_content(
                        "Reihenfolge wird geprüft und die Tests werden ausgeführt …"
                    )
                    parsons_run_state["running"] = True
                    # Das native Pyxel-Fenster darf erst starten, nachdem NiceGUI
                    # das Klick-Ereignis beantwortet und den Laufzustand an den
                    # Browser übertragen hat. Sonst wirkt das Webview kurz wie
                    # eingefroren oder getrennt.
                    ui.timer(0.1, execute_parsons, once=True)

                async def launch_parsons_preview(path=target) -> None:
                    selected_course = get_course_directory()
                    if selected_course is None:
                        ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                        return
                    try:
                        await nicegui_run.io_bound(
                            execution_manager.launch_preview,
                            path,
                            selected_course,
                        )
                        ui.notify(
                            "Animation wurde im Pyxel-Fenster geöffnet.",
                            type="positive",
                        )
                    except (OSError, ValueError, RuntimeError) as error:
                        ui.notify(str(error), type="negative")

                with ui.row().classes("items-center gap-2"):
                    parsons_run_button = ui.button(
                        "Reihenfolge und Tests prüfen",
                        on_click=run_parsons,
                        icon="rule",
                    ).props("color=primary")
                    parsons_preview_button = ui.button(
                        "Animation öffnen",
                        on_click=launch_parsons_preview,
                        icon="open_in_new",
                    ).props("outline color=primary")
                    parsons_preview_button.set_visibility(False)
                continue
            if target is not None:
                course = get_course_directory()
                try:
                    source = (
                        read_student_source(target, course)
                        if course is not None
                        else ""
                    )
                except (OSError, ValueError) as error:
                    source = ""
                    ui.label(f"Quellcode konnte nicht geladen werden: {error}").classes(
                        "text-negative"
                    )

                ui.label("Dein vollständiger Quellcode").classes("font-bold mt-2")
                source_editor = ui.codemirror(
                    value=source,
                    language="Python",
                    line_wrapping=False,
                ).classes("w-full").style("height: 24rem")

                editor_state = {
                    "disk_hash": source_hash(source),
                    "dirty": False,
                }
                save_state = ui.label("Gespeichert").classes("text-grey-7 text-sm")

                def mark_dirty(
                    _, exercise_name=name, state=editor_state,
                    label=save_state,
                ) -> None:
                    state["dirty"] = True
                    dirty_exercises.add(exercise_name)
                    label.set_text("Ungespeicherte Änderungen")
                    label.classes(replace="text-orange-8 text-sm")
                    ui.run_javascript("window.pykimHasUnsavedChanges = true")

                source_editor.on("change", mark_dirty)

                action_row = ui.row()
                with ui.expansion(
                    "Programmausgabe",
                    icon="terminal",
                ).classes("w-full border rounded"):
                    execution_output = ui.code(
                        "Noch keine Ausgabe in dieser Sitzung.",
                        language="text",
                    ).classes("w-full")

                test_results_container = ui.column().classes("w-full gap-2")

                def render_test_results(
                    exercise_name=name,
                    container=test_results_container,
                ) -> None:
                    container.clear()
                    with container:
                        render_exercise_test_results(ui, exercise_name)

                render_test_results()

                def save_task(
                    path=target, editor=source_editor, state=editor_state,
                    label=save_state, exercise_name=name, notify=True,
                ) -> bool:
                    selected_course = get_course_directory()
                    if selected_course is None:
                        ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                        return False
                    try:
                        save_student_source(
                            path, editor.value, selected_course,
                            expected_hash=state["disk_hash"],
                        )
                        state["disk_hash"] = source_hash(editor.value)
                        state["dirty"] = False
                        dirty_exercises.discard(exercise_name)
                        label.set_text("Gespeichert")
                        label.classes(replace="text-grey-7 text-sm")
                        ui.run_javascript(
                            "window.pykimHasUnsavedChanges = "
                            + str(bool(dirty_exercises)).lower()
                        )
                        if notify:
                            ui.notify("Quellcode wurde gespeichert.", type="positive")
                        return True
                    except SourceConflictError:
                        label.set_text("Datei wurde außerhalb der Suite geändert")
                        label.classes(replace="text-negative text-sm")
                        ui.notify(
                            "Die Datei wurde inzwischen in einer IDE geändert. "
                            "Lade sie neu, damit nichts überschrieben wird.",
                            type="warning",
                        )
                        return False
                    except (OSError, ValueError) as error:
                        ui.notify(f"Speichern fehlgeschlagen: {error}", type="negative")
                        return False

                async def save_and_start_task(
                    path=target,
                    editor=source_editor,
                    output_view=execution_output,
                    refresh_tests=render_test_results,
                    refresh_summary=refresh_overview,
                    save_current=save_task,
                    exercise_name=name,
                    code_editor=source_editor,
                ) -> None:
                    selected_course = get_course_directory()
                    if selected_course is None:
                        ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                        return
                    if execution_manager.is_running(path):
                        ui.notify("Diese Aufgabe läuft bereits.", type="warning")
                        return
                    if not save_current(notify=False):
                        return
                    run_button.disable()
                    stop_button.enable()
                    run_status.set_text("LÄUFT")
                    run_status.props("color=warning")
                    try:
                        output_view.set_content("Programm läuft …")
                        result = await nicegui_run.io_bound(
                            execution_manager.execute, path, selected_course
                        )
                        output = result.stdout
                        if result.stderr:
                            output += ("\n" if output else "") + result.stderr
                        output_view.set_content(
                            output.strip()
                            or f"Programm beendet (Code {result.returncode}), ohne Ausgabe."
                        )
                        refresh_tests()
                        refresh_summary()
                        if result.stderr:
                            line, message = friendly_python_error(result.stderr)
                            code_editor.line_tooltips = {line: message} if line else {}
                        else:
                            code_editor.line_tooltips = {}
                        ui.notify(
                            "Programm wurde gestoppt."
                            if result.stopped else "Tests aktualisiert."
                            if result.returncode == 0
                            else f"Programm mit Fehlercode {result.returncode} beendet.",
                            type="warning" if result.stopped else
                            "positive" if result.returncode == 0 else "negative",
                        )
                    except (OSError, ValueError, RuntimeError) as error:
                        ui.notify(str(error), type="negative")
                    finally:
                        run_button.enable()
                        stop_button.disable()
                        run_status.set_text("BEREIT")
                        run_status.props("color=grey")

                def stop_task(path=target, output_view=execution_output) -> None:
                    if execution_manager.stop(path):
                        output_view.set_content("Programm wird beendet …")
                        run_status.set_text("WIRD BEENDET")
                    else:
                        ui.notify("Diese Aufgabe läuft gerade nicht.", type="info")

                def reload_task(
                    path=target, editor=source_editor, state=editor_state,
                    label=save_state, exercise_name=name,
                ) -> None:
                    selected_course = get_course_directory()
                    if selected_course is None:
                        return
                    try:
                        current = read_student_source(path, selected_course)
                        editor.set_value(current)
                        state.update(disk_hash=source_hash(current), dirty=False)
                        dirty_exercises.discard(exercise_name)
                        label.set_text("Neu von Datei geladen")
                        label.classes(replace="text-grey-7 text-sm")
                        ui.run_javascript(
                            "window.pykimHasUnsavedChanges = "
                            + str(bool(dirty_exercises)).lower()
                        )
                    except (OSError, ValueError) as error:
                        ui.notify(f"Neuladen fehlgeschlagen: {error}", type="negative")

                def reset_task(
                    exercise_name=name, editor=source_editor,
                    state=editor_state, label=save_state,
                    refresh_tests=render_test_results,
                    refresh_summary=refresh_overview,
                ) -> None:
                    selected_course = get_course_directory()
                    if selected_course is None:
                        return
                    try:
                        reset_path = reset_exercise_file(exercise_name, selected_course)
                        clear_exercise_progress(exercise_name, selected_course)
                        current = read_student_source(reset_path, selected_course)
                        editor.set_value(current)
                        state.update(disk_hash=source_hash(current), dirty=False)
                        dirty_exercises.discard(exercise_name)
                        label.set_text("Aufgabe zurückgesetzt; Backup wurde angelegt")
                        refresh_tests()
                        refresh_summary()
                        ui.notify("Aufgabe und Lernstand wurden zurückgesetzt.", type="positive")
                    except (OSError, ValueError) as error:
                        ui.notify(f"Zurücksetzen fehlgeschlagen: {error}", type="negative")

                def open_task_in_ide(path=target) -> None:
                    try:
                        open_in_preferred_ide(path)
                        ui.notify("Aufgabe wurde in der IDE geöffnet.", type="positive")
                    except (OSError, RuntimeError) as error:
                        ui.notify(f"IDE konnte nicht gestartet werden: {error}", type="negative")

                def copy_task_source(editor=source_editor) -> None:
                    ui.clipboard.write(editor.value)
                    ui.notify("Quellcode wurde kopiert.", type="positive")

                with action_row:
                    ui.button(
                        "Speichern",
                        on_click=save_task,
                        icon="save",
                    )
                    run_button = ui.button(
                        "Ausführen",
                        on_click=save_and_start_task,
                        icon="play_arrow",
                    )
                    stop_button = ui.button(
                        "Stoppen", on_click=stop_task, icon="stop",
                    ).props("outline")
                    stop_button.disable()
                    ui.button(
                        "Kopieren",
                        on_click=copy_task_source,
                        icon="content_copy",
                    ).props("outline")
                    ide_button = ui.button(
                        f"In {preferred_ide_label()} öffnen",
                        on_click=open_task_in_ide,
                        icon="open_in_new",
                    ).props("outline")
                    ide_open_buttons.append(ide_button)
                    ui.button(
                        "Neu laden", on_click=reload_task, icon="refresh",
                    ).props("flat")
                    with ui.dialog() as reset_dialog, ui.card():
                        ui.label("Aufgabe wirklich zurücksetzen?").classes("font-bold")
                        ui.label(
                            "Quellcode und Lernstand werden zurückgesetzt. "
                            "Vorher legt PyKIM Backups an."
                        )
                        with ui.row():
                            ui.button("Abbrechen", on_click=reset_dialog.close).props("flat")
                            ui.button(
                                "Zurücksetzen",
                                on_click=lambda dialog=reset_dialog, reset=reset_task: (
                                    dialog.close(), reset()
                                ),
                            )
                    ui.button(
                        "Zurücksetzen", on_click=reset_dialog.open, icon="restart_alt",
                    ).props("flat color=negative")
                    run_status = ui.badge("BEREIT", color="grey")

                source_editor.map_key("Mod-s", save_task)
                source_editor.map_key("F5", save_and_start_task)
            old_entry = journal.get(name, {}) if isinstance(journal, dict) else {}
            notes = ui.textarea(
                "Mein Dokubuch-Eintrag",
                value=old_entry.get("text", "") if isinstance(old_entry, dict) else "",
            ).classes("w-full")
            ui.button(
                "Eintrag speichern",
                on_click=lambda exercise=name, field=notes: (
                    save_journal_entry(exercise, field.value),
                    ui.notify("Dokubuch gespeichert", type="positive"),
                ),
            )



__all__ = ["render_tasks_panel"]
