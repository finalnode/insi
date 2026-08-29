import json
import errno

import pytest

from insi.course import create_course
from insi.data_migrations import (
    COURSE_DATA_FORMAT,
    COURSE_DATA_MARKER,
    LOCAL_SETTINGS_FORMAT,
    MigrationStorageError,
    migrate_course_data,
    migrate_local_settings,
)


def test_legacy_settings_are_backed_up_versioned_and_idempotent(tmp_path):
    settings = tmp_path / "config.json"
    original = {"course_directory": "/media/course", "unknown": {"keep": True}}
    settings.write_text(json.dumps(original), encoding="utf-8")

    first = migrate_local_settings(settings)
    second = migrate_local_settings(settings)

    migrated = json.loads(settings.read_text(encoding="utf-8"))
    backup = (
        tmp_path / "backups" / "migrations" / "0.7-to-0.8" / "config.json"
    )
    assert migrated == {"format": LOCAL_SETTINGS_FORMAT, **original}
    assert json.loads(backup.read_text(encoding="utf-8")) == original
    assert first.changed == ("config.json",)
    assert second.changed == ()


def test_course_migration_normalizes_progress_and_writes_marker_last(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course, "Ada")
    progress = course / ".pykim" / "progress.json"
    progress.parent.mkdir(exist_ok=True)
    original = {"format": 1, "attempts": [], "journal": {"a": {"text": "x"}}}
    progress.write_text(json.dumps(original), encoding="utf-8")

    report = migrate_course_data(course)

    migrated = json.loads(progress.read_text(encoding="utf-8"))
    marker = json.loads(
        (course / ".pykim" / COURSE_DATA_MARKER).read_text(encoding="utf-8")
    )
    backup = (
        course
        / ".pykim"
        / "backups"
        / "migrations"
        / "0.7-to-0.8"
        / "progress.json"
    )
    assert migrated["journal"] == original["journal"]
    assert migrated["answers"] == {}
    assert migrated["hints"] == {}
    assert json.loads(backup.read_text(encoding="utf-8")) == original
    assert marker["format"] == COURSE_DATA_FORMAT
    assert marker["version"] == 1
    assert report.changed == (
        ".pykim/progress.json",
        ".pykim/data-version.json",
    )
    assert migrate_course_data(course).changed == ()


def test_interrupted_course_migration_can_resume_without_replacing_backup(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course)
    progress = course / ".pykim" / "progress.json"
    progress.parent.mkdir(exist_ok=True)
    original = {"attempts": [], "journal": {}}
    progress.write_text(json.dumps(original), encoding="utf-8")
    from insi import data_migrations

    real_write = data_migrations._atomic_write_json
    interrupted = {"value": True}

    def fail_marker(path, document):
        if path.name == COURSE_DATA_MARKER and interrupted["value"]:
            interrupted["value"] = False
            raise OSError("simulierter Abbruch")
        real_write(path, document)

    monkeypatch.setattr(data_migrations, "_atomic_write_json", fail_marker)

    with pytest.raises(OSError, match="simulierter Abbruch"):
        migrate_course_data(course)
    report = migrate_course_data(course)

    backup = (
        course
        / ".pykim"
        / "backups"
        / "migrations"
        / "0.7-to-0.8"
        / "progress.json"
    )
    assert json.loads(backup.read_text(encoding="utf-8")) == original
    assert report.changed == (".pykim/data-version.json",)


@pytest.mark.parametrize(
    "filename, document, message",
    [
        ("progress.json", {"format": 1, "attempts": "kaputt"}, "Lernstand"),
        (COURSE_DATA_MARKER, {"format": COURSE_DATA_FORMAT, "version": 99}, "neueren"),
    ],
)
def test_invalid_or_future_course_data_is_never_changed(
    tmp_path, monkeypatch, filename, document, message
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course)
    target = course / ".pykim" / filename
    target.parent.mkdir(exist_ok=True)
    original = json.dumps(document)
    target.write_text(original, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        migrate_course_data(course)

    assert target.read_text(encoding="utf-8") == original
    if filename != COURSE_DATA_MARKER:
        assert not (course / ".pykim" / COURSE_DATA_MARKER).exists()


def test_current_marker_does_not_hide_later_progress_corruption(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course)
    migrate_course_data(course)
    progress = course / ".pykim" / "progress.json"
    progress.write_text('{"format": 1, "attempts": "kaputt"}', encoding="utf-8")

    with pytest.raises(ValueError, match="Lernstand"):
        migrate_course_data(course)

    assert "kaputt" in progress.read_text(encoding="utf-8")


def test_removed_drive_during_backup_never_changes_source(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "usb-course"
    create_course(course)
    progress = course / ".pykim" / "progress.json"
    progress.parent.mkdir(exist_ok=True)
    original = '{"attempts": [], "journal": {}}'
    progress.write_text(original, encoding="utf-8")
    from insi import data_migrations

    real_copy = data_migrations.shutil.copy2
    monkeypatch.setattr(
        data_migrations.shutil,
        "copy2",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError(errno.ENODEV, "Datenträger entfernt")
        ),
    )

    with pytest.raises(MigrationStorageError, match="Quelldatei wurde nicht verändert"):
        migrate_course_data(course)

    assert progress.read_text(encoding="utf-8") == original
    assert not (course / ".pykim" / COURSE_DATA_MARKER).exists()
    assert not tuple((course / ".pykim").rglob("*.tmp"))

    monkeypatch.setattr(data_migrations.shutil, "copy2", real_copy)
    assert migrate_course_data(course).version == 1


def test_removed_drive_during_atomic_replace_keeps_original_and_backup(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "usb-course"
    create_course(course)
    progress = course / ".pykim" / "progress.json"
    progress.parent.mkdir(exist_ok=True)
    original = '{"attempts": [], "journal": {}}'
    progress.write_text(original, encoding="utf-8")
    from insi import data_migrations

    real_replace = data_migrations.os.replace

    def fail_progress_replace(source, target):
        if target == progress:
            raise OSError(errno.ENODEV, "Datenträger entfernt")
        real_replace(source, target)

    monkeypatch.setattr(data_migrations.os, "replace", fail_progress_replace)

    with pytest.raises(MigrationStorageError, match="bisherige Stand bleibt"):
        migrate_course_data(course)

    backup = (
        course / ".pykim" / "backups" / "migrations" / "0.7-to-0.8" / "progress.json"
    )
    assert progress.read_text(encoding="utf-8") == original
    assert backup.read_text(encoding="utf-8") == original
    assert not (course / ".pykim" / COURSE_DATA_MARKER).exists()
    assert not tuple(progress.parent.glob(".progress.json.*.tmp"))

    monkeypatch.setattr(data_migrations.os, "replace", real_replace)
    assert migrate_course_data(course).version == 1
