"""Portabler Export und kontrolliertes Entfernen lokaler in:si-Daten."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from . import __version__
from .course import (
    _config_directory,
    get_course_directories,
    validate_registered_course,
)


EXPORT_FORMAT = "insi-local-data-v1"
REPRODUCIBLE_APP_DIRECTORIES = frozenset({"content", "runtimes"})


@dataclass(frozen=True)
class LocalDataExport:
    path: Path
    files: int
    bytes: int
    courses: int
    skipped_symlinks: tuple[str, ...]
    missing_courses: tuple[str, ...]


@dataclass(frozen=True)
class LocalDataDeletion:
    trashed: tuple[Path, ...]
    missing_courses: tuple[Path, ...]


def local_data_roots() -> tuple[Path, tuple[Path, ...]]:
    """Liefere App-Datenwurzel und registrierte Kursordner ohne Schreibzugriff."""
    app_data = _config_directory().expanduser().absolute()
    courses = tuple(dict.fromkeys(get_course_directories()))
    return app_data, courses


def _requested_export_path(destination: str | Path | None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    directory = (
        Path(destination).expanduser().absolute()
        if destination is not None
        else Path.home() / "Downloads"
    )
    return directory / f"insi-datenexport-{stamp}.zip"


def _regular_files(
    root: Path,
    *,
    excluded_top_level: frozenset[str] = frozenset(),
) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    skipped: list[Path] = []
    for directory, names, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        kept_names = []
        for name in sorted(names):
            path = current / name
            if current == root and name in excluded_top_level:
                continue
            if path.is_symlink():
                skipped.append(path)
            else:
                kept_names.append(name)
        names[:] = kept_names
        for name in sorted(filenames):
            path = current / name
            if path.is_symlink() or not path.is_file():
                skipped.append(path)
            else:
                files.append(path)
    return files, skipped


def _assert_export_outside_sources(target: Path, roots: tuple[Path, ...]) -> None:
    resolved_target = target.resolve(strict=False)
    for root in roots:
        if root.exists() and resolved_target.is_relative_to(root.resolve()):
            raise ValueError(
                "Der Datenexport muss außerhalb der zu exportierenden Ordner liegen."
            )


def create_local_data_export(
    destination: str | Path | None = None,
) -> LocalDataExport:
    """Exportiere persönliche App-Daten und alle erreichbaren registrierten Kurse."""
    app_data, registered_courses = local_data_roots()
    if app_data.is_symlink():
        raise ValueError("Der App-Datenordner darf kein symbolischer Link sein.")
    courses = tuple(
        validate_registered_course(course)
        for course in registered_courses
        if course.exists()
    )
    missing = tuple(str(course) for course in registered_courses if not course.is_dir())
    roots = ((app_data,) if app_data.is_dir() else ()) + courses
    target = _requested_export_path(destination)
    _assert_export_outside_sources(target, roots)
    target.parent.mkdir(parents=True, exist_ok=True)

    sources: list[tuple[Path, str, frozenset[str]]] = []
    if app_data.is_dir():
        sources.append((app_data, "app-data", REPRODUCIBLE_APP_DIRECTORIES))
    course_entries = []
    for index, course in enumerate(courses, 1):
        prefix = f"courses/{index:02d}-{course.name}"
        sources.append((course, prefix, frozenset()))
        course_entries.append(
            {"archive_path": prefix, "name": course.name, "original_path": str(course)}
        )

    temporary: Path | None = None
    file_count = 0
    byte_count = 0
    skipped: list[str] = []
    try:
        with NamedTemporaryFile(
            "wb",
            dir=target.parent,
            prefix=".insi-data-export-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
            for root, prefix, excluded in sources:
                files, ignored = _regular_files(
                    root, excluded_top_level=excluded
                )
                skipped.extend(str(path) for path in ignored)
                for path in files:
                    archive.write(path, f"{prefix}/{path.relative_to(root).as_posix()}")
                    file_count += 1
                    byte_count += path.stat().st_size
            manifest = {
                "format": EXPORT_FORMAT,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "insi_version": __version__,
                "excluded_reproducible_app_directories": sorted(
                    REPRODUCIBLE_APP_DIRECTORIES
                ),
                "courses": course_entries,
                "missing_courses": list(missing),
                "skipped_symlinks": skipped,
            }
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            )
        with temporary.open("rb") as exported:
            os.fsync(exported.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return LocalDataExport(
        target, file_count, byte_count, len(courses), tuple(skipped), missing
    )


def _safe_app_data_root(path: Path) -> Path:
    if path.is_symlink():
        raise ValueError("Der App-Datenordner darf kein symbolischer Link sein.")
    resolved = path.resolve()
    if resolved in {Path.home().resolve(), Path(resolved.anchor)}:
        raise ValueError("Dieser App-Datenordner darf nicht entfernt werden.")
    return resolved


def _outermost_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    result: list[Path] = []
    for path in sorted(paths, key=lambda item: len(item.parts)):
        if not any(path == parent or path.is_relative_to(parent) for parent in result):
            result.append(path)
    return tuple(result)


def trash_all_local_data() -> LocalDataDeletion:
    """Verschiebe alle erreichbaren registrierten Kurse und App-Daten in den Müll."""
    app_data, registered_courses = local_data_roots()
    missing = tuple(course for course in registered_courses if not course.exists())
    courses = tuple(
        validate_registered_course(course)
        for course in registered_courses
        if course.exists()
    )
    targets = courses
    if app_data.exists():
        targets += (_safe_app_data_root(app_data),)
    targets = _outermost_paths(targets)
    if not targets:
        return LocalDataDeletion((), missing)
    try:
        from send2trash import send2trash
    except ImportError as error:
        raise RuntimeError("Die Papierkorb-Unterstützung ist nicht installiert.") from error
    for target in targets:
        send2trash(str(target))
    return LocalDataDeletion(targets, missing)
