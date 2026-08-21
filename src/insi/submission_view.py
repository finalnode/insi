"""Optionale verschlüsselte Abgabeansicht."""

from pathlib import Path

from insi.submission.export import (
    course_certificate_info,
    create_encrypted_submission,
    install_course_certificate,
)

from insi.course import get_course_directory
from insi.system import open_path


def render_submission_panel(ui, nicegui_app, nicegui_run, *, desktop: bool) -> None:
    """Rendere Zertifikatsimport und verschlüsselten Lernstandexport."""
    ui.label("Verschlüsselte Moodle-Abgabe").classes("text-2xl font-bold")
    ui.markdown(
        "Moodle dient nur zum Hochladen der erzeugten Datei. Die Suite "
        "überträgt selbst keine Daten. Nur die Lehrkraft mit dem privaten "
        "Schlüssel kann den Export lesen."
    )
    submission_course = get_course_directory()
    if submission_course is None:
        ui.label("Richte zuerst im Setup einen Kursordner ein.").classes(
            "text-orange"
        )
    else:
        ui.label("1. Zertifikat der Lehrkraft").classes("text-xl font-bold")
        certificate_container = ui.column().classes("w-full gap-1")

        def render_certificate() -> None:
            certificate_container.clear()
            with certificate_container:
                try:
                    info = course_certificate_info(submission_course)
                except (OSError, ValueError) as error:
                    ui.label(f"Zertifikat ungültig: {error}").classes("text-negative")
                    return
                if info is None:
                    ui.label("Noch kein Kurszertifikat importiert.").classes("text-grey-7")
                    return
                ui.label(f"Kurs: {info.course}").classes("font-bold")
                ui.label(f"Lehrkraft: {info.teacher}")
                ui.label(f"Schule: {info.school}")
                if info.content is not None:
                    ui.label("Inhaltsquelle").classes("font-bold mt-2")
                    ui.label(f"Repository: {info.content.repository}")
                    ui.label(f"Branch: {info.content.branch}")
                    if info.content.certificate_name:
                        ui.label(
                            f"Zertifikatshash: certificates/"
                            f"{info.content.certificate_name}"
                        )
                    ui.label(
                        "Pfade: "
                        f"{info.content.scripts_path}, "
                        f"{info.content.assignments_path}, "
                        f"{info.content.trainers_path}"
                    )
                ui.label(f"Gültig bis: {info.valid_until}")
                ui.label(f"Fingerabdruck: {info.fingerprint}").classes(
                    "font-mono text-xs break-all"
                )

        render_certificate()

        def import_certificate_data(data: bytes) -> None:
            try:
                info = install_course_certificate(data, submission_course)
                render_certificate()
                ui.notify(
                    f"Zertifikat für {info.course} wurde importiert.",
                    type="positive",
                )
            except (OSError, ValueError) as error:
                ui.notify(f"Import fehlgeschlagen: {error}", type="negative")

        async def import_uploaded_certificate(event) -> None:
            import_certificate_data(await event.file.read())

        async def choose_native_certificate() -> None:
            if nicegui_app.native.main_window is None:
                return
            import webview

            downloads = Path.home() / "Downloads"
            try:
                # pywebview akzeptiert keine Bindestriche in Dateifiltern;
                # .pykim-cert wird deshalb nach der Auswahl inhaltlich geprüft.
                selected = await nicegui_app.native.main_window.create_file_dialog(
                    dialog_type=webview.FileDialog.OPEN,
                    directory=str(downloads if downloads.is_dir() else Path.home()),
                )
            except Exception as error:
                ui.notify(f"Dateiauswahl fehlgeschlagen: {error}", type="negative")
                return
            if selected:
                try:
                    certificate_path = Path(selected[0])
                    if certificate_path.suffix != ".pykim-cert":
                        raise ValueError("Wähle eine Datei mit der Endung .pykim-cert aus.")
                    import_certificate_data(certificate_path.read_bytes())
                except (OSError, ValueError) as error:
                    ui.notify(f"Datei konnte nicht gelesen werden: {error}", type="negative")

        if desktop:
            ui.button(
                "Zertifikat auswählen",
                on_click=choose_native_certificate,
                icon="workspace_premium",
            ).props("outline")
        else:
            ui.upload(
                label=".pykim-cert aus dem Lernraum auswählen",
                on_upload=import_uploaded_certificate,
                auto_upload=True,
                max_file_size=1_000_000,
            ).props("accept=.pykim-cert").classes("w-full")

        ui.separator()
        ui.label("2. Lernstand exportieren").classes("text-xl font-bold")
        ui.markdown(
            "Verschlüsselt werden dein im Kurs eingetragener Name oder dein "
            "Kürzel, die aktuellen Quellcodes, letzte Testergebnisse, "
            "Leistungsübersicht und Codefingerprints. Dein Systembenutzername "
            "wird nicht exportiert."
        )
        include_journal = ui.checkbox(
            "Meine Dokubuch-Einträge ebenfalls exportieren",
            value=False,
        )
        export_result = ui.label("").classes("text-sm")

        async def export_learning_record() -> None:
            try:
                target = await nicegui_run.io_bound(
                    create_encrypted_submission,
                    submission_course,
                    None,
                    include_journal=include_journal.value,
                )
                export_result.set_text(f"Export erstellt: {target}")
                ui.notify("Verschlüsselte Moodle-Abgabe erstellt.", type="positive")
                open_path(target.parent)
            except (OSError, ValueError) as error:
                ui.notify(f"Export fehlgeschlagen: {error}", type="negative")

        ui.button(
            "Verschlüsselte Abgabe erstellen",
            on_click=export_learning_record,
            icon="lock",
        )



__all__ = ["render_submission_panel"]
