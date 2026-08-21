from pathlib import Path

import pytest

from insi.author_workspace import (
    compose_task_markdown,
    split_task_markdown,
)
from insi.markdown_editor import insert_course_annotation, validate_editor_markdown


def test_task_annotations_roundtrip_outside_the_visual_body():
    source = """# Datenbank planen
@difficulty:fortgeschritten
@tags: sqlite, modellierung
@hint: Beginne mit den Entitäten.
@source: SQLite-Dokumentation | https://sqlite.org/docs.html

Beschreibe dein Schema.

- Tabelle anlegen
"""

    parts = split_task_markdown(source)

    assert parts.title == "Datenbank planen"
    assert parts.body == "Beschreibe dein Schema.\n\n- Tabelle anlegen"
    assert parts.difficulty == "fortgeschritten"
    assert parts.hints == ("Beginne mit den Entitäten.",)
    assert parts.tags == ("sqlite", "modellierung")
    assert compose_task_markdown(parts) == source


def test_course_annotation_menu_only_inserts_known_templates():
    class Recorder:
        call = None

        def insert_text(self, text, *, markdown_mode=False):
            self.call = (text, markdown_mode)

    editor = Recorder()
    insert_course_annotation(editor, "run")
    assert editor.call == ("@button:run\n", True)

    with pytest.raises(ValueError, match="Unbekannte Kursannotation"):
        insert_course_annotation(editor, "python")


def test_toast_assets_and_licenses_are_packaged():
    root = Path(__file__).resolve().parents[1] / "src" / "insi" / "vendor" / "toastui_editor"
    assert (root / "toastui-editor-all.min.js").stat().st_size > 500_000
    assert "@license MIT" in (root / "toastui-editor-all.min.js").read_text(
        encoding="utf-8"
    )[:500]
    assert "MIT License" in (root / "LICENSE.txt").read_text(encoding="utf-8")
    assert "Apache License" in (root / "DOMPURIFY-LICENSE.txt").read_text(
        encoding="utf-8"
    )


def test_editor_disables_telemetry_and_loads_only_local_assets():
    source = (
        Path(__file__).resolve().parents[1] / "src" / "insi" / "markdown_editor.js"
    ).read_text(encoding="utf-8")

    assert 'import "toastui-editor-all"' in source
    assert 'import "de-de"' in source
    assert "usageStatistics: false" in source
    assert "https://" not in source


def test_course_plugin_uses_toast_toolbar_and_live_server_validation():
    source = (
        Path(__file__).resolve().parents[1] / "src" / "insi" / "markdown_editor.js"
    ).read_text(encoding="utf-8")

    assert "createCoursePlugin" in source
    assert 'name: "insiAnnotations"' in source
    assert 'name: "insiValidation"' in source
    assert 'this.$emit("validation"' in source
    assert "setValidation(payload)" in source
    assert "setSelection([line, 1]" in source
    assert "modeSettling" in source
    assert "getCurrentMode()" in source
    assert "beginModeSwitch()" in source
    assert "changeMode: mode => this.finishModeSwitch(mode)" in source
    assert "this.emitting = false" in source
    assert "if (!this.emitting || !this.editor || this.modeSettling) return" in source
    assert "emitCurrentValue(false)" in source
    assert ".insi-markdown-editor .toastui-editor-defaultUI-toolbar" in source
    assert "overflow-x: auto" in source
    assert ".toastui-editor-defaultUI {\n          overflow: hidden" in source
    assert "scrollbar-gutter: stable" in source
    assert "window.dispatchEvent(new Event(\"resize\"))" in source
    assert "document.body.appendChild(menu)" in source
    assert "if (this.annotationMenu) this.annotationMenu.remove()" in source
    assert "itemIndex: 0" in source


def test_global_code_actions_ignore_toast_prosemirror_dom():
    source = (
        Path(__file__).resolve().parents[1] / "src" / "insi" / "theme.py"
    ).read_text(encoding="utf-8")

    exclusion = "pre.closest('.toastui-editor-defaultUI, .ProseMirror')"
    assert exclusion in source
    assert source.index(exclusion) < source.index("pre.classList.add('pykim-copy-ready')")


def test_live_script_validation_uses_the_canonical_markedown_rules():
    issues = validate_editor_markdown(
        "# Beispiel\n\n@button:start\n```python\nprint('x')\n```\n",
        course_kind="script",
    )

    assert [(issue.line, issue.code) for issue in issues] == [(3, "button")]


def test_task_body_validation_reports_editor_local_line_numbers():
    issues = validate_editor_markdown(
        "Einleitung\n\n@block:Falsch\n```python\npass\n```\n",
        course_kind="task-body",
    )

    assert [(issue.line, issue.code) for issue in issues] == [(3, "block")]
