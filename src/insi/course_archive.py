"""Sicherer, vollständig lokaler Import portabler PyKIM-Kursarchive."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .course_setup import CourseSetup, setup_info
from .updates import MAX_CONTENT_FILES, MAX_CONTENT_SIZE, _validate_content, content_directory


ARCHIVE_SOURCE_FORMAT = "pykim-course-source-v1"
ARCHIVE_SOURCE_FILENAME = "content-source.json"
MAX_ARCHIVE_SIZE = 25 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = MAX_CONTENT_FILES + 50


@dataclass(frozen=True)
class CourseArchive:
    setup: CourseSetup
    setup_data: bytes
    revision: str
    files: dict[str, bytes]


def _member_path(name: str) -> PurePosixPath:
    if not name or "\\" in name or "\x00" in name:
        raise ValueError("Das Kursarchiv enthält einen unsicheren Dateipfad.")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Das Kursarchiv enthält einen unsicheren Dateipfad.")
    if path.parts[0].endswith(":"):
        raise ValueError("Das Kursarchiv enthält einen unsicheren Dateipfad.")
    return path


def _regular_member(member: zipfile.ZipInfo) -> None:
    mode = member.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ValueError("Das Kursarchiv darf keine symbolischen Links enthalten.")
    file_type = stat.S_IFMT(mode)
    if file_type and not member.is_dir() and not stat.S_ISREG(mode):
        raise ValueError("Das Kursarchiv enthält einen nicht unterstützten Dateityp.")
    if member.flag_bits & 0x1:
        raise ValueError("Verschlüsselte Kursarchive werden nicht unterstützt.")


def parse_course_archive(data: bytes) -> CourseArchive:
    """Prüfe ein ZIP vollständig und liefere ausschließlich sichtbare Kursinhalte."""
    if len(data) > MAX_ARCHIVE_SIZE:
        raise ValueError("Das Kursarchiv ist komprimiert zu groß.")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_ARCHIVE_MEMBERS:
                raise ValueError("Das Kursarchiv enthält zu viele Dateien.")
            if sum(member.file_size for member in members) > MAX_CONTENT_SIZE:
                raise ValueError("Das Kursarchiv ist entpackt zu groß.")

            files: dict[PurePosixPath, zipfile.ZipInfo] = {}
            folded: set[str] = set()
            for member in members:
                path = _member_path(member.filename)
                _regular_member(member)
                if member.is_dir():
                    continue
                normalized = path.as_posix().casefold()
                if normalized in folded:
                    raise ValueError(
                        "Das Kursarchiv enthält doppelte oder nur durch "
                        "Großschreibung verschiedene Dateipfade."
                    )
                folded.add(normalized)
                files[path] = member

            # Finder und einige ZIP-Werkzeuge legen AppleDouble-Dateien unter
            # ``__MACOSX`` bzw. als ``._…`` an. Sie beginnen wie unsere bewusst
            # ausgeblendeten Kursdateien mit einem Unterstrich und dürfen weder
            # als zweite Setupdatei noch als Kursinhalt gezählt werden.
            visible_files = {
                path: member
                for path, member in files.items()
                if not any(part.startswith("_") for part in path.parts)
            }
            setup_paths = [
                path
                for path in visible_files
                if path.name.endswith(".pykim-setup")
            ]
            if len(setup_paths) != 1:
                raise ValueError(
                    "Das Kursarchiv muss genau eine .pykim-setup-Datei enthalten."
                )
            setup_path = setup_paths[0]
            if len(setup_path.parts) > 2:
                raise ValueError(
                    "Die Setupdatei muss direkt im Kursstamm liegen. Das gewählte "
                    "ZIP ist vermutlich ein App-Quellarchiv und kein mit der "
                    "Kurswerkstatt erzeugtes Kursarchiv."
                )
            setup_data = archive.read(visible_files[setup_path])
            if len(setup_data) > 1_000_000:
                raise ValueError("Die Setupdatei im Kursarchiv ist zu groß.")
            setup = setup_info(setup_data)
            if setup_path.name != setup.name:
                raise ValueError(
                    "Der Dateiname der Setupdatei stimmt nicht mit ihrem "
                    "eingetragenen Namen überein."
                )
            root = setup_path.parent
            roots = {
                setup.scripts_path.rstrip("/"): ".md",
                setup.assignments_path.rstrip("/"): ".md",
                setup.trainers_path.rstrip("/"): ".yml",
            }
            content: dict[str, bytes] = {}
            content_folded: set[str] = set()
            for path, member in visible_files.items():
                try:
                    relative = path.relative_to(root)
                except ValueError:
                    continue
                name = relative.as_posix()
                if any(part.startswith("_") for part in relative.parts):
                    continue
                if not any(
                    name.startswith(directory + "/") and name.endswith(suffix)
                    for directory, suffix in roots.items()
                ):
                    continue
                folded_name = name.casefold()
                if folded_name in content_folded:
                    raise ValueError("Das Kursarchiv enthält mehrdeutige Inhaltspfade.")
                content_folded.add(folded_name)
                content[name] = archive.read(member)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError) as error:
        raise ValueError("Die Datei ist kein lesbares PyKIM-Kursarchiv.") from error

    if not content:
        raise ValueError(
            "Das Kursarchiv enthält weder sichtbare Skripte noch Aufgaben oder Trainer."
        )
    if len(content) > MAX_CONTENT_FILES:
        raise ValueError("Das Kursarchiv enthält zu viele Kursdateien.")

    digest = hashlib.sha256(data).hexdigest()
    return CourseArchive(setup, setup_data, f"archive-{digest}", content)


def build_course_archive(
    source_directory: str | Path,
    setup_file: str | Path,
) -> bytes:
    """Erzeuge aus Kursrepository und Setupdatei ein validiertes Offline-ZIP."""
    source = Path(source_directory).expanduser().resolve()
    setup_path = Path(setup_file).expanduser().resolve()
    if not source.is_dir() or not setup_path.is_file():
        raise FileNotFoundError("Kursordner oder Setupdatei wurde nicht gefunden.")
    setup_data = setup_path.read_bytes()
    setup = setup_info(setup_data)
    selected: dict[str, Path] = {}
    for directory, suffix in (
        (setup.scripts_path, ".md"),
        (setup.assignments_path, ".md"),
        (setup.trainers_path, ".yml"),
    ):
        root = source / PurePosixPath(directory)
        if not root.is_dir():
            continue
        for path in root.rglob(f"*{suffix}"):
            relative = path.relative_to(source)
            if path.is_file() and not any(part.startswith("_") for part in relative.parts):
                selected[relative.as_posix()] = path
    if len(selected) > MAX_CONTENT_FILES:
        raise ValueError("Der Kurs enthält zu viele sichtbare Dateien.")
    if sum(path.stat().st_size for path in selected.values()) > MAX_CONTENT_SIZE:
        raise ValueError("Der Kurs ist für ein portables Archiv zu groß.")

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(setup.name, setup_data)
        for name, path in sorted(selected.items()):
            archive.writestr(name, path.read_bytes())
    data = output.getvalue()
    parse_course_archive(data)
    return data


def install_course_archive_content(bundle: CourseArchive) -> Path:
    """Installiere bereits geprüftes Archivmaterial versioniert und atomar."""
    base = content_directory()
    versions = base / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / bundle.revision
    manifest = {
        "content_version": bundle.revision,
        "source": "archive",
        "files": {
            name: hashlib.sha256(data).hexdigest()
            for name, data in sorted(bundle.files.items())
        },
    }
    if target.is_dir():
        try:
            _validate_content(target, manifest)
            return target
        except (OSError, ValueError):
            pass

    with tempfile.TemporaryDirectory(prefix="pykim-archive-", dir=base) as temporary:
        staging = Path(temporary) / "content"
        staging.mkdir()
        for name, data in bundle.files.items():
            destination = staging / PurePosixPath(name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        _validate_content(staging, manifest)

        from pykim.trainer.activities import load_activities
        from pykim.trainer.definitions import load_exercises

        trainer_directory = staging / bundle.setup.trainers_path
        if trainer_directory.is_dir():
            load_exercises(trainer_directory)
            load_activities(
                trainer_directory,
                staging / bundle.setup.assignments_path,
            )
        (staging / "content-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if target.exists():
            shutil.rmtree(target)
        os.replace(staging, target)
    return target


def course_source_path(course: str | Path) -> Path:
    return Path(course).expanduser().resolve() / ".pykim" / ARCHIVE_SOURCE_FILENAME


def course_content_source(course: str | Path) -> dict[str, str]:
    try:
        document = json.loads(course_source_path(course).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {"type": "repository"}
    if (
        not isinstance(document, dict)
        or document.get("format") != ARCHIVE_SOURCE_FORMAT
        or document.get("type") not in {"archive", "repository"}
    ):
        return {"type": "repository"}
    result = {"type": str(document["type"])}
    version = document.get("content_version")
    if isinstance(version, str) and version:
        result["content_version"] = version
    return result


def write_course_content_source(
    course: str | Path,
    source_type: str,
    *,
    content_version: str = "",
) -> None:
    if source_type not in {"archive", "repository"}:
        raise ValueError("Unbekannte Kursquelle.")
    target = course_source_path(course)
    target.parent.mkdir(parents=True, exist_ok=True)
    document = {"format": ARCHIVE_SOURCE_FORMAT, "type": source_type}
    if content_version:
        document["content_version"] = content_version
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary, target)


__all__ = [
    "CourseArchive",
    "build_course_archive",
    "course_content_source",
    "install_course_archive_content",
    "parse_course_archive",
    "write_course_content_source",
]
