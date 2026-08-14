"""Galerie der mit Pyxel ausgelieferten Beispielprogramme."""

from __future__ import annotations

import ast
import shutil
from pathlib import Path

from .course import get_course_directory
from .projects import create_project
from .system import (
    launch_pyxel_example,
    open_in_preferred_ide,
    pyxel_examples,
)


def _title(path: Path) -> str:
    name = path.stem
    if "_" in name and name.split("_", 1)[0].isdigit():
        name = name.split("_", 1)[1]
    return name.replace("_", " ").title()


def _description(source: str) -> str:
    try:
        return ast.get_docstring(ast.parse(source)) or "Offizielles Pyxel-Beispiel"
    except SyntaxError:
        return "Offizielles Pyxel-Beispiel"


def copy_pyxel_example_to_course(
    example: str | Path,
    course: str | Path,
) -> tuple[Path, bool]:
    """Kopiere Beispielcode und die zugehörigen Assets in ein Schülerprojekt."""
    available = {path.resolve() for path in pyxel_examples()}
    source_path = Path(example).expanduser().resolve()
    if source_path not in available:
        raise ValueError("Es dürfen nur mitgelieferte Pyxel-Beispiele kopiert werden.")

    source = source_path.read_text(encoding="utf-8")
    try:
        project = create_project(
            course,
            _title(source_path),
            "pyxel",
            source=source,
            parent="Pyxel Beispiele",
            with_resources=False,
        )
    except FileExistsError:
        from .projects import project_slug, projects_directory

        target = (
            projects_directory(course)
            / project_slug("Pyxel Beispiele")
            / project_slug(_title(source_path))
            / "main.py"
        )
        return target, False

    assets = source_path.parent / "assets"
    if assets.is_dir():
        shutil.copytree(assets, project.directory / "assets")
    return project.entrypoint, True


def render_pyxel_examples_view(
    ui,
    preferred_ide_label: str,
    ide_open_buttons: list,
    on_project_saved=None,
) -> None:
    ui.label("Pyxel-Beispiele").classes("text-2xl font-bold")
    ui.markdown(
        "Diese Programme gehören zur installierten Pyxel-Version. Du kannst sie "
        "direkt starten, den vollständigen Quellcode ansehen oder zusammen mit "
        "ihren Ressourcen in deine eigenen Projekte übernehmen."
    )
    examples = pyxel_examples()
    if not examples:
        ui.label("Es wurden keine Pyxel-Beispiele gefunden.").classes("text-orange")
        return

    for example in examples:
        source = example.read_text(encoding="utf-8")
        with ui.expansion(_title(example), icon="sports_esports").classes("w-full"):
            ui.label(_description(source)).classes("text-base")
            editor = ui.codemirror(
                value=source,
                language="Python",
                line_wrapping=False,
            ).classes("w-full").style("height: 28rem")
            editor.disable()

            def copy_source(source_editor=editor) -> None:
                ui.clipboard.write(source_editor.value)
                ui.notify("Pyxel-Code wurde kopiert.", type="positive")

            def start(selected=example) -> None:
                try:
                    launch_pyxel_example(selected)
                    ui.notify("Pyxel-Beispiel wurde gestartet.", type="positive")
                except (OSError, RuntimeError, ValueError) as error:
                    ui.notify(f"Start fehlgeschlagen: {error}", type="negative")

            def personal_copy(selected=example):
                course = get_course_directory()
                if course is None:
                    ui.notify("Richte zuerst einen Kursordner ein.", type="warning")
                    return None
                try:
                    return course, copy_pyxel_example_to_course(selected, course)
                except (OSError, ValueError) as error:
                    ui.notify(str(error), type="negative")
                    return None

            def save(selected=example) -> None:
                result = personal_copy(selected)
                if result is None:
                    return
                course, (target, created) = result
                ui.notify(
                    f"Projekt angelegt: {target.parent.relative_to(course)}"
                    if created else "Das persönliche Projekt ist bereits vorhanden.",
                    type="positive",
                )
                if on_project_saved is not None:
                    on_project_saved()

            def open_in_ide(selected=example) -> None:
                result = personal_copy(selected)
                if result is None:
                    return
                _course, (target, _created) = result
                if on_project_saved is not None:
                    on_project_saved()
                try:
                    open_in_preferred_ide(target.parent)
                    ui.notify("Pyxel-Projekt wurde in der IDE geöffnet.", type="positive")
                except (OSError, RuntimeError, ValueError) as error:
                    ui.notify(str(error), type="negative")

            with ui.row().classes("items-center"):
                ui.button("Ausführen", on_click=start, icon="play_arrow")
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
                    icon="create_new_folder",
                ).props("outline")


__all__ = ["copy_pyxel_example_to_course", "render_pyxel_examples_view"]
