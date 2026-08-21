"""Getrennte Updatekanäle für App-Bundles und Lerninhalte."""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import shutil
import stat
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.parse import quote

from . import __version__
from .course import _config_directory
from .network import urlopen
from .course_runtime import RUNTIME_FILENAME, parse_runtime_manifest


REPOSITORY = "finalnode/insi"
RELEASE_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
CONTENT_MANIFEST_URL = (
    f"https://raw.githubusercontent.com/{REPOSITORY}/main/content-manifest.json"
)
MAX_CONTENT_FILES = 500
MAX_CONTENT_SIZE = 20 * 1024 * 1024
_VALIDATED_CONTENT_ROOTS: set[Path] = set()


@dataclass(frozen=True)
class AppUpdate:
    installed: str
    available: str
    newer: bool
    download_url: str
    release_url: str


@dataclass(frozen=True)
class ContentUpdate:
    installed: str
    available: str
    newer: bool
    compatible: bool
    manifest: dict[str, object]


@dataclass(frozen=True)
class UpdateStatus:
    app: AppUpdate | None
    content: ContentUpdate | None
    error: str = ""


@dataclass(frozen=True)
class TrainerVerification:
    """Ergebnis der Trainerprüfung vor einem Aufgabenlauf."""

    checked_online: bool
    updated: bool
    message: str = ""


def verify_certificate_authorization(
    certificate_data: bytes,
    configuration,
    *,
    timeout: float = 3.0,
    allow_offline: bool = False,
) -> TrainerVerification:
    """Kompatibilitätsprüfung für den ausgeblendeten alten Abgabeweg."""
    name = configuration.certificate_name
    repository = _repository_name(configuration.repository)
    branch = quote(configuration.branch, safe="")
    url = (
        f"https://raw.githubusercontent.com/{repository}/{branch}/"
        f"certificates/{quote(name, safe='')}"
    )
    try:
        remote = _download(url, timeout).decode("ascii").strip()
    except (URLError, TimeoutError, ConnectionError) as error:
        if allow_offline:
            return TrainerVerification(False, False, f"Zertifikatsprüfung offline: {error}")
        raise
    expected = remote.removeprefix("sha256:").strip().casefold()
    if hashlib.sha256(certificate_data).hexdigest() != expected:
        raise ValueError("Das Kurszertifikat ist im angegebenen Repository nicht zugelassen.")
    return TrainerVerification(True, False)


def _version(value: str) -> tuple[int, ...]:
    parts = []
    for item in value.strip().lstrip("v").split("."):
        digits = "".join(character for character in item if character.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts)


def format_content_version(value: str) -> str:
    """Zeige datumsartige Inhaltsversionen im deutschen Datumsformat."""
    parts = value.split(".")
    if len(parts) == 3 and len(parts[0]) == 4 and all(part.isdigit() for part in parts):
        year, month, day = (int(part) for part in parts)
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{day:02d}.{month:02d}.{year:04d}"
    return value


def _json_url(url: str, timeout: float) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": f"insi/{__version__}"})
    with urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Die Updateantwort ist kein JSON-Objekt.")
    return data


def content_directory() -> Path:
    return _config_directory() / "content"


def _course_content_key(configuration) -> str:
    values = (
        configuration.repository,
        configuration.branch,
        configuration.scripts_path,
        configuration.assignments_path,
        configuration.trainers_path,
    )
    return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()


def _course_active_marker(configuration) -> Path:
    return content_directory() / "active-courses" / f"{_course_content_key(configuration)}.json"


def _bundled_content_version(packaged_root: Path) -> str:
    manifest = packaged_root / "content-manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return str(data.get("content_version", "0"))
    except (OSError, ValueError, TypeError):
        return "0"


