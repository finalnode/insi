"""Sichere Dateiablage innerhalb der von in:si verwalteten Arbeitsbereiche."""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile

from .course import CONFIG_DIR_ENV


MAX_IMPORTED_FILE_BYTES = 100 * 1024 * 1024
GLOBAL_FILES_DIRECTORY = "Dateien"
COURSE_FILES_DIRECTORY = "Dateien"
PROJECT_FILES_DIRECTORY = "Dateien"
SNAPSHOT_DIRECTORY = "project-snapshots"
MAX_PROJECT_SNAPSHOTS = 10


class FileScope(str, Enum):
    GLOBAL = "global"
    COURSE = "course"
    PROJECT = "project"


@dataclass(frozen=True)
class ImportedWorkspaceFile:
    scope: FileScope
    path: Path
    size: int
    sha256: str


def global_workspace_directory() -> Path:
    """Liefere den app-eigenen, kursübergreifenden Arbeitsbereich."""

    configured = os.environ.get(CONFIG_DIR_ENV)
    config = Path(configured).expanduser() if configured else Path.home() / ".pykim"
    return (config / "insi-workspace").resolve()


def global_files_directory(*, create: bool = False) -> Path:
    directory = global_workspace_directory() / GLOBAL_FILES_DIRECTORY
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def course_files_directory(course: str | Path, *, create: bool = False) -> Path:
    directory = Path(course).expanduser().resolve() / COURSE_FILES_DIRECTORY
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def project_files_directory(project: str | Path, *, create: bool = False) -> Path:
    directory = Path(project).expanduser().resolve() / PROJECT_FILES_DIRECTORY
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def workspace_file_roots(course: str | Path | None = None) -> tuple[Path, ...]:
    """Liefere vorhandene globale und kursweite, nur lesbare Ressourcenwurzeln."""

    roots = [global_files_directory()]
    if course is not None:
        roots.append(course_files_directory(course))
    return tuple(root for root in roots if root.is_dir())


def sandbox_readable_roots(
    course: str | Path | None = None,
    *program_paths: str | Path,
) -> tuple[Path, ...]:
    """Liefere nur die für einen Lauf benötigten Kurs- und Inhaltsdateien."""

    roots = list(workspace_file_roots(course))
    roots.extend(Path(path).expanduser().resolve() for path in program_paths)
    try:
        from .library import PACKAGED_CONTENT_ROOT
        from .updates import active_content_root

        roots.append(active_content_root(PACKAGED_CONTENT_ROOT).resolve())
    except (OSError, RuntimeError, ValueError):
        pass
    if course is not None:
        from .extensions import extension_file

        extension = extension_file(course)
        if extension.is_file():
            roots.append(extension.resolve())
    result: list[Path] = []
    for root in roots:
        if root.exists() and root not in result:
            result.append(root)
    return tuple(result)


def _safe_filename(filename: str) -> str:
    if not isinstance(filename, str) or not filename.strip() or "\x00" in filename:
        raise ValueError("Die Datei benötigt einen gültigen Namen.")
    name = Path(filename).name
    if name != filename or name in {".", ".."}:
        raise ValueError("Der Dateiname darf keinen Verzeichnispfad enthalten.")
    return name


def _destination(
    scope: FileScope,
    *,
    course: str | Path | None = None,
    project: str | Path | None = None,
) -> Path:
    if scope is FileScope.GLOBAL:
        return global_files_directory(create=True)
    if scope is FileScope.COURSE:
        if course is None:
            raise ValueError("Für eine Kursdatei fehlt der ausgewählte Kurs.")
        return course_files_directory(course, create=True)
    if project is None:
        raise ValueError("Für eine Projektdatei fehlt das ausgewählte Projekt.")
    project_root = Path(project).expanduser().resolve()
    if course is not None:
        course_root = Path(course).expanduser().resolve()
        expected = course_root / "Projekte"
        if not project_root.is_relative_to(expected):
            raise ValueError("Das Projekt liegt nicht im ausgewählten Kurs.")
    return project_files_directory(project_root, create=True)


