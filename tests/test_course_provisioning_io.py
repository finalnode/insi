"""Starterdateien mit höchstens einer Suche nach bestehenden Schülerdateien."""

from pathlib import Path
from types import SimpleNamespace

from insi.course import provision_course_exercises
from insi.training.contracts import StarterFile


def test_starters_reuse_one_lazy_index_and_preserve_existing_files(tmp_path, monkeypatch):
    names = ("one", "two", "existing", "nested")
    monkeypatch.setattr("insi.training.registry.exercise_names", lambda: names)
    monkeypatch.setattr("insi.library.task_documents", lambda paradigm: [
        SimpleNamespace(name=name) for name in names
    ] if paradigm == "imperativ" else [])
    monkeypatch.setattr("insi.training.registry.exercise_starter_files", lambda name: (
        StarterFile("package/main.py" if name == "nested" else f"{name}.py", f"new {name}"),
    ))
    old = tmp_path / "old"
    old.mkdir()
    (old / "one.py").write_text("student one", encoding="utf-8")
    (old / "two.py").write_text("student two", encoding="utf-8")
    (old / "main.py").write_text("unrelated", encoding="utf-8")
    target = tmp_path / "Aufgaben" / "imperativ"
    target.mkdir(parents=True)
    (target / "existing.py").write_text("keep", encoding="utf-8")
    searches = []
    rglob = Path.rglob

    def counted_search(path, pattern):
        searches.append((path, pattern))
        return rglob(path, pattern)

    monkeypatch.setattr(Path, "rglob", counted_search)
    result = provision_course_exercises(tmp_path)
    assert searches == [(tmp_path, "*")]
    assert len(result["created"]) == 3
    assert (target / "one.py").read_text(encoding="utf-8") == "student one"
    assert (target / "two.py").read_text(encoding="utf-8") == "student two"
    assert (target / "existing.py").read_text(encoding="utf-8") == "keep"
    assert (target / "package/main.py").read_text(encoding="utf-8") == "new nested"
    searches.clear()
    assert provision_course_exercises(tmp_path)["created"] == []
    assert searches == []
