"""Dateiaustausch bei Erfolg, Schreibfehlern und entfernten Datenträgern."""

import json

import pytest

from insi import file_storage


@pytest.mark.parametrize("content", ["Grüße\nzweite Zeile", b"\x00\xff\x01"])
def test_atomic_write_replaces_complete_file(tmp_path, content):
    target = tmp_path / "course" / "file"
    file_storage.atomic_write(target, content)
    read = target.read_bytes() if isinstance(content, bytes) else target.read_text(encoding="utf-8")
    assert read == content
    assert list(target.parent.iterdir()) == [target]


@pytest.mark.parametrize("failure", ["fsync", "replace"])
def test_failed_write_keeps_original_and_removes_temporary(tmp_path, monkeypatch, failure):
    target = tmp_path / "progress.json"
    target.write_text("original", encoding="utf-8")

    def fail(*args):
        raise OSError("Datenträger getrennt")

    monkeypatch.setattr(file_storage.os, failure, fail)
    with pytest.raises(OSError, match="Datenträger getrennt"):
        file_storage.atomic_write_json(target, {"answer": "neu"})
    assert target.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [target]


def test_json_serialization_failure_does_not_create_temporary(tmp_path):
    target = tmp_path / "metadata.json"
    file_storage.atomic_write_json(target, {"title": "Grüße"})
    with pytest.raises(TypeError):
        file_storage.atomic_write_json(target, {"invalid": object()})
    assert json.loads(target.read_text(encoding="utf-8")) == {"title": "Grüße"}
    assert list(tmp_path.iterdir()) == [target]


def test_temporary_name_does_not_extend_long_destination_name(tmp_path):
    target = tmp_path / ("x" * 245 + ".txt")
    file_storage.atomic_write(target, "Inhalt")
    assert target.read_text(encoding="utf-8") == "Inhalt"
