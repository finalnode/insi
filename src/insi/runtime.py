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


def _executable_path(executable: str | Path) -> Path:
    """Normalisiere einen Interpreterpfad, ohne venv-Symlinks aufzulösen."""
    return Path(os.path.abspath(Path(executable).expanduser()))


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


@dataclass(frozen=True)
class RuntimePackageCheck:
    """Vergleiche eine geforderte mit der tatsächlich installierten Version."""

    requirement: str
    installed: str
    ready: bool


@dataclass(frozen=True)
class RuntimePreflight:
    """Vollständiges Ergebnis der Kursstart-Kompatibilitätsprüfung."""

    ready: bool
    candidate: RuntimeCandidate | None
    required_python: str
    platform_target: str | None
    packages: tuple[RuntimePackageCheck, ...]
    issues: tuple[str, ...]
    warnings: tuple[str, ...]
    offline_packages: bool
    repairable: bool
    provision_candidates: tuple[RuntimeCandidate, ...]

    @property
    def summary(self) -> str:
        if self.ready:
            return "Die Kurslaufzeit ist kompatibel und vollständig."
        return self.issues[0] if self.issues else "Die Kurslaufzeit ist nicht bereit."

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
    path = _executable_path(executable)
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
    path = _executable_path(executable)
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
        executable = _executable_path(path)
        if executable in seen or not executable.is_file():
            continue
        seen.add(executable)
        if executable == _executable_path(sys.executable):
            found.append(
                RuntimeCandidate(
                    str(executable),
                    platform.python_version(),
                    source,
                    sys.version_info >= MINIMUM_PYTHON,
                    importlib.util.find_spec("pykim") is not None,
                    importlib.util.find_spec("pyxel") is not None,
                )
            )
        else:
            found.append(inspect_runtime(executable, source))
    return tuple(found)


def _requirement_versions(
    executable: str | Path,
    requirements: tuple[str, ...],
) -> dict[str, str]:
    """Lese Paketversionen aus genau dem geprüften Interpreter."""
    names = tuple(requirement.split("==", 1)[0] for requirement in requirements)
    if not names:
        return {}
    probe = (
        "import importlib.metadata as m,json,sys;"
        "result={};"
        "exec(\"for name in sys.argv[1:]:\\n"
        " try: result[name]=m.version(name)\\n"
        " except m.PackageNotFoundError: result[name]=''\");"
        "print(json.dumps(result))"
    )
    try:
        completed = subprocess.run(
            [*command_for(str(_executable_path(executable))), "-c", probe, *names],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or "Paketprüfung fehlgeschlagen")
        result = json.loads(completed.stdout)
        if not isinstance(result, dict):
            raise ValueError("Paketprüfung lieferte kein Objekt")
        return {
            name: str(result.get(name, ""))
            for name in names
        }
    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError) as error:
        raise RuntimeError(f"Paketversionen konnten nicht geprüft werden: {error}") from error


def _package_checks(
    candidate: RuntimeCandidate,
    requirements: tuple[str, ...],
) -> tuple[RuntimePackageCheck, ...]:
    installed = _requirement_versions(candidate.executable, requirements)
    return tuple(
        RuntimePackageCheck(
            requirement,
            installed.get(requirement.split("==", 1)[0], ""),
            installed.get(requirement.split("==", 1)[0], "")
            == requirement.split("==", 1)[1],
        )
        for requirement in requirements
    )


