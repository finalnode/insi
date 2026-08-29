"""Sicherer, vollständig lokaler Import portabler PyKIM-Kursarchive."""

from __future__ import annotations

import hashlib
import io
import stat
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .course_setup import (
    CourseSetup,
    canonical_setup_data,
    is_setup_filename,
    setup_info,
)
from .course_runtime import (
    MAX_OFFLINE_PACKAGE_SIZE,
    MAX_OFFLINE_WHEELS,
    RUNTIME_FILENAME,
    RuntimeManifest,
    parse_runtime_manifest,
    runtime_manifest_bytes,
)
from .updates import MAX_CONTENT_FILES, MAX_CONTENT_SIZE


MAX_STANDARD_ARCHIVE_SIZE = 25 * 1024 * 1024
MAX_ARCHIVE_SIZE = MAX_OFFLINE_PACKAGE_SIZE + MAX_STANDARD_ARCHIVE_SIZE
MAX_ARCHIVE_MEMBERS = MAX_CONTENT_FILES + MAX_OFFLINE_WHEELS + 50


@dataclass(frozen=True)
class CourseArchive:
    setup: CourseSetup
    setup_data: bytes
    revision: str
    files: dict[str, bytes]
    runtime: RuntimeManifest | None = None
    runtime_data: bytes | None = None
    offline_wheels: dict[str, bytes] = field(default_factory=dict)


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
            if sum(member.file_size for member in members) > (
                MAX_CONTENT_SIZE + MAX_OFFLINE_PACKAGE_SIZE + 1_000_000
            ):
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
                if is_setup_filename(path.name)
            ]
            if len(setup_paths) != 1:
                raise ValueError(
                    "Das Kursarchiv muss genau eine .insi-setup-Datei enthalten."
                )
            setup_path = setup_paths[0]
            if len(setup_path.parts) > 2:
                raise ValueError(
                    "Die Setupdatei muss direkt im Kursstamm liegen. Das gewählte "
                    "ZIP ist vermutlich ein App-Quellarchiv und kein mit der "
                    "Kurswerkstatt erzeugtes Kursarchiv."
                )
            uploaded_setup_data = archive.read(visible_files[setup_path])
            if len(uploaded_setup_data) > 1_000_000:
                raise ValueError("Die Setupdatei im Kursarchiv ist zu groß.")
            uploaded_setup = setup_info(uploaded_setup_data)
            if setup_path.name != uploaded_setup.name:
                raise ValueError(
                    "Der Dateiname der Setupdatei stimmt nicht mit ihrem "
                    "eingetragenen Namen überein."
                )
            setup_data = canonical_setup_data(uploaded_setup_data)
            setup = setup_info(setup_data)
            root = setup_path.parent
            runtime_paths = [
                path for path in visible_files
                if path.parent == root and path.name == RUNTIME_FILENAME
            ]
            if len(runtime_paths) > 1:
                raise ValueError("Das Kursarchiv enthält mehrere Runtime-Manifeste.")
            runtime_data = (
                archive.read(visible_files[runtime_paths[0]])
                if runtime_paths else None
            )
            if runtime_data is not None and len(runtime_data) > 1_000_000:
                raise ValueError("Das Runtime-Manifest ist zu groß.")
            runtime = (
                parse_runtime_manifest(runtime_data)
                if runtime_data is not None else None
            )

            wheel_members: dict[str, zipfile.ZipInfo] = {}
            for path, member in visible_files.items():
                try:
                    relative = path.relative_to(root)
                except ValueError:
                    continue
                if relative.parts and relative.parts[0] == "wheelhouse" and not (
                    len(relative.parts) == 3
                    and relative.suffix.casefold() == ".whl"
                ):
                    raise ValueError(
                        "Das Kursarchiv enthält einen ungültigen Offline-Wheelpfad."
                    )
                if (
                    len(relative.parts) == 3
                    and relative.parts[0] == "wheelhouse"
                    and relative.suffix.casefold() == ".whl"
                ):
                    wheel_members[relative.as_posix()] = member
            if wheel_members and runtime is None:
                raise ValueError("Offline-Wheels benötigen ein Runtime-Manifest.")
            if len(data) > MAX_STANDARD_ARCHIVE_SIZE and not wheel_members:
                raise ValueError("Das Kursarchiv ist ohne Offline-Pakete zu groß.")
            if len(wheel_members) > MAX_OFFLINE_WHEELS:
                raise ValueError("Das Kursarchiv enthält zu viele Offline-Wheels.")
            if sum(member.file_size for member in wheel_members.values()) > MAX_OFFLINE_PACKAGE_SIZE:
                raise ValueError("Die Offline-Pakete im Kursarchiv sind größer als 1 GB.")
            expected_wheels = runtime.hashes if runtime is not None else {}
            if set(wheel_members) != set(expected_wheels):
                raise ValueError(
                    "Runtime-Manifest und eingebettete Offline-Wheels stimmen nicht überein."
                )
            offline_wheels: dict[str, bytes] = {}
            for name, member in wheel_members.items():
                wheel_data = archive.read(member)
                if hashlib.sha256(wheel_data).hexdigest() != expected_wheels[name]:
                    raise ValueError(f"Prüfsumme des Offline-Wheels stimmt nicht: {name}")
                offline_wheels[name] = wheel_data

            roots = {
                setup.scripts_path.rstrip("/"): ".md",
                setup.assignments_path.rstrip("/"): ".md",
                setup.trainers_path.rstrip("/"): ".yml",
            }
            content: dict[str, bytes] = {}
            for path, member in visible_files.items():
                try:
                    relative = path.relative_to(root)
                except ValueError:
                    continue
                name = relative.as_posix()
                if not any(
                    name.startswith(directory + "/") and name.endswith(suffix)
                    for directory, suffix in roots.items()
                ):
                    continue
                content[name] = archive.read(member)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError) as error:
        raise ValueError("Die Datei ist kein lesbares PyKIM-Kursarchiv.") from error

    if not content:
        raise ValueError(
            "Das Kursarchiv enthält weder sichtbare Skripte noch Aufgaben oder Trainer."
        )
    if len(content) > MAX_CONTENT_FILES:
        raise ValueError("Das Kursarchiv enthält zu viele Kursdateien.")
    if sum(len(item) for item in content.values()) > MAX_CONTENT_SIZE:
        raise ValueError("Die Kursinhalte sind entpackt zu groß.")

    digest = hashlib.sha256(data).hexdigest()
    return CourseArchive(
        setup,
        setup_data,
        f"archive-{digest}",
        content,
        runtime,
        runtime_data,
        offline_wheels,
    )


