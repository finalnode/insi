"""Erkennung und Auswahl der Python-Laufzeit für Schülerprogramme."""

from __future__ import annotations

import json
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .interpreter import command_for


MINIMUM_PYTHON = (3, 10)
RUNTIME_ENV = "PYKIM_PYTHON"


@dataclass(frozen=True)
class RuntimeCandidate:
    """Ein gefundener Python-Interpreter mit geprüftem Funktionsumfang."""

    executable: str
    version: str
    source: str
    supported: bool
    pykim: bool
    pyxel: bool
    error: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _python_in_environment(root: Path) -> Path:
    return root / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")


def _matching_pythons(directory: Path) -> list[Path]:
    """Finde echte Python-Programme, aber keine python-config-Helfer."""
    try:
        entries = tuple(directory.iterdir())
    except OSError:
        return []
    pattern = re.compile(r"python(?:3(?:\.\d+)?)?(?:\.exe)?$", re.IGNORECASE)
    return [entry for entry in entries if entry.is_file() and pattern.fullmatch(entry.name)]


def _environment_pythons(root: Path) -> list[Path]:
    candidates = [
        root / "bin" / "python",
        root / "bin" / "python3",
        root / "Scripts" / "python.exe",
        root / "python.exe",
    ]
    return [candidate for candidate in candidates if candidate.is_file()]


def _windows_launcher_pythons() -> list[Path]:
    launcher = shutil.which("py")
    if not launcher:
        return []
    try:
        completed = subprocess.run(
            [launcher, "-0p"], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return []
    found: list[Path] = []
    for line in completed.stdout.splitlines():
        match = re.search(r"([A-Za-z]:\\.*?python(?:\.exe)?)\s*$", line, re.IGNORECASE)
        if match:
            found.append(Path(match.group(1).strip()))
    return found


def _installed_python_paths() -> list[tuple[Path, str]]:
    """Durchsuche übliche Installationsorte aller unterstützten Plattformen."""
    home = Path.home()
    system_name = platform.system()
    found: list[tuple[Path, str]] = []

    for variable, label in (
        ("CONDA_PREFIX", "Conda"),
        ("VIRTUAL_ENV", "Virtuelle Umgebung"),
    ):
        value = os.environ.get(variable)
        if value:
            found.extend((path, label) for path in _environment_pythons(Path(value)))

    environment_roots = (
        (home / ".conda" / "envs", "Conda"),
        (home / "anaconda3" / "envs", "Conda"),
        (home / "miniconda3" / "envs", "Conda"),
        (home / "miniforge3" / "envs", "Conda"),
        (home / ".pyenv" / "versions", "pyenv"),
        (home / ".local" / "share" / "uv" / "python", "uv"),
    )
    for parent, label in environment_roots:
        try:
            roots = tuple(parent.iterdir())
        except OSError:
            continue
        for root in roots:
            if root.is_dir():
                found.extend((path, label) for path in _environment_pythons(root))

    for root, label in (
        (home / "anaconda3", "Conda"),
        (home / "miniconda3", "Conda"),
        (home / "miniforge3", "Conda"),
    ):
        found.extend((path, label) for path in _environment_pythons(root))

    if system_name == "Darwin":
        for directory, label in (
            (Path("/usr/bin"), "macOS"),
            (Path("/usr/local/bin"), "Homebrew/System"),
            (Path("/opt/homebrew/bin"), "Homebrew"),
        ):
            found.extend((path, label) for path in _matching_pythons(directory))
        framework = Path("/Library/Frameworks/Python.framework/Versions")
        try:
            versions = tuple(framework.iterdir())
        except OSError:
            versions = ()
        for version in versions:
            found.extend((path, "python.org") for path in _matching_pythons(version / "bin"))
        for application_root in (Path("/Applications"), home / "Applications"):
            thonny = application_root / "Thonny.app" / "Contents"
            for relative in (
                Path("Frameworks/Python.framework/Versions/Current/bin"),
                Path("Resources/Python/bin"),
                Path("MacOS"),
            ):
                found.extend((path, "Thonny") for path in _matching_pythons(thonny / relative))
    elif system_name == "Windows":
        found.extend((path, "Python Launcher") for path in _windows_launcher_pythons())
        roots = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Thonny",
            Path(os.environ.get("PROGRAMFILES", "")),
            Path(os.environ.get("PROGRAMFILES(X86)", "")),
        ]
        for root in roots:
            if str(root) in {".", ""}:
                continue
            try:
                directories = tuple(root.iterdir())
            except OSError:
                continue
            for directory in directories:
                if directory.is_dir() and (
                    "python" in directory.name.lower() or "thonny" in str(root).lower()
                ):
                    found.extend((path, "Windows/Thonny") for path in _environment_pythons(directory))
    else:
        for directory in (Path("/usr/bin"), Path("/usr/local/bin"), home / ".local" / "bin"):
            found.extend((path, "Linux") for path in _matching_pythons(directory))

    return found