def course_runtime_preflight(
    course: str | Path,
    *,
    candidates: tuple[RuntimeCandidate, ...] | None = None,
) -> RuntimePreflight:
    """Prüfe vor Kursstart Python, Pakete, Plattform und Offline-Integrität."""
    from .course import get_runtime_preference
    from .course_archive import course_offline_wheelhouse, installed_course_runtime
    from .course_runtime import RUNTIME_TARGETS, current_runtime_target

    root = Path(course).expanduser().resolve()
    installed_runtime = installed_course_runtime(root)
    manifest = installed_runtime[0] if installed_runtime is not None else None
    required_python = manifest.python if manifest is not None else ""
    requirements = manifest.requirements if manifest is not None else ()
    target = current_runtime_target()
    issues: list[str] = []
    warnings: list[str] = []
    hard_failure = False
    offline_packages = False

    if manifest is not None and target is None:
        issues.append(
            "Die aktuelle Kombination aus Betriebssystem und Architektur wird "
            "von diesem Kurs nicht unterstützt."
        )
        hard_failure = True
    elif manifest is not None and target in manifest.offline_targets:
        try:
            wheelhouse = course_offline_wheelhouse(root, target)
            offline_packages = wheelhouse is not None
            has_extras = any(
                re.sub(r"[-_.]+", "-", item.split("==", 1)[0].casefold())
                not in {"pykim", "pyxel"}
                for item in requirements
            )
            if has_extras and wheelhouse is None:
                issues.append(
                    "Das Offlinepaket ist für diese Plattform unvollständig. "
                    "Importiere das Kurs-ZIP erneut."
                )
                hard_failure = True
        except RuntimeError as error:
            issues.append(str(error))
            hard_failure = True
    elif manifest is not None and any(
        re.sub(r"[-_.]+", "-", item.split("==", 1)[0].casefold())
        not in {"pykim", "pyxel"}
        for item in requirements
    ):
        label = RUNTIME_TARGETS[target].label if target in RUNTIME_TARGETS else "dieses System"
        warnings.append(
            f"Für {label} sind keine Zusatzpakete eingebettet; eine Einrichtung "
            "oder Reparatur kann Internetzugang benötigen."
        )

    discovered = candidates if candidates is not None else discover_runtimes(root)
    ordered: list[RuntimeCandidate] = []
    preference = get_runtime_preference()
    if preference:
        ordered.append(inspect_runtime(preference, "Ausgewählt"))
    for candidate in discovered:
        if all(_executable_path(item.executable) != _executable_path(candidate.executable) for item in ordered):
            ordered.append(candidate)

    def python_matches(candidate: RuntimeCandidate) -> bool:
        version = ".".join(candidate.version.split(".")[:2])
        return candidate.supported and (
            not required_python or version == required_python
        )

    matching = tuple(candidate for candidate in ordered if python_matches(candidate))
    checked: dict[str, tuple[RuntimePackageCheck, ...]] = {}
    probe_errors: dict[str, str] = {}
    ready_candidate = None
    ready_packages: tuple[RuntimePackageCheck, ...] = ()
    for candidate in matching:
        if not (candidate.pykim and candidate.pyxel):
            continue
        try:
            package_status = _package_checks(candidate, requirements)
        except RuntimeError as error:
            probe_errors[candidate.executable] = str(error)
            continue
        checked[candidate.executable] = package_status
        if all(item.ready for item in package_status):
            ready_candidate = candidate
            ready_packages = package_status
            break

    selected = ready_candidate
    if selected is None:
        selected = next(
            (
                candidate for candidate in matching
                if is_managed_runtime(candidate.executable, root)
            ),
            matching[0] if matching else None,
        )
    packages = ready_packages
    if selected is not None and ready_candidate is None and requirements:
        try:
            packages = checked.get(selected.executable) or _package_checks(
                selected, requirements
            )
        except RuntimeError as error:
            probe_errors[selected.executable] = str(error)
            packages = ()

    if selected is None:
        version_note = f" {required_python}" if required_python else ""
        issues.append(
            f"Es wurde kein geeignetes Python{version_note} gefunden. "
            "Installiere die benötigte Python-Version und versuche es erneut."
        )
    elif ready_candidate is None:
        if not selected.pykim:
            issues.append("PyKIM fehlt in der ausgewählten Kurslaufzeit.")
        if not selected.pyxel:
            issues.append("Pyxel fehlt in der ausgewählten Kurslaufzeit.")
        for package in packages:
            if package.ready:
                continue
            name, expected = package.requirement.split("==", 1)
            normalized = re.sub(r"[-_.]+", "-", name.casefold())
            if (normalized == "pykim" and not selected.pykim) or (
                normalized == "pyxel" and not selected.pyxel
            ):
                continue
            if package.installed:
                issues.append(
                    f"{name} hat Version {package.installed}; benötigt wird {expected}."
                )
            else:
                issues.append(f"{package.requirement} ist nicht installiert.")
        if selected.executable in probe_errors:
            issues.append(probe_errors[selected.executable])

    ready = ready_candidate is not None and not hard_failure
    repairable = bool(
        not ready
        and not hard_failure
        and selected is not None
        and python_matches(selected)
        and is_managed_runtime(selected.executable, root)
    )
    managed_root = managed_runtime_path(root).resolve()
    provision_candidates = tuple(
        candidate
        for candidate in matching
        if not _executable_path(candidate.executable).is_relative_to(managed_root)
    ) if not hard_failure else ()
    return RuntimePreflight(
        ready,
        ready_candidate or selected,
        required_python,
        target,
        packages,
        tuple(dict.fromkeys(issues)),
        tuple(warnings),
        offline_packages,
        repairable,
        provision_candidates,
    )


