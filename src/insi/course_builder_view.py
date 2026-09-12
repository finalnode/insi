"""Datei- und Exportfunktionen für die visuelle Kurswerkstatt."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .author_workspace import AuthorDraft, validate_author_draft

from .course_archive import build_course_archive
from .course_runtime import (
    RUNTIME_FILENAME,
    RuntimeManifest,
    download_offline_wheels,
    manifest_with_wheels,
    parse_runtime_manifest,
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
    runtime_python: str,
    runtime_requirements: str | tuple[str, ...],
    include_offline_packages: bool = False,
    offline_targets: tuple[str, ...] = (),
) -> tuple[Path, Path]:
    """Erzeuge ein kleines Kurs-ZIP oder bewusst ein erweitertes Offlinepaket."""
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError("Der Kursordner wurde nicht gefunden.")
    requirements = parse_runtime_requirements(runtime_requirements)
    if offline_targets and not include_offline_packages:
        raise ValueError("Zielplattformen benötigen den aktivierten Offline-Export.")
    if include_offline_packages and not requirements:
        raise ValueError(
            "Gib mindestens ein Kurspaket an, bevor du Pakete einbettest."
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
    source_manifest = parse_runtime_manifest(
        runtime_manifest_bytes(RuntimeManifest(runtime_python, requirements))
    )
    manifest_path = write_runtime_manifest(root / RUNTIME_FILENAME, source_manifest)
    if include_offline_packages:
        with TemporaryDirectory(prefix="insi-offline-export-") as temporary:
            wheels = download_offline_wheels(
                requirements,
                tuple(offline_targets),
                temporary,
            )
            manifest = manifest_with_wheels(
                source_manifest.python,
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



__all__ = [
    "CourseFileCandidate",
    "analyze_course_directory",
    "course_documents",
    "course_source_counts",
    "create_portable_course",
    "ensure_course_source",
    "load_course_document",
    "import_course_candidates",
    "save_course_assignment",
    "save_course_markdown",
]