def managed_runtime_path(course: str | Path) -> Path:
    """Liefere den lokalen Runtime-Pfad eines Kurses.

    Die Umgebung liegt absichtlich nicht im synchronisierten Kursordner. Der
    stabile Hash verhindert gleichzeitig Kollisionen zwischen Kursen.
    """
    from hashlib import sha256

    root = Path(course).expanduser().resolve()
    key = sha256(str(root).encode("utf-8")).hexdigest()[:12]
    base = Path(os.environ.get("PYKIM_RUNTIME_DIR", Path.home() / ".pykim" / "runtimes"))
    return base.expanduser() / key


def is_managed_runtime(executable: str | Path, course: str | Path) -> bool:
    path = Path(executable).expanduser().resolve()
    return path.is_relative_to(managed_runtime_path(course).resolve())


def _candidate_paths(course: str | Path | None = None) -> list[tuple[Path, str]]:
    paths: list[tuple[Path, str]] = []
    configured = os.environ.get(RUNTIME_ENV)
    if configured:
        paths.append((Path(configured).expanduser(), "Umgebungsvariable"))
    if course is not None:
        paths.append((_python_in_environment(managed_runtime_path(course)), "PyKIM-Kursumgebung"))
    paths.append((Path(sys.executable), "Suite"))
    for command in ("python3", "python"):
        executable = shutil.which(command)
        if executable:
            paths.append((Path(executable), "System"))
    paths.extend(_installed_python_paths())
    return paths


def inspect_runtime(executable: str | Path, source: str = "Benutzerdefiniert") -> RuntimeCandidate:
    """Prüfe einen Interpreter in einem getrennten Prozess."""
    path = Path(executable).expanduser().resolve()
    if not path.is_file():
        return RuntimeCandidate(str(path), "", source, False, False, False, "Nicht gefunden")
    probe = (
        "import importlib.util,json,sys;"
        "print(json.dumps({'version':list(sys.version_info[:3]),"
        "'pykim':importlib.util.find_spec('pykim') is not None,"
        "'pyxel':importlib.util.find_spec('pyxel') is not None}))"
    )
    try:
        completed = subprocess.run(
            [*command_for(str(path)), "-c", probe],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or "Prüfung fehlgeschlagen")
        data = json.loads(completed.stdout)
        version_parts = tuple(int(value) for value in data["version"])
        return RuntimeCandidate(
            str(path),
            ".".join(str(value) for value in version_parts),
            source,
            version_parts >= MINIMUM_PYTHON,
            bool(data["pykim"]),
            bool(data["pyxel"]),
        )
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, RuntimeError) as error:
        return RuntimeCandidate(str(path), "", source, False, False, False, str(error))


def discover_runtimes(course: str | Path | None = None) -> tuple[RuntimeCandidate, ...]:
    """Finde Interpreter ohne Duplikate und prüfe jeden genau einmal."""
    found: list[RuntimeCandidate] = []
    seen: set[Path] = set()
    for path, source in _candidate_paths(course):
        resolved = path.expanduser().resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        if resolved == Path(sys.executable).resolve():
            found.append(
                RuntimeCandidate(
                    str(resolved),
                    platform.python_version(),
                    source,
                    sys.version_info >= MINIMUM_PYTHON,
                    importlib.util.find_spec("pykim") is not None,
                    importlib.util.find_spec("pyxel") is not None,
                )
            )
        else:
            found.append(inspect_runtime(resolved, source))
    return tuple(found)


def selected_runtime(course: str | Path | None = None) -> RuntimeCandidate:
    """Wähle eine funktionierende PyKIM-Laufzeit deterministisch aus."""
    from .course import get_runtime_preference

    preference = get_runtime_preference()
    if preference:
        preferred = inspect_runtime(preference, "Ausgewählt")
        if preferred.supported and preferred.pykim and preferred.pyxel:
            return preferred
    candidates = discover_runtimes(course)
    for candidate in candidates:
        if candidate.supported and candidate.pykim and candidate.pyxel:
            return candidate
    raise RuntimeError(
        "Keine geeignete Python-Laufzeit mit PyKIM und Pyxel gefunden. "
        "Richte im Setup zuerst eine PyKIM-Laufzeit ein."
    )


def create_managed_runtime(course: str | Path, base_python: str | Path) -> RuntimeCandidate:
    """Erzeuge eine isolierte Kursumgebung aus einem geprüften Interpreter.

    Die Installation von PyKIM/Pyxel bleibt ein eigener, expliziter Schritt;
    damit löst diese Funktion weder ungefragt Downloads noch Updates aus.
    """
    base = inspect_runtime(base_python, "Basis")
    if not base.supported:
        raise RuntimeError("Der ausgewählte Interpreter wird von PyKIM nicht unterstützt.")
    root = managed_runtime_path(course)
    subprocess.run([base.executable, "-m", "venv", str(root)], check=True)
    return inspect_runtime(_python_in_environment(root), "PyKIM-Kursumgebung")


