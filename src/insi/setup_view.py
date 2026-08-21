"""Einrichtung von Kursordner, IDE und Python-Laufzeit."""

from __future__ import annotations

from pathlib import Path

from .branding import APP_DISPLAY_NAME
from insi.course import (
    create_course,
    get_course_directory,
    get_ide_preference,
    get_runtime_preference,
    set_ide_preference,
    set_runtime_preference,
)
from insi.course_archive import (
    MAX_ARCHIVE_SIZE,
    course_content_source,
    parse_course_archive,
)
from .course_import_dialogs import archive_runtime_details, confirm_external_course_import
from insi.course_setup import (
    course_setup_info,
    is_setup_filename,
    install_course_archive,
    install_course_setup,
    setup_info,
)
from insi.execution_security import ACTIVE_PROTECTION
from insi.runtime import (
    bundled_wheelhouse,
    course_runtime_preflight,
    discover_runtimes,
    provision_managed_runtime,
    repair_runtime,
    runtime_diagnostics,
)
from insi.system import detected_ides, install_or_repair_pyxel, system_status


IDE_LABELS = {
    "system": "Systemstandard",
    "thonny": "Thonny",
    "vscode": "VS Code",
    "pycharm": "PyCharm",
}


def preferred_ide_label() -> str:
    """Liefere die kurze, nutzerseitige Bezeichnung der gewählten IDE."""
    preference = get_ide_preference()
    if preference["ide"] == "custom":
        path = Path(preference["path"])
        return path.stem if path.name else "eigener IDE"
    return IDE_LABELS.get(preference["ide"], "IDE")


