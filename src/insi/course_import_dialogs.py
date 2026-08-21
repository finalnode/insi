"""Gemeinsame Sicherheitsdialoge für externe Kursquellen."""

from .course_runtime import RUNTIME_TARGETS


def archive_runtime_details(bundle) -> tuple[str, ...]:
    """Fasse den installierbaren Runtime-Anteil eines Kurs-ZIPs verständlich zusammen."""
    runtime = bundle.runtime
    if runtime is None:
        return ()
    extras = tuple(
        requirement
        for requirement in runtime.requirements
        if requirement.split("==", 1)[0].casefold().replace("_", "-")
        not in {"pykim", "pyxel"}
    )
    details = [f"Vorgesehene Laufzeit: Python {runtime.python}"]
    if extras:
        details.append("Zusätzliche Pythonpakete: " + ", ".join(extras))
    if runtime.offline_targets:
        labels = ", ".join(
            RUNTIME_TARGETS[target].label for target in runtime.offline_targets
        )
        size = sum(len(data) for data in bundle.offline_wheels.values())
        details.append(
            f"Eingebettete Offlinepakete: {labels} · {size / (1024 * 1024):.1f} MB"
        )
    return tuple(details)


async def confirm_external_course_import(
    ui,
    course_name: str = "der ausgewählte Kurs",
    source: str = "",
    runtime_details: tuple[str, ...] = (),
) -> bool:
    """Hole vor dem Einrichten einer externen Kursquelle Zustimmung ein."""
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-xl"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("security", color="warning", size="md")
            ui.label("Externe Kursquelle importieren?").classes("text-xl font-bold")
        ui.label(course_name).classes("font-bold")
        if source:
            ui.label(source).classes("text-sm text-grey-7 break-all")
        if runtime_details:
            with ui.column().classes("w-full gap-1 rounded border p-3 bg-orange-1"):
                ui.label("Runtime des Kurses").classes("font-bold")
                for detail in runtime_details:
                    ui.label(detail).classes("text-sm")
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


__all__ = ["archive_runtime_details", "confirm_external_course_import"]
