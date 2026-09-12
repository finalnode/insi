"""Projektmodell, Konfliktschutz und lokale Projektstarts."""

import json
import os
from pathlib import Path

import pytest

from insi.project_history import project_states
from insi.projects import (
    create_project,
    launch_project,
    launch_project_editor,
    load_project,
    project_slug,
    project_text,
    project_text_hash,
    save_project_text,
    student_projects,
)
from insi.runtime import RuntimeCandidate


def test_create_and_load_pyxel_project_with_relative_resources(tmp_path):
    project = create_project(tmp_path, "Mein Rätsel!", "pyxel")

    assert project.slug == "mein_ratsel"
    assert project.entrypoint == tmp_path / "Projekte" / "mein_ratsel" / "main.py"
    assert project.resources == project.directory / "ressourcen.pyxres"
    assert project.documentation == project.directory / "README.md"
    assert "# Mein Projekt" in project.documentation.read_text(encoding="utf-8")
    assert 'pyxel.load("ressourcen.pyxres")' in project.entrypoint.read_text(encoding="utf-8")
    assert load_project(project.directory) == project
    assert student_projects(tmp_path) == (project,)
    with pytest.raises(FileExistsError, match="existiert bereits"):
        create_project(tmp_path, "Mein Rätsel!", "pyxel")


def test_project_code_and_documentation_detect_external_changes(tmp_path):
    project = create_project(tmp_path, "Dokumentiertes Spiel", "pykim")
    documentation = project_text(project, project.documentation)

    save_project_text(
        project,
        project.documentation,
        "# Meine Erklärung\n",
        expected_hash=project_text_hash(documentation),
    )
    assert project.documentation.read_text(encoding="utf-8") == "# Meine Erklärung\n"

    project.documentation.write_text("# Extern geändert\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="außerhalb"):
        save_project_text(
            project,
            project.documentation,
            "# Überschreiben\n",
            expected_hash=project_text_hash("# Meine Erklärung\n"),
        )


def test_project_metadata_cannot_escape_its_directory(tmp_path):
    directory = tmp_path / "Projekte" / "boese"
    directory.mkdir(parents=True)
    (directory / "projekt.json").write_text(
        json.dumps({
            "format": 1,
            "name": "Böse",
            "kind": "pyxel",
            "entrypoint": "../fremd.py",
            "resources": "ressourcen.pyxres",
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Programmeinstieg"):
        load_project(directory)


def test_project_launch_uses_selected_runtime_and_project_working_directory(
    tmp_path, monkeypatch
):
    project = create_project(tmp_path, "Spiel", "pykim")
    python = tmp_path / "runtime" / "python"
    calls = []
    monkeypatch.setattr(
        "insi.runtime.selected_runtime",
        lambda course=None: RuntimeCandidate(
            str(python), "3.13", "Test", True, ("PyKIM", "Pyxel")
        ),
    )
    monkeypatch.setattr(
        "insi.projects.sandbox_popen",
        lambda command, cwd=None, env=None, **_options: calls.append(
            (command, cwd, env)
        ),
    )

    assert launch_project(project, tmp_path) == project.entrypoint
    assert calls[0][:2] == ([str(python), str(project.entrypoint)], project.directory)
    assert str(tmp_path.resolve()) in calls[0][2]["PYTHONPATH"].split(os.pathsep)
    states = project_states(project.directory, tmp_path)
    assert len(states) == 1
    assert states[0].title == "Automatisch vor Ausführung"

    launch_project(project, tmp_path)

    assert len(project_states(project.directory, tmp_path)) == 1


def test_pyxel_project_launch_requires_the_pinned_pyxel_runtime(tmp_path, monkeypatch):
    project = create_project(tmp_path, "Spiel", "pyxel")
    project.resources.write_bytes(b"resource")
    python = tmp_path / "runtime" / "python"
    requested = []

    def select(course=None, **options):
        requested.append((course, options))
        return RuntimeCandidate(
            str(python), "3.13", "Test", True, ("PyKIM", "Pyxel")
        )

    monkeypatch.setattr("insi.runtime.selected_runtime", select)
    monkeypatch.setattr("insi.projects.sandbox_popen", lambda *_args, **_kwargs: None)

    launch_project(project, tmp_path)

    assert requested == [
        (
            tmp_path.resolve(),
            {"additional_requirements": ("Pyxel==2.9.9",)},
        )
    ]


def test_project_slug_rejects_empty_names():
    with pytest.raises(ValueError, match="Buchstaben"):
        project_slug("!!!")


def test_project_editor_uses_selected_runtime_and_requested_area(tmp_path, monkeypatch):
    project = create_project(tmp_path, "Spiel", "pyxel")
    python = tmp_path / "runtime" / "python"
    calls = []
    monkeypatch.setattr(
        "insi.runtime.selected_runtime",
        lambda course=None, **_options: RuntimeCandidate(
            str(python), "3.13", "Test", True, ("PyKIM", "Pyxel")
        ),
    )
    monkeypatch.setattr(
        "insi.system.launch_pyxel_editor",
        lambda resource, python=None, editor="image": calls.append(
            (resource, python, editor)
        ) or Path(resource),
    )

    assert launch_project_editor(project, tmp_path, "music") == project.resources
    assert calls == [(project.resources, str(python), "music")]
