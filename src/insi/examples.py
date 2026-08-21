"""Katalog der mitinstallierten PyKIM-Beispielprogramme."""

import ast
import tempfile
import shutil
import threading
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from .interpreter import python_command
from .execution import script_example_manager
from .execution_security import (
    builtin_policy,
    execution_environment,
)
from .sandbox import sandbox_popen


@dataclass(frozen=True)
class ExampleProgram:
    name: str
    title: str
    category: str
    description: str
    path: Path
    source: str


CATEGORIES = {
    "color_checkerboard": "Farben und Schleifen",
    "color_palette": "Farben",
    "color_sensor": "Farben und Sensoren",
    "color_tones": "Farben und Töne",
    "farben_melodie_aufgabe": "Musterlösungen",
    "follow_path": "Bewegung",
    "fuer_elise": "Musik",
    "interaktive_steuerung_aufgabe": "Musterlösungen",
    "mehrere_pixel": "Mehrere Pixel",
    "musik_pixel_aufgabe": "Musterlösungen",
    "pachelbel_canon": "Musik",
    "paint_line": "Zeichnen",
    "paint_trace": "Zeichnen",
    "punktlinie_aufgabe": "Musterlösungen",
    "quadrat_aufgabe": "Musterlösungen",
    "rhythmus_aufgabe": "Musterlösungen",
    "schachbrett_aufgabe": "Musterlösungen",
    "tonleiter_aufgabe": "Musterlösungen",
    "treppe_aufgabe": "Musterlösungen",
    "vier_quadrate_aufgabe": "Musterlösungen",
}


def example_programs() -> tuple[ExampleProgram, ...]:
    result = []
    root = files("pykim.examples")
    for name, category in CATEGORIES.items():
        resource = root.joinpath(f"{name}.py")
        source = resource.read_text(encoding="utf-8")
        description = ast.get_docstring(ast.parse(source)) or "Ausführbares PyKIM-Beispiel"
        result.append(
            ExampleProgram(
                name=name,
                title=name.replace("_aufgabe", "").replace("_", " ").title(),
                category=category,
                description=description,
                path=Path(str(resource)).resolve(),
                source=source,
            )
        )
    return tuple(result)


def _example(name: str) -> ExampleProgram:
    try:
        return next(example for example in example_programs() if example.name == name)
    except StopIteration:
        raise ValueError(f"Unbekanntes PyKIM-Beispiel: {name}") from None


def launch_example(name: str) -> Path:
    """Starte ausschließlich ein Programm aus dem installierten Beispielkatalog."""
    example = _example(name)
    run_root = Path(tempfile.mkdtemp(prefix="insi-example-"))
    policy = builtin_policy(
        run_root,
        readable_roots=(example.path.parent,),
        writable_roots=(run_root,),
        allow_gui=True,
    )
    environment = execution_environment(
        policy,
        overrides={"PYKIM_PROGRESS_MODE": "disabled"},
    )
    process = sandbox_popen(
        [*python_command(), str(example.path)],
        policy=policy,
        cwd=run_root,
        env=environment,
    )

    def cleanup() -> None:
        process.wait()
        shutil.rmtree(run_root, ignore_errors=True)

    threading.Thread(target=cleanup, daemon=True).start()
    return example.path


def start_example(name: str) -> str:
    """Starte ein geprüftes Galeriebeispiel und liefere seine Laufkennung."""
    example = _example(name)
    return script_example_manager.start(example.source, trusted=True)


def copy_example_to_course(name: str, course: str | Path) -> tuple[Path, bool]:
    """Lege eine bearbeitbare Kopie an, ohne vorhandene Schülerarbeit zu ersetzen."""
    example = _example(name)
    root = Path(course).expanduser().resolve()
    from .projects import create_project, project_slug, projects_directory

    directory = projects_directory(root) / "beispiele" / project_slug(example.title)
    target = directory / "main.py"
    if target.exists():
        return target, False
    project = create_project(
        root,
        example.title,
        "pykim",
        source=example.source,
        parent="Beispiele",
    )
    return project.entrypoint, True
