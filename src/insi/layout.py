"""Gemeinsamer Seitenrahmen der in:si-Lernumgebung."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import __version__
from .branding import APP_DISPLAY_NAME
from insi.course import get_course_directory, get_student_name
from insi.course_setup import course_setup_info
from insi.navigation import create_navigation
from insi.system import open_path, system_user_name
from .desktop import browser_favicon
from .sources import source_references


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    """UI-Elemente und Werte, die nach dem Aufbau des Headers benötigt werden."""

    tabs: Any
    pages: tuple[Any, ...]
    update_badge: Any
    course_setup: Any
    student_name: str


def render_workspace_header(ui, course_selection) -> WorkspaceLayout:
    """Erzeuge Kopfzeile und Hauptnavigation und liefere deren Bindungen zurück."""
    ui.link("Zum Hauptinhalt springen", "#pykim-main").classes("pykim-skip-link")
    configured = get_course_directory()
    course_setup = None
    if configured is not None:
        try:
            course_setup = course_setup_info(configured)
        except (OSError, ValueError):
            course_setup = None
    student_name = get_student_name(configured) or system_user_name()

    with ui.header().classes("pykim-header"):
        with ui.row().classes("pykim-header-top w-full items-center no-wrap"):
            ui.image(browser_favicon()).classes("insi-header-logo").props(
                f'alt="{APP_DISPLAY_NAME}"'
            )
            if course_setup is not None:
                ui.label(course_setup.course).classes("insi-course-title")
            ui.space()
            ui.label(f"Hallo, {student_name}").classes("text-sm")
            update_badge = ui.badge("Updates werden geprüft …", color="grey")
            update_badge.classes("cursor-pointer").props(
                "title='Verfügbare Updates anzeigen' role=button tabindex=0"
            )
            ui.button(
                "Kurs wechseln",
                on_click=lambda: (
                    course_selection.update(confirmed=False),
                    ui.navigate.reload(),
                ),
                icon="swap_horiz",
            ).props("flat dense color=white")
        tabs, pages = create_navigation(ui)

    return WorkspaceLayout(
        tabs=tabs,
        pages=pages,
        update_badge=update_badge,
        course_setup=course_setup,
        student_name=student_name,
    )


def render_workspace_footer(ui) -> None:
    """Erzeuge den stabilen Footer unabhängig von den fachlichen Views."""
    configured = get_course_directory()

    def open_course_directory() -> None:
        if configured is None:
            return
        try:
            open_path(configured)
        except (OSError, RuntimeError) as error:
            ui.notify(f"Kursordner konnte nicht geöffnet werden: {error}", type="negative")

    display_path = ""
    if configured is not None:
        try:
            display_path = f"~/{configured.relative_to(configured.home())}"
        except ValueError:
            display_path = str(configured)

    try:
        setup = course_setup_info(configured) if configured is not None else None
    except (OSError, ValueError):
        setup = None
    references = source_references(setup)

    with ui.dialog() as sources_dialog, ui.card().classes("w-full max-w-2xl"):
        with ui.row().classes("w-full items-center gap-2"):
            ui.icon("source", color="primary", size="md")
            ui.label("Quellen, Lizenzen und Verantwortung").classes(
                "text-xl font-bold"
            )
        if setup is not None:
            with ui.column().classes("w-full gap-0"):
                ui.label(f"Kurs: {setup.course}").classes("font-bold")
                ui.label(f"Verantwortlich: {setup.teacher}")
                if setup.school:
                    ui.label(f"Organisation: {setup.school}")
        ui.separator()
        with ui.column().classes("w-full gap-2"):
            for reference in references:
                with ui.row().classes("w-full items-center gap-2 no-wrap"):
                    ui.icon(
                        "license" if reference.kind == "license" else "open_in_new",
                        size="xs",
                    ).classes("text-grey-7")
                    if reference.url:
                        ui.link(
                            reference.label, reference.url, new_tab=True
                        ).classes("text-primary break-all")
                    else:
                        ui.label(reference.label)
        ui.label(
            "Aufgabenspezifische Quellen erscheinen zusätzlich direkt bei der Aufgabe."
        ).classes("text-sm text-grey-7")
        with ui.row().classes("w-full justify-end"):
            ui.button("Schließen", on_click=sources_dialog.close).props("flat")

    with ui.element("footer").classes("pykim-footer w-full"):
        with ui.row().classes(
            "w-full max-w-screen-2xl mx-auto items-center justify-between gap-3 no-wrap"
        ):
            ui.label("Concept by human. Crafted by human + AI.").classes(
                "pykim-footer-claim"
            )
            if configured is not None:
                ui.button(
                    display_path,
                    icon="folder_open",
                    on_click=open_course_directory,
                ).props(
                    f'flat dense color=white title="Kursordner öffnen: {configured}"'
                ).classes("insi-footer-course-path")
            with ui.row().classes("items-center gap-4"):
                ui.label(f"Version {__version__}").classes(
                    "pykim-footer-version"
                )
                ui.button(
                    "Quellen",
                    icon="source",
                    on_click=sources_dialog.open,
                ).props("flat dense color=white").classes("pykim-footer-link")


__all__ = ["WorkspaceLayout", "render_workspace_footer", "render_workspace_header"]
