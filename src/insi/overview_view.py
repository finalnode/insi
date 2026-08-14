"""Übersichtsseite des aktuell ausgewählten Kurses."""

from .branding import APP_DISPLAY_NAME
from insi.course import get_course_directory
from insi.course_setup import course_setup_info
from insi.learning_view import render_overview


def render_overview_panel(ui):
    """Rendere die Übersicht und liefere ihre Aktualisierungsfunktion zurück."""
    container = ui.column().classes("w-full")

    def refresh() -> None:
        container.clear()
        with container:
            course = get_course_directory()
            if course is not None and course_setup_info(course) is not None:
                render_overview(ui)
            else:
                ui.label(APP_DISPLAY_NAME).classes("text-2xl font-bold")
                ui.label(
                    "Lege zuerst einen Kursordner an und importiere die "
                    ".pykim-setup-Datei deiner Lehrkraft. Danach erscheinen "
                    "hier Skript, Aufgaben und Lernstand."
                ).classes("text-grey-7")

    refresh()
    return refresh


__all__ = ["render_overview_panel"]