def _unused_target(directory: Path, filename: str) -> Path:
    requested = directory / filename
    if not requested.exists():
        return requested
    stem = requested.stem
    suffix = requested.suffix
    for index in range(2, 10_000):
        candidate = directory / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Es sind zu viele Dateien mit demselben Namen vorhanden.")


def import_workspace_bytes(
    content: bytes,
    filename: str,
    scope: FileScope | str,
    *,
    course: str | Path | None = None,
    project: str | Path | None = None,
) -> ImportedWorkspaceFile:
    """Kopiere Upload-Daten atomar in einen ausdrücklich gewählten Bereich."""

    selected_scope = FileScope(scope)
    name = _safe_filename(filename)
    if len(content) > MAX_IMPORTED_FILE_BYTES:
        raise ValueError("Die Datei ist größer als die erlaubten 100 MB.")
    directory = _destination(selected_scope, course=course, project=project)
    target = _unused_target(directory, name)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "wb", dir=directory, prefix=".insi-import-", delete=False
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return ImportedWorkspaceFile(
        selected_scope,
        target,
        len(content),
        hashlib.sha256(content).hexdigest(),
    )


def import_workspace_file(
    source: str | Path,
    scope: FileScope | str,
    *,
    course: str | Path | None = None,
    project: str | Path | None = None,
) -> ImportedWorkspaceFile:
    """Kopiere genau eine reguläre externe Datei ohne Linkübernahme."""

    path = Path(source).expanduser()
    if path.is_symlink() or not path.is_file():
        raise ValueError("Es können nur reguläre Dateien importiert werden.")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ValueError(f"Die Datei kann nicht gelesen werden: {error}") from error
    if size > MAX_IMPORTED_FILE_BYTES:
        raise ValueError("Die Datei ist größer als die erlaubten 100 MB.")
    return import_workspace_bytes(
        path.read_bytes(),
        path.name,
        scope,
        course=course,
        project=project,
    )


def snapshot_project(
    project: str | Path,
    course: str | Path,
    *,
    keep: int = MAX_PROJECT_SNAPSHOTS,
) -> Path:
    """Sichere ein Projekt vor dem Start und behalte nur begrenzt viele Stände."""

    project_root = Path(project).expanduser().resolve()
    course_root = Path(course).expanduser().resolve()
    projects_root = course_root / "Projekte"
    if not project_root.is_dir() or not project_root.is_relative_to(projects_root):
        raise ValueError("Nur ein vorhandenes Projekt des Kurses kann gesichert werden.")
    if keep <= 0:
        raise ValueError("Mindestens ein Projektstand muss erhalten bleiben.")
    try:
        linked = next((item for item in project_root.rglob("*") if item.is_symlink()), None)
    except OSError as error:
        raise ValueError(f"Das Projekt kann nicht sicher gelesen werden: {error}") from error
    if linked is not None:
        raise ValueError(
            "Projekte mit symbolischen Links werden nur in der externen IDE gestartet."
        )
    backup_root = course_root / ".pykim" / "backups" / SNAPSHOT_DIRECTORY
    relative = project_root.relative_to(projects_root)
    target_root = backup_root.joinpath(*relative.parts)
    target_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    target = target_root / stamp
    shutil.copytree(project_root, target, symlinks=False)
    snapshots = sorted(
        (item for item in target_root.iterdir() if item.is_dir()),
        key=lambda item: item.name,
        reverse=True,
    )
    for expired in snapshots[keep:]:
        if expired.parent == target_root and expired.is_relative_to(backup_root):
            shutil.rmtree(expired)
    return target


__all__ = [
    "COURSE_FILES_DIRECTORY",
    "FileScope",
    "GLOBAL_FILES_DIRECTORY",
    "ImportedWorkspaceFile",
    "MAX_IMPORTED_FILE_BYTES",
    "MAX_PROJECT_SNAPSHOTS",
    "PROJECT_FILES_DIRECTORY",
    "course_files_directory",
    "global_files_directory",
    "global_workspace_directory",
    "import_workspace_bytes",
    "import_workspace_file",
    "project_files_directory",
    "sandbox_readable_roots",
    "snapshot_project",
    "workspace_file_roots",
]
