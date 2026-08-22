"""Versionierte, wiederanlaufbare Migration dauerhafter in:si-Daten."""

from __future__ import annotations

import json
import os
import shutil
import filecmp
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile


LOCAL_SETTINGS_FORMAT = "insi-settings-v1"
COURSE_DATA_FORMAT = "insi-course-data-v1"
CURRENT_COURSE_DATA_VERSION = 1
COURSE_DATA_MARKER = "data-version.json"
MIGRATION_BACKUP_DIRECTORY = "migrations/0.7-to-0.8"


@dataclass(frozen=True)
class MigrationReport:
    scope: str
    version: int
    changed: tuple[str, ...]


class MigrationStorageError(OSError):
    """Ein Datenträger verschwand oder verweigerte einen sicheren Schreibschritt."""


def _discard_temporary(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        # Bei einem entfernten Datenträger ist auch Aufräumen unmöglich. Der
        # ursprüngliche Speicherfehler bleibt die aussagekräftigere Ursache.
        pass


def _read_object(path: Path, label: str) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} ist beschädigt: {error}") from error
    if not isinstance(document, dict):
        raise ValueError(f"{label} enthält kein JSON-Objekt.")
    return document


def _atomic_write_json(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            json.dump(document, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    except OSError as error:
        raise MigrationStorageError(
            f"{path.name} konnte nicht sicher ersetzt werden. "
            "Der bisherige Stand bleibt maßgeblich; verbinde den Datenträger "
            "erneut und wiederhole die Migration."
        ) from error
    finally:
        _discard_temporary(temporary_path)


def _backup_once(source: Path, target: Path) -> None:
    if target.is_symlink():
        raise ValueError("Das Migrationsbackup darf kein symbolischer Link sein.")
    if target.exists():
        if not target.is_file() or not filecmp.cmp(source, target, shallow=False):
            raise ValueError(
                "Das vorhandene Migrationsbackup unterscheidet sich vom Original. "
                "Die Migration wurde angehalten."
            )
        return
    temporary: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "wb", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
        shutil.copy2(source, temporary)
        with temporary.open("rb") as copied:
            os.fsync(copied.fileno())
        os.replace(temporary, target)
    except OSError as error:
        raise MigrationStorageError(
            "Das Originalbackup konnte nicht vollständig angelegt werden. "
            "Die Quelldatei wurde nicht verändert; verbinde den Datenträger "
            "erneut und wiederhole die Migration."
        ) from error
    finally:
        _discard_temporary(temporary)


def migrate_local_settings(path: str | Path) -> MigrationReport:
    """Kennzeichne 0.7-Einstellungen, ohne unbekannte Schlüssel zu verlieren."""

    target = Path(path).expanduser().absolute()
    if not target.exists():
        return MigrationReport("settings", 1, ())
    document = _read_object(target, "Die lokalen Einstellungen")
    stored_format = document.get("format")
    if stored_format == LOCAL_SETTINGS_FORMAT:
        return MigrationReport("settings", 1, ())
    if stored_format is not None:
        raise ValueError(
            f"Unbekanntes Einstellungsformat: {stored_format}. "
            "Die Datei wurde nicht verändert."
        )
    backup = target.parent / "backups" / MIGRATION_BACKUP_DIRECTORY / target.name
    _backup_once(target, backup)
    migrated = {"format": LOCAL_SETTINGS_FORMAT, **document}
    _atomic_write_json(target, migrated)
    return MigrationReport("settings", 1, (target.name,))


def _validate_course_metadata(path: Path) -> None:
    document = _read_object(path, "Die Kurskennung")
    if document.get("format") != 1:
        raise ValueError("Die Kurskennung besitzt ein unbekanntes Format.")
    for key in ("course", "student_name"):
        if key in document and not isinstance(document[key], str):
            raise ValueError(f"Die Kurskennung enthält ein ungültiges Feld: {key}.")


def _migrated_progress(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    document = _read_object(path, "Der Lernstand")
    stored_format = document.get("format", 1)
    if stored_format != 1:
        raise ValueError(
            f"Unbekanntes Lernstandsformat: {stored_format}. "
            "Die Datei wurde nicht verändert."
        )
    expected = {
        "attempts": list,
        "journal": dict,
        "answers": dict,
        "hints": dict,
    }
    for key, expected_type in expected.items():
        value = document.get(key, expected_type())
        if not isinstance(value, expected_type):
            raise ValueError(f"Der Lernstand enthält ein ungültiges Feld: {key}.")
    migrated = dict(document)
    migrated["format"] = 1
    for key, expected_type in expected.items():
        migrated.setdefault(key, expected_type())
    return migrated if migrated != document else None


def _current_course_version(marker: Path) -> int:
    if not marker.exists():
        return 0
    document = _read_object(marker, "Der Migrationsstand")
    if document.get("format") != COURSE_DATA_FORMAT:
        raise ValueError("Der Migrationsstand besitzt ein unbekanntes Format.")
    version = document.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 0:
        raise ValueError("Der Migrationsstand enthält keine gültige Version.")
    if version > CURRENT_COURSE_DATA_VERSION:
        raise ValueError(
            "Die Kursdaten stammen aus einer neueren in:si-Version und wurden "
            "nicht verändert."
        )
    return version


def migrate_course_data(course: str | Path) -> MigrationReport:
    """Migriere 0.7-Kursdaten verlustfrei auf den aktuellen Datenvertrag."""

    root = Path(course).expanduser().resolve()
    metadata = root / ".pykim-course.json"
    if not root.is_dir() or not metadata.is_file():
        raise ValueError("Der Ordner enthält keinen erkannten in:si-Kurs.")
    internal = root / ".pykim"
    marker = internal / COURSE_DATA_MARKER
    version = _current_course_version(marker)

    # Alle Quelldaten werden geprüft, bevor die erste Datei verändert wird.
    _validate_course_metadata(metadata)
    progress = internal / "progress.json"
    migrated_progress = _migrated_progress(progress)
    if version == CURRENT_COURSE_DATA_VERSION and migrated_progress is None:
        return MigrationReport("course", version, ())
    changed: list[str] = []
    if migrated_progress is not None:
        backup = internal / "backups" / MIGRATION_BACKUP_DIRECTORY / "progress.json"
        _backup_once(progress, backup)
        _atomic_write_json(progress, migrated_progress)
        changed.append(".pykim/progress.json")

    _atomic_write_json(
        marker,
        {
            "format": COURSE_DATA_FORMAT,
            "version": CURRENT_COURSE_DATA_VERSION,
            "migrated_from": "0.7",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    changed.append(f".pykim/{COURSE_DATA_MARKER}")
    return MigrationReport("course", CURRENT_COURSE_DATA_VERSION, tuple(changed))


__all__ = [
    "COURSE_DATA_FORMAT",
    "COURSE_DATA_MARKER",
    "CURRENT_COURSE_DATA_VERSION",
    "LOCAL_SETTINGS_FORMAT",
    "MigrationReport",
    "MigrationStorageError",
    "migrate_course_data",
    "migrate_local_settings",
]