def build_course_archive(
    source_directory: str | Path,
    setup_file: str | Path,
    *,
    runtime_manifest: bytes | str | Path | None = None,
    offline_wheels: dict[str, Path] | None = None,
) -> bytes:
    """Erzeuge aus Kursrepository und Setupdatei ein validiertes Offline-ZIP."""
    source = Path(source_directory).expanduser().resolve()
    setup_path = Path(setup_file).expanduser().resolve()
    if not source.is_dir() or not setup_path.is_file():
        raise FileNotFoundError("Kursordner oder Setupdatei wurde nicht gefunden.")
    setup_data = canonical_setup_data(setup_path)
    setup = setup_info(setup_data)
    selected: dict[str, bytes] = {}
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
                selected[relative.as_posix()] = path.read_bytes()
    if len(selected) > MAX_CONTENT_FILES:
        raise ValueError("Der Kurs enthält zu viele sichtbare Dateien.")
    if sum(len(data) for data in selected.values()) > MAX_CONTENT_SIZE:
        raise ValueError("Der Kurs ist für ein portables Archiv zu groß.")

    runtime_data: bytes | None
    if runtime_manifest is None:
        runtime_path = source / RUNTIME_FILENAME
        runtime_data = runtime_path.read_bytes() if runtime_path.is_file() else None
    elif isinstance(runtime_manifest, bytes):
        runtime_data = runtime_manifest
    elif isinstance(runtime_manifest, Path):
        runtime_data = runtime_manifest.read_bytes()
    else:
        runtime_data = runtime_manifest.encode("utf-8")
    runtime = parse_runtime_manifest(runtime_data) if runtime_data is not None else None
    wheel_paths = offline_wheels or {}
    if wheel_paths and runtime is None:
        raise ValueError("Offline-Wheels benötigen ein Runtime-Manifest.")
    if set(wheel_paths) != set(runtime.hashes if runtime is not None else {}):
        raise ValueError("Runtime-Manifest und Offline-Wheels stimmen nicht überein.")
    wheels: dict[str, bytes] = {}
    for name, path in wheel_paths.items():
        member = PurePosixPath(name)
        if (
            member.is_absolute()
            or ".." in member.parts
            or len(member.parts) != 3
            or member.parts[0] != "wheelhouse"
            or member.suffix.casefold() != ".whl"
            or not Path(path).is_file()
        ):
            raise ValueError(f"Ungültiger Offline-Wheelpfad: {name!r}")
        data = Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest() != runtime.hashes[name]:
            raise ValueError(f"Prüfsumme des Offline-Wheels stimmt nicht: {name}")
        wheels[name] = data

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(setup.name, setup_data)
        if runtime_data is not None:
            archive.writestr(RUNTIME_FILENAME, runtime_manifest_bytes(runtime))
        for name, data in sorted(selected.items()):
            archive.writestr(name, data)
        for name, data in sorted(wheels.items()):
            archive.writestr(name, data)
    data = output.getvalue()
    parse_course_archive(data)
    return data
