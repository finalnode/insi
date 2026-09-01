"""Lokales Staging für portable Windows-Starts aus Netzlaufwerken."""

from __future__ import annotations

import ctypes
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from pathlib import PureWindowsPath
from typing import Mapping, Sequence

from .windows_paths import is_windows_network_path


STAGED_SOURCE_ENV = "INSI_STAGED_FROM_NETWORK"
STAGED_APPLICATION_ENV = "INSI_STAGED_APPLICATION_ROOT"
APPLICATION_IDENTITY_FILE = ".insi-build-id"
_COMPLETE_MARKER = ".insi-stage-complete"
_APPCONTAINER_ACCESS_MARKER = ".insi-appcontainer-access"
_ALL_APPLICATION_PACKAGES_SID = "S-1-15-2-1"
_SINGLE_PATH_ENVIRONMENT = frozenset(
    {
        "INSI_COURSE_FILES",
        "INSI_GLOBAL_FILES",
        "INSI_PROGRESS_FILE",
        "INSI_PROJECT_FILES",
        "INSI_RUN_FILES",
        "PYKIM_CONTENT_DIR",
        "PYKIM_COURSE_DIR",
    }
)


def environment_has_network_path(environment: Mapping[str, str]) -> bool:
    """Erkenne freigegebene Einzelpfade und Einträge im Python-Suchpfad."""

    if any(
        value and is_windows_network_path(value)
        for name, value in environment.items()
        if name in _SINGLE_PATH_ENVIRONMENT
    ):
        return True
    return any(
        value and is_windows_network_path(value)
        for value in environment.get("PYTHONPATH", "").split(os.pathsep)
    )


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_digests(root: Path) -> dict[str, str]:
    if root.is_file():
        return {".": _file_digest(root)}
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise OSError(f"Verknüpfungen im Netzlaufwerk werden nicht ausgeführt: {path}")
        if path.is_file():
            result[str(path.relative_to(root))] = _file_digest(path)
    return result


def _ensure_no_links(root: Path) -> None:
    if root.is_symlink():
        raise OSError(f"Verknüpfungen im Netzlaufwerk werden nicht ausgeführt: {root}")
    if root.is_dir():
        for path in root.rglob("*"):
            if path.is_symlink():
                raise OSError(
                    f"Verknüpfungen im Netzlaufwerk werden nicht ausgeführt: {path}"
                )


@dataclass(frozen=True)
class NetworkWriteback:
    """Ein lokal ausgeführter, kontrolliert zurückzuschreibender Bereich."""

    source: Path
    staged: Path
    baseline: Mapping[str, str]


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".insi-sync-",
        dir=target.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def sync_network_writebacks(writebacks: Sequence[NetworkWriteback]) -> None:
    """Synchronisiere nur neue/geänderte Dateien und erkenne Fremdänderungen."""

    for writeback in writebacks:
        current = _tree_digests(writeback.staged)
        deleted = {
            relative: digest
            for relative, digest in writeback.baseline.items()
            if relative not in current
        }
        changed = {
            relative: digest
            for relative, digest in current.items()
            if writeback.baseline.get(relative) != digest
        }
        staged_directories = (
            sorted(
                (path for path in writeback.staged.rglob("*") if path.is_dir()),
                key=lambda path: len(path.parts),
            )
            if writeback.staged.is_dir()
            else []
        )

        # Erst alle Ziele prüfen. Bei einem Konflikt darf noch keine andere
        # Datei desselben Schreibbereichs verändert worden sein.
        for staged_directory in staged_directories:
            relative = staged_directory.relative_to(writeback.staged)
            source_directory = writeback.source / relative
            if source_directory.is_symlink() or (
                source_directory.exists() and not source_directory.is_dir()
            ):
                raise OSError(
                    "Ein neuer Projektordner kollidiert mit einem Eintrag im "
                    f"Netzlaufwerk: {source_directory}"
                )
        for relative, original in deleted.items():
            source_file = (
                writeback.source
                if relative == "."
                else writeback.source / relative
            )
            if not source_file.exists():
                continue
            if source_file.is_symlink() or not source_file.is_file():
                raise OSError(
                    f"Unerwarteter Dateityp beim Zurückschreiben: {source_file}"
                )
            if _file_digest(source_file) != original:
                raise OSError(
                    "Die Datei wurde während des Programmlaufs im Netzlaufwerk "
                    f"geändert und deshalb nicht gelöscht: {source_file}"
                )
        for relative in changed:
            source_file = (
                writeback.source
                if relative == "."
                else writeback.source / relative
            )
            original = writeback.baseline.get(relative)
            if source_file.is_symlink():
                raise OSError(
                    f"Eine Verknüpfung wird nicht überschrieben: {source_file}"
                )
            if original is None and source_file.exists():
                raise OSError(
                    "Die Datei wurde während des Programmlaufs im Netzlaufwerk "
                    f"neu angelegt und deshalb nicht überschrieben: {source_file}"
                )
            if original is not None:
                if not source_file.is_file() or _file_digest(source_file) != original:
                    raise OSError(
                        "Die Datei wurde während des Programmlaufs im Netzlaufwerk "
                        f"geändert und deshalb nicht überschrieben: {source_file}"
                    )

        for staged_directory in staged_directories:
            relative = staged_directory.relative_to(writeback.staged)
            (writeback.source / relative).mkdir(parents=True, exist_ok=True)
        for relative in deleted:
            source_file = (
                writeback.source
                if relative == "."
                else writeback.source / relative
            )
            if source_file.exists():
                source_file.unlink()
        for relative in changed:
            source_file = (
                writeback.source
                if relative == "."
                else writeback.source / relative
            )
            staged_file = (
                writeback.staged
                if relative == "."
                else writeback.staged / relative
            )
            _atomic_copy(staged_file, source_file)
        if writeback.staged.is_dir() and writeback.source.is_dir():
            directories = sorted(
                (path for path in writeback.source.rglob("*") if path.is_dir()),
                key=lambda path: len(path.parts),
                reverse=True,
            )
            for directory in directories:
                relative = directory.relative_to(writeback.source)
                if not (writeback.staged / relative).exists():
                    try:
                        directory.rmdir()
                    except OSError:
                        pass


