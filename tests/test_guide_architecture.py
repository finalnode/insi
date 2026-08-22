"""Architekturgrenzen des NiceGUI-Einstiegspunkts."""

import ast
from pathlib import Path
import subprocess
import sys

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


def test_guide_test_collection_no_longer_owns_every_domain():
    source = (PROJECT / "tests" / "test_guide.py").read_text(encoding="utf-8")
    runtime_tools = (PROJECT / "tests" / "test_runtime_tools.py").read_text(
        encoding="utf-8"
    )

    assert len(source.splitlines()) <= 2000
    assert len(runtime_tools.splitlines()) <= 750
    assert (PROJECT / "tests" / "test_progress.py").is_file()
    assert (PROJECT / "tests" / "test_projects.py").is_file()


def test_heavy_views_are_imported_lazily_inside_main():
    tree = ast.parse((GUIDE / "app.py").read_text(encoding="utf-8"))
    top_level_names = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    top_level_modules = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    }

    assert "register_workspace" not in top_level_names
    assert "workspace_view" not in top_level_modules
    assert "course_selection_view" not in top_level_modules


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


def test_inactive_workspace_views_are_rendered_only_on_first_selection():
    source = (GUIDE / "workspace_view.py").read_text(encoding="utf-8")

    assert "async def load_lazy_view" in source
    assert "tabs.on_value_change(load_lazy_view)" in source
    assert '"loaded": False' in source
    assert "with ui.tab_panel(tasks_tab):" not in source
    assert "with ui.tab_panel(projects_tab):" not in source


def test_tasks_reuse_one_progress_snapshot_for_initial_render():
    source = (GUIDE / "tasks_view.py").read_text(encoding="utf-8")

    assert source.count("load_progress()") == 1
    assert "progress=progress" in source
    assert "cached_progress=progress" in source


def test_setup_runtime_is_preloaded_off_the_ui_thread_and_rendered_lazily():
    workspace = (GUIDE / "workspace_view.py").read_text(encoding="utf-8")
    setup = (GUIDE / "setup_view.py").read_text(encoding="utf-8")

    assert "nicegui_run.io_bound(inspect_setup_runtime, course)" in workspace
    assert "ui.timer(0.25, preload_setup, once=True)" in workspace
    assert workspace.count("render_setup_panel(") == 1
    assert workspace.index("async def load_setup") < workspace.index(
        "render_setup_panel("
    )
    inspection = setup.split("def inspect_setup_runtime", 1)[1].split(
        "def preferred_ide_label", 1
    )[0]
    assert "ui." not in inspection


def test_setup_view_stays_bounded_and_uses_generic_runtime_language():
    source = (GUIDE / "setup_view.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    render = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "render_setup_panel"
    )

    assert len(source.splitlines()) <= 750
    assert render.end_lineno - render.lineno + 1 <= 630
    assert "PyKIM-Laufzeit" not in source
    assert "PyKIM-Kursumgebung" not in source


def test_course_selection_has_no_artificial_open_delay_or_duplicate_scan():
    source = (GUIDE / "course_selection_view.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    render = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "render_course_selection"
    )

    assert len(source.splitlines()) <= 680
    assert render.end_lineno - render.lineno + 1 <= 630
    assert "asyncio.sleep" not in source
    assert source.count("get_course_directories()") == 1
    assert "pykim-course-pixel-field" not in source


def test_course_builder_core_has_no_second_parallel_page():
    """Die Kurswerkstatt besitzt genau eine UI; Exportlogik bleibt UI-frei."""
    builder = (GUIDE / "course_builder_view.py").read_text(encoding="utf-8")
    workspace = (GUIDE / "workspace_view.py").read_text(encoding="utf-8")

    assert len(builder.splitlines()) <= 350
    assert "register_course_builder_page" not in builder
    assert "register_course_studio_page" in workspace


def test_course_studio_view_stays_bounded():
    studio = (GUIDE / "course_studio_view.py").read_text(encoding="utf-8")

    assert len(studio.splitlines()) <= 850
    assert 'state = {"selection": None}' not in studio


def test_author_tools_link_to_the_canonical_course_studio():
    source = (GUIDE / "author_view.py").read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 100
    assert 'ui.navigate.to("/course-builder")' in source
    assert "generate_exercise_source" not in source


def test_project_ui_keeps_history_and_editing_responsibilities_separate():
    projects = (GUIDE / "projects_view.py").read_text(encoding="utf-8")
    history = (GUIDE / "project_history_view.py").read_text(encoding="utf-8")
    model = (GUIDE / "project_history.py").read_text(encoding="utf-8")

    assert len(projects.splitlines()) <= 350
    assert len(history.splitlines()) <= 250
    assert len(model.splitlines()) <= 400
    assert "restore_project_state" not in projects
    assert "nicegui" not in model.casefold()


def test_data_migrations_stay_ui_free_and_bounded():
    migrations = (GUIDE / "data_migrations.py").read_text(encoding="utf-8")

    assert len(migrations.splitlines()) <= 260
    assert "nicegui" not in migrations.casefold()
    assert "from .course" not in migrations
    assert "from .progress" not in migrations


def test_theme_loader_and_browser_assets_stay_bounded():
    theme = (GUIDE / "theme.py").read_text(encoding="utf-8")
    assets = GUIDE / "assets"

    assert len(theme.splitlines()) <= 60
    assert "ui.add_head_html(r\"\"\"" not in theme
    assert len((assets / "theme.css").read_text(encoding="utf-8").splitlines()) <= 500
    for script in assets.glob("theme_*.js"):
        assert len(script.read_text(encoding="utf-8").splitlines()) <= 250, script.name


def test_tools_view_does_not_schedule_automatic_network_checks():
    source = (GUIDE / "tools_view.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    render = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "render_tools_panel"
    )
    automatic_network_timers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "timer"
        and any(
            isinstance(argument, ast.Name)
            and argument.id in {"refresh_updates", "refresh_course_content"}
            for argument in node.args
        )
    ]

    assert automatic_network_timers == []
    assert len(source.splitlines()) <= 380
    assert render.end_lineno - render.lineno + 1 <= 350
    assert source.count("system_status()") == 1
    assert "ui.dialog()" not in source


def test_update_badge_navigates_to_the_single_tools_update_view():
    workspace = (GUIDE / "workspace_view.py").read_text(encoding="utf-8")

    assert 'update_badge.on("click", lambda: tabs.set_value(tools_tab))' in workspace


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


def test_generic_core_paths_do_not_import_pykim_modules():
    for relative in (
        "author_view.py",
        "author_workspace.py",
        "course_builder_view.py",
        "course_studio_view.py",
        "submission/fingerprints.py",
        "system.py",
        "submission/export.py",
        "training/registry.py",
    ):
        tree = ast.parse((GUIDE / relative).read_text(encoding="utf-8"))
        imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and (
                (isinstance(node, ast.ImportFrom) and (node.module or "").startswith("pykim"))
                or (
                    isinstance(node, ast.Import)
                    and any(alias.name.startswith("pykim") for alias in node.names)
                )
            )
        ]
        assert imports == [], relative


def test_neutral_training_registry_does_not_eagerly_import_pykim():
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, {str(GUIDE.parent)!r}); "
            "import insi.training.registry; "
            "raise SystemExit('pykim' in sys.modules)",
        ],
        cwd=PROJECT,
    )

    assert probe.returncode == 0


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
