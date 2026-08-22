"""Benannte und automatische Versionsstände persönlicher Projekte."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4


SNAPSHOT_DIRECTORY = "project-snapshots"
PROJECT_STATE_FORMAT = "insi-project-state-v1"
MAX_PROJECT_SNAPSHOTS = 10


@dataclass(frozen=True)
class ProjectStateFile:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ProjectState:
    id: str
    path: Path
    kind: str
    created_at: str
    title: str
    comment: str
    files: tuple[ProjectStateFile, ...]
    error: str = ""

    @property
    def named(self) -> bool:
        return self.kind == "named"

    @property
    def restorable(self) -> bool:
        return not self.error


def _project_snapshot_roots(
    project: str | Path,
    course: str | Path,
) -> tuple[Path, Path, Path]:
    project_root = Path(project).expanduser().resolve()
    course_root = Path(course).expanduser().resolve()
    projects_root = course_root / "Projekte"
    if not project_root.is_dir() or not project_root.is_relative_to(projects_root):
        raise ValueError("Nur ein vorhandenes Projekt des Kurses kann gesichert werden.")
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
    return project_root, target_root, backup_root


def _state_files(directory: Path) -> tuple[ProjectStateFile, ...]:
    files: list[ProjectStateFile] = []
    try:
        entries = sorted(directory.rglob("*"), key=lambda item: item.as_posix())
    except OSError as error:
        raise ValueError(f"Projektstand konnte nicht gelesen werden: {error}") from error
    for entry in entries:
        if entry.is_symlink():
            raise ValueError("Projektstände mit symbolischen Links sind ungültig.")
        if entry.is_dir():
            continue
        if not entry.is_file():
            raise ValueError("Projektstände dürfen nur reguläre Dateien enthalten.")
        try:
            content = entry.read_bytes()
        except OSError as error:
            raise ValueError(f"Projektstand konnte nicht gelesen werden: {error}") from error
        files.append(
            ProjectStateFile(
                entry.relative_to(directory).as_posix(),
                len(content),
                hashlib.sha256(content).hexdigest(),
            )
        )
    return tuple(files)


def _state_metadata_path(snapshot: Path) -> Path:
    return snapshot.parent / f"{snapshot.name}.json"


def _write_state_metadata(snapshot: Path, document: dict[str, object]) -> None:
    target = _state_metadata_path(snapshot)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".insi-project-state-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(document, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_state_text(value: str, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} muss Text sein.")
    cleaned = value.strip()
    if len(cleaned) > maximum:
        raise ValueError(f"{label} darf höchstens {maximum} Zeichen enthalten.")
    return cleaned


def snapshot_project(
    project: str | Path,
    course: str | Path,
    *,
    keep: int = MAX_PROJECT_SNAPSHOTS,
    title: str = "",
    comment: str = "",
    named: bool = False,
) -> Path:
    """Sichere einen automatischen oder bewusst benannten Projektstand."""

    if keep <= 0:
        raise ValueError("Mindestens ein Projektstand muss erhalten bleiben.")
    clean_title = _validate_state_text(title, "Der Titel", 120)
    clean_comment = _validate_state_text(comment, "Der Kommentar", 2_000)
    if named and not clean_title:
        raise ValueError("Ein benannter Projektstand benötigt einen Titel.")
    project_root, target_root, backup_root = _project_snapshot_roots(project, course)
    target_root.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    stamp = created.strftime("%Y%m%dT%H%M%S.%fZ")
    target = target_root / stamp
    try:
        shutil.copytree(project_root, target, symlinks=False)
        files = _state_files(target)
        _write_state_metadata(
            target,
            {
                "format": PROJECT_STATE_FORMAT,
                "kind": "named" if named else "automatic",
                "created_at": created.isoformat(),
                "title": clean_title,
                "comment": clean_comment,
                "files": [file.__dict__ for file in files],
            },
        )
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        _state_metadata_path(target).unlink(missing_ok=True)
        raise

    automatic = [state for state in project_states(project_root, course) if not state.named]
    for expired in automatic[keep:]:
        if expired.path.parent == target_root and expired.path.is_relative_to(backup_root):
            shutil.rmtree(expired.path)
            _state_metadata_path(expired.path).unlink(missing_ok=True)
    return target


def save_project_state(
    project: str | Path,
    course: str | Path,
    title: str,
    comment: str = "",
) -> ProjectState:
    """Speichere einen dauerhaft benannten Projektstand."""

    snapshot = snapshot_project(
        project,
        course,
        title=title,
        comment=comment,
        named=True,
    )
    return next(state for state in project_states(project, course) if state.path == snapshot)


def snapshot_project_if_changed(
    project: str | Path,
    course: str | Path,
    *,
    keep: int = MAX_PROJECT_SNAPSHOTS,
    title: str = "Automatisch vor Ausführung",
    comment: str = "Stand vor dem Start des Projekts.",
) -> Path | None:
    """Sichere den aktuellen Inhalt nur, wenn er vom letzten intakten Stand abweicht."""

    project_root, _target_root, _backup_root = _project_snapshot_roots(project, course)
    current_files = _state_files(project_root)
    for state in project_states(project_root, course):
        if not state.restorable:
            continue
        try:
            if _state_files(state.path) != state.files:
                continue
        except ValueError:
            continue
        if state.files == current_files:
            return None
        break
    return snapshot_project(
        project_root,
        course,
        keep=keep,
        title=title,
        comment=comment,
    )


def _state_from_snapshot(snapshot: Path) -> ProjectState:
    metadata = _state_metadata_path(snapshot)
    if not metadata.is_file():
        return ProjectState(
            snapshot.name,
            snapshot,
            "automatic",
            snapshot.name,
            "Automatische Sicherung",
            "Älterer Projektstand ohne zusätzliche Beschreibung.",
            _state_files(snapshot),
        )
    document: object = None
    try:
        document = json.loads(metadata.read_text(encoding="utf-8"))
        required = {"format", "kind", "created_at", "title", "comment", "files"}
        if not isinstance(document, dict) or set(document) != required:
            raise ValueError("Metadaten sind unvollständig.")
        if document["format"] != PROJECT_STATE_FORMAT:
            raise ValueError("Unbekanntes Projektstandformat.")
        if document["kind"] not in {"automatic", "named"}:
            raise ValueError("Unbekannte Projektstandart.")
        if not all(isinstance(document[key], str) for key in ("created_at", "title", "comment")):
            raise ValueError("Metadaten enthalten ungültigen Text.")
        raw_files = document["files"]
        if not isinstance(raw_files, list):
            raise ValueError("Die Dateiliste ist ungültig.")
        files = tuple(
            ProjectStateFile(
                str(item["path"]),
                int(item["size"]),
                str(item["sha256"]),
            )
            for item in raw_files
            if isinstance(item, dict) and set(item) == {"path", "size", "sha256"}
        )
        if len(files) != len(raw_files):
            raise ValueError("Die Dateiliste ist unvollständig.")
        return ProjectState(
            snapshot.name,
            snapshot,
            document["kind"],
            document["created_at"],
            document["title"],
            document["comment"],
            files,
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        damaged_kind = (
            "named"
            if isinstance(document, dict) and document.get("kind") == "named"
            else "invalid"
        )
        return ProjectState(
            snapshot.name,
            snapshot,
            damaged_kind,
            snapshot.name,
            "Beschädigter Projektstand",
            "",
            (),
            str(error),
        )


def project_states(project: str | Path, course: str | Path) -> tuple[ProjectState, ...]:
    """Liefere Projektstände, neueste zuerst; beschädigte bleiben sichtbar."""

    _project_root, target_root, _backup_root = _project_snapshot_roots(project, course)
    if not target_root.is_dir():
        return ()
    try:
        snapshots = tuple(
            item
            for item in target_root.iterdir()
            if item.is_dir() and not item.is_symlink()
        )
    except OSError:
        return ()
    return tuple(
        _state_from_snapshot(snapshot)
        for snapshot in sorted(snapshots, key=lambda item: item.name, reverse=True)
    )


def restore_project_state(
    project: str | Path,
    course: str | Path,
    state_id: str,
) -> ProjectState:
    """Aktiviere einen geprüften Stand und sichere zuvor den aktuellen Inhalt."""

    if Path(state_id).name != state_id or state_id in {"", ".", ".."}:
        raise ValueError("Ungültige Kennung des Projektstands.")
    project_root, target_root, backup_root = _project_snapshot_roots(project, course)
    snapshot = target_root / state_id
    if (
        not snapshot.is_dir()
        or snapshot.is_symlink()
        or snapshot.parent != target_root
        or not snapshot.is_relative_to(backup_root)
    ):
        raise ValueError("Der Projektstand wurde nicht gefunden.")
    state = _state_from_snapshot(snapshot)
    if not state.restorable:
        raise ValueError(f"Der Projektstand ist beschädigt: {state.error}")
    actual_files = _state_files(snapshot)
    if state.files != actual_files:
        raise ValueError("Der Projektstand wurde nachträglich verändert.")
    if not any(file.path == "projekt.json" for file in actual_files):
        raise ValueError("Der Projektstand enthält keine gültige Projektbeschreibung.")

    token = uuid4().hex
    staging = project_root.parent / f".{project_root.name}.restore-{token}"
    rollback = project_root.parent / f".{project_root.name}.rollback-{token}"
    try:
        shutil.copytree(snapshot, staging, symlinks=False)
        if _state_files(staging) != actual_files:
            raise ValueError("Der vorbereitete Projektstand ist unvollständig.")
        snapshot_project(
            project_root,
            course,
            title="Vor Wiederherstellung",
            comment=f"Automatische Sicherung vor dem Wechsel zu „{state.title}“.",
        )
        os.replace(project_root, rollback)
        try:
            os.replace(staging, project_root)
        except Exception:
            os.replace(rollback, project_root)
            raise
        shutil.rmtree(rollback, ignore_errors=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return state


__all__ = [
    "MAX_PROJECT_SNAPSHOTS",
    "PROJECT_STATE_FORMAT",
    "ProjectState",
    "ProjectStateFile",
    "project_states",
    "restore_project_state",
    "save_project_state",
    "snapshot_project",
    "snapshot_project_if_changed",
]