class WindowsNetworkRunStage:
    """Lokale Sicht auf explizit freigegebene Netzwerkpfade eines Laufs."""

    def __init__(self, environment: Mapping[str, str]) -> None:
        candidates = (
            environment.get("LOCALAPPDATA", ""),
            environment.get("TEMP", ""),
            environment.get("TMP", ""),
            tempfile.gettempdir(),
        )
        base = next(
            (
                Path(value)
                for value in candidates
                if value and not is_windows_network_path(value)
            ),
            None,
        )
        if base is None:
            raise OSError("Windows stellt keinen lokalen Staging-Ordner bereit.")
        staging_base = base / "in-si" / "sandbox-staging"
        staging_base.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="run-", dir=staging_base))
        self._writebacks: dict[str, NetworkWriteback] = {}

    def local_path(self, value: str | os.PathLike[str]) -> Path:
        """Bilde UNC und verbundene Laufwerke kollisionsfrei lokal ab."""

        windows_path = PureWindowsPath(os.fspath(value).replace("/", "\\"))
        anchor = windows_path.anchor or windows_path.drive
        anchor_key = hashlib.sha256(anchor.casefold().encode("utf-8")).hexdigest()[:12]
        parts = windows_path.parts[1:] if windows_path.anchor else windows_path.parts
        return self.root / "paths" / anchor_key / Path(*parts)

    def stage_path(
        self,
        value: str | os.PathLike[str],
        *,
        writable: bool = False,
    ) -> Path:
        if not is_windows_network_path(value):
            return Path(value)
        source = Path(value)
        target = self.local_path(value)
        if source.is_symlink():
            raise OSError(f"Verknüpfungen im Netzlaufwerk werden nicht ausgeführt: {source}")
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif source.is_dir():
            _ensure_no_links(source)
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            raise FileNotFoundError(f"Netzwerkpfad wurde nicht gefunden: {source}")
        if writable:
            key = os.fspath(source).casefold()
            self._writebacks[key] = NetworkWriteback(
                source,
                target,
                _tree_digests(target),
            )
        return target

    def map_path(self, value: str | os.PathLike[str]) -> Path:
        return self.local_path(value) if is_windows_network_path(value) else Path(value)

    def map_environment(self, environment: Mapping[str, str]) -> dict[str, str]:
        mapped = dict(environment)
        for name in _SINGLE_PATH_ENVIRONMENT:
            value = mapped.get(name)
            if value and is_windows_network_path(value):
                mapped[name] = str(self.local_path(value))
        pythonpath = mapped.get("PYTHONPATH")
        if pythonpath:
            mapped["PYTHONPATH"] = os.pathsep.join(
                str(self.map_path(value))
                for value in pythonpath.split(os.pathsep)
                if value
            )
        return mapped

    @property
    def writebacks(self) -> tuple[NetworkWriteback, ...]:
        return tuple(self._writebacks.values())


def _application_fingerprint(executable: Path) -> str:
    digest = hashlib.sha256()
    with executable.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    identity_file = executable.parent / APPLICATION_IDENTITY_FILE
    try:
        identity = identity_file.read_text(encoding="ascii").strip()
    except (FileNotFoundError, OSError, UnicodeError):
        identity = ""
    if len(identity) == 64 and all(
        character in "0123456789abcdef" for character in identity
    ):
        digest.update(identity.encode("ascii"))
    return digest.hexdigest()[:20]