def selected_runtime(course: str | Path | None = None) -> RuntimeCandidate:
    """Wähle eine funktionierende PyKIM-Laufzeit deterministisch aus."""
    from .course import get_runtime_preference

    required_python = None
    requirements: tuple[str, ...] = ()
    if course is not None:
        from .course_archive import installed_course_runtime

        installed = installed_course_runtime(course)
        if installed is not None:
            required_python = installed[0].python
            requirements = installed[0].requirements

    def suitable(candidate: RuntimeCandidate) -> bool:
        version = ".".join(candidate.version.split(".")[:2])
        basics_ready = (
            candidate.supported
            and candidate.pykim
            and candidate.pyxel
            and (required_python is None or version == required_python)
        )
        if not basics_ready:
            return False
        try:
            return all(
                package.ready
                for package in _package_checks(candidate, requirements)
            )
        except RuntimeError:
            return False

    preference = get_runtime_preference()
    if preference:
        preferred = inspect_runtime(preference, "Ausgewählt")
        if suitable(preferred):
            return preferred
    candidates = discover_runtimes(course)
    for candidate in candidates:
        if suitable(candidate):
            return candidate
    version_note = f" in Version {required_python}" if required_python else ""
    raise RuntimeError(
        f"Keine geeignete Python-Laufzeit{version_note} mit PyKIM und Pyxel gefunden. "
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
    from .course_archive import installed_course_runtime

    installed = installed_course_runtime(course)
    if installed is not None and ".".join(base.version.split(".")[:2]) != installed[0].python:
        raise RuntimeError(
            f"Dieser Kurs benötigt Python {installed[0].python}; ausgewählt ist "
            f"Python {base.version or 'unbekannt'}."
        )
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
    course: str | Path | None = None,
    wheelhouse: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [str(_executable_path(python)), "-m", "pip", "install", "--upgrade"]
    explicit = Path(wheelhouse).expanduser().resolve() if wheelhouse is not None else None
    course_wheels = None
    manifest = None
    if course is not None:
        from .course_archive import course_offline_wheelhouse, installed_course_runtime

        course_wheels = course_offline_wheelhouse(course)
        installed = installed_course_runtime(course)
        manifest = installed[0] if installed is not None else None
    bundled = bundled_wheelhouse()
    wheelhouses = []
    for wheels in (explicit, course_wheels, bundled):
        if wheels is None or wheels in wheelhouses:
            continue
        if not wheels.is_dir():
            raise RuntimeError("Das konfigurierte Offline-Wheel-Verzeichnis fehlt.")
        wheelhouses.append(wheels)
    requirements = tuple(manifest.requirements) if manifest is not None else ()
    additional = tuple(
        item for item in requirements
        if re.sub(r"[-_.]+", "-", item.split("==", 1)[0].casefold()) != "pykim"
    )
    has_nonstandard = any(
        re.sub(r"[-_.]+", "-", item.split("==", 1)[0].casefold())
        not in {"pykim", "pyxel"}
        for item in requirements
    )
    current_target_is_offline = False
    if manifest is not None:
        from .course_runtime import current_runtime_target

        current_target_is_offline = current_runtime_target() in manifest.offline_targets
    if current_target_is_offline and not wheelhouses:
        raise RuntimeError(
            "Der Kurs wurde für diese Plattform als Offlinepaket exportiert, "
            "aber die benötigten Wheel-Verzeichnisse fehlen."
        )
    if wheelhouses:
        if explicit is not None or current_target_is_offline or not has_nonstandard:
            command.append("--no-index")
        for wheels in wheelhouses:
            command.extend(["--find-links", str(wheels)])
    command.append(str(_package_source()))
    command.extend(additional)
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
    _install_runtime_packages(python, course=course, wheelhouse=wheelhouse)
    ready = inspect_runtime(python, "PyKIM-Kursumgebung")
    if not (ready.supported and ready.pykim and ready.pyxel):
        raise RuntimeError("Die Kursumgebung wurde erstellt, ist aber noch nicht vollständig.")
    from .course_archive import installed_course_runtime

    installed = installed_course_runtime(course)
    if installed is not None:
        packages = _package_checks(ready, installed[0].requirements)
        missing = [item.requirement for item in packages if not item.ready]
        if missing:
            raise RuntimeError(
                "Die Kursumgebung enthält nicht die geforderten Paketversionen: "
                + ", ".join(missing)
            )
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
    from .course_archive import installed_course_runtime

    installed = installed_course_runtime(course)
    if installed is not None and ".".join(before.version.split(".")[:2]) != installed[0].python:
        raise RuntimeError(
            f"Dieser Kurs benötigt Python {installed[0].python}; die vorhandene "
            f"Kursumgebung verwendet Python {before.version or 'unbekannt'}."
        )
    _install_runtime_packages(executable, course=course, wheelhouse=wheelhouse)
    ready = inspect_runtime(executable, "PyKIM-Kursumgebung")
    if not (ready.supported and ready.pykim and ready.pyxel):
        raise RuntimeError("Die Reparatur wurde beendet, aber die Laufzeit ist nicht vollständig.")
    if installed is not None:
        packages = _package_checks(ready, installed[0].requirements)
        missing = [item.requirement for item in packages if not item.ready]
        if missing:
            raise RuntimeError(
                "Die Reparatur hat nicht alle geforderten Paketversionen hergestellt: "
                + ", ".join(missing)
            )
    set_runtime_preference(ready.executable)
    return ready


def runtime_diagnostics(course: str | Path | None = None) -> dict[str, object]:
    """Liefere einen exportierbaren, datensparsamen Runtime-Systembericht."""
    from .course import get_runtime_preference

    selected = get_runtime_preference()
    candidates = discover_runtimes(course)
    report = {
        "platform": platform.platform(),
        "selected": selected,
        "wheelhouse": str(bundled_wheelhouse() or ""),
        "candidates": [candidate.as_dict() for candidate in candidates],
    }
    if course is not None:
        report["preflight"] = course_runtime_preflight(
            course, candidates=candidates
        ).as_dict()
    return report
