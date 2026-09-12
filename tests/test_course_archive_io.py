"""Exportdateien werden gestreamt; Größen- und Integritätsprüfungen bleiben aktiv."""

from pathlib import Path

import pytest

from insi import course_archive
from insi.course_runtime import manifest_with_wheels, runtime_manifest_bytes
from insi.course_setup import generate_course_setup
from insi.course_builder_view import ensure_course_source


@pytest.fixture
def archive_inputs(tmp_path):
    source = ensure_course_source(tmp_path / "Kurs")
    chapter = source / "Skripte" / "start.md"
    chapter.write_text("# Start\n", encoding="utf-8")
    setup = generate_course_setup(source, teacher="Ada", school="Schule", course="Streaming")
    wheel = tmp_path / "demo-1.2.3-py3-none-any.whl"
    wheel.write_bytes(b"wheel data" * 100_000)
    name = f"wheelhouse/windows-x86_64-python311/{wheel.name}"
    manifest = manifest_with_wheels("3.11", ("demo==1.2.3",), ("windows-x86_64-python311",), {name: wheel})
    return source, setup, chapter, wheel, name, runtime_manifest_bytes(manifest)


def test_export_does_not_buffer_source_files(archive_inputs, monkeypatch):
    source, setup, chapter, wheel, name, manifest = archive_inputs
    original = Path.read_bytes

    def read(path):
        assert path not in (chapter, wheel), "Exportdateien dürfen nicht vollständig gepuffert werden."
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    data = course_archive.build_course_archive(source, setup, runtime_manifest=manifest, offline_wheels={name: wheel})
    bundle = course_archive.parse_course_archive(data)
    assert bundle.files["Skripte/start.md"] == b"# Start\n"
    assert bundle.offline_wheels[name] == b"wheel data" * 100_000


def test_oversized_content_is_rejected_before_copying(archive_inputs, monkeypatch):
    source, setup, *_ = archive_inputs
    monkeypatch.setattr(course_archive, "MAX_CONTENT_SIZE", 1)
    monkeypatch.setattr(course_archive.shutil, "copyfileobj", lambda *args:
                        pytest.fail("Zu große Inhalte dürfen nicht kopiert werden."))
    with pytest.raises(ValueError, match="zu groß"):
        course_archive.build_course_archive(source, setup)


def test_wheel_changed_after_hashing_is_rejected_by_final_validation(archive_inputs, monkeypatch):
    source, setup, chapter, wheel, name, manifest = archive_inputs
    original = course_archive.shutil.copyfileobj

    def copy(source_file, destination):
        if Path(source_file.name) == chapter:
            wheel.write_bytes(b"changed during export")
        return original(source_file, destination)

    monkeypatch.setattr(course_archive.shutil, "copyfileobj", copy)
    with pytest.raises(ValueError, match="Prüfsumme"):
        course_archive.build_course_archive(source, setup, runtime_manifest=manifest, offline_wheels={name: wheel})