def _package_source() -> Path:
    """Finde ein mitgeliefertes Wheel oder den Entwicklungs-Quellbaum."""
    configured = os.environ.get("PYKIM_PACKAGE_SOURCE")
    if configured:
        source = Path(configured).expanduser().resolve()
        if source.exists():
            return source
        raise RuntimeError("Die konfigurierte PyKIM-Paketquelle wurde nicht gefunden.")
    wheels = bundled_wheelhouse()
    if wheels is not None:
        pykim_wheels = sorted(wheels.glob("PyKIM-*.whl"))
        if pykim_wheels:
            return pykim_wheels[-1]
    project = Path(__file__).resolve().parents[3]
    if (project / "pyproject.toml").is_file():
        return project
    raise RuntimeError(
        "Im Suite-Paket wurde kein PyKIM-Wheel gefunden. Die Installation kann nicht fortgesetzt werden."
    )


def bundled_wheelhouse() -> Path | None:
    """Finde ein vollständiges Offline-Wheel-Verzeichnis der Suite."""
    configured = os.environ.get("PYKIM_WHEELHOUSE")
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend(
        (
            Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)) / "wheels",
            Path(sys.executable).resolve().parent / "wheels",
            Path(sys.executable).resolve().parents[1] / "Resources" / "wheels",
            Path(__file__).resolve().parent / "wheels",
            Path(__file__).resolve().parents[3] / "dist" / "wheelhouse",
        )
    )
    for directory in candidates:
        try:
            if directory.is_dir() and any(directory.glob("*.whl")):
                return directory.resolve()
        except OSError:
            continue
    return None


def _install_runtime_packages(
    python: str | Path,
    *,
    wheelhouse: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [str(Path(python).expanduser().resolve()), "-m", "pip", "install", "--upgrade"]
    wheels = Path(wheelhouse).expanduser().resolve() if wheelhouse is not None else bundled_wheelhouse()
    if wheels is not None:
        if not wheels.is_dir():
            raise RuntimeError("Das konfigurierte Offline-Wheel-Verzeichnis fehlt.")
        command.extend(["--no-index", "--find-links", str(wheels)])
    command.append(str(_package_source()))
    return subprocess.run(command, check=True, capture_output=True, text=True)


def provision_managed_runtime(
    course: str | Path,
    base_python: str | Path,
    *,
    wheelhouse: str | Path | None = None,
) -> RuntimeCandidate:
    """Erzeuge eine Kursumgebung und installiere PyKIM samt Abhängigkeiten."""
    candidate = create_managed_runtime(course, base_python)
    python = candidate.executable
    _install_runtime_packages(python, wheelhouse=wheelhouse)
    ready = inspect_runtime(python, "PyKIM-Kursumgebung")
    if not (ready.supported and ready.pykim and ready.pyxel):
        raise RuntimeError("Die Kursumgebung wurde erstellt, ist aber noch nicht vollständig.")
    from .course import set_runtime_preference

    set_runtime_preference(ready.executable)
    return ready


def repair_runtime(
    course: str | Path,
    *,
    wheelhouse: str | Path | None = None,
) -> RuntimeCandidate:
    """Installiere die vorgesehenen Pakete erneut in der gewählten Runtime."""
    from .course import get_runtime_preference, set_runtime_preference

    executable = get_runtime_preference()
    if not executable:
        raise RuntimeError("Es wurde noch keine Python-Laufzeit ausgewählt.")
    if not is_managed_runtime(executable, course):
        raise RuntimeError(
            "Nur eine von PyKIM verwaltete Kursumgebung kann automatisch repariert werden."
        )
    before = inspect_runtime(executable, "Ausgewählt")
    if not before.supported:
        raise RuntimeError("Die gewählte Python-Laufzeit ist nicht mehr verfügbar oder ungeeignet.")
    _install_runtime_packages(executable, wheelhouse=wheelhouse)
    ready = inspect_runtime(executable, "PyKIM-Kursumgebung")
    if not (ready.supported and ready.pykim and ready.pyxel):
        raise RuntimeError("Die Reparatur wurde beendet, aber die Laufzeit ist nicht vollständig.")
    set_runtime_preference(ready.executable)
    return ready


def runtime_diagnostics(course: str | Path | None = None) -> dict[str, object]:
    """Liefere einen exportierbaren, datensparsamen Runtime-Systembericht."""
    from .course import get_runtime_preference

    selected = get_runtime_preference()
    candidates = discover_runtimes(course)
    return {
        "platform": platform.platform(),
        "selected": selected,
        "wheelhouse": str(bundled_wheelhouse() or ""),
        "candidates": [candidate.as_dict() for candidate in candidates],
    }
