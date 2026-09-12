"""Projektstände prüfen, ohne unnötig alte Metadaten oder ganze Dateien zu laden."""

import hashlib
from pathlib import Path

from insi import project_history as history
from insi.projects import create_project


def test_unchanged_project_only_reads_newest_snapshot_metadata(tmp_path, monkeypatch):
    project = create_project(tmp_path, "Versionen", kind="empty")
    for index in range(4):
        project.entrypoint.write_text(f"print({index})", encoding="utf-8")
        history.save_project_state(project.directory, tmp_path, f"Stand {index}")
    reads = []
    read_state = history._state_from_snapshot

    def counted_read(snapshot):
        reads.append(snapshot)
        return read_state(snapshot)

    monkeypatch.setattr(history, "_state_from_snapshot", counted_read)
    assert history.snapshot_project_if_changed(project.directory, tmp_path) is None
    assert len(reads) == 1


def test_changed_or_damaged_newest_snapshot_does_not_hide_valid_older_state(tmp_path):
    project = create_project(tmp_path, "Prüfsummen", kind="empty")
    first = history.save_project_state(project.directory, tmp_path, "Intakt")
    second = history.save_project_state(project.directory, tmp_path, "Manipuliert")
    (second.path / "main.py").write_text("manipuliert", encoding="utf-8")
    assert history.snapshot_project_if_changed(project.directory, tmp_path) is None
    assert first.path.is_dir()
    project.entrypoint.write_text("print('neu')", encoding="utf-8")
    assert history.snapshot_project_if_changed(project.directory, tmp_path) is not None


def test_project_hashes_do_not_load_whole_files(tmp_path, monkeypatch):
    content = b"\x00\xff" * 1_000_000
    (tmp_path / "resource.bin").write_bytes(content)

    def reject_full_read(*args, **kwargs):
        raise AssertionError("Projektdateien müssen blockweise gelesen werden.")

    monkeypatch.setattr(Path, "read_bytes", reject_full_read)
    assert history._state_files(tmp_path) == (
        history.ProjectStateFile("resource.bin", len(content), hashlib.sha256(content).hexdigest()),
    )
