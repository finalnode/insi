"""Komposition der Kursansichten innerhalb des NiceGUI-Workspace."""

import asyncio
from pathlib import Path

from .course_selection_view import render_course_selection
from insi.course import get_course_directory
from insi.course_studio_view import register_course_studio_page
from insi.examples_view import render_examples_view
from insi.extensions_view import render_extensions_view
from .layout import render_workspace_footer, render_workspace_header
from .overview_view import render_overview_panel
from insi.projects_view import render_projects_view
from .reference_views import (
    render_browser_playground_panel,
    render_cheatsheet_panel,
    render_pyxel_panel,
    render_script_panel,
)
from insi.script_api import register_script_api
from .setup_view import (
    inspect_setup_runtime,
    preferred_ide_label,
    render_setup_panel,
)
from .submission_view import render_submission_panel
from .tasks_view import render_tasks_panel
from insi.theme import configure_theme
from .tools_view import render_tools_panel


def register_workspace(context) -> None:
    """Registriere Seiten und UI der Lernumgebung im übergebenen App-Kontext."""
    ui = context.ui
    nicegui_app = context.app
    nicegui_run = context.run
    desktop = context.desktop
    register_script_api(nicegui_app)
    register_course_studio_page(
        ui, nicegui_app, nicegui_run, desktop=desktop
    )

    course_selection_state = context.course_selection

    @ui.page("/")
    def index() -> None:
        ide_open_buttons = []
        # Farben des OSZ KIM: kräftiges Orange, technisches Grau und Weiß.
        configure_theme(ui)

        if render_course_selection(context):
            return

        layout = render_workspace_header(ui, course_selection_state)
        update_badge = layout.update_badge
        header_setup = layout.course_setup
        current_student = layout.student_name
        tabs = layout.tabs
        (
                setup_tab,
                tools_tab,
                overview_tab,
                tasks_tab,
                examples_tab,
                projects_tab,
                extensions_tab,
                submission_tab,
                sheet_tab,
                script_tab,
                pyxel_tab,
                browser_tab,
        ) = layout.pages
        update_badge.on("click", lambda: tabs.set_value(tools_tab))

        lazy_views = {}
        project_refresh = {"callback": lambda: None}

        def refresh_projects() -> None:
            project_refresh["callback"]()

        def render_projects_panel() -> None:
            project_refresh["callback"] = render_projects_view(
                ui,
                nicegui_run,
                preferred_ide_label(),
                ide_open_buttons,
            )

        def lazy_panel(tab, renderer) -> None:
            with ui.tab_panel(tab):
                container = ui.column().classes("w-full gap-3")
                with container:
                    ui.label("Ansicht wird geladen …").classes("text-grey-7")
            lazy_views[tab.props["name"]] = {
                "container": container,
                "renderer": renderer,
                "loaded": False,
                "loading": False,
            }

        with ui.tab_panels(tabs, value=overview_tab).classes(
            "w-full max-w-6xl mx-auto mb-10"
        ).props("id=pykim-main role=main"):
            with ui.tab_panel(setup_tab):
                setup_panel = ui.column().classes("w-full gap-3")
                with setup_panel:
                    with ui.row().classes("items-center gap-2"):
                        ui.spinner(size="sm", color="primary")
                        ui.label("Setup wird im Hintergrund vorbereitet …")
            lazy_panel(
                tools_tab,
                lambda: render_tools_panel(
                    context,
                    update_badge,
                    header_setup,
                    tabs,
                    projects_tab,
                ),
            )
            with ui.tab_panel(overview_tab):
                refresh_overview = render_overview_panel(ui)
            lazy_panel(
                tasks_tab,
                lambda: render_tasks_panel(
                    ui,
                    nicegui_run,
                    ide_open_buttons,
                    refresh_overview,
                    preferred_ide_label,
                ),
            )
            lazy_panel(
                examples_tab,
                lambda: render_examples_view(
                    ui, preferred_ide_label(), ide_open_buttons
                ),
            )
            lazy_panel(projects_tab, render_projects_panel)
            lazy_panel(extensions_tab, lambda: render_extensions_view(ui))
            lazy_panel(
                submission_tab,
                lambda: render_submission_panel(
                    ui,
                    nicegui_app,
                    nicegui_run,
                    desktop=desktop,
                ),
            )
            lazy_panel(sheet_tab, lambda: render_cheatsheet_panel(ui))
            lazy_panel(script_tab, lambda: render_script_panel(ui))
            lazy_panel(
                pyxel_tab,
                lambda: render_pyxel_panel(
                    ui,
                    preferred_ide_label(),
                    ide_open_buttons,
                    on_project_saved=refresh_projects,
                ),
            )
            lazy_panel(
                browser_tab,
                lambda: render_browser_playground_panel(ui),
            )

        render_workspace_footer(ui)

        setup_state = {"task": None, "loaded": False, "loading": False}

        async def setup_snapshot():
            task = setup_state["task"]
            if task is None:
                course = get_course_directory() or Path.home() / "in-si-Kurs"
                task = asyncio.create_task(
                    nicegui_run.io_bound(inspect_setup_runtime, course)
                )
                setup_state["task"] = task
            snapshot = await task
            if snapshot is None:
                raise RuntimeError("Die Laufzeitprüfung wurde abgebrochen.")
            return snapshot

        async def preload_setup() -> None:
            try:
                await setup_snapshot()
            except Exception:
                setup_state["task"] = None

        async def load_setup(event) -> None:
            if event.value != setup_tab.props["name"]:
                return
            if setup_state["loaded"] or setup_state["loading"]:
                return
            setup_state["loading"] = True
            try:
                snapshot = await setup_snapshot()
                setup_panel.clear()
                with setup_panel:
                    render_setup_panel(
                        context,
                        ide_open_buttons,
                        current_student,
                        snapshot,
                    )
                setup_state["loaded"] = True
            except Exception as error:
                setup_state["task"] = None
                setup_panel.clear()
                with setup_panel:
                    ui.label(f"Setup konnte nicht geladen werden: {error}").classes(
                        "text-negative"
                    )
                    ui.button("Erneut versuchen", on_click=lambda: load_setup(event))
            finally:
                setup_state["loading"] = False

        async def load_lazy_view(event) -> None:
            view = lazy_views.get(event.value)
            if view is None or view["loaded"] or view["loading"]:
                return
            view["loading"] = True
            try:
                await ui.run_javascript(
                    "await new Promise(resolve => requestAnimationFrame(resolve))"
                )
            except TimeoutError:
                pass
            container = view["container"]
            container.clear()
            try:
                with container:
                    view["renderer"]()
                view["loaded"] = True
            except Exception as error:
                with container:
                    ui.label(f"Ansicht konnte nicht geladen werden: {error}").classes(
                        "text-negative"
                    )
            finally:
                view["loading"] = False

        tabs.on_value_change(load_setup)
        tabs.on_value_change(load_lazy_view)
        ui.timer(0.25, preload_setup, once=True)
