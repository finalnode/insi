"""Kleine Kurswerkstatt zum Erzeugen portabler PyKIM-Kurse."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from pykim.trainer.authoring import RULE_LABELS, RULE_TEMPLATES, generate_exercise_source

from .author_workspace import AuthorDraft, assignment_markdown, validate_author_draft

from .course_archive import build_course_archive
from .course_runtime import (
    RUNTIME_FILENAME,
    RUNTIME_PYTHON,
    RUNTIME_TARGETS,
    RuntimeManifest,
    combined_runtime_requirements,
    download_offline_wheels,
    manifest_with_wheels,
    parse_runtime_requirements,
    runtime_manifest_bytes,
    write_runtime_manifest,
)
from .course_setup import generate_course_setup
from .library import is_repository_document
from .markedown import validate_markedown


@dataclass(frozen=True)
class CourseFileCandidate:
    relative_path: str
    suggested_kind: str
    reason: str


def analyze_course_directory(source: str | Path) -> tuple[CourseFileCandidate, ...]:
    """Ordne noch unstrukturierte Text-, Markdown- und YAML-Dateien heuristisch ein."""
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError("Der zu analysierende Ordner wurde nicht gefunden.")
    result = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part.startswith("_") or part.startswith(".") for part in relative.parts):
            continue
        if relative.parts[0] in {"Skripte", "Aufgaben", "Trainer"}:
            continue
        suffix = path.suffix.casefold()
        if suffix not in {".md", ".markdown", ".txt", ".yml", ".yaml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if suffix in {".yml", ".yaml"}:
            try:
                import yaml

                payload = yaml.safe_load(text)
            except yaml.YAMLError:
                payload = None
            if isinstance(payload, dict) and payload.get("format") == 1:
                kind, reason = "trainer", "YAML mit PyKIM-Formatkennung"
            else:
                kind, reason = "ignore", "YAML ohne erkennbare Trainerdefinition"
        elif is_repository_document(relative):
            kind, reason = "ignore", "Übliche Repository-Dokumentation"
        elif any(
            marker in text
            for marker in ("@difficulty:", "@hint:", "@block:", "## Anforderungen")
        ):
            kind, reason = "task", "Aufgabenannotation oder Anforderungen erkannt"
        elif text.lstrip().startswith("#"):
            kind, reason = "script", "Markdown-Überschrift erkannt"
        else:
            kind, reason = "ignore", "Keine eindeutige Kursstruktur erkannt"
        result.append(CourseFileCandidate(relative.as_posix(), kind, reason))
    return tuple(result)


def import_course_candidates(
    source: str | Path,
    mappings: dict[str, str],
    *,
    paradigm: str = "imperativ",
) -> tuple[Path, ...]:
    """Kopiere bestätigte Zuordnungen in die Kursstruktur, ohne Quellen zu löschen."""
    root = Path(source).expanduser().resolve()
    if paradigm not in {"imperativ", "oop"}:
        raise ValueError("Unbekannter Lernweg.")
    imported = []
    for relative_name, kind in mappings.items():
        if kind == "ignore":
            continue
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsicherer Quelldateipfad.")
        source_path = (root / relative).resolve()
        if root not in source_path.parents or not source_path.is_file() or source_path.is_symlink():
            raise ValueError("Die Quelldatei liegt außerhalb des Kursordners.")
        if kind == "trainer":
            destination = root / "Trainer" / f"{source_path.stem}.yml"
        elif kind in {"script", "task"}:
            folder = "Skripte" if kind == "script" else "Aufgaben"
            destination = root / folder / paradigm / f"{source_path.stem}.md"
        else:
            raise ValueError("Unbekannte Dateizuordnung.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        candidate = destination
        index = 2
        while candidate.exists():
            candidate = destination.with_name(f"{destination.stem}-{index}{destination.suffix}")
            index += 1
        shutil.copy2(source_path, candidate)
        imported.append(candidate)
    return tuple(imported)


def _available_output(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def course_source_counts(source: str | Path) -> dict[str, int]:
    root = Path(source).expanduser().resolve()

    def count(directory: str, suffix: str) -> int:
        location = root / directory
        if not location.is_dir():
            return 0
        return sum(
            1
            for path in location.rglob(f"*{suffix}")
            if path.is_file()
            and not path.is_symlink()
            and not any(part.startswith("_") for part in path.relative_to(root).parts)
            and not is_repository_document(path)
        )

    return {
        "scripts": count("Skripte", ".md"),
        "assignments": count("Aufgaben", ".md"),
        "trainers": count("Trainer", ".yml"),
    }


def ensure_course_source(source: str | Path) -> Path:
    root = Path(source).expanduser().resolve()
    for directory in ("Skripte", "Aufgaben", "Trainer"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    return root


def _document_path(
    source: str | Path,
    kind: str,
    name: str,
    *,
    paradigm: str = "imperativ",
) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", name):
        raise ValueError(
            "Der Dateiname darf nur Kleinbuchstaben, Zahlen, - und _ enthalten."
        )
    root = Path(source).expanduser().resolve()
    if kind == "trainer":
        return root / "Trainer" / f"{name}.yml"
    if kind not in {"Skripte", "Aufgaben"} or paradigm not in {"imperativ", "oop"}:
        raise ValueError("Unbekannter Kursbereich.")
    return root / kind / paradigm / f"{name}.md"


def course_documents(
    source: str | Path,
    kind: str,
    *,
    paradigm: str = "imperativ",
) -> tuple[str, ...]:
    root = Path(source).expanduser().resolve()
    directory = root / "Trainer" if kind == "trainer" else root / kind / paradigm
    suffix = ".yml" if kind == "trainer" else ".md"
    if not directory.is_dir():
        return ()
    return tuple(
        path.stem
        for path in sorted(directory.glob(f"*{suffix}"))
        if path.is_file()
        and not path.name.startswith("_")
        and not is_repository_document(path)
    )


def load_course_document(
    source: str | Path,
    kind: str,
    name: str,
    *,
    paradigm: str = "imperativ",
) -> str:
    return _document_path(source, kind, name, paradigm=paradigm).read_text(
        encoding="utf-8"
    )


def save_course_markdown(
    source: str | Path,
    kind: str,
    name: str,
    content: str,
    *,
    paradigm: str = "imperativ",
) -> Path:
    if kind not in {"Skripte", "Aufgaben"}:
        raise ValueError("Markdown kann nur als Skript oder Aufgabe gespeichert werden.")
    issues = validate_markedown(
        content, kind="script" if kind == "Skripte" else "task"
    )
    if issues:
        raise ValueError(
            " ".join(f"Zeile {issue.line}: {issue.message}" for issue in issues)
        )
    target = _document_path(source, kind, name, paradigm=paradigm)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")
    return target


def save_course_assignment(
    source: str | Path,
    draft: AuthorDraft,
    *,
    paradigm: str = "imperativ",
) -> tuple[Path, Path]:
    issues = validate_author_draft(draft)
    if issues:
        raise ValueError(" ".join(issues))
    markdown = _document_path(source, "Aufgaben", draft.name, paradigm=paradigm)
    trainer = _document_path(source, "trainer", draft.name)
    markdown.parent.mkdir(parents=True, exist_ok=True)
    trainer.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text(draft.assignment_markdown.rstrip() + "\n", encoding="utf-8")
    trainer.write_text(draft.trainer_source.rstrip() + "\n", encoding="utf-8")
    return markdown, trainer


def create_portable_course(
    source: str | Path,
    *,
    teacher: str,
    school: str,
    course: str,
    repository: str = "",
    branch: str = "main",
    additional_requirements: str | tuple[str, ...] = (),
    include_offline_packages: bool = False,
    offline_targets: tuple[str, ...] = (),
) -> tuple[Path, Path]:
    """Erzeuge ein kleines Kurs-ZIP oder bewusst ein erweitertes Offlinepaket."""
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError("Der Kursordner wurde nicht gefunden.")
    extra = parse_runtime_requirements(additional_requirements)
    requirements = combined_runtime_requirements(extra)
    if offline_targets and not include_offline_packages:
        raise ValueError("Zielplattformen benötigen den aktivierten Offline-Export.")
    if include_offline_packages and not extra:
        raise ValueError(
            "Gib mindestens ein zusätzliches Paket an, bevor du Pakete einbettest. "
            "PyKIM und Pyxel liefert in:si bereits selbst mit."
        )
    if include_offline_packages and not offline_targets:
        raise ValueError("Wähle mindestens eine Zielplattform für das Offlinepaket.")
    setup = generate_course_setup(
        root,
        teacher=teacher,
        school=school,
        course=course,
        repository=repository,
        branch=branch,
    )
    output = _available_output(root.parent / f"{setup.stem}.zip")
    source_manifest = RuntimeManifest(RUNTIME_PYTHON, requirements)
    manifest_path = write_runtime_manifest(root / RUNTIME_FILENAME, source_manifest)
    if include_offline_packages:
        with TemporaryDirectory(prefix="insi-offline-export-") as temporary:
            wheels = download_offline_wheels(
                extra,
                tuple(offline_targets),
                temporary,
            )
            manifest = manifest_with_wheels(
                requirements,
                tuple(offline_targets),
                wheels,
            )
            output.write_bytes(
                build_course_archive(
                    root,
                    setup,
                    runtime_manifest=runtime_manifest_bytes(manifest),
                    offline_wheels=wheels,
                )
            )
    else:
        output.write_bytes(
            build_course_archive(root, setup, runtime_manifest=manifest_path)
        )
    return setup, output


def register_course_builder_page(ui, nicegui_app, nicegui_run, *, desktop: bool) -> None:
    @ui.page("/course-builder")
    def course_builder() -> None:
        ui.colors(primary="#f36b2b", secondary="#9b9da0", accent="#5f6164")
        with ui.column().classes("w-full max-w-3xl mx-auto gap-4 p-6"):
            with ui.row().classes("w-full items-center gap-2"):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/"),
                ).props("flat round")
                ui.label("PyKIM Kurswerkstatt").classes("text-2xl font-bold text-primary")
            ui.label(
                "Erzeugt eine Setupdatei im Kursordner und ein direkt "
                "importierbares Kurs-ZIP."
            ).classes("text-grey-7")

            with ui.card().classes("w-full shadow-none border"):
                ui.label("Kursordner").classes("text-lg font-bold")
                source = ui.input(
                    "Ordner mit Skripte, Aufgaben und Trainer",
                    placeholder=str(Path.home() / "Mein-PyKIM-Kurs"),
                ).classes("w-full")
                source_status = ui.label("Noch kein Kursordner ausgewählt.").classes(
                    "text-sm text-grey-7"
                )

                def refresh_source_status() -> None:
                    if not source.value:
                        source_status.set_text("Noch kein Kursordner ausgewählt.")
                        return
                    counts = course_source_counts(source.value)
                    source_status.set_text(
                        f"{counts['scripts']} Skriptdateien · "
                        f"{counts['assignments']} Aufgaben · "
                        f"{counts['trainers']} Trainerdateien"
                    )

                async def choose_source() -> None:
                    if not desktop or nicegui_app.native.main_window is None:
                        return
                    import webview

                    selected = await nicegui_app.native.main_window.create_file_dialog(
                        dialog_type=webview.FileDialog.FOLDER,
                        directory=str(Path.home()),
                    )
                    if selected:
                        source.set_value(str(Path(selected[0]).resolve()))
                        refresh_source_status()

                with ui.row().classes("items-center gap-2"):
                    if desktop:
                        ui.button(
                            "Ordner auswählen", icon="folder_open", on_click=choose_source
                        ).props("outline")

                    def create_structure() -> None:
                        if not source.value:
                            ui.notify("Gib zuerst einen Kursordner an.", type="warning")
                            return
                        ensure_course_source(source.value)
                        refresh_source_status()
                        ui.notify("Kursstruktur ist bereit.", type="positive")

                    ui.button(
                        "Struktur anlegen", icon="create_new_folder", on_click=create_structure
                    ).props("outline")
                source.on_value_change(lambda _: refresh_source_status())

            with ui.card().classes("w-full shadow-none border"):
                ui.label("Kursangaben").classes("text-lg font-bold")
                course_name = ui.input("Kursname").classes("w-full")
                with ui.row().classes("w-full gap-3 items-start flex-wrap"):
                    teacher = ui.input("Lehrkraft oder Herausgeber").classes("grow")
                    school = ui.input("Schule oder Organisation").classes("grow")
                repository = ui.input(
                    "Repository (optional)",
                    placeholder="https://github.com/name/kurs.git",
                ).classes("w-full")
                branch = ui.input("Branch", value="main").classes("w-48")
                ui.label(
                    "Die Setupdatei wird auch in den Kursstamm geschrieben. Damit "
                    "ist später ebenfalls das normale Repository-ZIP importierbar."
                ).classes("text-sm text-grey-7")

            with ui.card().classes("w-full shadow-none border"):
                ui.label("Runtime und Exportgröße").classes("text-lg font-bold")
                ui.label(
                    "PyKIM und Pyxel werden von in:si bereitgestellt. Zusätzliche "
                    "Pakete müssen mit einer exakten Version angegeben werden."
                ).classes("text-sm text-grey-7")
                additional_packages = ui.textarea(
                    "Zusätzliche Pythonpakete – eines pro Zeile",
                    placeholder="numpy==2.2.3\nrequests==2.32.5",
                ).props("outlined autogrow").classes("w-full")
                include_offline_packages = ui.checkbox(
                    "Zusätzliche Pakete für eine vollständig offline nutzbare Installation einbetten",
                    value=False,
                )
                ui.label(
                    "Standardmäßig bleibt das Kurs-ZIP klein. Aktiviere diese "
                    "Option nur, wenn die Zusatzpakete ohne Internet installiert werden müssen."
                ).classes("text-sm text-grey-7")
                offline_options = ui.column().classes(
                    "w-full gap-2 rounded border p-3 bg-orange-1"
                )
                with offline_options:
                    ui.label("Zielplattformen").classes("font-bold")
                    ui.label(
                        "Jede zusätzliche Plattform kann das Archiv deutlich vergrößern. "
                        "Die tatsächliche Größe wird nach dem Export angezeigt."
                    ).classes("text-sm text-orange-10")
                    target_choices = {
                        target_id: ui.checkbox(target.label, value=False)
                        for target_id, target in RUNTIME_TARGETS.items()
                    }
                offline_options.bind_visibility_from(
                    include_offline_packages, "value"
                )

            with ui.expansion("Skripte schreiben", icon="menu_book").classes(
                "w-full border rounded"
            ):
                ui.label(
                    "Schreibe Kapitel direkt als Markdown. Python-Blöcke können "
                    "wie gewohnt mit ```python eingefügt werden."
                ).classes("text-sm text-grey-7")
                with ui.row().classes("w-full gap-3 items-end"):
                    script_paradigm = ui.select(
                        {"imperativ": "Imperativ", "oop": "OOP"},
                        value="imperativ",
                        label="Lernweg",
                    ).classes("w-40")
                    script_name = ui.input(
                        "Dateiname", placeholder="01-erste-schritte"
                    ).classes("grow")
                    existing_script = ui.select(
                        [], label="Vorhandenes Kapitel laden"
                    ).classes("grow")
                script_editor = ui.codemirror(
                    value=(
                        "# Neues Kapitel\n\n"
                        "Erkläre hier das Thema.\n\n"
                        "```python\nfrom pykim import *\n\n# Beispiel\n```\n"
                    ),
                    language="Markdown",
                    line_wrapping=True,
                ).classes("w-full").style("height: 25rem")

                def refresh_script_options() -> None:
                    if not source.value:
                        existing_script.set_options([])
                        return
                    existing_script.set_options(
                        list(
                            course_documents(
                                source.value,
                                "Skripte",
                                paradigm=script_paradigm.value or "imperativ",
                            )
                        )
                    )

                def load_script() -> None:
                    if not source.value or not existing_script.value:
                        return
                    try:
                        script_name.set_value(existing_script.value)
                        script_editor.set_value(
                            load_course_document(
                                source.value,
                                "Skripte",
                                existing_script.value,
                                paradigm=script_paradigm.value or "imperativ",
                            )
                        )
                    except (OSError, ValueError) as error:
                        ui.notify(str(error), type="negative")

                def save_script() -> None:
                    if not source.value:
                        ui.notify("Wähle zuerst den Kursordner.", type="warning")
                        return
                    try:
                        target = save_course_markdown(
                            source.value,
                            "Skripte",
                            script_name.value or "",
                            script_editor.value or "",
                            paradigm=script_paradigm.value or "imperativ",
                        )
                        refresh_script_options()
                        refresh_source_status()
                        ui.notify(f"Kapitel gespeichert: {target.name}", type="positive")
                    except (OSError, ValueError) as error:
                        ui.notify(str(error), type="negative")

                script_paradigm.on_value_change(lambda _: refresh_script_options())
                existing_script.on_value_change(lambda _: load_script())
                ui.button("Skript speichern", icon="save", on_click=save_script)

            with ui.expansion("PyKIM-Aufgabe und Trainer erstellen", icon="rule").classes(
                "w-full border rounded"
            ):
                ui.label(
                    "Aufgabentext und sichere Trainerdefinition werden gemeinsam "
                    "erstellt und auf Übereinstimmung geprüft."
                ).classes("text-sm text-grey-7")
                with ui.row().classes("w-full gap-3"):
                    task_name = ui.input(
                        "Aufgabenkennung", placeholder="meine-aufgabe"
                    ).classes("grow")
                    task_title = ui.input("Titel", placeholder="Meine Aufgabe").classes(
                        "grow"
                    )
                    task_paradigm = ui.select(
                        {"imperativ": "Imperativ", "oop": "OOP"},
                        value="imperativ",
                        label="Lernweg",
                    ).classes("w-40")
                existing_task = ui.select(
                    [], label="Vorhandene Aufgabe laden"
                ).classes("w-full")
                task_summary = ui.input(
                    "Kurze Aufgabenstellung", placeholder="Zeichne ..."
                ).classes("w-full")
                task_requirements = ui.textarea(
                    "Anforderungen – eine pro Zeile",
                    placeholder="Beginne bei ...\nVerwende eine Schleife ...",
                ).props("outlined autogrow").classes("w-full")
                with ui.row().classes("w-full gap-3"):
                    task_difficulty = ui.select(
                        {
                            "einfach": "Einfach",
                            "mittel": "Mittel",
                            "fortgeschritten": "Fortgeschritten",
                        },
                        value="mittel",
                        label="Schwierigkeit",
                    ).classes("w-full sm:w-48")
                    task_rules = ui.select(
                        {key: RULE_LABELS[key] for key in RULE_TEMPLATES},
                        multiple=True,
                        label="Prüfbausteine",
                    ).classes("grow min-w-64")
                    task_optimal = ui.number(
                        "Optimale Codezeilen", min=1
                    ).props("hint='optional' persistent-hint").classes(
                        "w-full sm:w-52"
                    )
                with ui.tabs().classes("w-full") as editor_tabs:
                    markdown_tab = ui.tab("Aufgabe.md")
                    trainer_tab = ui.tab("Trainer.yml")
                with ui.tab_panels(editor_tabs, value=markdown_tab).classes("w-full"):
                    with ui.tab_panel(markdown_tab):
                        task_markdown = ui.codemirror(
                            value="", language="Markdown", line_wrapping=True
                        ).classes("w-full").style("height: 24rem")
                    with ui.tab_panel(trainer_tab):
                        task_trainer = ui.codemirror(
                            value="", language="YAML", line_wrapping=False
                        ).classes("w-full").style("height: 24rem")
                task_validation = ui.label("Noch kein Entwurf erzeugt.").classes(
                    "text-grey-7"
                )

                def current_task_draft() -> AuthorDraft:
                    return AuthorDraft(
                        task_name.value or "",
                        task_trainer.value or "",
                        task_markdown.value or "",
                    )

                def refresh_task_options() -> None:
                    if not source.value:
                        existing_task.set_options([])
                        return
                    existing_task.set_options(
                        list(
                            course_documents(
                                source.value,
                                "Aufgaben",
                                paradigm=task_paradigm.value or "imperativ",
                            )
                        )
                    )

                def load_task() -> None:
                    if not source.value or not existing_task.value:
                        return
                    try:
                        task_name.set_value(existing_task.value)
                        markdown = load_course_document(
                            source.value,
                            "Aufgaben",
                            existing_task.value,
                            paradigm=task_paradigm.value or "imperativ",
                        )
                        trainer = load_course_document(
                            source.value,
                            "trainer",
                            existing_task.value,
                        )
                        task_markdown.set_value(markdown)
                        task_trainer.set_value(trainer)
                        title_line = next(
                            (
                                line.removeprefix("# ").strip()
                                for line in markdown.splitlines()
                                if line.startswith("# ")
                            ),
                            existing_task.value,
                        )
                        task_title.set_value(title_line)
                        validate_task()
                    except (OSError, ValueError) as error:
                        ui.notify(str(error), type="negative")

                def validate_task() -> tuple[str, ...]:
                    issues = validate_author_draft(current_task_draft())
                    task_validation.set_text(
                        "✓ Aufgabe und Trainer sind vollständig."
                        if not issues
                        else "✗ " + " · ".join(issues)
                    )
                    task_validation.classes(
                        remove="text-grey-7 text-positive text-negative",
                        add="text-positive" if not issues else "text-negative",
                    )
                    return issues

                def generate_task() -> None:
                    try:
                        task_trainer.set_value(
                            generate_exercise_source(
                                task_name.value or "",
                                task_title.value or "",
                                tuple(task_rules.value or ()),
                                optimal_lines=(
                                    int(task_optimal.value)
                                    if task_optimal.value
                                    else None
                                ),
                            )
                        )
                        task_markdown.set_value(
                            assignment_markdown(
                                task_title.value or "",
                                task_summary.value or "",
                                task_requirements.value or "",
                                task_difficulty.value or "mittel",
                            )
                        )
                        validate_task()
                        ui.notify("Aufgabe und Trainer wurden erzeugt.", type="positive")
                    except ValueError as error:
                        ui.notify(str(error), type="warning")

                def save_task() -> None:
                    if not source.value:
                        ui.notify("Wähle zuerst den Kursordner.", type="warning")
                        return
                    if validate_task():
                        ui.notify("Behebe zuerst die angezeigten Fehler.", type="warning")
                        return
                    try:
                        markdown, trainer = save_course_assignment(
                            source.value,
                            current_task_draft(),
                            paradigm=task_paradigm.value or "imperativ",
                        )
                        refresh_source_status()
                        refresh_task_options()
                        ui.notify(
                            f"{markdown.name} und {trainer.name} gespeichert.",
                            type="positive",
                        )
                    except (OSError, ValueError) as error:
                        ui.notify(str(error), type="negative")

                task_markdown.on("update:model-value", lambda: validate_task())
                task_trainer.on("update:model-value", lambda: validate_task())
                task_paradigm.on_value_change(lambda _: refresh_task_options())
                existing_task.on_value_change(lambda _: load_task())
                source.on_value_change(
                    lambda _: (refresh_script_options(), refresh_task_options())
                )
                with ui.row().classes("gap-2"):
                    ui.button(
                        "Entwurf erzeugen", icon="auto_fix_high", on_click=generate_task
                    )
                    ui.button(
                        "Aufgabe und Trainer speichern", icon="save", on_click=save_task
                    ).props("outline")

            activity = ui.column().classes("w-full gap-1")
            with activity:
                with ui.row().classes("items-center gap-2"):
                    ui.spinner(size="sm", color="primary")
                    ui.label("Kurs wird geprüft und gepackt …")
                ui.linear_progress(value=None, color="primary").props("indeterminate")
            activity.set_visibility(False)

            async def build() -> None:
                values = (
                    source.value,
                    teacher.value,
                    school.value,
                    course_name.value,
                    branch.value,
                )
                if not all(str(value or "").strip() for value in values):
                    ui.notify("Fülle bitte alle Kursangaben aus.", type="warning")
                    return
                selected_targets = tuple(
                    target_id
                    for target_id, checkbox in target_choices.items()
                    if checkbox.value
                )
                if include_offline_packages.value and not selected_targets:
                    ui.notify(
                        "Wähle mindestens eine Zielplattform für das Offlinepaket.",
                        type="warning",
                    )
                    return
                activity.set_visibility(True)
                build_button.disable()
                try:
                    setup, archive = await nicegui_run.io_bound(
                        create_portable_course,
                        source.value,
                        teacher=teacher.value,
                        school=school.value,
                        course=course_name.value,
                        repository=repository.value or "",
                        branch=branch.value,
                        additional_requirements=additional_packages.value or "",
                        include_offline_packages=bool(include_offline_packages.value),
                        offline_targets=selected_targets,
                    )
                    refresh_source_status()
                    ui.notify(
                        f"Kurs erstellt: {archive.name}",
                        type="positive",
                        timeout=6000,
                    )
                    with ui.dialog() as result_dialog, ui.card().classes("w-full max-w-xl"):
                        ui.label("Kurs ist bereit").classes("text-xl font-bold")
                        ui.label(f"Setupdatei: {setup}").classes("break-all")
                        ui.label(f"Kurs-ZIP: {archive}").classes("break-all")
                        ui.label(
                            f"Archivgröße: {archive.stat().st_size / (1024 * 1024):.1f} MB"
                        )
                        if include_offline_packages.value:
                            labels = ", ".join(
                                RUNTIME_TARGETS[target].label
                                for target in selected_targets
                            )
                            ui.label(f"Eingebettete Zielplattformen: {labels}")
                        else:
                            ui.label(
                                "Kompakter Export ohne eingebettete Zusatzpakete."
                            ).classes("text-grey-7")
                        with ui.row().classes("w-full justify-end"):
                            ui.button("Schließen", on_click=result_dialog.close)
                    result_dialog.open()
                except Exception as error:
                    ui.notify(f"Kurs konnte nicht erstellt werden: {error}", type="negative")
                finally:
                    activity.set_visibility(False)
                    build_button.enable()

            build_button = ui.button(
                "Setupdatei und Kurs-ZIP erstellen",
                icon="inventory_2",
                on_click=build,
            ).classes("self-end")


__all__ = [
    "CourseFileCandidate",
    "analyze_course_directory",
    "course_documents",
    "course_source_counts",
    "create_portable_course",
    "ensure_course_source",
    "load_course_document",
    "import_course_candidates",
    "register_course_builder_page",
    "save_course_assignment",
    "save_course_markdown",
]