def _valid_application_stage(directory: Path, executable_name: str, key: str) -> bool:
    try:
        marker = (directory / _COMPLETE_MARKER).read_text(encoding="ascii").strip()
        access = (directory / _APPCONTAINER_ACCESS_MARKER).read_text(
            encoding="ascii"
        ).strip()
    except (FileNotFoundError, OSError, UnicodeError):
        return False
    return (
        marker == key
        and access == _ALL_APPLICATION_PACKAGES_SID
        and (directory / executable_name).is_file()
        and (directory / "_internal").is_dir()
    )


def _grant_staged_application_access(directory: Path) -> None:
    """Setze Vererbung, bevor Dateien in den leeren App-Cache kopiert werden."""

    if os.name == "nt":
        subprocess.run(
            [
                "icacls",
                str(directory),
                "/grant:r",
                f"*{_ALL_APPLICATION_PACKAGES_SID}:(OI)(CI)RX",
                "/Q",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    (directory / _APPCONTAINER_ACCESS_MARKER).write_text(
        _ALL_APPLICATION_PACKAGES_SID,
        encoding="ascii",
    )


def _show_windows_error(message: str) -> None:
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        message_box = user32.MessageBoxW
        message_box.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
        ]
        message_box.restype = ctypes.c_int
        message_box(None, message, "in:si – Netzwerkstart", 0x10)
    except (AttributeError, OSError, TypeError):
        pass


def stage_application_directory(
    executable: str | os.PathLike[str],
    *,
    environment: Mapping[str, str],
) -> Path:
    """Kopiere genau einen portablen Build versionsgebunden in LocalAppData."""

    source_executable = Path(executable)
    source_directory = source_executable.parent
    key = _application_fingerprint(source_executable)
    local_app_data = environment.get("LOCALAPPDATA", "").strip()
    if not local_app_data or is_windows_network_path(local_app_data):
        raise OSError("Windows stellt keinen lokalen Benutzerordner bereit.")
    cache_root = Path(local_app_data) / "in-si" / "staged-apps"
    cache_root.mkdir(parents=True, exist_ok=True)
    target_directory = cache_root / key
    if _valid_application_stage(target_directory, source_executable.name, key):
        return target_directory / source_executable.name

    temporary = Path(tempfile.mkdtemp(prefix=f".{key}-", dir=cache_root))
    try:
        # Die ACL am noch leeren Ordner zu setzen ist konstant schnell. Alle
        # danach kopierten Unterordner und Dateien erben ausschließlich RX;
        # ein minutenlanger rekursiver icacls-Durchlauf entfällt.
        _grant_staged_application_access(temporary)
        shutil.copytree(source_directory, temporary, dirs_exist_ok=True)
        copied_executable = temporary / source_executable.name
        if _application_fingerprint(copied_executable) != key:
            raise OSError("Die lokal kopierte in:si-EXE ist unvollständig.")
        (temporary / _COMPLETE_MARKER).write_text(key, encoding="ascii")
        if target_directory.exists():
            shutil.rmtree(target_directory)
        os.replace(temporary, target_directory)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return target_directory / source_executable.name


def relaunch_frozen_windows_application(
    executable: str | os.PathLike[str] | None = None,
    *,
    arguments: Sequence[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> None:
    """Setze einen UNC-/Netzlaufwerkstart transparent aus LocalAppData fort."""

    if sys.platform != "win32":
        return
    source = os.fspath(executable or sys.executable)
    if not is_windows_network_path(source):
        return
    child_environment = dict(environment or os.environ)
    child_arguments = list(arguments or sys.argv[1:])
    try:
        local_executable = stage_application_directory(
            source,
            environment=child_environment,
        )
        child_environment[STAGED_SOURCE_ENV] = source
        child_environment[STAGED_APPLICATION_ENV] = str(local_executable.parent)
        child_environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        command = [str(local_executable), *child_arguments]
        if child_arguments[:1] == ["--pykim-python"]:
            completed = subprocess.run(
                command,
                cwd=local_executable.parent,
                env=child_environment,
                check=False,
            )
            raise SystemExit(completed.returncode)
        subprocess.Popen(
            command,
            cwd=local_executable.parent,
            env=child_environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        message = (
            "in:si konnte den Netzwerkstart nicht lokal vorbereiten. "
            f"Quelle: {source}\n\n{error}"
        )
        _show_windows_error(message)
        raise SystemExit(message) from error
    raise SystemExit(0)
