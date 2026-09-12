"""Verständliche Oberfläche für Export und Entfernen lokaler Daten."""

from .local_data import (
    create_local_data_export,
    local_data_roots,
    trash_all_local_data,
)
from .system import open_path


DELETE_CONFIRMATION = "ALLE LOKALEN DATEN"


def render_local_data_management(context) -> None:
    """Rendere einen expliziten Export- und Papierkorbablauf."""
    ui = context.ui
    app_data, courses = local_data_roots()

    ui.separator()
    ui.label("Meine lokalen Daten").classes("text-xl font-bold")
    ui.label(
        f"Erfasst sind {len(courses)} registrierte Kursordner sowie Einstellungen, "
        "globale Dateien und lokale App-Daten."
    ).classes("text-sm text-grey-7")
    ui.label(str(app_data)).classes("text-xs text-grey-7")
    export_status = ui.label("").classes("text-sm")
    export_button = ui.button("Datenexport erstellen", icon="archive")

    async def export_local_data() -> None:
        export_button.disable()
        export_status.text = "Datenexport wird erstellt …"
        try:
            report = await context.run.io_bound(create_local_data_export)
        except (OSError, RuntimeError, ValueError) as error:
            export_status.text = "Datenexport fehlgeschlagen."
            ui.notify(f"Datenexport fehlgeschlagen: {error}", type="negative")
            return
        finally:
            export_button.enable()
        export_status.text = (
            f"{report.files} Dateien aus {report.courses} Kursen "
            f"({report.bytes / (1024 * 1024):.1f} MiB): {report.path}"
        )
        warnings = len(report.skipped_symlinks) + len(report.missing_courses)
        if warnings:
            ui.notify(
                f"{warnings} nicht erreichbare oder verknüpfte Pfade wurden "
                "aus Sicherheitsgründen ausgelassen.",
                type="warning",
            )
        ui.notify("Lokaler Datenexport wurde erstellt.", type="positive")
        try:
            open_path(report.path.parent)
        except (OSError, RuntimeError):
            ui.notify("Der Exportordner konnte nicht automatisch geöffnet werden.")

    export_button.on("click", export_local_data)
    ui.label(
        "Persönliche Kursarbeit und Einstellungen werden exportiert; erneut "
        "ladbare Inhalte und Runtimes nicht."
    ).classes("text-xs text-grey-7")

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl"):
        ui.label("Alle lokalen Daten in den Papierkorb?").classes(
            "text-xl font-bold text-negative"
        )
        ui.label(
            "Alle erreichbaren registrierten Kurse und der vollständige lokale "
            "App-Datenordner werden verschoben – einschließlich Lösungen, Projekte, "
            "Lernstände, Backups, globale Dateien, Caches, Runtimes und IDE-Profil."
        )
        ui.label(
            "Exporte und Kopien an anderen Orten bleiben bestehen. Schließe vorher "
            "externe IDEs; mehrere Datenträger bilden keine gemeinsame Transaktion."
        ).classes("text-sm text-grey-7")
        ui.label(f"Gib exakt „{DELETE_CONFIRMATION}“ ein.").classes(
            "text-negative font-bold"
        )
        confirmation = ui.input("Bestätigung").classes("w-full")

        async def delete_local_data() -> None:
            delete_button.disable()
            try:
                report = await context.run.io_bound(trash_all_local_data)
            except (OSError, RuntimeError, ValueError) as error:
                ui.notify(
                    f"Lokale Daten nicht vollständig verschoben: {error}",
                    type="negative",
                )
                delete_button.enable()
                return
            context.course_selection.update(confirmed=False)
            dialog.close()
            ui.notify(
                f"{len(report.trashed)} Datenordner liegen jetzt im Systempapierkorb.",
                type="positive",
            )
            if report.missing_courses:
                ui.notify(
                    f"{len(report.missing_courses)} nicht erreichbare Kursordner "
                    "konnten nicht verschoben werden.",
                    type="warning",
                )
            ui.navigate.reload()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Abbrechen", on_click=dialog.close).props("flat")
            delete_button = ui.button(
                "Alle Daten in Papierkorb",
                icon="delete_forever",
                on_click=delete_local_data,
            ).props("color=negative")
            delete_button.disable()
        confirmation.on_value_change(
            lambda event: (
                delete_button.enable()
                if event.value == DELETE_CONFIRMATION
                else delete_button.disable()
            )
        )

    ui.button(
        "Lokale Daten entfernen",
        icon="delete_outline",
        on_click=dialog.open,
    ).props("outline color=negative")