def render_setup_panel(
    context,
    ide_open_buttons: list,
    current_student: str,
) -> None:
    """Rendere Kursordner-, IDE-, Runtime- und Sicherheitskonfiguration."""
    ui = context.ui
    nicegui_app = context.app
    nicegui_run = context.run
    desktop = context.desktop
    ui.label("Kursordner einrichten").classes("text-2xl font-bold")
    ui.markdown(
        "Der Ordner darf auf einem lokalen, USB- oder eingebundenen "
        "WebDAV-Laufwerk liegen. Vorhandene Lösungen werden nicht überschrieben."
    )
    default = str(get_course_directory() or Path.home() / "PyKIM-Kurs")
    with ui.row().classes("w-full items-end gap-2"):
        path = ui.input("Kursordner", value=default).classes("grow")

        def initial_browser_directory() -> Path:
            candidate = Path(path.value or Path.home()).expanduser()
            while not candidate.is_dir() and candidate != candidate.parent:
                candidate = candidate.parent
            return candidate if candidate.is_dir() else Path.home()

        async def open_course_browser() -> None:
            if desktop and nicegui_app.native.main_window is not None:
                import webview

                selected = await nicegui_app.native.main_window.create_file_dialog(
                    dialog_type=webview.FileDialog.FOLDER,
                    directory=str(initial_browser_directory()),
                )
                if selected:
                    path.set_value(str(Path(selected[0]).resolve()))
                return
            try:
                show_directory(initial_browser_directory())
                folder_dialog.open()
            except OSError as error:
                ui.notify(str(error), type="warning")

        ui.button(
            "Ordner auswählen",
            on_click=open_course_browser,
            icon="folder_open",
        )

    with ui.dialog() as folder_dialog, ui.card().classes("w-full max-w-2xl"):
        ui.label("Kursordner auswählen").classes("text-xl font-bold")
        current_directory = ui.input("Aktueller Ordner").classes("w-full")
        current_directory.props("readonly")
        directory_list = ui.column().classes(
            "w-full gap-1 max-h-96 overflow-y-auto border rounded p-2"
        )

        def show_directory(directory: Path) -> None:
            selected = directory.expanduser().resolve()
            try:
                children = sorted(
                    (entry for entry in selected.iterdir() if entry.is_dir()),
                    key=lambda entry: entry.name.casefold(),
                )
            except (OSError, PermissionError) as error:
                ui.notify(f"Ordner nicht lesbar: {error}", type="warning")
                return

            current_directory.set_value(str(selected))
            directory_list.clear()
            with directory_list:
                if selected != selected.parent:
                    ui.button(
                        "..  Übergeordneter Ordner",
                        on_click=lambda parent=selected.parent: show_directory(parent),
                        icon="drive_folder_upload",
                    ).props("flat").classes("w-full justify-start")
                for child in children[:250]:
                    ui.button(
                        child.name,
                        on_click=lambda target=child: show_directory(target),
                        icon="folder",
                    ).props("flat").classes("w-full justify-start")
                if len(children) > 250:
                    ui.label(
                        "Es werden nur die ersten 250 Unterordner angezeigt."
                    ).classes("text-sm text-grey-7")

        def use_current_directory() -> None:
            path.set_value(current_directory.value)
            folder_dialog.close()

        with ui.row().classes("w-full justify-end"):
            ui.button("Abbrechen", on_click=folder_dialog.close).props("flat")
            ui.button(
                "Diesen Ordner verwenden",
                on_click=use_current_directory,
                icon="check",
            )

    student = ui.input(
        "Dein Name oder Kürzel (optional)",
        value=current_student,
        placeholder="z. B. Ada L. oder ada-l",
    ).classes("w-full")
    ui.label(
        "Diese Angabe wird nur im Kursordner gespeichert, damit du deine "
        "Unterlagen und deinen Lernfortschritt zuordnen kannst."
    ).classes("text-sm text-grey-7")

    ui.separator()
    ui.label("Bevorzugte Entwicklungsumgebung").classes("text-xl font-bold")
    installed_ides = detected_ides()
    ide_labels = {**IDE_LABELS, "custom": "Eigener Programmpfad"}
    available_ide_options = {"system": ide_labels["system"]}
    available_ide_options.update(
        {
            key: f"{ide_labels[key]} – gefunden"
            for key in ("thonny", "vscode", "pycharm")
            if key in installed_ides
        }
    )
    available_ide_options["custom"] = ide_labels["custom"]
    preference = get_ide_preference()
    selected_ide = (
        preference["ide"]
        if preference["ide"] in available_ide_options
        else "system"
    )
    ide_choice = ui.radio(
        available_ide_options,
        value=selected_ide,
    ).props("inline")
    custom_ide_path = ui.input(
        "Pfad zur eigenen IDE oder .app-Datei",
        value=preference["path"],
        placeholder="z. B. /Applications/Meine IDE.app",
    ).classes("w-full")
    ui.label("Die Auswahl wird automatisch gespeichert.").classes(
        "text-sm text-grey-7"
    )

    def save_ide() -> None:
        if ide_choice.value == "custom" and not custom_ide_path.value:
            return
        try:
            saved = set_ide_preference(
                ide_choice.value,
                custom_ide_path.value or "",
            )
            ui.notify(
                f"Standard-IDE gespeichert: {ide_labels[saved['ide']]}",
                type="positive",
            )
            button_text = f"In {preferred_ide_label()} öffnen"
            for button in ide_open_buttons:
                button.set_text(button_text)
        except ValueError as error:
            ui.notify(str(error), type="negative")

    ide_choice.on_value_change(lambda _: save_ide())
    custom_ide_path.on_value_change(lambda _: save_ide())

    ui.separator()
    ui.label("Python-Laufzeit für Aufgaben").classes("text-xl font-bold")
    ui.label(
        "Die Suite und die Entwicklungsumgebung verwenden für Schülerprogramme "
        "denselben geprüften Interpreter."
    ).classes("text-sm text-grey-7")
    offline_wheels = bundled_wheelhouse()
    ui.label(
        "Offline-Pakete gefunden: Die Einrichtung benötigt kein Internet."
        if offline_wheels
        else "Noch kein Offline-Paket eingebunden: Für die Einrichtung kann Internetzugang erforderlich sein."
    ).classes("text-sm text-positive" if offline_wheels else "text-sm text-orange")
    runtimes = discover_runtimes(path.value or None)
    preflight = course_runtime_preflight(path.value, candidates=runtimes)
    runtime_options = {
        item.executable: (
            f"Python {item.version or '?'} · {item.source} · "
            + (
                "bereit"
                if (
                    preflight.ready
                    and preflight.candidate is not None
                    and item.executable == preflight.candidate.executable
                )
                else " · ".join(
                    problem for problem, applies in (
                        ("Python-Version ungeeignet", not item.supported),
                        (
                            f"Kurs benötigt Python {preflight.required_python}",
                            bool(preflight.required_python)
                            and ".".join(item.version.split(".")[:2])
                            != preflight.required_python,
                        ),
                        ("PyKIM fehlt", not item.pykim),
                        ("Pyxel fehlt", not item.pyxel),
                        (
                            "Paketstand nicht freigegeben",
                            item.supported
                            and item.pykim
                            and item.pyxel
                            and not (
                                preflight.ready
                                and preflight.candidate is not None
                                and item.executable == preflight.candidate.executable
                            ),
                        ),
                    ) if applies
                )
            )
        )
        for item in runtimes
    }
    ready_runtime_paths = (
        {preflight.candidate.executable}
        if preflight.ready and preflight.candidate is not None
        else set()
    )
    configured_runtime = get_runtime_preference()
    runtime_value = (
        configured_runtime
        if configured_runtime in runtime_options
        else next(iter(ready_runtime_paths), None)
    )
    runtime_choice = ui.select(
        runtime_options,
        value=runtime_value,
        label="Interpreter",
    ).classes("w-full")

    with ui.column().classes(
        "w-full gap-1 rounded border p-3 "
        + ("bg-green-1" if preflight.ready else "bg-orange-1")
    ):
        with ui.row().classes("items-center gap-2"):
            ui.icon(
                "verified" if preflight.ready else "warning",
                color="positive" if preflight.ready else "warning",
            )
            ui.label(
                "Kursstartprüfung bestanden"
                if preflight.ready
                else "Kursstartprüfung: Eingriff erforderlich"
            ).classes("font-bold")
        if preflight.required_python:
            ui.label(f"Kursvorgabe: Python {preflight.required_python}").classes(
                "text-sm"
            )
        for issue in preflight.issues:
            ui.label(issue).classes("text-sm text-negative")
        for warning in preflight.warnings:
            ui.label(warning).classes("text-sm text-orange-9")
        for package in preflight.packages:
            installed = package.installed or "fehlt"
            ui.label(
                f"{'✓' if package.ready else '✗'} {package.requirement} "
                f"(installiert: {installed})"
            ).classes("text-xs")

    def save_runtime() -> None:
        if not runtime_choice.value:
            return
        if runtime_choice.value not in ready_runtime_paths:
            runtime_setup_confirmation.open()
            return
        try:
            set_runtime_preference(runtime_choice.value)
            ui.notify("Python-Laufzeit gespeichert.", type="positive")
        except ValueError as error:
            ui.notify(str(error), type="negative")

    runtime_choice.on_value_change(lambda _: save_runtime())
    if not ready_runtime_paths:
        ui.label(
            "Noch keine vollständige Laufzeit mit PyKIM und Pyxel gefunden."
        ).classes("text-orange")
    incomplete = [
        item for item in runtimes
        if not (item.supported and item.pykim and item.pyxel)
    ]
    for item in incomplete:
        missing = []
        if not item.supported:
            missing.append("Python-Version ungeeignet")
        if not item.pykim:
            missing.append("PyKIM fehlt")
        if not item.pyxel:
            missing.append("Pyxel fehlt")
        ui.label(
            f"{item.source}: {item.executable} – {', '.join(missing)}"
        ).classes("text-xs text-grey-7")

    async def provision_selected_runtime() -> None:
        selected = runtime_choice.value
        if not selected:
            return
        runtime_setup_confirmation.close()
        runtime_setup_button.disable()
        runtime_activity.set_visibility(True)
        try:
            ready = await nicegui_run.io_bound(
                provision_managed_runtime,
                path.value,
                selected,
            )
            ui.notify(
                f"Python {ready.version}: PyKIM-Laufzeit ist bereit.",
                type="positive",
            )
            runtime_choice.options[ready.executable] = (
                f"Python {ready.version} · PyKIM-Kursumgebung · bereit"
            )
            runtime_choice.set_value(ready.executable)
            runtime_choice.update()
            runtime_repair_button.enable()
        except Exception as error:
            ui.notify(f"Einrichtung fehlgeschlagen: {error}", type="negative")
            runtime_choice.set_value(runtime_value)
        finally:
            runtime_activity.set_visibility(False)
            runtime_setup_button.enable()

    with ui.dialog() as runtime_setup_confirmation, ui.card():
        ui.label("PyKIM-Laufzeit einrichten?").classes("text-xl font-bold")
        ui.label(
            "Die Suite erstellt außerhalb des Kursordners eine isolierte "
            "Python-Umgebung und installiert dort PyKIM und Pyxel."
        )
        ui.label(
            "Aufgaben, Projekte und Lernstand werden nicht verändert."
        ).classes("text-sm text-grey-7")
        with ui.row().classes("justify-end w-full"):
            ui.button(
                "Abbrechen",
                on_click=lambda: (
                    runtime_setup_confirmation.close(),
                    runtime_choice.set_value(runtime_value),
                ),
            ).props("flat")
            runtime_setup_button = ui.button(
                "Umgebung einrichten",
                on_click=provision_selected_runtime,
                icon="build",
            )

    async def repair_selected_runtime() -> None:
        runtime_repair_confirmation.close()
        runtime_repair_button.disable()
        runtime_activity.set_visibility(True)
        try:
            ready = await nicegui_run.io_bound(repair_runtime, path.value)
            ui.notify(
                f"Python {ready.version}: Laufzeit wurde erfolgreich repariert.",
                type="positive",
            )
        except Exception as error:
            ui.notify(f"Reparatur fehlgeschlagen: {error}", type="negative")
        finally:
            runtime_activity.set_visibility(False)
            runtime_repair_button.enable()

    with ui.row().classes("items-center gap-2"):
        runtime_repair_button = ui.button(
            "Laufzeit reparieren",
            on_click=lambda: runtime_repair_confirmation.open(),
            icon="handyman",
        ).props("outline")
        runtime_activity = ui.spinner(size="lg", color="primary")
        runtime_activity.set_visibility(False)
        if not preflight.repairable:
            runtime_repair_button.disable()
            runtime_repair_button.tooltip(
                "Die aktuelle Diagnose kann nicht durch eine Reparatur der "
                "vorhandenen Kursumgebung behoben werden."
            )

        def copy_runtime_diagnostics() -> None:
            import json

            report = json.dumps(
                runtime_diagnostics(path.value),
                ensure_ascii=False,
                indent=2,
            )
            ui.clipboard.write(report)
            ui.notify("Runtime-Diagnose wurde kopiert.", type="positive")

        ui.button(
            "Diagnose kopieren",
            on_click=copy_runtime_diagnostics,
            icon="content_copy",
        ).props("flat")

    with ui.dialog() as runtime_repair_confirmation, ui.card():
        ui.label("PyKIM-Laufzeit reparieren?").classes("text-xl font-bold")
        ui.label(
            "PyKIM, Pyxel und benötigte Pakete werden in der verwalteten "
            "Kursumgebung erneut installiert."
        )
        ui.label("Schülerdateien werden nicht verändert.").classes("text-sm text-grey-7")
        with ui.row().classes("w-full justify-end"):
            ui.button("Abbrechen", on_click=runtime_repair_confirmation.close).props("flat")
            ui.button(
                "Jetzt reparieren",
                on_click=repair_selected_runtime,
                icon="handyman",
            )

    def setup() -> None:
        try:
            result = create_course(path.value, student.value)
            ui.notify(
                f"{len(result['created'])} Dateien angelegt; "
                f"{len(result['existing'])} vorhandene Dateien behalten.",
                type="positive",
            )
        except OSError as error:
            ui.notify(f"Setup fehlgeschlagen: {error}", type="negative")

    ui.button("Kursordner anlegen oder ergänzen", on_click=setup, icon="create_new_folder")

    ui.separator()
    ui.label("Kursdatei und Lerninhalte").classes("text-xl font-bold")
    ui.label(
        "Eine Setupdatei lädt den Kurs aus seinem Repository. Ein portables "
        "Kurs-ZIP enthält denselben geprüften Stand für die vollständig "
        "offline nutzbare Einrichtung."
    ).classes("text-sm text-grey-7")
    setup_certificate_status = ui.column().classes("w-full gap-1")

    def render_setup_certificate() -> None:
        setup_certificate_status.clear()
        course = Path(path.value).expanduser().resolve()
        with setup_certificate_status:
            try:
                info = course_setup_info(course)
            except (OSError, ValueError) as error:
                ui.label(f"Setupdatei ungültig: {error}").classes("text-negative")
                return
            if info is None:
                ui.label("Noch keine Kurs-Setupdatei importiert.").classes("text-grey-7")
            else:
                ui.label(f"Kurs: {info.course}").classes("font-bold")
                source = course_content_source(course)
                if source.get("type") == "archive":
                    ui.label("Quelle: lokales Kurs-ZIP · offline")
                else:
                    ui.label(f"{info.repository} · {info.branch}")

    async def import_setup_certificate(
        data: bytes,
        filename: str = "course.insi-setup",
    ) -> None:
        course = Path(path.value).expanduser().resolve()
        if not course.is_dir():
            ui.notify("Lege zuerst den Kursordner an.", type="warning")
            return
        is_archive = filename.casefold().endswith(".zip")
        if is_archive:
            bundle = await nicegui_run.io_bound(parse_course_archive, data)
            candidate = bundle.setup
            source = f"Lokales ZIP-Archiv · {filename}"
            runtime_details = archive_runtime_details(bundle)
        elif is_setup_filename(filename):
            candidate = setup_info(data)
            source = candidate.repository
            runtime_details = ()
        else:
            ui.notify(
                "Wähle eine .insi-setup-, ältere .pykim-setup- oder .zip-Datei.",
                type="negative",
            )
            return
        if not await confirm_external_course_import(
            ui,
            candidate.course,
            source,
            runtime_details,
        ):
            ui.notify("Kursimport abgebrochen.", type="info")
            return
        certificate_activity.set_visibility(True)
        certificate_button.disable()
        try:
            installer = (
                install_course_archive
                if is_archive
                else install_course_setup
            )
            info = await nicegui_run.io_bound(
                installer, data, course
            )
            render_setup_certificate()
            ui.notify(
                f"Setupdatei für {info.course} importiert; Lerninhalte wurden aktiviert.",
                type="positive", timeout=5000,
            )
            ui.navigate.reload()
        except Exception as error:
            ui.notify(f"Import oder Synchronisierung fehlgeschlagen: {error}", type="negative")
        finally:
            certificate_activity.set_visibility(False)
            certificate_button.enable()

    async def choose_setup_certificate() -> None:
        if not desktop or nicegui_app.native.main_window is None:
            return
        import webview

        selected = await nicegui_app.native.main_window.create_file_dialog(
            dialog_type=webview.FileDialog.OPEN,
            directory=str(Path.home() / "Downloads"),
        )
        if selected:
            certificate_path = Path(selected[0])
            if not (
                is_setup_filename(certificate_path.name)
                or certificate_path.suffix.casefold() == ".zip"
            ):
                ui.notify(
                    "Wähle eine .insi-setup-, ältere .pykim-setup- oder .zip-Datei.",
                    type="negative",
                )
                return
            await import_setup_certificate(
                certificate_path.read_bytes(), certificate_path.name
            )

    async def upload_setup_certificate(event) -> None:
        await import_setup_certificate(
            await event.file.read(), event.file.name
        )

    with ui.row().classes("items-center gap-2"):
        if desktop:
            certificate_button = ui.button(
                "Setupdatei oder Kurs-ZIP auswählen",
                on_click=choose_setup_certificate,
                icon="settings_suggest",
            ).props("outline")
        else:
            certificate_button = ui.upload(
                label="Setupdatei oder Kurs-ZIP auswählen",
                on_upload=upload_setup_certificate,
                auto_upload=True,
                max_file_size=MAX_ARCHIVE_SIZE,
            ).props("accept=.insi-setup,.pykim-setup,.zip")
        with ui.column().classes("gap-1") as certificate_activity:
            with ui.row().classes("items-center gap-2"):
                ui.spinner(size="sm", color="primary")
                ui.label("Kursinhalt wird geprüft und eingerichtet …")
            ui.linear_progress(value=None, color="primary").props(
                "indeterminate rounded"
            ).classes("w-72")
        certificate_activity.set_visibility(False)
    render_setup_certificate()

    ui.separator()
    ui.label("Systemcheck").classes("text-xl font-bold")
    status = system_status()

    def status_line(text: str, available: bool = True) -> None:
        with ui.row().classes("items-center gap-2"):
            ui.icon(
                "check_circle" if available else "info",
                color="positive" if available else "grey",
            )
            ui.label(text)

    with ui.column().classes("w-full gap-1"):
        status_line(
            f"Python {status.python}"
            + ("" if status.python_supported else " – benötigt wird mindestens 3.10"),
            status.python_supported,
        )
        status_line(f"PyKIM {status.pykim}")
        status_line("Pyxel installiert" if status.pyxel else "Pyxel fehlt", status.pyxel)
        status_line("Thonny gefunden" if status.thonny else "Thonny nicht gefunden", status.thonny)
        status_line("VS Code gefunden" if status.vscode else "VS Code nicht gefunden", status.vscode)
    ui.label("Schutz bei Codeausführung").classes("font-bold mt-2")
    with ui.column().classes("w-full gap-1"):
        status_line("Schülercode läuft in einem getrennten Prozess")
        status_line(
            "Integrierte Aufgabenläufe begrenzen Laufzeit und gespeicherte Ausgabe"
        )
        status_line("Typische Zugangsdaten werden nicht weitergegeben")
        status_line(
            "Noch keine aktive Betriebssystem-Sandbox für Dateisystem und Netzwerk",
            ACTIVE_PROTECTION.os_sandbox_active,
        )
    ui.label(ACTIVE_PROTECTION.summary).classes(
        "text-sm text-orange-8"
    )
    with ui.row().classes("items-center gap-3"):
        ui.link(
            "Thonny herunterladen",
            "https://thonny.org/",
            new_tab=True,
        )
        ui.link(
            "VS Code herunterladen",
            "https://code.visualstudio.com/download",
            new_tab=True,
        )
        ui.link(
            "Python herunterladen",
            "https://www.python.org/downloads/",
            new_tab=True,
        )

    def repair_pyxel() -> None:
        try:
            install_or_repair_pyxel()
            ui.notify(
                f"Pyxel wurde installiert bzw. repariert. Bitte {APP_DISPLAY_NAME} neu starten.",
                type="positive",
            )
        except Exception as error:
            ui.notify(f"Pyxel-Installation fehlgeschlagen: {error}", type="negative")

    with ui.dialog() as pyxel_confirmation, ui.card():
        ui.label("Pyxel installieren oder reparieren?").classes("font-bold")
        ui.code(
            f'{__import__("sys").executable} -m pip install --upgrade "pyxel>=2.2,<3"',
            language="bash",
        )
        ui.label("Der Kursordner und alle Schülerlösungen bleiben unverändert.")
        with ui.row():
            ui.button("Abbrechen", on_click=pyxel_confirmation.close).props("flat")
            ui.button(
                "Installation starten",
                on_click=lambda: (pyxel_confirmation.close(), repair_pyxel()),
            )
    ui.button(
        "Pyxel installieren / reparieren",
        on_click=pyxel_confirmation.open,
        icon="build",
    ).props("outline")



__all__ = ["preferred_ide_label", "render_setup_panel"]
