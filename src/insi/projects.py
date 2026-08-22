"""Persönliche PyKIM- und Pyxel-Projekte im portablen Kursordner."""

from __future__ import annotations

import json
import hashlib
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .interpreter import command_for
from .execution_security import (
    execution_environment,
    student_policy,
)
from .sandbox import sandbox_popen
from .workspace_files import (
    project_files_directory,
    sandbox_readable_roots,
)
from .project_history import snapshot_project_if_changed
from tempfile import NamedTemporaryFile

PROJECTS_DIRECTORY = "Projekte"
METADATA_FILE = "projekt.json"


@dataclass(frozen=True)
class StudentProject:
    slug: str
    name: str
    kind: str
    directory: Path
    entrypoint: Path
    resources: Path | None
    documentation: Path


DOCUMENTATION_TEMPLATE = """\
# Mein Projekt

## Was macht mein Programm?

Beschreibe hier kurz deine Idee.

## Wie funktioniert es?

## Welche Probleme hatte ich?

## Wie habe ich sie gelöst?

## Was möchte ich noch verbessern?
"""


TEMPLATES = {
    "empty": """\
\"\"\"Mein Python-Projekt.\"\"\"

print("Hallo Welt!")
""",
    "pykim": """\
\"\"\"Mein PyKIM-Projekt.\"\"\"

from pykim import *

speed(30)
paint("orange")
right(10)
paint_stop()

run()
""",
    "pyxel": """\
\"\"\"Mein Pyxel-Spiel mit eigenen Ressourcen.\"\"\"

import pyxel

pyxel.init(160, 120, title="Mein Pyxel-Spiel")
pyxel.load("ressourcen.pyxres")


def update():
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()


def draw():
    pyxel.cls(0)
    pyxel.text(10, 10, "Mein Spiel", 7)


pyxel.run(update, draw)
""",
}


def project_slug(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.strip())
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name).strip("_")
    if not slug:
        raise ValueError("Der Projektname benötigt mindestens einen Buchstaben oder eine Zahl.")
    return slug[:60]


def projects_directory(course: str | Path) -> Path:
    return Path(course).expanduser().resolve() / PROJECTS_DIRECTORY


def _safe_child(directory: Path, value: str, label: str) -> Path:
    path = (directory / value).resolve()
    if not path.is_relative_to(directory.resolve()) or path.parent != directory.resolve():
        raise ValueError(f"Ungültiger {label} in {METADATA_FILE}.")
    return path


