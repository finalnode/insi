"""Atomare Speicherung installierter Kursinhalte und Laufzeitverträge."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from .course_runtime import (
    RUNTIME_FILENAME,
    RuntimeManifest,
    current_runtime_target,
    parse_runtime_manifest,
    runtime_manifest_bytes,
)
from .updates import _validate_content, content_directory

if TYPE_CHECKING:
    from .course_archive import CourseArchive


ARCHIVE_SOURCE_FORMAT = "pykim-course-source-v1"
ARCHIVE_SOURCE_FILENAME = "content-source.json"


def _write_json(target: Path, document: dict[str, str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary, target)


def install_course_archive_runtime(
    bundle: "CourseArchive", course: str | Path
) -> Path | None:
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
    base = Path(course).expanduser().resolve() / ".pykim" / "runtime"
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
    _write_json(base / "active.json", {"revision": revision})
    return target


def clear_course_runtime(course: str | Path) -> None:
    """Deaktiviere einen alten Runtime-Vertrag, ohne Versionen zu löschen."""
    marker = Path(course).expanduser().resolve() / ".pykim" / "runtime" / "active.json"
    marker.unlink(missing_ok=True)


def installed_course_runtime(course: str | Path) -> tuple[RuntimeManifest, Path] | None:
    base = Path(course).expanduser().resolve() / ".pykim" / "runtime"
    try:
        marker = json.loads((base / "active.json").read_text(encoding="utf-8"))
        revision = str(marker["revision"])
        if not re.fullmatch(r"[A-Za-z0-9._-]+", revision):
            return None
        root = base / "versions" / revision
        return parse_runtime_manifest(root / RUNTIME_FILENAME), root
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


def install_course_archive_content(bundle: "CourseArchive") -> Path:
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


def course_content_source(course: str | Path) -> dict[str, str]:
    source = Path(course).expanduser().resolve() / ".pykim" / ARCHIVE_SOURCE_FILENAME
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
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
    target = Path(course).expanduser().resolve() / ".pykim" / ARCHIVE_SOURCE_FILENAME
    document = {"format": ARCHIVE_SOURCE_FORMAT, "type": source_type}
    if content_version:
        document["content_version"] = content_version
    _write_json(target, document)
