"""Einmaliges Laden und atomarer Austausch der Aufgabenmetadaten."""

from pathlib import Path

import pytest

from insi import assignments


def test_refresh_reads_each_markdown_once_and_keeps_dictionary(tmp_path, monkeypatch):
    root = tmp_path / "Material" / "imperativ"
    root.mkdir(parents=True)
    for name in ("eins", "zwei", "drei"):
        (root / f"{name}.md").write_text(f"# {name}\n\nBeschreibung {name}", encoding="utf-8")
    duplicate = tmp_path / "Material" / "oop" / "eins.md"
    duplicate.parent.mkdir()
    duplicate.write_text("# Anderer Lernweg", encoding="utf-8")
    monkeypatch.setattr(assignments, "trainable_names", lambda: ("eins", "zwei", "drei"))
    reads = []
    read_text = Path.read_text

    def counted_read(path, *args, **kwargs):
        reads.append(path)
        return read_text(path, *args, **kwargs)

    original = assignments.ASSIGNMENTS
    monkeypatch.setattr(Path, "read_text", counted_read)
    assert assignments.refresh_assignments(tmp_path, "Material") == ("drei", "eins", "zwei")
    assert assignments.ASSIGNMENTS is original
    assert len(reads) == 4
    assert len(set(reads)) == 4
    assert assignments.get_assignment("eins").summary == "Beschreibung eins"
    (root / "eins.md").write_text("# eins\n\nGeändert", encoding="utf-8")
    assignments.refresh_assignments(tmp_path, "Material")
    assert assignments.get_assignment("eins").summary == "Geändert"


def test_missing_assignment_keeps_previous_registry(tmp_path, monkeypatch):
    previous = assignments.ASSIGNMENTS.copy()
    monkeypatch.setattr(assignments, "trainable_names", lambda: ("fehlt",))
    with pytest.raises(ValueError, match="fehlt"):
        assignments.refresh_assignments(tmp_path)
    assert assignments.ASSIGNMENTS == previous
