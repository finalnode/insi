"""IDE-Adapter für eine gemeinsame PyKIM-Laufzeit."""

from __future__ import annotations

import json
import configparser
import hashlib
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IDEInstallation:
    key: str
    label: str
    executable: str


IDE_SPECS = {
    "thonny": ("Thonny", "thonny"),
    "vscode": ("Visual Studio Code", "code"),
    "pycharm": ("PyCharm", "pycharm"),
}


def _mac_application(label: str) -> Path | None:
    if platform.system() != "Darwin":
        return None
    for root in (Path("/Applications"), Path.home() / "Applications"):
        candidate = root / f"{label}.app"
        if candidate.exists():
            return candidate
    return None


def discover_ides() -> dict[str, IDEInstallation]:
    found: dict[str, IDEInstallation] = {}
    for key, (label, command) in IDE_SPECS.items():
        executable = shutil.which(command)
        application = _mac_application(label) if not executable else None
        selected = executable or (str(application) if application else "")
        if selected:
            found[key] = IDEInstallation(key, label, selected)
    return found


def configure_vscode(course: str | Path, python: str | Path) -> tuple[Path, Path]:
    """Konfiguriere ausschließlich den aktuellen Kurs-Workspace."""
    root = Path(course).expanduser().resolve()
    directory = root / ".vscode"
    directory.mkdir(parents=True, exist_ok=True)
    settings = directory / "settings.json"
    extensions = directory / "extensions.json"
    existing: dict[str, object] = {}
    try:
        loaded = json.loads(settings.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            existing = loaded
    except (FileNotFoundError, OSError, ValueError):
        pass
    existing.update(
        {
            "python.defaultInterpreterPath": str(Path(python).expanduser().resolve()),
            "python.terminal.activateEnvironment": True,
        }
    )
    settings.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not extensions.exists():
        extensions.write_text(
            json.dumps({"recommendations": ["ms-python.python"]}, indent=2) + "\n",
            encoding="utf-8",
        )
    return settings, extensions


def thonny_profile_directory(course: str | Path) -> Path:
    root = Path(course).expanduser().resolve()
    key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:12]
    config_root = Path(os.environ.get("PYKIM_CONFIG_DIR", Path.home() / ".pykim"))
    return config_root.expanduser() / "thonny" / key


def configure_thonny(course: str | Path, python: str | Path) -> Path:
    """Erzeuge ein isoliertes Thonny-Profil mit der PyKIM-Runtime."""
    executable = Path(python).expanduser().resolve()
    if not executable.is_file():
        raise FileNotFoundError("Der PyKIM-Interpreter für Thonny wurde nicht gefunden.")
    directory = thonny_profile_directory(course)
    directory.mkdir(parents=True, exist_ok=True)
    configuration = directory / "configuration.ini"
    parser = configparser.ConfigParser(interpolation=None)
    if configuration.exists():
        try:
            parser.read(configuration, encoding="utf-8")
        except configparser.Error as error:
            raise RuntimeError(f"Das PyKIM-Thonny-Profil ist beschädigt: {error}") from error
    for section in ("run", "LocalCPython", "general"):
        if not parser.has_section(section):
            parser.add_section(section)
    parser.set("run", "backend_name", "LocalCPython")
    parser.set("LocalCPython", "executable", str(executable))
    parser.set("general", "single_instance", "False")
    temporary = configuration.with_suffix(".ini.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        parser.write(stream)
    os.replace(temporary, configuration)
    try:
        configuration.chmod(0o600)
    except OSError:
        pass
    return directory


def launch_ide(
    path: str | Path,
    ide: str,
    *,
    python: str | Path | None = None,
    course: str | Path | None = None,
    custom_executable: str | Path | None = None,
) -> None:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"{target} wurde nicht gefunden.")
    if ide == "vscode" and python is not None:
        configure_vscode(target if target.is_dir() else target.parent, python)
    if ide == "custom":
        if custom_executable is None:
            raise RuntimeError("Für die eigene IDE wurde kein Programmpfad festgelegt.")
        executable = Path(custom_executable).expanduser().resolve()
        if not executable.exists():
            raise FileNotFoundError(f"Die eingestellte IDE {executable} wurde nicht gefunden.")
        installed = str(executable)
    else:
        installation = discover_ides().get(ide)
        if installation is None:
            raise RuntimeError(f"Die ausgewählte IDE {ide} wurde nicht gefunden.")
        installed = installation.executable
    executable = Path(installed)
    environment = None
    if ide == "thonny" and python is not None:
        profile_root = course if course is not None else (target if target.is_dir() else target.parent)
        profile = configure_thonny(profile_root, python)
        environment = os.environ.copy()
        environment["THONNY_USER_DIR"] = str(profile)
    if platform.system() == "Darwin" and executable.suffix == ".app":
        command = (
            ["open", "-na", installed, "--args", str(target)]
            if ide == "thonny"
            else ["open", "-a", installed, str(target)]
        )
    else:
        command = [installed, str(target)]
    subprocess.Popen(command, env=environment) if environment is not None else subprocess.Popen(command)
