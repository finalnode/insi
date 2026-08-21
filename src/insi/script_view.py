"""Kapitelansicht des dateibasierten PyKIM-Skripts."""

from .library import PARADIGMS, render_script_markdown, script_chapters


def render_script_reader(ui) -> None:
    """Zeige ein dauerhaftes Inhaltsmenü und genau ein Kapitel gleichzeitig."""
    from .course import get_course_directory
    from .course_setup import course_setup_info

    course = get_course_directory()
    if course is None or course_setup_info(course) is None:
        ui.label("PyKIM-Skript").classes("text-2xl font-bold")
        ui.label(
            "Noch kein Kurs eingerichtet. Importiere im Setup die "
            ".insi-setup-Datei deiner Lehrkraft."
        ).classes("text-grey-7")
        return
    chapters = tuple(
        chapter
        for paradigm in PARADIGMS
        for chapter in script_chapters(paradigm)
    )
    if not chapters:
        ui.label("Es wurden noch keine Skriptkapitel gefunden.").classes("text-warning")
        return

    ui.label("PyKIM-Skript").classes("text-2xl font-bold")
    ui.label(
        "Wähle links ein Kapitel. Mit Zurück und Weiter kannst du das Skript "
        "in seiner vorgesehenen Reihenfolge durcharbeiten."
    ).classes("text-grey-7")

    with ui.element("div").classes("pykim-script-layout w-full items-start"):
        menu = ui.card().classes("pykim-script-menu shadow-none")
        content = ui.column().classes("pykim-script-page w-full min-w-0")

    menu_buttons = []

    def show_chapter(index: int) -> None:
        chapter = chapters[index]
        for button_index, button in enumerate(menu_buttons):
            selected = button_index == index
            button.props(f"color={'primary' if selected else 'grey-8'}")
            button.props(f"aria-current={'page' if selected else 'false'}")
        content.clear()
        with content:
            with ui.row().classes("w-full items-center"):
                ui.badge(
                    "IMPERATIV" if chapter.paradigm == "imperativ" else "OOP",
                    color="primary" if chapter.paradigm == "imperativ" else "secondary",
                )
                ui.label(f"Kapitel {index + 1} von {len(chapters)}").classes("text-grey-7")
            ui.markdown(render_script_markdown(chapter.content)).classes(
                "pykim-chapter-markdown w-full"
            )
            ui.separator()
            with ui.row().classes("w-full items-center"):
                if index > 0:
                    ui.button(
                        f"Zurück: {chapters[index - 1].title}",
                        on_click=lambda previous=index - 1: show_chapter(previous),
                        icon="arrow_back",
                    ).props("outline no-caps")
                ui.space()
                if index + 1 < len(chapters):
                    ui.button(
                        f"Weiter: {chapters[index + 1].title}",
                        on_click=lambda following=index + 1: show_chapter(following),
                        icon="arrow_forward",
                    ).props("no-caps icon-right")

    with menu:
        ui.label("Inhaltsverzeichnis").classes("text-lg font-bold").props(
            "role=heading aria-level=2"
        )
        for paradigm in PARADIGMS:
            ui.label(
                "Imperativer Lernweg" if paradigm == "imperativ"
                else "Objektorientierter Lernweg"
            ).classes("font-bold text-primary mt-2")
            for index, chapter in enumerate(chapters):
                if chapter.paradigm != paradigm:
                    continue
                button = ui.button(
                    chapter.title,
                    on_click=lambda chapter_index=index: show_chapter(chapter_index),
                ).props("flat no-caps align=left color=grey-8").classes(
                    "pykim-script-menu-button w-full"
                )
                menu_buttons.append(button)

    show_chapter(0)
