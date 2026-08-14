"""Gemeinsame Sicherheitsdialoge für externe Kursquellen."""


async def confirm_external_course_import(
    ui,
    course_name: str = "der ausgewählte Kurs",
    source: str = "",
) -> bool:
    """Hole vor dem Einrichten einer externen Kursquelle Zustimmung ein."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-xl"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("security", color="warning", size="md")
            ui.label("Externe Kursquelle importieren?").classes("text-xl font-bold")
        ui.label(course_name).classes("font-bold")
        if source:
            ui.label(source).classes("text-sm text-grey-7 break-all")
        ui.label(
            "in:si prüft Struktur und Trainerdateien beim Import. "
            "Python-Programme aus Kursen laufen derzeit jedoch noch nicht "
            "auf jedem Betriebssystem in einer garantierten OS-Sandbox."
        )
        ui.label(
            "Erst beim späteren, bewussten Start eines Programms kann dessen "
            "Code mit deinen Benutzerrechten auf Dateien, Netzwerk oder "
            "weitere Systemfunktionen zugreifen. Importiere deshalb nur "
            "Kurse aus einer Quelle, der du vertraust."
        ).classes("text-warning")
        trust = ui.checkbox(
            "Ich vertraue der Quelle und möchte den Kurs importieren."
        )
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=lambda: dialog.submit(False)).props("flat")
            confirm_button = ui.button(
                "Kurs importieren",
                icon="download",
                on_click=lambda: dialog.submit(True),
            ).props("color=warning")
            confirm_button.disable()
        trust.on_value_change(
            lambda event: (
                confirm_button.enable() if event.value else confirm_button.disable()
            )
        )
    return bool(await dialog)


__all__ = ["confirm_external_course_import"]
