"""Architekturgrenzen des NiceGUI-Einstiegspunkts."""

import ast
from pathlib import Path

import pytest

from insi.context import (
    AppContext,
    CourseSelectionState,
    CourseSyncState,
)


PROJECT = Path(__file__).resolve().parents[1]
GUIDE = PROJECT / "src" / "insi"


def test_app_is_a_small_application_composer():
    source = (GUIDE / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    main = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )

    assert len(source.splitlines()) <= 150
    assert main.end_lineno - main.lineno <= 80


def test_heavy_workspace_is_imported_lazily_inside_main():
    tree = ast.parse((GUIDE / "app.py").read_text(encoding="utf-8"))
    top_level_modules = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    assert "register_workspace" not in top_level_modules


def test_workspace_only_composes_smaller_views():
    source = (GUIDE / "workspace_view.py").read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 300
    for view in (
        "render_course_selection",
        "render_setup_panel",
        "render_tools_panel",
        "render_overview_panel",
        "render_tasks_panel",
        "render_submission_panel",
    ):
        assert view in source


def test_app_context_owns_mutable_session_state():
    context = AppContext(object(), object(), object(), desktop=True)

    context.course_sync.update(result="ok", pending=True)
    context.course_selection.update(confirmed=True)

    assert context.course_sync == CourseSyncState(result="ok", pending=True)
    assert context.course_selection == CourseSelectionState(confirmed=True)


def test_context_state_rejects_unknown_compatibility_keys():
    with pytest.raises(KeyError):
        CourseSyncState().update(unknown=True)


def test_pykim_package_contains_no_insi_guide_namespace():
    import pykim

    assert not (Path(pykim.__file__).resolve().parent / "guide").exists()


def test_pykim_core_does_not_depend_on_insi_application():
    import pykim

    core = Path(pykim.__file__).resolve().parent
    offenders = []
    for path in core.rglob("*.py"):
        if "from insi" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(core).as_posix())

    assert offenders == []


def test_course_training_state_belongs_to_insi_instead_of_pykim():
    import pykim

    trainer = Path(pykim.__file__).resolve().parent / "trainer"
    application_modules = {
        "activities.py",
        "content.py",
        "feedback.py",
        "progress.py",
        "runner.py",
    }

    assert not application_modules.intersection(
        path.name for path in trainer.glob("*.py")
    )
    assert not (trainer / "exercises" / "__init__.py").exists()
