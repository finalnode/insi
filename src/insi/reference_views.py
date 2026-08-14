"""Kleine, zustandslose Lern- und Referenzansichten."""

from insi.content import CHEATSHEET, PYODIDE_PLAYGROUND, PYXEL_REFERENCE
from insi.pyxel_examples_view import render_pyxel_examples_view
from insi.script_view import render_script_reader


def render_cheatsheet_panel(ui) -> None:
    ui.markdown(CHEATSHEET).classes("prose max-w-none")


def render_script_panel(ui) -> None:
    render_script_reader(ui)


def render_pyxel_panel(
    ui,
    ide_label: str,
    ide_open_buttons: list,
    *,
    on_project_saved,
) -> None:
    ui.markdown(PYXEL_REFERENCE).classes("prose max-w-none")
    ui.separator()
    render_pyxel_examples_view(
        ui,
        ide_label,
        ide_open_buttons,
        on_project_saved=on_project_saved,
    )


def render_browser_playground_panel(ui) -> None:
    ui.label("Python-Grundlagen im Browser").classes("text-2xl font-bold")
    ui.markdown(
        "Diese Pyodide-Spielwiese ist nur für **reines Python ohne PyKIM und "
        "Pyxel** gedacht, zum Beispiel für Variablen, Schleifen, Listen und "
        "Funktionen. PyKIM- und Pyxel-Programme benötigen Grafik, Audio und "
        "die lokale Runtime und werden deshalb über **Ausführen** in in:si "
        "gestartet."
    )
    ui.html(PYODIDE_PLAYGROUND, sanitize=False).classes("w-full")


__all__ = [
    "render_browser_playground_panel",
    "render_cheatsheet_panel",
    "render_pyxel_panel",
    "render_script_panel",
]
