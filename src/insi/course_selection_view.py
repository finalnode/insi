"""Kursauswahl, Kursimport und öffentlicher Kurskatalog."""

from __future__ import annotations

import asyncio
from pathlib import Path

from .branding import APP_DISPLAY_NAME
from .desktop import browser_favicon
from insi.course import (
    get_course_directories,
    set_runtime_preference,
    set_course_directory,
    trash_course,
)
from insi.course_archive import MAX_ARCHIVE_SIZE, parse_course_archive
from insi.course_catalog import load_course_catalog
from .course_import_dialogs import archive_runtime_details, confirm_external_course_import
from insi.course_setup import (
    activate_installed_course_content,
    course_import_target,
    course_setup_info,
    is_setup_filename,
    install_new_course_archive,
    install_new_course_setup,
    setup_info,
)
from insi.system import open_path
from insi.runtime import (
    RuntimePreflight,
    course_runtime_preflight,
    provision_managed_runtime,
    repair_runtime,
)


def course_name_confirmation_matches(value: object, expected: str) -> bool:
    """Prüfe den aktuellen Eingabewert ohne verzögerten UI-Zustand."""
    return isinstance(value, str) and value == expected


def render_course_selection(context) -> bool:
    """Rendere bei Bedarf die Kursauswahl und melde, ob sie die Seite belegt."""
    ui = context.ui
    nicegui_run = context.run
    course_sync_state = context.course_sync
    course_selection_state = context.course_selection

    async def choose_course_collision(info) -> str | None:
        """Frage bei einem belegten Ziel nach Kopie, Update oder Abbruch."""
        target = course_import_target(info)
        if not target.exists():
            return "reuse"
        with ui.dialog() as collision_dialog, ui.card().classes("w-full max-w-xl"):
            ui.label("Kurs ist bereits vorhanden").classes("text-xl font-bold")
            ui.label(
                f"Der reguläre Kursordner „{target.name}“ existiert bereits."
            )
            ui.label(
                "Als zweiten Kurs anlegen bewahrt beide Kursstände getrennt. "
                "Beim Aktualisieren bleiben vorhandene Schülerlösungen, Projekte "
                "und Lernstände erhalten; nur die aktive Kursquelle wird ersetzt."
            ).classes("text-sm text-grey-7")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Abbrechen",
                    on_click=lambda: collision_dialog.submit(None),
                ).props("flat")
                ui.button(
                    "Bestehenden aktualisieren",
                    icon="sync",
                    on_click=lambda: collision_dialog.submit("reuse"),
                ).props("outline color=warning")
                ui.button(
                    "Als zweiten Kurs anlegen",
                    icon="content_copy",
                    on_click=lambda: collision_dialog.submit("copy"),
                ).props("color=primary")
        result = await collision_dialog
        return result if result in {"reuse", "copy"} else None

    if not course_selection_state["confirmed"]:
        async def prompt_runtime_preflight(
            report: RuntimePreflight,
        ) -> tuple[str, str]:
            """Erkläre einen blockierten Kursstart und liefere die gewählte Aktion."""
            with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("rule", color="warning", size="md")
                    ui.label("Kurslaufzeit ist noch nicht bereit").classes(
                        "text-xl font-bold"
                    )
                if report.required_python:
                    ui.label(
                        f"Benötigte Laufzeit: Python {report.required_python}"
                    ).classes("font-bold")
                with ui.column().classes("w-full gap-1 rounded border p-3 bg-red-1"):
                    for issue in report.issues:
                        with ui.row().classes("items-start gap-2 no-wrap"):
                            ui.icon("error", color="negative", size="xs")
                            ui.label(issue).classes("text-sm")
                for warning in report.warnings:
                    ui.label(warning).classes("text-sm text-orange-9")
                if report.packages:
                    ui.label("Paketprüfung").classes("font-bold mt-2")
                    with ui.column().classes("w-full gap-1"):
                        for package in report.packages:
                            installed = package.installed or "fehlt"
                            with ui.row().classes("items-center gap-2"):
                                ui.icon(
                                    "check_circle" if package.ready else "cancel",
                                    color="positive" if package.ready else "negative",
                                    size="xs",
                                )
                                ui.label(
                                    f"{package.requirement} · installiert: {installed}"
                                ).classes("text-sm")
                base_choice = None
                if report.provision_candidates:
                    base_choice = ui.select(
                        {
                            candidate.executable: (
                                f"Python {candidate.version} · {candidate.source}"
                            )
                            for candidate in report.provision_candidates
                        },
                        value=report.provision_candidates[0].executable,
                        label="Basis-Python für die neue Kursumgebung",
                    ).classes("w-full")
                    ui.label(
                        "in:si erstellt eine getrennte Umgebung außerhalb des "
                        "Kursordners. Schülerdateien bleiben unverändert."
                    ).classes("text-xs text-grey-7")
                elif not report.repairable and report.required_python:
                    ui.label(
                        f"Installiere Python {report.required_python} für dein "
                        "Betriebssystem und starte die Prüfung danach erneut."
                    ).classes("text-sm")
                    ui.link(
                        "Python herunterladen",
                        "https://www.python.org/downloads/",
                        new_tab=True,
                    )
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button(
                        "Abbrechen",
                        on_click=lambda: dialog.submit(("cancel", "")),
                    ).props("flat")
                    if report.repairable:
                        ui.button(
                            "Laufzeit reparieren",
                            icon="handyman",
                            on_click=lambda: dialog.submit(("repair", "")),
                        ).props("outline")
                    if base_choice is not None:
                        ui.button(
                            "Kursumgebung einrichten",
                            icon="build",
                            on_click=lambda: dialog.submit(
                                ("provision", str(base_choice.value or ""))
                            ),
                        )
            result = await dialog
            return result if isinstance(result, tuple) else ("cancel", "")

        async def select_course(course: Path, card, button, sync_activity) -> None:
            def reset_opening_state() -> None:
                card.classes(remove="pykim-course-opening")
                sync_activity.set_visibility(False)
                button.text = "Öffnen"
                button.enable()

            card.classes(add="pykim-course-opening")
            sync_activity.set_visibility(True)
            button.text = "Wird geöffnet …"
            button.disable()
            try:
                await ui.run_javascript(
                    "await new Promise(resolve => requestAnimationFrame("
                    "() => requestAnimationFrame(resolve)))"
                )
            except TimeoutError:
                # Die Animation ist rein visuell. Ein langsamer oder browserloser
                # Client darf das eigentliche Öffnen des Kurses nicht verhindern.
                pass
            set_course_directory(course)
            # Die lokale Kurskopie wird ohne Netzwerk aktiviert. Ein Abgleich
            # mit dem Repository erfolgt später nur über den sichtbaren Button.
            course_sync_state.update(result=None, error="", pending=False)
            try:
                await asyncio.gather(
                    nicegui_run.io_bound(
                        activate_installed_course_content, course
                    ),
                    asyncio.sleep(1.05),
                )
            except Exception as error:
                course_sync_state["error"] = str(error)
                course_sync_state["pending"] = False
                ui.notify(
                    f"Kursinhalt konnte nicht aktiviert werden: {error}",
                    type="negative",
                )
                reset_opening_state()
                return

            report = await nicegui_run.io_bound(course_runtime_preflight, course)
            while not report.ready:
                action, executable = await prompt_runtime_preflight(report)
                if action == "cancel":
                    course_sync_state["pending"] = False
                    reset_opening_state()
                    return
                try:
                    if action == "repair":
                        await nicegui_run.io_bound(repair_runtime, course)
                    elif action == "provision" and executable:
                        await nicegui_run.io_bound(
                            provision_managed_runtime,
                            course,
                            executable,
                        )
                    else:
                        course_sync_state["pending"] = False
                        reset_opening_state()
                        return
                    report = await nicegui_run.io_bound(
                        course_runtime_preflight, course
                    )
                except Exception as error:
                    ui.notify(
                        f"Laufzeit konnte nicht vorbereitet werden: {error}",
                        type="negative",
                    )
                    course_sync_state["pending"] = False
                    reset_opening_state()
                    return
            if report.candidate is not None:
                set_runtime_preference(report.candidate.executable)
            if report.warnings:
                ui.notify(report.warnings[0], type="warning", timeout=6000)
            course_selection_state["confirmed"] = True
            ui.navigate.reload()

        with ui.column().classes(
            "w-full max-w-4xl mx-auto items-stretch gap-3 p-6"
        ):
            with ui.row().classes("w-full items-center gap-3"):
                ui.image(browser_favicon()).classes("insi-selection-logo").props(
                    f'alt="{APP_DISPLAY_NAME}"'
                )
                ui.label("Kurs auswählen").classes("text-lg text-grey-7")
                ui.space()
                ui.button(
                    "Kurs erstellen",
                    icon="inventory_2",
                    on_click=lambda: ui.navigate.to("/course-builder"),
                ).props("flat")
            known_courses = get_course_directories()
            for course in known_courses:
                try:
                    info = course_setup_info(course)
                except (OSError, ValueError):
                    info = None
                with ui.card().classes(
                    "w-full py-2 px-3 shadow-none border gap-1"
                ) as course_card:
                    with ui.row().classes("w-full items-center no-wrap gap-3"):
                        ui.icon("school", color="primary", size="sm")
                        with ui.column().classes("grow gap-0 min-w-0"):
                            ui.label(
                                info.course if info is not None else course.name
                            ).classes("font-bold")
                            details = (
                                f"{info.school} · {info.teacher}"
                                if info is not None
                                else str(course)
                            )
                        ui.label(details).classes(
                                "text-sm text-grey-7 ellipsis"
                            )
                        def open_course_folder(selected=course) -> None:
                            try:
                                open_path(selected)
                            except (OSError, RuntimeError) as error:
                                ui.notify(
                                    f"Ordner konnte nicht geöffnet werden: {error}",
                                    type="negative",
                                )

                        ui.button(
                            icon="folder_open",
                            on_click=open_course_folder,
                        ).props("flat round dense").tooltip("Kursordner öffnen")
                        open_course_button = ui.button(
                            "Öffnen",
                            icon="arrow_forward",
                        ).props("flat dense")
                        expected_name = (
                            info.course if info is not None else course.name
                        )
                        with ui.dialog() as delete_dialog, ui.card().classes(
                            "w-full max-w-lg"
                        ):
                            ui.label("Kurs in den Papierkorb verschieben?").classes(
                                "text-xl font-bold"
                            )
                            ui.label(
                                "Schülerlösungen, Antworten und Lernstand in diesem "
                                "Kursordner werden ebenfalls verschoben. Der Vorgang kann "
                                "über den Systempapierkorb rückgängig gemacht werden."
                            )
                            ui.label(
                                f"Gib zur Bestätigung exakt „{expected_name}“ ein."
                            ).classes("text-negative")
                            delete_name = ui.input("Kursname").classes("w-full")

                            async def delete_selected_course(
                                button,
                                selected=course,
                                dialog=delete_dialog,
                            ) -> None:
                                button.disable()
                                try:
                                    await nicegui_run.io_bound(trash_course, selected)
                                    dialog.close()
                                    ui.notify(
                                        "Der Kurs wurde in den Papierkorb verschoben.",
                                        type="positive",
                                    )
                                    ui.navigate.reload()
                                except Exception as error:
                                    ui.notify(
                                        f"Kurs konnte nicht gelöscht werden: {error}",
                                        type="negative",
                                    )
                                    button.enable()

                            with ui.row().classes("w-full justify-end"):
                                ui.button(
                                    "Abbrechen",
                                    on_click=delete_dialog.close,
                                ).props("flat")
                                confirm_delete = ui.button(
                                    "In Papierkorb",
                                    icon="delete",
                                ).props("color=negative")
                                confirm_delete.disable()
                                confirm_delete.on(
                                    "click",
                                    lambda _, action=delete_selected_course,
                                    button=confirm_delete: action(button),
                                )
                            delete_name.on_value_change(
                                lambda event,
                                button=confirm_delete,
                                expected=expected_name: (
                                    button.enable()
                                    if course_name_confirmation_matches(
                                        event.value, expected
                                    )
                                    else button.disable()
                                ),
                            )
                        ui.button(
                            icon="delete_outline",
                            on_click=delete_dialog.open,
                        ).props("flat round dense color=negative").tooltip(
                            "Kurs löschen"
                        )
                    with ui.column().classes(
                        "w-full items-center gap-1 py-1 text-positive"
                    ) as course_sync_activity:
                        with ui.row().classes("items-center justify-center gap-2"):
                            ui.icon("sync", size="sm").classes(
                                "pykim-course-sync-icon"
                            )
                            ui.label(
                                "Lokaler Kurs wird geladen · Online-Abgleich folgt"
                            ).classes("pykim-course-sync-dots text-sm font-medium")
                    course_sync_activity.set_visibility(False)
                    pixel_palette = (
                        ("#f36b2b", "#ffd166"),
                        ("#00a8e8", "#70d6ff"),
                        ("#9b5de5", "#f15bb5"),
                        ("#21ba45", "#8bd450"),
                        ("#ff9f1c", "#ff4d6d"),
                    )
                    ui.html(
                        "".join(
                            '<span style="'
                            f'--pixel-x:{(index * 37 + index * index * 3) % 94 + 2}%;'
                            f'--pixel-y:{(index * 53 + index * index * 7) % 78 + 8}%;'
                            f'--pixel-size:{0.46 + (index % 4) * 0.12:.2f}rem;'
                            f'--pixel-delay:-{(index * 0.23) % 3.7:.2f}s;'
                            f'--pixel-duration:{2.25 + (index % 6) * 0.31:.2f}s;'
                            f'--pixel-color-a:{pixel_palette[index % len(pixel_palette)][0]};'
                            f'--pixel-color-b:{pixel_palette[index % len(pixel_palette)][1]}'
                            '"></span>'
                            for index in range(32)
                        ),
                        sanitize=False,
                    ).classes("pykim-course-pixel-field").props(
                        "aria-hidden=true"
                    )
                    open_course_button.on(
                        "click",
                        lambda _, selected=course, card=course_card,
                        button=open_course_button,
                        activity=course_sync_activity: select_course(
                            selected, card, button, activity
                        ),
                    )
            if not known_courses:
                ui.label("Noch kein Kurs eingerichtet.").classes("text-grey-7")

            ui.separator()
            with ui.row().classes("w-full items-center gap-3 no-wrap"):
                with ui.column().classes("grow gap-0"):
                    ui.label("Kurs hinzufügen").classes("font-bold")
                    ui.label(
                        "Eine .insi-setup-Datei oder ein portables Kurs-ZIP auswählen."
                    ).classes("text-sm text-grey-7")

                async def upload_new_course(event) -> None:
                    course_upload.disable()
                    try:
                        data = await event.file.read()
                        filename = event.file.name or "Ausgewählte Kursdatei"
                        is_archive = filename.casefold().endswith(".zip")
                        if is_archive:
                            bundle = await nicegui_run.io_bound(
                                parse_course_archive, data
                            )
                            info = bundle.setup
                            source = f"Lokales ZIP-Archiv · {filename}"
                            runtime_details = archive_runtime_details(bundle)
                        elif is_setup_filename(filename):
                            info = setup_info(data)
                            source = info.repository
                            runtime_details = ()
                        else:
                            raise ValueError(
                                "Wähle eine .insi-setup-, ältere .pykim-setup- oder .zip-Datei."
                            )
                        course_import_activity.set_visibility(False)
                        if not await confirm_external_course_import(
                            ui, info.course, source, runtime_details
                        ):
                            course_upload.reset()
                            ui.notify("Kursimport abgebrochen.", type="info")
                            return
                        collision = await choose_course_collision(info)
                        if collision is None:
                            course_upload.reset()
                            ui.notify("Kursimport abgebrochen.", type="info")
                            return
                        course_import_activity.set_visibility(True)
                        installer = (
                            install_new_course_archive
                            if is_archive
                            else install_new_course_setup
                        )
                        info, course = await nicegui_run.io_bound(
                            installer, data, collision=collision
                        )
                        course_selection_state["confirmed"] = True
                        ui.notify(
                            f"{info.course} wurde eingerichtet.",
                            type="positive",
                        )
                        ui.navigate.reload()
                    except Exception as error:
                        ui.notify(
                            f"Kurs konnte nicht eingerichtet werden: {error}",
                            type="negative",
                        )
                        course_upload.reset()
                    finally:
                        course_upload.enable()
                        course_import_activity.set_visibility(False)

                def begin_course_import() -> None:
                    course_import_activity.set_visibility(True)

                def reject_course_import() -> None:
                    course_import_activity.set_visibility(False)
                    ui.notify(
                        "Die Kursdatei konnte nicht hochgeladen werden.",
                        type="negative",
                    )

                with ui.column().classes("w-72 items-stretch gap-2"):
                    course_upload = ui.upload(
                        label="Setupdatei oder Kurs-ZIP auswählen",
                        on_begin_upload=begin_course_import,
                        on_upload=upload_new_course,
                        on_rejected=reject_course_import,
                        auto_upload=True,
                        max_files=1,
                        max_file_size=MAX_ARCHIVE_SIZE,
                    ).props("accept=.insi-setup,.pykim-setup,.zip flat bordered").classes("w-full")
                    with ui.column().classes(
                        "w-full gap-1 rounded border p-3 bg-orange-1"
                    ) as course_import_activity:
                        with ui.row().classes("items-center gap-2"):
                            ui.spinner(size="sm", color="primary")
                            ui.label("Kurs wird eingerichtet …").classes("font-bold")
                        ui.linear_progress(value=None, color="primary").props(
                            "indeterminate rounded"
                        )
                        ui.label(
                            "Kursdatei und Inhalte werden geprüft und eingerichtet. "
                            "Bei Online-Kursen kann der erste Import etwas dauern."
                        ).classes("text-xs text-grey-7")
                    course_import_activity.set_visibility(False)

            ui.separator()
            with ui.row().classes("w-full items-center gap-2"):
                ui.icon("public", color="primary")
                with ui.column().classes("grow gap-0"):
                    ui.label("Freie Kurse entdecken").classes("font-bold")
                    ui.label(
                        "Öffentliche PyKIM-Kurse direkt aus dem Kurskatalog installieren."
                    ).classes("text-sm text-grey-7")
                catalog_refresh_button = ui.button(
                    "Katalog aktualisieren", icon="refresh"
                ).props("flat dense")
            catalog_container = ui.column().classes("w-full gap-2")
            catalog_state = {"courses": load_course_catalog(online=False)}

            def render_course_catalog() -> None:
                catalog_container.clear()
                installed_repositories = set()
                for path in get_course_directories():
                    try:
                        installed_setup = course_setup_info(path)
                    except (OSError, ValueError):
                        installed_setup = None
                    if installed_setup is not None:
                        installed_repositories.add(
                            installed_setup.repository.removesuffix(".git")
                        )
                with catalog_container:
                    for catalog_course in catalog_state["courses"]:
                        installed = (
                            catalog_course.setup.repository.removesuffix(".git")
                            in installed_repositories
                        )
                        caption = " · ".join(catalog_course.tags)
                        if installed:
                            caption += " · Installiert"
                        with ui.expansion(
                            f"{catalog_course.setup.course} · {catalog_course.level}",
                            caption=caption,
                            icon="menu_book",
                        ).classes("w-full border rounded").props(
                            "header-class='text-primary'"
                        ):
                            ui.label(catalog_course.description).classes(
                                "text-sm text-grey-8"
                            )
                            with ui.row().classes("w-full items-center gap-2"):
                                ui.label(
                                    f"{catalog_course.setup.school} · "
                                    f"{catalog_course.setup.teacher}"
                                ).classes("text-xs text-grey-6")
                                ui.space()
                                ui.link(
                                    "Repository ansehen",
                                    catalog_course.setup.repository.removesuffix(".git"),
                                    new_tab=True,
                                ).classes("text-xs text-primary")
                            with ui.row().classes(
                                "w-full items-center justify-end gap-2"
                            ):
                                if installed:
                                    ui.badge("Bereits installiert", color="positive")
                                else:
                                    install_button = ui.button(
                                        "Installieren", icon="download"
                                    ).props("outline color=primary")
                                    install_status = ui.row().classes(
                                        "items-center gap-2 text-primary"
                                    )
                                    with install_status:
                                        ui.spinner(size="sm", color="primary")
                                        ui.label("Kurs wird geladen …")
                                    install_status.set_visibility(False)

                                    async def install_catalog_course(
                                        item=catalog_course,
                                        button=install_button,
                                        status=install_status,
                                    ) -> None:
                                        button.disable()
                                        try:
                                            if not await confirm_external_course_import(
                                                ui,
                                                item.setup.course,
                                                item.setup.repository,
                                            ):
                                                button.enable()
                                                return
                                            collision = await choose_course_collision(
                                                item.setup
                                            )
                                            if collision is None:
                                                button.enable()
                                                return
                                            status.set_visibility(True)
                                            info, _course = await nicegui_run.io_bound(
                                                install_new_course_setup,
                                                item.setup_data,
                                                collision=collision,
                                            )
                                            course_selection_state["confirmed"] = True
                                            course_sync_state.update(
                                                result=None, error="", pending=False
                                            )
                                            ui.notify(
                                                f"{info.course} wurde installiert.",
                                                type="positive",
                                            )
                                            ui.navigate.reload()
                                        except Exception as error:
                                            status.set_visibility(False)
                                            button.enable()
                                            ui.notify(
                                                f"Kursinstallation fehlgeschlagen: {error}",
                                                type="negative",
                                            )

                                    install_button.on(
                                        "click",
                                        lambda _, action=install_catalog_course: action(),
                                    )

            async def refresh_course_catalog() -> None:
                catalog_refresh_button.disable()
                try:
                    catalog_state["courses"] = await nicegui_run.io_bound(
                        load_course_catalog
                    )
                    render_course_catalog()
                    ui.notify("Kurskatalog wurde aktualisiert.", type="positive")
                finally:
                    catalog_refresh_button.enable()

            catalog_refresh_button.on("click", refresh_course_catalog)
            render_course_catalog()
        return True
    return False


__all__ = ["course_name_confirmation_matches", "render_course_selection"]
