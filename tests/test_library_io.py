"""Gezielte Dokumentzugriffe ohne Änderungen an Auswahl und Reihenfolge."""

from pathlib import Path

import pytest

from insi import library


@pytest.fixture
def documents(tmp_path):
    files = {
        "imperativ/01/alpha.md": "# Erster Treffer\n\nText",
        "imperativ/02/alpha.md": "# Zweiter Treffer",
        "imperativ/zeta.md": "Ohne Überschrift",
        "oop/alpha.md": "# Anderer Lernweg",
        "oop/beta.md": "# Beta",
        "imperativ/_privat/hidden.md": "# Versteckt",
        "imperativ/_secret.md": "# Versteckt",
        "imperativ/README.md": "# Repository",
    }
    for name, content in files.items():
        path = tmp_path / "Material" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp_path


@pytest.fixture
def markdown_reads(monkeypatch):
    reads = []
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.suffix == ".md":
            reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    return reads


def test_single_task_reads_only_first_matching_document(documents, markdown_reads):
    selected = library.task_document("alpha", content_root=documents, assignments_path="Material")
    assert selected.title == "Erster Treffer"
    assert selected.paradigm == "imperativ"
    assert markdown_reads == [documents / "Material/imperativ/01/alpha.md"]

    selected.path.write_text("# Aktualisiert", encoding="utf-8")
    assert library.task_document(
        "alpha", content_root=documents, assignments_path="Material",
    ).title == "Aktualisiert"


@pytest.mark.parametrize("name", ["missing", "hidden", "_secret", "README"])
def test_missing_or_excluded_task_reads_no_markdown(documents, markdown_reads, name):
    assert library.task_document(name, content_root=documents, assignments_path="Material") is None
    assert markdown_reads == []


def test_task_names_preserve_order_and_duplicates_without_reading_contents(documents, markdown_reads, monkeypatch):
    (documents / "Material").rename(documents / "Aufgaben")
    monkeypatch.setattr("insi.updates.active_content_root", lambda fallback: documents)
    monkeypatch.setattr("insi.training.registry.trainable_names", lambda: (
        "alpha", "beta", "hidden", "_secret", "README", "missing",
    ))
    assert library.task_names() == ("alpha", "alpha", "alpha", "beta")
    assert markdown_reads == []


def test_full_documents_keep_filtering_sorting_and_title_fallback(documents, markdown_reads):
    result = library.task_documents("imperativ", content_root=documents, assignments_path="Material")
    assert [document.title for document in result] == ["Erster Treffer", "Zweiter Treffer", "Zeta"]
    assert markdown_reads == [document.path for document in result]
    with pytest.raises(ValueError, match="Programmierparadigma"):
        library.task_documents("unknown", content_root=documents)
