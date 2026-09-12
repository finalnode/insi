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
from .documentation import documentation_text
from .legal import legal_document_text
from .sources import source_references


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    """UI-Elemente und Werte, die nach dem Aufbau des Headers benötigt werden."""

    tabs: Any
    pages: tuple[Any, ...]
    update_badge: Any
    course_setup: Any
    student_name: str


def _configure_course_path_button(button, course: str) -> None:
    """Setze dynamische Pfadtexte ohne Auswertung als Python-Literal."""
    button.props("flat dense color=white")
    button.props["title"] = f"Kursordner öffnen: {course}"


def render_workspace_header(ui, course_selection) -> WorkspaceLayout:
    """Erzeuge Kopfzeile und Hauptnavigation und liefere deren Bindungen zurück."""
    ui.link("Zum Hauptinhalt springen", "#pykim-main").classes(
        "fixed left-4 -top-20 z-[9999] px-4 py-2 rounded-md "
        "bg-grey-10 text-white focus:top-4"
    )
    configured = get_course_directory()
    course_setup = None
    if configured is not None:
        try:
            course_setup = course_setup_info(configured)
        except (OSError, ValueError):
            course_setup = None
    student_name = get_student_name(configured) or system_user_name()

    with ui.header().classes(
        "column items-stretch q-pa-none bg-white text-dark shadow-2"
    ):
        with ui.row().classes(
            "w-full min-h-[3.25rem] items-center no-wrap q-px-md q-py-sm "
            "q-ma-none bg-primary text-white"
        ):
            ui.image(browser_favicon()).classes(
                "flex-none w-[2.35rem] h-[2.35rem] rounded-lg drop-shadow-sm"
            ).props(
                f'alt="{APP_DISPLAY_NAME}"'
            )
            if course_setup is not None:
                ui.label(course_setup.course).classes(
                    "flex items-center min-w-0 ml-3 overflow-hidden text-white/90 "
                    "text-base font-medium leading-tight truncate"
                )
            ui.space()
            ui.label(f"Hallo, {student_name}").classes("text-sm")
            update_badge = ui.badge("Updates prüfen", color="grey")
            update_badge.classes("cursor-pointer").props(
                "title='Updates manuell über GitHub prüfen' role=button tabindex=0"
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

    def text_dialog(title, icon, reader, documents):
        """Lade Hilfs- und Lizenztexte erst beim Öffnen und behalte den Dialog."""
        with ui.dialog() as dialog, ui.card().classes(
            "w-full max-w-5xl max-h-[min(90vh,58rem)]"
        ):
            with ui.row().classes("w-full items-center gap-2"):
                ui.icon(icon, color="primary", size="md")
                ui.label(title).classes("text-xl font-bold")
            content = ui.column().classes("w-full")
            with ui.row().classes("w-full justify-end"):
                ui.button("Schließen", on_click=dialog.close).props("flat")
        loaded = False

        def open_dialog():
            nonlocal loaded
            if not loaded:
                content.clear()
                with content:
                    try:
                        texts = {key: reader(key) for key, _, _ in documents}
                    except (OSError, ValueError) as error:
                        ui.label(str(error)).classes("text-negative")
                    else:
                        with ui.tabs().classes("w-full") as tabs:
                            pages = [ui.tab(label) for _, label, _ in documents]
                        with ui.tab_panels(tabs, value=pages[0], animated=False).classes(
                            "w-full min-h-[28rem] max-h-[68vh] overflow-y-auto"
                        ):
                            for (key, _, plain), page in zip(documents, pages):
                                with ui.tab_panel(page):
                                    if plain:
                                        ui.textarea(value=texts[key]).props(
                                            "readonly outlined rows=22"
                                        ).classes("w-full insi-license-text")
                                    else:
                                        ui.markdown(texts[key]).classes("prose max-w-none")
                        loaded = True
            dialog.open()

        return open_dialog

    open_documentation = text_dialog(
        "Dokumentation · Documentation", "menu_book", documentation_text,
        (("de", "Deutsch", False), ("en", "English", False)),
    )
    open_legal = text_dialog(
        "Lizenz und rechtliche Hinweise", "gavel", legal_document_text,
        (("agpl", "AGPL-3.0+", True), ("scope", "Lizenzumfang", False),
         ("third-party", "Drittanbieter", False)),
    )

    sources_dialog = None

    def open_sources():
        nonlocal sources_dialog
        if get_course_directory() != configured:
            ui.notify("Der Kurs wurde gewechselt. Öffne die Kursansicht erneut.", type="warning")
            return
        if sources_dialog is None:
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
                with ui.column().classes("w-full gap-1"):
                    ui.label("Copyright © 2026 in:si contributors").classes("font-bold")
                    ui.label(
                        "in:si ist freie Software unter AGPL-3.0-or-later. "
                        "Weitergabe und Änderungen sind nach den Lizenzbedingungen "
                        "erlaubt; die Software kommt ohne Gewährleistung."
                    ).classes("text-sm text-grey-8")
                    ui.button(
                        "Lizenztexte offline lesen",
                        icon="gavel",
                        on_click=open_legal,
                    ).props("outline dense")
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
        sources_dialog.open()

    with ui.element("footer").classes(
        "fixed inset-x-0 bottom-0 z-[2000] w-full min-h-7 q-px-md q-py-xs "
        "bg-grey-8 text-grey-2 border-t-2 border-[#f36b2b] shadow-up-2"
    ):
        with ui.row().classes(
            "w-full max-w-screen-2xl mx-auto items-center justify-between gap-3 no-wrap"
        ):
            ui.label("Concept by human. Crafted by human + AI.").classes(
                "text-grey-2 text-xs tracking-wide"
            )
            if configured is not None:
                course_path_button = ui.button(
                    display_path,
                    icon="folder_open",
                    on_click=open_course_directory,
                ).classes("insi-footer-course-path")
                _configure_course_path_button(course_path_button, str(configured))
            with ui.row().classes("items-center gap-2 no-wrap"):
                ui.label(f"Version {__version__}").classes("text-grey-4 text-xs")
                ui.button(
                    "Hilfe",
                    icon="menu_book",
                    on_click=open_documentation,
                ).props("flat dense color=white").classes("pykim-footer-link")
                ui.button(
                    "Quellen",
                    icon="source",
                    on_click=open_sources,
                ).props("flat dense color=white").classes("pykim-footer-link")


__all__ = ["WorkspaceLayout", "render_workspace_footer", "render_workspace_header"]