def _write_json(path: Path, data: dict[str, object]) -> None:
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=".projekt-", delete=False
        ) as temporary:
            json.dump(data, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def create_project(
    course: str | Path,
    name: str,
    kind: str = "pykim",
    *,
    source: str | None = None,
    parent: str = "",
    with_resources: bool | None = None,
) -> StudentProject:
    if kind not in TEMPLATES:
        raise ValueError(f"Unbekannte Projektvorlage: {kind}")
    root = projects_directory(course)
    if parent:
        parent_slug = project_slug(parent)
        root = root / parent_slug
    root.mkdir(parents=True, exist_ok=True)
    slug = project_slug(name)
    directory = root / slug
    try:
        directory.mkdir()
    except FileExistsError:
        raise FileExistsError(f"Das Projekt „{name}“ existiert bereits.") from None
    entrypoint = directory / "main.py"
    entrypoint.write_text(source if source is not None else TEMPLATES[kind], encoding="utf-8")
    (directory / "README.md").write_text(DOCUMENTATION_TEMPLATE, encoding="utf-8")
    if with_resources is None:
        with_resources = kind == "pyxel"
    resource_name = "ressourcen.pyxres" if with_resources else ""
    _write_json(
        directory / METADATA_FILE,
        {
            "format": 1,
            "name": name.strip(),
            "kind": kind,
            "entrypoint": entrypoint.name,
            "resources": resource_name,
        },
    )
    return load_project(directory)


def load_project(directory: str | Path) -> StudentProject:
    root = Path(directory).expanduser().resolve()
    try:
        data = json.loads((root / METADATA_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as error:
        raise ValueError(f"Projektdatei konnte nicht gelesen werden: {error}") from error
    if not isinstance(data, dict) or data.get("format") != 1:
        raise ValueError("Unbekanntes Projektformat.")
    name = data.get("name")
    kind = data.get("kind")
    entrypoint_name = data.get("entrypoint")
    resource_name = data.get("resources", "")
    if not all(isinstance(value, str) for value in (name, kind, entrypoint_name, resource_name)):
        raise ValueError("Unvollständige Projektdatei.")
    entrypoint = _safe_child(root, entrypoint_name, "Programmeinstieg")
    resources = _safe_child(root, resource_name, "Ressourcenpfad") if resource_name else None
    return StudentProject(
        root.name, name, kind, root, entrypoint, resources, root / "README.md"
    )


def project_text(project: StudentProject, path: Path) -> str:
    """Lese eine bearbeitbare Projektdatei oder die Vorlage einer alten README."""
    target = path.resolve()
    allowed = {project.entrypoint.resolve(), project.documentation.resolve()}
    if target not in allowed:
        raise ValueError("Diese Datei gehört nicht zum bearbeitbaren Projektbereich.")
    if target == project.documentation.resolve() and not target.exists():
        return DOCUMENTATION_TEMPLATE
    return target.read_text(encoding="utf-8")


def project_text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def save_project_text(
    project: StudentProject,
    path: Path,
    value: str,
    *,
    expected_hash: str,
) -> Path:
    """Speichere Code oder Dokumentation atomar mit Konflikterkennung."""
    target = path.resolve()
    current = project_text(project, target)
    if project_text_hash(current) != expected_hash:
        raise RuntimeError(
            "Die Datei wurde außerhalb der Suite verändert. Lade das Projekt neu."
        )
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=target.parent,
            prefix=f".{target.name}.", suffix=".tmp", delete=False,
        ) as temporary:
            temporary.write(value)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return target


def student_projects(course: str | Path) -> tuple[StudentProject, ...]:
    root = projects_directory(course)
    try:
        metadata_files = tuple(root.rglob(METADATA_FILE))
    except OSError:
        return ()
    result = []
    for metadata in metadata_files:
        try:
            result.append(load_project(metadata.parent))
        except ValueError:
            continue
    return tuple(sorted(result, key=lambda project: project.name.casefold()))


def launch_project(project: StudentProject, course: str | Path) -> Path:
    course_root = Path(course).expanduser().resolve()
    if not project.directory.is_relative_to(projects_directory(course_root)):
        raise ValueError("Das Projekt liegt nicht im Kursordner.")
    if not project.entrypoint.is_file():
        raise FileNotFoundError(f"{project.entrypoint.name} wurde nicht gefunden.")
    if project.resources is not None and not project.resources.is_file():
        raise RuntimeError(
            "Die Ressourcendatei fehlt noch. Öffne zuerst den Sprite- oder Musikeditor "
            "und speichere die Ressourcen."
        )
    from .runtime import PYXEL_RUNTIME_REQUIREMENT, selected_runtime

    python = (
        selected_runtime(
            course_root,
            additional_requirements=(PYXEL_RUNTIME_REQUIREMENT,),
        ).executable
        if project.kind == "pyxel"
        else selected_runtime(course_root).executable
    )
    project_files = project_files_directory(project.directory, create=True)
    snapshot_project_if_changed(project.directory, course_root)
    policy = student_policy(
        project.directory,
        readable_roots=sandbox_readable_roots(course_root),
        writable_roots=(project.directory,),
        allow_gui=project.kind in {"pykim", "pyxel"},
    )
    environment = execution_environment(
        policy,
        pythonpath=(course_root,),
        overrides={
            "INSI_PROJECT_FILES": str(project_files),
            "PYKIM_PROGRESS_MODE": "disabled",
        },
    )
    sandbox_popen(
        [*command_for(python), str(project.entrypoint)],
        policy=policy,
        cwd=project.directory,
        env=environment,
    )
    return project.entrypoint


def launch_project_editor(
    project: StudentProject,
    course: str | Path,
    editor: str,
) -> Path:
    if project.resources is None:
        raise ValueError("Dieses Projekt besitzt keine Pyxel-Ressourcendatei.")
    from .runtime import PYXEL_RUNTIME_REQUIREMENT, selected_runtime
    from .system import launch_pyxel_editor

    python = selected_runtime(
        course,
        additional_requirements=(PYXEL_RUNTIME_REQUIREMENT,),
    ).executable
    return launch_pyxel_editor(project.resources, python=python, editor=editor)