def active_content_root(packaged_root: Path) -> Path:
    """Liefere ein geprüft aktiviertes Overlay oder die eingebauten Inhalte."""
    configured = os.environ.get("PYKIM_CONTENT_DIR")
    if configured:
        root = Path(configured).expanduser().resolve()
        return root if root.is_dir() else packaged_root
    marker = content_directory() / "active.json"
    course_specific = False
    try:
        from .course import get_course_directory
        from .course_archive import course_content_source
        from .course_setup import course_setup_info

        course = get_course_directory()
        setup = course_setup_info(course) if course is not None else None
        if setup is not None:
            source = course_content_source(course)
            archive_version = source.get("content_version")
            if source.get("type") == "archive" and archive_version:
                marker_data = {"content_version": archive_version}
                version = str(marker_data["content_version"])
                root = content_directory() / "versions" / version
                manifest = json.loads(
                    (root / "content-manifest.json").read_text(encoding="utf-8")
                )
                if root.is_dir() and isinstance(manifest, dict):
                    if root not in _VALIDATED_CONTENT_ROOTS:
                        _validate_content(root, manifest)
                        _VALIDATED_CONTENT_ROOTS.add(root)
                    return root
            marker = _course_active_marker(setup)
            course_specific = True
    except (OSError, ValueError):
        pass
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        version = str(data["content_version"])
        root = content_directory() / "versions" / version
        manifest = json.loads(
            (root / "content-manifest.json").read_text(encoding="utf-8")
        )
        if root.is_dir() and isinstance(manifest, dict):
            if root not in _VALIDATED_CONTENT_ROOTS:
                _validate_content(root, manifest)
                _VALIDATED_CONTENT_ROOTS.add(root)
            return root
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if course_specific:
        return packaged_root
    return packaged_root


def installed_content_version(packaged_root: Path) -> str:
    root = active_content_root(packaged_root)
    return _bundled_content_version(root)


def check_app_update(timeout: float = 5.0) -> AppUpdate:
    data = _json_url(RELEASE_URL, timeout)
    available = str(data.get("tag_name", "0")).lstrip("v")
    architecture = platform.machine().lower()
    assets = data.get("assets", [])
    download = ""
    if isinstance(assets, list):
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name", "")).lower()
            if name.endswith(".dmg") and architecture in name:
                download = str(asset.get("browser_download_url", ""))
                break
    return AppUpdate(
        __version__,
        available,
        _version(available) > _version(__version__),
        download,
        str(data.get("html_url", f"https://github.com/{REPOSITORY}/releases")),
    )


def check_content_update(packaged_root: Path, timeout: float = 5.0) -> ContentUpdate:
    manifest = _json_url(CONTENT_MANIFEST_URL, timeout)
    available = str(manifest.get("content_version", "0"))
    installed = installed_content_version(packaged_root)
    minimum = str(manifest.get("minimum_app_version", "0"))
    return ContentUpdate(
        installed,
        available,
        _version(available) > _version(installed),
        _version(__version__) >= _version(minimum),
        manifest,
    )


