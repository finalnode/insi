"""Verträge für portablen Datenexport und vollständige lokale Löschung."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from insi.course import create_course, set_course_directory
from insi.local_data import (
    EXPORT_FORMAT,
    create_local_data_export,
    trash_all_local_data,
)


def marked_course(path: Path, name: str) -> Path:
    course = path / name
    create_course(course, "Ada")
    setup = course / ".pykim" / "course.insi-setup"
    setup.parent.mkdir(exist_ok=True)
    setup.write_text("{}", encoding="utf-8")
    return course


def test_local_data_export_contains_personal_data_but_not_reproducible_caches(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))
    course = marked_course(tmp_path, "python-kurs")
    (course / "Projekte" / "spiel.py").write_text("print('hi')", encoding="utf-8")
    set_course_directory(course)
    (config / "insi-workspace" / "Dateien").mkdir(parents=True)
    (config / "insi-workspace" / "Dateien" / "daten.csv").write_text(
        "x,y\n1,2\n", encoding="utf-8"
    )
    (config / "content").mkdir()
    (config / "content" / "cache.bin").write_bytes(b"cache")
    (config / "runtimes").mkdir()
    (config / "runtimes" / "python").write_bytes(b"runtime")

    report = create_local_data_export(tmp_path / "exports")

    with ZipFile(report.path) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
    assert "app-data/config.json" in names
    assert "app-data/insi-workspace/Dateien/daten.csv" in names
    assert "courses/01-python-kurs/Projekte/spiel.py" in names
    assert not any(name.startswith("app-data/content/") for name in names)
    assert not any(name.startswith("app-data/runtimes/") for name in names)
    assert manifest["format"] == EXPORT_FORMAT
    assert manifest["courses"][0]["original_path"] == str(course.resolve())
    assert report.courses == 1
    assert report.files == len(names) - 1


def test_local_data_export_refuses_destination_inside_exported_data(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))
    config.mkdir()

    with pytest.raises(ValueError, match="außerhalb"):
        create_local_data_export(config / "exports")


def test_local_data_export_rejects_registered_non_course_before_reading_it(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))
    ordinary = tmp_path / "ordinary"
    ordinary.mkdir()
    (ordinary / "private.txt").write_text("nicht exportieren", encoding="utf-8")
    set_course_directory(ordinary)

    with pytest.raises(ValueError, match="Kurskennung"):
        create_local_data_export(tmp_path / "exports")

    assert not (tmp_path / "exports").exists()


def test_local_data_export_removes_temporary_archive_after_storage_failure(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    exports = tmp_path / "exports"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))
    config.mkdir()

    def fail_replace(_source, _target):
        raise OSError("Datenträger entfernt")

    monkeypatch.setattr("insi.local_data.os.replace", fail_replace)

    with pytest.raises(OSError, match="Datenträger entfernt"):
        create_local_data_export(exports)

    assert list(exports.iterdir()) == []


def test_local_data_deletion_validates_every_course_before_using_trash(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))
    valid = marked_course(tmp_path, "valid")
    invalid = tmp_path / "ordinary"
    invalid.mkdir()
    set_course_directory(valid)
    set_course_directory(invalid)
    trashed = []
    monkeypatch.setitem(
        sys.modules,
        "send2trash",
        SimpleNamespace(send2trash=lambda path: trashed.append(path)),
    )

    with pytest.raises(ValueError, match="Kurskennung"):
        trash_all_local_data()

    assert trashed == []


def test_local_data_deletion_moves_courses_and_app_data_to_system_trash(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))
    first = marked_course(tmp_path, "first")
    second = marked_course(tmp_path, "second")
    set_course_directory(first)
    set_course_directory(second)
    trashed = []
    monkeypatch.setitem(
        sys.modules,
        "send2trash",
        SimpleNamespace(send2trash=lambda path: trashed.append(Path(path))),
    )

    report = trash_all_local_data()

    assert set(report.trashed) == {first.resolve(), second.resolve(), config.resolve()}
    assert set(trashed) == set(report.trashed)
    assert report.missing_courses == ()


def test_local_data_deletion_never_accepts_home_as_app_data_root(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(Path.home()))
    monkeypatch.setattr("insi.local_data.get_course_directories", lambda: ())

    with pytest.raises(ValueError, match="darf nicht entfernt"):
        trash_all_local_data()
