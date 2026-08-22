"""Sicherer, vollständig lokaler Import portabler PyKIM-Kursarchive."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import stat
import tempfile
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
    current_runtime_target,
    parse_runtime_manifest,
    runtime_manifest_bytes,
)
from .updates import MAX_CONTENT_FILES, MAX_CONTENT_SIZE, _validate_content, content_directory


ARCHIVE_SOURCE_FORMAT = "pykim-course-source-v1"
ARCHIVE_SOURCE_FILENAME = "content-source.json"
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
    wheels = offline_wheels or {}
    if wheels and runtime is None:
        raise ValueError("Offline-Wheels benötigen ein Runtime-Manifest.")
    if set(wheels) != set(runtime.hashes if runtime is not None else {}):
        raise ValueError("Runtime-Manifest und Offline-Wheels stimmen nicht überein.")
    for name, path in wheels.items():
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
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != runtime.hashes[name]:
            raise ValueError(f"Prüfsumme des Offline-Wheels stimmt nicht: {name}")

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(setup.name, setup_data)
        if runtime_data is not None:
            archive.writestr(RUNTIME_FILENAME, runtime_manifest_bytes(runtime))
        for name, path in sorted(selected.items()):
            archive.writestr(name, path.read_bytes())
        for name, path in sorted(wheels.items()):
            archive.writestr(name, Path(path).read_bytes())
    data = output.getvalue()
    parse_course_archive(data)
    return data


def install_course_archive_runtime(bundle: CourseArchive, course: str | Path) -> Path | None:
    """Installiere Manifest und Wheels versioniert im portablen Kursordner."""
    if bundle.runtime is None or bundle.runtime_data is None:
        clear_course_runtime(course)
        return None
    return install_course_runtime(
        bundle.runtime_data,
        course,
        revision=bundle.revision,
        offline_wheels=bundle.offline_wheels,
    )


def install_course_runtime(
    runtime_data: bytes,
    course: str | Path,
    *,
    revision: str,
    offline_wheels: dict[str, bytes] | None = None,
) -> Path:
    """Aktiviere einen bereits geprüften Runtime-Stand atomar für einen Kurs."""
    runtime = parse_runtime_manifest(runtime_data)
    wheels = offline_wheels or {}
    if set(wheels) != set(runtime.hashes):
        raise ValueError("Runtime-Manifest und Offline-Wheels stimmen nicht überein.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", revision):
        raise ValueError("Die Runtime-Revision ist ungültig.")
    course_root = Path(course).expanduser().resolve()
    base = course_root / ".pykim" / "runtime"
    versions = base / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / revision

    def target_is_valid() -> bool:
        try:
            if parse_runtime_manifest(target / RUNTIME_FILENAME) != runtime:
                return False
            wheel_root = target / "wheelhouse"
            actual = {
                f"wheelhouse/{path.relative_to(wheel_root).as_posix()}":
                hashlib.sha256(path.read_bytes()).hexdigest()
                for path in wheel_root.rglob("*.whl")
                if path.is_file()
            } if wheel_root.is_dir() else {}
            return actual == runtime.hashes
        except (OSError, ValueError):
            return False

    if not target_is_valid():
        with tempfile.TemporaryDirectory(prefix="insi-runtime-", dir=base) as temporary:
            staging = Path(temporary) / "runtime"
            staging.mkdir()
            (staging / RUNTIME_FILENAME).write_bytes(
                runtime_manifest_bytes(runtime)
            )
            for name, data in wheels.items():
                if hashlib.sha256(data).hexdigest() != runtime.hashes[name]:
                    raise ValueError(f"Prüfsumme des Offline-Wheels stimmt nicht: {name}")
                relative = PurePosixPath(name).relative_to("wheelhouse")
                destination = staging / "wheelhouse" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            if target.exists():
                shutil.rmtree(target)
            os.replace(staging, target)
    marker = base / "active.json"
    temporary_marker = marker.with_suffix(".json.tmp")
    temporary_marker.write_text(
        json.dumps({"revision": revision}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_marker, marker)
    return target


def clear_course_runtime(course: str | Path) -> None:
    """Deaktiviere einen alten Runtime-Vertrag, ohne Versionen zu löschen."""
    marker = Path(course).expanduser().resolve() / ".pykim" / "runtime" / "active.json"
    try:
        marker.unlink()
    except FileNotFoundError:
        pass


def installed_course_runtime(course: str | Path) -> tuple[RuntimeManifest, Path] | None:
    base = Path(course).expanduser().resolve() / ".pykim" / "runtime"
    try:
        marker = json.loads((base / "active.json").read_text(encoding="utf-8"))
        revision = str(marker["revision"])
        if not re.fullmatch(r"[A-Za-z0-9._-]+", revision):
            return None
        root = base / "versions" / revision
        manifest = parse_runtime_manifest(root / RUNTIME_FILENAME)
        return manifest, root
    except (OSError, ValueError, KeyError, TypeError):
        return None


def course_offline_wheelhouse(
    course: str | Path,
    target: str | None = None,
) -> Path | None:
    installed = installed_course_runtime(course)
    if installed is None:
        return None
    manifest, root = installed
    selected = target or current_runtime_target()
    if selected is None or selected not in manifest.offline_targets:
        return None
    wheelhouse = root / "wheelhouse" / selected
    prefix = f"wheelhouse/{selected}/"
    expected = {
        name.removeprefix(prefix): digest
        for name, digest in manifest.hashes.items()
        if name.startswith(prefix)
    }
    if not expected:
        return None
    try:
        actual = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in wheelhouse.glob("*.whl")
            if path.is_file()
        }
    except OSError as error:
        raise RuntimeError("Die eingebetteten Offline-Pakete sind nicht lesbar.") from error
    if actual != expected:
        raise RuntimeError(
            "Die eingebetteten Offline-Pakete fehlen oder ihre Prüfsummen stimmen nicht."
        )
    return wheelhouse


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

        from insi.training.registry import validate_training_directory

        trainer_directory = staging / bundle.setup.trainers_path
        if trainer_directory.is_dir():
            validate_training_directory(
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
    "clear_course_runtime",
    "course_offline_wheelhouse",
    "course_content_source",
    "install_course_archive_content",
    "install_course_archive_runtime",
    "install_course_runtime",
    "installed_course_runtime",
    "parse_course_archive",
    "write_course_content_source",
]
