"""Komposition der Kursansichten innerhalb des NiceGUI-Workspace."""

from .course_selection_view import render_course_selection
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
from .setup_view import preferred_ide_label, render_setup_panel
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

        with ui.tab_panels(tabs, value=overview_tab).classes(
            "w-full max-w-6xl mx-auto mb-10"
        ).props("id=pykim-main role=main"):
            with ui.tab_panel(setup_tab):
                render_setup_panel(context, ide_open_buttons, current_student)
            with ui.tab_panel(tools_tab):
                render_tools_panel(
                    context,
                    update_badge,
                    header_setup,
                    tabs,
                    projects_tab,
                )
            with ui.tab_panel(overview_tab):
                refresh_overview = render_overview_panel(ui)

            with ui.tab_panel(tasks_tab):
                render_tasks_panel(
                    ui,
                    nicegui_run,
                    ide_open_buttons,
                    refresh_overview,
                    preferred_ide_label,
                )
            with ui.tab_panel(examples_tab):
                render_examples_view(ui, preferred_ide_label(), ide_open_buttons)

            with ui.tab_panel(projects_tab):
                refresh_projects = render_projects_view(
                    ui, preferred_ide_label(), ide_open_buttons
                )

            with ui.tab_panel(extensions_tab):
                render_extensions_view(ui)

            with ui.tab_panel(submission_tab):
                render_submission_panel(
                    ui,
                    nicegui_app,
                    nicegui_run,
                    desktop=desktop,
                )
            with ui.tab_panel(sheet_tab):
                render_cheatsheet_panel(ui)
            with ui.tab_panel(script_tab):
                render_script_panel(ui)
            with ui.tab_panel(pyxel_tab):
                render_pyxel_panel(
                    ui,
                    preferred_ide_label(),
                    ide_open_buttons,
                    on_project_saved=refresh_projects,
                )
            with ui.tab_panel(browser_tab):
                render_browser_playground_panel(ui)

        render_workspace_footer(ui)
