"""NiceGUI-Ansicht für die persönliche PyKIM-Werkzeugkiste."""

from .course import get_course_directory
from .extensions import MODULE_NAME, add_extension, list_extensions, update_extension


STARTER = '''def square(length):
    """Zeichne ein Quadrat mit der angegebenen Kantenlänge."""
    for _ in range(4):
        right(length)
        down(length)
'''


def render_extensions_view(ui) -> None:
    ui.label("Meine Erweiterungen").classes("text-2xl font-bold")
    ui.markdown(
        "Hier sammelst du eigene Funktionen und Klassen in einem gemeinsamen "
        "Modul namens `erweiterungen`."
    )
    course = get_course_directory()
    if course is None:
        ui.label("Richte zuerst einen Kursordner ein.").classes("text-orange")
        return

    content = ui.column().classes("w-full gap-3")

    def render() -> None:
        content.clear()
        snippets = list_extensions(course)
        with content:
            with ui.card().classes("w-full bg-orange-1 shadow-none"):
                ui.label("Alle Erweiterungen importieren").classes("font-bold")
                complete_import = f"from {MODULE_NAME} import *"
                ui.code(complete_import, language="python")
            if not snippets:
                ui.label("Deine Werkzeugkiste ist noch leer.").classes("text-grey-7")
            for snippet in snippets:
                with ui.expansion(
                    f"{snippet.name} · {snippet.kind}", icon="extension"
                ).classes("w-full"):
                    ui.label("Nur diese Erweiterung importieren").classes("font-bold")
                    ui.code(snippet.import_line, language="python")
                    editor = ui.codemirror(
                        value=snippet.source, language="Python", line_wrapping=False,
                    ).classes("w-full").style("height: 18rem")

                    def update(name=snippet.name, source_editor=editor) -> None:
                        try:
                            update_extension(course, name, source_editor.value)
                            ui.notify("Erweiterung aktualisiert.", type="positive")
                            render()
                        except (OSError, ValueError) as error:
                            ui.notify(str(error), type="negative")

                    ui.button("Aktualisieren", on_click=update, icon="save")

    with ui.card().classes("w-full"):
        ui.label("Funktion oder Klasse hinzufügen").classes("text-xl font-bold")
        editor = ui.codemirror(
            value=STARTER, language="Python", line_wrapping=False,
        ).classes("w-full").style("height: 18rem")

        def create() -> None:
            try:
                created = add_extension(course, editor.value)
                names = ", ".join(item.name for item in created)
                ui.notify(f"Hinzugefügt: {names}.", type="positive")
                render()
            except (OSError, ValueError) as error:
                ui.notify(str(error), type="negative")

        ui.button("Zur Werkzeugkiste hinzufügen", on_click=create, icon="add")
    render()


__all__ = ["render_extensions_view"]
