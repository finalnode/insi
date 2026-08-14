"""Wiederverwendbare Lernstands-, Test- und Fehlerdarstellung der Suite."""

import re

from insi.training.registry import get_activity, get_exercise

from .library import task_names
from .progress import load_progress, revealed_hint_count, save_revealed_hint_count
from .components import empty_state, section_heading


def latest_attempts(progress: dict[str, object]) -> dict[str, dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    attempts = progress.get("attempts", [])
    if isinstance(attempts, list):
        for attempt in attempts:
            if isinstance(attempt, dict) and isinstance(attempt.get("exercise"), str):
                latest[attempt["exercise"]] = attempt
    return latest


def render_task_hints(ui, task: str, hints: tuple[str, ...]) -> None:
    """Zeige Autorenhinweise schrittweise und merke den geöffneten Stand."""
    if not hints:
        return
    state = {"count": min(revealed_hint_count(task), len(hints))}
    container = ui.column().classes("w-full gap-2")

    def reveal_next() -> None:
        if state["count"] < len(hints):
            state["count"] += 1
            save_revealed_hint_count(task, state["count"])
            render()

    def render() -> None:
        container.clear()
        with container:
            with ui.row().classes("w-full items-center gap-2"):
                ui.icon("lightbulb", size="sm").classes("text-primary")
                ui.label("Hinweise").classes("font-bold")
                if state["count"]:
                    ui.badge(f"{state['count']} / {len(hints)}", color="grey")
            for index, hint in enumerate(hints[:state["count"]], start=1):
                with ui.card().classes("w-full shadow-none bg-orange-1 border-l-4 border-primary"):
                    ui.label(f"Hinweis {index}").classes("text-sm font-bold text-primary")
                    ui.markdown(hint).classes("prose max-w-none")
            if state["count"] < len(hints):
                label = "Ersten Hinweis anzeigen" if state["count"] == 0 else "Nächsten Hinweis anzeigen"
                ui.button(label, on_click=reveal_next, icon="lightbulb_outline").props(
                    "outline color=primary"
                )
            else:
                ui.label("Alle verfügbaren Hinweise sind geöffnet.").classes("text-grey-7 text-sm")

    render()


def render_task_sources(ui, sources) -> None:
    """Zeige eine oder mehrere Aufgabenquellen platzsparend an."""
    if not sources:
        return
    with ui.row().classes("w-full items-center gap-1 text-sm text-grey-7"):
        ui.icon("source", size="xs")
        ui.label("Quelle:" if len(sources) == 1 else "Quellen:")
        for index, source in enumerate(sources):
            if index:
                ui.label("·")
            if source.url:
                ui.link(source.label, source.url, new_tab=True).classes("text-primary")
            else:
                ui.label(source.label)


def render_test_results(ui, exercise_name: str) -> None:
    attempt = latest_attempts(load_progress()).get(exercise_name)
    if attempt is None:
        empty_state(
            ui,
            "Automatische Tests",
            "Noch kein Testlauf vorhanden. Starte dein Programm, um die "
            "einzelnen Prüffälle auszuführen.",
            icon="fact_check",
        )
        return

    tests = attempt.get("tests", [])
    passed_tests = int(attempt.get("passed", 0))
    total_tests = int(attempt.get("total", len(tests)))
    with ui.row().classes("w-full items-center gap-3 mt-3"):
        ui.label("Automatische Tests").classes("text-lg font-bold")
        ui.badge(
            f"{passed_tests} / {total_tests} bestanden",
            color="positive" if passed_tests == total_tests else "negative",
        )
    with ui.expansion("Testdetails anzeigen", icon="fact_check").classes(
        "w-full border rounded"
    ):
        for index, test in enumerate(tests, start=1):
            passed = bool(test["passed"])
            style = "pykim-test-passed" if passed else "pykim-test-failed"
            with ui.card().classes(f"w-full pykim-test-result {style}"):
                with ui.row().classes("w-full items-center"):
                    ui.icon(
                        "check_circle" if passed else "cancel",
                        color="positive" if passed else "negative",
                    )
                    ui.label(f"Testfall {index}").classes("font-bold")
                    ui.space()
                    ui.badge(
                        "BESTANDEN" if passed else "FEHLGESCHLAGEN",
                        color="positive" if passed else "negative",
                    )
                ui.label(test["message"]).classes("text-base")
                if test.get("hint"):
                    ui.label(f"Tipp: {test['hint']}").classes("w-full pykim-test-hint")


def render_overview(ui) -> None:
    progress = load_progress()
    latest = latest_attempts(progress)
    completed = sum(bool(item.get("successful")) for item in latest.values())
    section_heading(ui, "Mein Lernstand")
    ui.linear_progress(value=completed / max(1, len(task_names())))
    ui.label(f"{completed} von {len(task_names())} Aufgaben vollständig gelöst")
    with ui.grid(columns=2).classes("w-full gap-4"):
        for name in task_names():
            activity = get_activity(name)
            exercise = None if activity is not None and activity.mode == "matching" else get_exercise(name)
            attempt = latest.get(name)
            with ui.card().classes("w-full"):
                ui.label(activity.title if exercise is None else exercise.title).classes("font-bold")
                if attempt is None:
                    ui.label("Noch nicht begonnen").classes("text-grey")
                else:
                    ui.label(f"Tests: {attempt['passed']}/{attempt['total']}")
                    optimization = attempt.get("optimization")
                    if isinstance(optimization, dict):
                        ui.label(f"Optimierung: {optimization['score']} %")


def friendly_python_error(stderr: str) -> tuple[int | None, str]:
    matches = re.findall(r'File "[^"]+", line (\d+)', stderr)
    line = int(matches[-1]) if matches else None
    last = next(
        (item.strip() for item in reversed(stderr.splitlines()) if item.strip()), ""
    )
    translations = {
        "SyntaxError": "Syntaxfehler",
        "IndentationError": "Einrückungsfehler",
        "NameError": "Unbekannter Name",
        "TypeError": "Falscher Datentyp oder Funktionsaufruf",
        "IndexError": "Ungültiger Listenindex",
    }
    for technical, german in translations.items():
        if technical in last:
            return line, f"{german}: {last.partition(':')[2].strip()}"
    return line, last or "Das Programm wurde mit einem Fehler beendet."


__all__ = [
    "friendly_python_error",
    "latest_attempts",
    "render_overview",
    "render_task_hints",
    "render_task_sources",
    "render_test_results",
]