def check_updates(packaged_root: Path, timeout: float = 5.0) -> UpdateStatus:
    app = content = None
    errors = []
    try:
        app = check_app_update(timeout)
    except HTTPError as error:
        if error.code == 404:
            app = AppUpdate(
                __version__,
                __version__,
                False,
                "",
                f"https://github.com/{REPOSITORY}/releases",
            )
        else:
            errors.append(f"App: {error}")
    except (OSError, ValueError, KeyError) as error:
        errors.append(f"App: {error}")
    try:
        content = check_content_update(packaged_root, timeout)
    except HTTPError as error:
        if error.code == 404:
            installed = installed_content_version(packaged_root)
            content = ContentUpdate(installed, installed, False, True, {})
        else:
            errors.append(f"Inhalte: {error}")
    except (OSError, ValueError, KeyError) as error:
        errors.append(f"Inhalte: {error}")
    status = UpdateStatus(app, content, " · ".join(errors))
    cache = content_directory() / "update-status.json"
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(asdict(status), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass
    return status


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _validate_content(root: Path, manifest: dict[str, object]) -> None:
    expected = manifest.get("files")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Das Inhaltsmanifest enthält keine Dateien.")
    for name, digest in expected.items():
        if not isinstance(name, str) or not _safe_member(name):
            raise ValueError(f"Unsicherer Inhaltspfad: {name!r}")
        target = root / name
        if not target.is_file():
            raise ValueError(f"Inhaltsdatei fehlt: {name}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != str(digest).removeprefix("sha256:"):
            raise ValueError(f"Prüfsumme stimmt nicht: {name}")


def _repository_name(url: str) -> str:
    match = __import__("re").fullmatch(
        r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?", url
    )
    if match is None:
        raise ValueError("Das Zertifikat enthält keine unterstützte GitHub-Adresse.")
    return match.group(1)


def _download(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": f"insi/{__version__}"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _hash_entries(data: object) -> dict[str, dict[str, object]]:
    entries = data.get("files") if isinstance(data, dict) else None
    if not isinstance(entries, dict) or not entries:
        raise ValueError("Die Remote-Hashliste ist leer oder ungültig.")
    result: dict[str, dict[str, object]] = {}
    for name, details in entries.items():
        if not isinstance(name, str) or not _safe_member(name):
            raise ValueError(f"Unsicherer Remote-Pfad: {name!r}")
        if not isinstance(details, dict):
            raise ValueError(f"Ungültiger Hasheintrag: {name}")
        digest = str(details.get("sha256", ""))
        size = details.get("size")
        if len(digest) != 64 or not isinstance(size, int) or size < 0:
            raise ValueError(f"Ungültiger Hasheintrag: {name}")
        result[name] = details
    return result


def _course_content_paths(tree: object, configuration) -> set[str]:
    """Entdecke sichtbare Kursdateien direkt im Git-Baum.

    Ein Pfad bleibt unsichtbar, sobald ein Datei- oder Ordnername mit ``_``
    beginnt. Dadurch genügt es, neue Inhalte ins Repository zu legen; ein
    zusätzlicher Inhaltskatalog ist nicht erforderlich.
    """
    if not isinstance(tree, dict) or tree.get("truncated") is True:
        raise ValueError("Der Repository-Dateibaum ist unvollständig.")
    entries = tree.get("tree")
    if not isinstance(entries, list):
        raise ValueError("Der Repository-Dateibaum ist ungültig.")
    roots = {
        configuration.scripts_path.rstrip("/"): ".md",
        configuration.assignments_path.rstrip("/"): ".md",
        configuration.trainers_path.rstrip("/"): ".yml",
    }
    result: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("type") != "blob":
            continue
        name = entry.get("path")
        if not isinstance(name, str) or not _safe_member(name):
            continue
        if name == RUNTIME_FILENAME:
            result.add(name)
            continue
        path = PurePosixPath(name)
        if any(part.startswith("_") for part in path.parts):
            continue
        for root, suffix in roots.items():
            if name.startswith(root + "/") and name.endswith(suffix):
                result.add(name)
                break
    if not (result - {RUNTIME_FILENAME}):
        raise ValueError(
            "Das Repository enthält weder sichtbare Skripte noch Aufgaben oder Trainer."
        )
    return result


def verify_certificate_trainers(configuration, timeout: float = 3.0) -> TrainerVerification:
    """Prüfe online ausschließlich die bewertungsrelevanten Trainerdateien.

    Ist GitHub nicht erreichbar, bleibt der zuletzt beim Zertifikatimport
    vollständig geprüfte Stand nutzbar. Eine erreichbare, aber ungültige
    Hashliste ist dagegen ein harter Fehler.
    """
    repository = _repository_name(configuration.repository)
    branch = quote(configuration.branch, safe="")
    raw = f"https://raw.githubusercontent.com/{repository}/{branch}"
    try:
        document = json.loads(
            _download(f"{raw}/.pykim/trainer-hashes.json", timeout).decode("utf-8")
        )
    except HTTPError as error:
        raise ValueError(
            f"Die Trainer-Hashliste ist im Repository nicht abrufbar (HTTP {error.code})."
        ) from error
    except (URLError, TimeoutError, ConnectionError) as error:
        return TrainerVerification(
            False,
            False,
            f"Trainerprüfung offline: {error}",
        )
    except UnicodeDecodeError as error:
        raise ValueError("Die Remote-Hashliste ist nicht als UTF-8 lesbar.") from error
    except json.JSONDecodeError as error:
        raise ValueError("Die Remote-Hashliste ist kein gültiges JSON.") from error

    entries = _hash_entries(document)
    prefix = configuration.trainers_path.rstrip("/") + "/"
    trainer_entries = {
        name: details for name, details in entries.items() if name.startswith(prefix)
    }
    if not trainer_entries:
        raise ValueError("Die Remote-Hashliste enthält keine Trainerdateien.")

    packaged_root = Path(__file__).resolve().parent
    local_root = active_content_root(packaged_root)
    trainer_root = local_root / configuration.trainers_path
    local_names = {
        path.relative_to(local_root).as_posix()
        for path in trainer_root.rglob("*.yml")
        if path.is_file()
    } if trainer_root.is_dir() else set()
    current = local_names == set(trainer_entries)
    for name, details in trainer_entries.items():
        if not current:
            break
        target = local_root / PurePosixPath(name)
        if not target.is_file():
            current = False
            break
        data = target.read_bytes()
        if len(data) != details["size"] or hashlib.sha256(data).hexdigest() != details["sha256"]:
            current = False
            break
    if current:
        return TrainerVerification(True, False)

    sync_certificate_content(configuration, timeout=max(timeout, 20.0))
    return TrainerVerification(True, True, "Trainerdaten wurden aktualisiert.")


def sync_certificate_content(configuration, timeout: float = 20.0) -> Path:
    """Spiegele den im Zertifikat festgelegten Git-Stand dateiweise und atomar."""
    repository = _repository_name(configuration.repository)
    branch = quote(configuration.branch, safe="")
    commit = _json_url(
        f"https://api.github.com/repos/{repository}/commits/{branch}", timeout
    )
    revision = str(commit.get("sha", ""))
    if len(revision) != 40:
        raise ValueError("Der Remote-Commit konnte nicht bestimmt werden.")
    tree = _json_url(
        f"https://api.github.com/repos/{repository}/git/trees/{revision}?recursive=1",
        timeout,
    )
    raw = f"https://raw.githubusercontent.com/{repository}/{revision}"
    trainer_prefix = configuration.trainers_path.rstrip("/") + "/"
    content_paths = _course_content_paths(tree, configuration)
    discovered_trainers = {
        name for name in content_paths if name.startswith(trainer_prefix)
    }
    trainer_entries = {}
    if discovered_trainers:
        trainer_hashes = json.loads(
            _download(f"{raw}/.pykim/trainer-hashes.json", timeout).decode("utf-8")
        )
        trainer_entries = _hash_entries(trainer_hashes)
        if set(trainer_entries) != {
            name for name in trainer_entries if name.startswith(trainer_prefix)
        }:
            raise ValueError("Die Trainer-Hashliste enthält fremde Dateien.")
        if set(trainer_entries) != discovered_trainers:
            raise ValueError(
                "Trainer-Hashliste und sichtbare Trainerdateien passen nicht zusammen."
            )
    if len(content_paths) > MAX_CONTENT_FILES:
        raise ValueError("Der Remote-Inhalt enthält zu viele Dateien.")

    base = content_directory()
    versions = base / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / revision
    manifest_files: dict[str, str] = {}
    manifest = {"content_version": revision, "files": manifest_files}
    target_valid = False
    if target.is_dir():
        try:
            stored_manifest = json.loads(
                (target / "content-manifest.json").read_text(encoding="utf-8")
            )
            stored_files = stored_manifest.get("files")
            if (
                stored_manifest.get("content_version") != revision
                or not isinstance(stored_files, dict)
                or set(stored_files) != content_paths
            ):
                raise ValueError("Der lokale Inhaltskatalog ist nicht aktuell.")
            _validate_content(target, stored_manifest)
            target_valid = True
        except (OSError, ValueError, TypeError):
            target_valid = False
    if not target_valid:
        with tempfile.TemporaryDirectory(prefix="pykim-git-", dir=base) as temporary:
            staging = Path(temporary) / "content"
            staging.mkdir()
            names = sorted(content_paths)

            def download_content(name: str) -> tuple[str, bytes]:
                return name, _download(f"{raw}/{quote(name, safe='/')}", timeout)

            # Ein Kurs besteht aus vielen kleinen Markdown-/YAML-Dateien. Ein
            # begrenzter paralleler Abruf verkürzt den ersten Import deutlich,
            # ohne GitHub mit einer Verbindung pro Datei zu überlasten.
            with ThreadPoolExecutor(max_workers=min(8, len(names))) as executor:
                downloaded = executor.map(download_content, names)

                total_size = 0
                for name, data in downloaded:
                    total_size += len(data)
                    if total_size > MAX_CONTENT_SIZE:
                        raise ValueError("Der Remote-Inhalt ist zu groß.")
                    digest = hashlib.sha256(data).hexdigest()
                    if name in trainer_entries and (
                        digest != trainer_entries[name]["sha256"]
                        or len(data) != trainer_entries[name]["size"]
                    ):
                        raise ValueError(f"Trainer-Prüfsumme stimmt nicht: {name}")
                    manifest_files[name] = digest
                    destination = staging / PurePosixPath(name)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
            _validate_content(staging, manifest)
            runtime_manifest = staging / RUNTIME_FILENAME
            if runtime_manifest.is_file():
                parse_runtime_manifest(runtime_manifest)
            from insi.training.registry import validate_training_directory

            trainer_directory = staging / configuration.trainers_path
            if trainer_directory.is_dir():
                validate_training_directory(
                    trainer_directory,
                    staging / configuration.assignments_path,
                )
            (staging / "content-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if target.exists():
                shutil.rmtree(target)
            os.replace(staging, target)
    marker_data = json.dumps({"content_version": revision}, indent=2)
    for marker in (base / "active.json", _course_active_marker(configuration)):
        marker.parent.mkdir(parents=True, exist_ok=True)
        temporary_marker = marker.with_suffix(marker.suffix + ".tmp")
        temporary_marker.write_text(marker_data, encoding="utf-8")
        os.replace(temporary_marker, marker)
    return target


def install_content_update(manifest: dict[str, object], timeout: float = 30.0) -> Path:
    """Lade, prüfe und aktiviere ein Inhaltspaket atomar."""
    version = str(manifest.get("content_version", "")).strip()
    package_url = str(manifest.get("package_url", "")).strip()
    package_hash = str(manifest.get("package_sha256", "")).removeprefix("sha256:")
    if not version or not package_url or len(package_hash) != 64:
        raise ValueError("Das Inhaltsmanifest ist unvollständig.")
    request = Request(package_url, headers={"User-Agent": f"insi/{__version__}"})
    archive: bytes | None = None
    try:
        with urlopen(request, timeout=timeout) as response:
            archive = response.read()
    except (URLError, TimeoutError, ConnectionError, OSError):
        # Manche Schulnetze lassen raw.githubusercontent.com passieren, beenden
        # aber GitHubs Release-Asset-Verbindung. Die Einzeldateien bleiben durch
        # das bereits über HTTPS geladene Manifest und dessen SHA-256-Werte
        # genauso streng abgesichert wie das ZIP.
        archive = None
    if archive is not None and hashlib.sha256(archive).hexdigest() != package_hash:
        raise ValueError("Die Prüfsumme des Inhaltspakets stimmt nicht.")

    base = content_directory()
    versions = base / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / version
    with tempfile.TemporaryDirectory(prefix="pykim-content-", dir=base) as temporary:
        extracted = Path(temporary) / "content"
        extracted.mkdir()
        if archive is not None:
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                members = bundle.infolist()
                if len(members) > MAX_CONTENT_FILES:
                    raise ValueError("Das Inhaltspaket enthält zu viele Dateien.")
                if sum(item.file_size for item in members) > MAX_CONTENT_SIZE:
                    raise ValueError("Das Inhaltspaket ist entpackt zu groß.")
                for item in members:
                    mode = item.external_attr >> 16
                    if not _safe_member(item.filename) or stat.S_ISLNK(mode):
                        raise ValueError("Das Inhaltspaket enthält unsichere Pfade.")
                    destination = extracted / PurePosixPath(item.filename)
                    if item.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.open(item) as source, destination.open("wb") as output:
                        shutil.copyfileobj(source, output)
        else:
            expected = manifest.get("files")
            if not isinstance(expected, dict) or not expected:
                raise ValueError("Das Inhaltsmanifest enthält keine Dateien.")
            if len(expected) > MAX_CONTENT_FILES:
                raise ValueError("Das Inhaltsmanifest enthält zu viele Dateien.")
            raw = f"https://raw.githubusercontent.com/{REPOSITORY}/main"

            def download_file(name: str) -> tuple[str, bytes]:
                if not _safe_member(name):
                    raise ValueError(f"Unsicherer Inhaltspfad: {name!r}")
                return name, _download(f"{raw}/{quote(name, safe='/')}", timeout)

            total_size = 0
            names = sorted(name for name in expected if isinstance(name, str))
            if len(names) != len(expected):
                raise ValueError("Das Inhaltsmanifest enthält ungültige Dateinamen.")
            with ThreadPoolExecutor(max_workers=min(8, len(names))) as executor:
                for name, data in executor.map(download_file, names):
                    total_size += len(data)
                    if total_size > MAX_CONTENT_SIZE:
                        raise ValueError("Die Lerninhalte sind zu groß.")
                    destination = extracted / PurePosixPath(name)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
        _validate_content(extracted, manifest)
        (extracted / "content-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if target.exists():
            shutil.rmtree(target)
        os.replace(extracted, target)

    marker = base / "active.json"
    temporary_marker = base / "active.json.tmp"
    temporary_marker.write_text(
        json.dumps({"content_version": version}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary_marker, marker)
    return target
