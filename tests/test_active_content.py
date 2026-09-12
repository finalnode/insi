"""Gemeinsame Inhaltsprüfung für Archiv-, Repository- und globale Aktivierung."""

import hashlib
import json

import pytest

from insi import updates


@pytest.fixture(params=["archive", "repository", "global"])
def active_version(request, tmp_path, monkeypatch):
    selected = {"version": "first"}
    base = tmp_path / "content"
    base.mkdir()
    marker = base / "active.json"
    monkeypatch.setattr(updates, "content_directory", lambda: base)
    monkeypatch.setattr(updates, "_VALIDATED_CONTENT_ROOTS", set())
    monkeypatch.setattr("insi.course.get_course_directory", lambda: tmp_path)
    monkeypatch.setattr("insi.course_setup.course_setup_info", lambda course:
                        None if request.param == "global" else object())
    monkeypatch.setattr("insi.course_storage.course_content_source", lambda course:
                        {"type": request.param, "content_version": selected["version"]})
    monkeypatch.setattr(updates, "_course_active_marker", lambda setup: marker)

    def activate(version):
        selected["version"] = version
        marker.write_text(json.dumps({"content_version": version}), encoding="utf-8")
        root = base / "versions" / version
        root.mkdir(parents=True, exist_ok=True)
        (root / "chapter.md").write_bytes(version.encode())
        (root / "content-manifest.json").write_text(json.dumps({
            "files": {"chapter.md": hashlib.sha256(version.encode()).hexdigest()},
        }), encoding="utf-8")
        return root

    return activate


def test_selection_changes_and_validates_each_root_once(active_version, tmp_path, monkeypatch):
    checked = []
    original = updates._validate_content

    def validate(root, manifest):
        checked.append(root)
        original(root, manifest)

    monkeypatch.setattr(updates, "_validate_content", validate)
    first = active_version("first")
    assert updates.active_content_root(tmp_path) == first
    assert updates.active_content_root(tmp_path) == first
    second = active_version("second")
    assert updates.active_content_root(tmp_path) == second
    assert checked == [first, second]


@pytest.mark.parametrize("damage", ["missing", "json", "shape", "hash"])
def test_invalid_content_falls_back_without_caching(active_version, tmp_path, damage):
    root = active_version("broken")
    manifest = root / "content-manifest.json"
    if damage == "missing":
        manifest.unlink()
    elif damage == "hash":
        (root / "chapter.md").write_text("beschädigt", encoding="utf-8")
    else:
        manifest.write_text("{" if damage == "json" else "[]", encoding="utf-8")
    assert updates.active_content_root(tmp_path) == tmp_path
    assert root not in updates._VALIDATED_CONTENT_ROOTS
    active_version("broken")
    assert updates.active_content_root(tmp_path) == root
