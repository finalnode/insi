"""Verträge der gemeinsamen Installation in vorhandene Kursworkspaces."""

import io
import json
from pathlib import Path
import zipfile

from insi.course_archive import course_content_source
from insi.course_setup import (
    course_setup_info,
    install_course_archive,
    install_course_setup,
)


def setup_data(*, repository: str) -> bytes:
    return json.dumps(
        {
            "format": "insi-course-setup-v1",
            "name": "python-11a.insi-setup",
            "teacher": "Frau Beispiel",
            "school": "OSZ KIM",
            "course": "Python 11A",
            "repository": repository,
            "branch": "main",
            "scripts_path": "Skripte",
            "assignments_path": "Aufgaben",
            "trainers_path": "Trainer",
        }
    ).encode()


def existing_workspace(tmp_path: Path) -> tuple[Path, Path]:
    course = tmp_path / "course"
    course.mkdir()
    personal = course / "mein-projekt.py"
    personal.write_text("print('bleibt')\n", encoding="utf-8")
    return course, personal


def reject_workspace_creation(_course) -> None:
    raise AssertionError("Ein vorhandener Workspace darf nicht neu angelegt werden.")


def test_repository_setup_reuses_existing_workspace(tmp_path, monkeypatch):
    course, personal = existing_workspace(tmp_path)
    content = tmp_path / "content"
    content.mkdir()
    calls = []
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.course.create_course", reject_workspace_creation)
    monkeypatch.setattr(
        "insi.updates.sync_certificate_content", lambda _info: content
    )
    monkeypatch.setattr(
        "insi.registries.activate_content_registries",
        lambda root, **paths: calls.append((root, paths)),
    )
    monkeypatch.setattr(
        "insi.course.provision_course_exercises", lambda root: calls.append(root)
    )

    info = install_course_setup(
        setup_data(repository="https://github.com/example/course.git"), course
    )

    assert course_setup_info(course) == info
    assert course_content_source(course) == {"type": "repository"}
    assert personal.read_text(encoding="utf-8") == "print('bleibt')\n"
    assert calls[-1] == course


def test_archive_setup_reuses_existing_workspace_offline(tmp_path, monkeypatch):
    course, personal = existing_workspace(tmp_path)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("python-11a.insi-setup", setup_data(repository=""))
        bundle.writestr("Skripte/imperativ/start.md", "# Start\n")
    calls = []
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.course.create_course", reject_workspace_creation)
    monkeypatch.setattr(
        "insi.registries.activate_content_registries",
        lambda root, **paths: calls.append((root, paths)),
    )
    monkeypatch.setattr(
        "insi.course.provision_course_exercises", lambda root: calls.append(root)
    )

    info = install_course_archive(archive.getvalue(), course)

    assert course_setup_info(course) == info
    assert course_content_source(course)["type"] == "archive"
    assert personal.read_text(encoding="utf-8") == "print('bleibt')\n"
    assert calls[-1] == course
