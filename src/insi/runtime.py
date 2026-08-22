"""Erkennung und Auswahl der Python-Laufzeit für Schülerprogramme."""

from __future__ import annotations

import json
import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path
from tempfile import NamedTemporaryFile, mkdtemp

from .interpreter import command_for


MINIMUM_PYTHON = (3, 10)
RUNTIME_ENV = "INSI_PYTHON"
LEGACY_RUNTIME_ENV = "PYKIM_PYTHON"
PYXEL_RUNTIME_REQUIREMENT = "Pyxel==2.9.9"
LEGACY_RUNTIME_REQUIREMENTS = (
    "PyKIM==0.6.0",
    PYXEL_RUNTIME_REQUIREMENT,
    "PyYAML==6.0.3",
)


def _normalized_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.casefold())


LEGACY_RUNTIME_PACKAGE_NAMES = frozenset(
    _normalized_package_name(requirement.split("==", 1)[0])
    for requirement in LEGACY_RUNTIME_REQUIREMENTS
)


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
    packages: tuple[str, ...]
    error: str = ""

    def has_package(self, name: str) -> bool:
        expected = _normalized_package_name(name)
        return any(_normalized_package_name(item) == expected for item in self.packages)

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


def _directory_entries(directory: Path) -> tuple[Path, ...]:
    try:
        return tuple(directory.iterdir())
    except OSError:
        return ()


def _matching_pythons(directory: Path) -> list[Path]:
    """Finde echte Python-Programme, aber keine python-config-Helfer."""
    pattern = re.compile(r"python(?:3(?:\.\d+)?)?(?:\.exe)?$", re.IGNORECASE)
    return [
        entry
        for entry in _directory_entries(directory)
        if entry.is_file() and pattern.fullmatch(entry.name)
    ]


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
        for root in _directory_entries(parent):
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
        for version in _directory_entries(framework):
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
            for directory in _directory_entries(root):
                if directory.is_dir() and (
                    "python" in directory.name.lower() or "thonny" in str(root).lower()
                ):
                    found.extend((path, "Windows/Thonny") for path in _environment_pythons(directory))
    else:
        for directory in (Path("/usr/bin"), Path("/usr/local/bin"), home / ".local" / "bin"):
            found.extend((path, "Linux") for path in _matching_pythons(directory))

    return found


def managed_runtime_path(course: str | Path) -> Path:
    """Liefere den stabilen lokalen Verwaltungsordner eines Kurses.

    Die Umgebung liegt absichtlich nicht im synchronisierten Kursordner. Der
    stabile Hash verhindert gleichzeitig Kollisionen zwischen Kursen.
    """
    from hashlib import sha256

    root = Path(course).expanduser().resolve()
    key = sha256(str(root).encode("utf-8")).hexdigest()[:12]
    configured = os.environ.get("INSI_RUNTIME_DIR") or os.environ.get(
        "PYKIM_RUNTIME_DIR"
    )
    base = Path(configured or Path.home() / ".pykim" / "runtimes")
    return base.expanduser() / key


def _active_managed_python(course: str | Path) -> Path | None:
    """Lese die atomar aktivierte Runtime-Generation eines Kurses."""
    root = managed_runtime_path(course).resolve()
    try:
        data = json.loads((root / "active.json").read_text(encoding="utf-8"))
        relative = Path(str(data["environment"]))
        if relative.is_absolute() or ".." in relative.parts:
            return None
        environment = (root / relative).resolve()
        if not environment.is_relative_to(root):
            return None
        python = _python_in_environment(environment)
        return python if python.is_file() else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _runtime_environment(executable: str | Path) -> Path:
    path = _executable_path(executable)
    if path.parent.name.casefold() in {"bin", "scripts"}:
        return path.parent.parent
    raise ValueError("Der Interpreter gehört zu keiner erkennbaren Kursumgebung.")


def _activate_managed_runtime(course: str | Path, executable: str | Path) -> None:
    """Aktiviere eine vollständig geprüfte Generation über einen atomaren Marker."""
    root = managed_runtime_path(course).resolve()
    environment = _runtime_environment(executable).resolve()
    if not environment.is_relative_to(root):
        raise ValueError("Die neue Laufzeit liegt außerhalb der Kursverwaltung.")
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "active.json"
    temporary_path = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=root, prefix="active-", delete=False
        ) as temporary:
            json.dump(
                {"environment": environment.relative_to(root).as_posix()},
                temporary,
                ensure_ascii=False,
                indent=2,
            )
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, marker)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def is_managed_runtime(executable: str | Path, course: str | Path) -> bool:
    path = _executable_path(executable)
    return path.is_relative_to(managed_runtime_path(course).resolve())


def _candidate_paths(course: str | Path | None = None) -> list[tuple[Path, str]]:
    paths: list[tuple[Path, str]] = []
    configured = os.environ.get(RUNTIME_ENV) or os.environ.get(LEGACY_RUNTIME_ENV)
    if configured:
        paths.append((Path(configured).expanduser(), "Umgebungsvariable"))
    if course is not None:
        active = _active_managed_python(course)
        if active is not None:
            paths.append((active, "Kursumgebung"))
        paths.append((_python_in_environment(managed_runtime_path(course)), "Kursumgebung"))
    paths.append((Path(sys.executable), "Suite"))
    for command in ("python3", "python"):
        executable = shutil.which(command)
        if executable:
            paths.append((Path(executable), "System"))
    paths.extend(_installed_python_paths())
    return paths


@cache
def _suite_packages() -> tuple[str, ...]:
    """Inventarisiere den unveränderlichen Paketbestand des App-Prozesses einmal."""
    names = {item.metadata.get("Name", "") for item in importlib.metadata.distributions()}
    return tuple(sorted(names - {""}))


def inspect_runtime(executable: str | Path, source: str = "Benutzerdefiniert") -> RuntimeCandidate:
    """Prüfe einen Interpreter in einem getrennten Prozess."""
    path = _executable_path(executable)
    if not path.is_file():
        return RuntimeCandidate(str(path), "", source, False, (), "Nicht gefunden")
    probe = (
        "import importlib.metadata as m,json,sys;"
        "print(json.dumps({'version':list(sys.version_info[:3]),"
        "'packages':sorted({d.metadata.get('Name','') for d in m.distributions()} - {''})}))"
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
            tuple(str(item) for item in data["packages"]),
        )
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, RuntimeError) as error:
        return RuntimeCandidate(str(path), "", source, False, (), str(error))


def discover_runtimes(course: str | Path | None = None) -> tuple[RuntimeCandidate, ...]:
    """Finde Interpreter und prüfe unabhängige Prozesse begrenzt parallel."""
    pending: list[RuntimeCandidate | tuple[Path, str]] = []
    seen: set[Path] = set()
    for path, source in _candidate_paths(course):
        executable = _executable_path(path)
        if executable in seen or not executable.is_file():
            continue
        seen.add(executable)
        if executable == _executable_path(sys.executable):
            pending.append(
                RuntimeCandidate(
                    str(executable),
                    platform.python_version(),
                    source,
                    sys.version_info >= MINIMUM_PYTHON,
                    _suite_packages(),
                )
            )
        else:
            pending.append((executable, source))

    probes = [item for item in pending if isinstance(item, tuple)]
    if not probes:
        return tuple(item for item in pending if isinstance(item, RuntimeCandidate))
    with ThreadPoolExecutor(max_workers=min(4, len(probes))) as executor:
        inspected = iter(executor.map(lambda item: inspect_runtime(*item), probes))
        return tuple(
            next(inspected) if isinstance(item, tuple) else item
            for item in pending
        )


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
    checks = []
    for requirement in requirements:
        name, expected = requirement.split("==", 1)
        actual = installed.get(name, "")
        checks.append(RuntimePackageCheck(requirement, actual, actual == expected))
    return tuple(checks)


def _installed_manifest(course: str | Path):
    from .course_storage import installed_course_runtime

    installed = installed_course_runtime(course)
    return installed[0] if installed is not None else None


def _has_nonstandard_requirements(requirements: tuple[str, ...]) -> bool:
    return any(
        _normalized_package_name(item.split("==", 1)[0])
        not in LEGACY_RUNTIME_PACKAGE_NAMES
        for item in requirements
    )


def _matches_python(candidate: RuntimeCandidate, required_python: str | None) -> bool:
    """Prüfe Support und optional die geforderte Python-Major/Minor-Version."""
    version = ".".join(candidate.version.split(".")[:2])
    return candidate.supported and (not required_python or version == required_python)


def course_runtime_preflight(
    course: str | Path,
    *,
    candidates: tuple[RuntimeCandidate, ...] | None = None,
) -> RuntimePreflight:
    """Prüfe vor Kursstart Python, Pakete, Plattform und Offline-Integrität."""
    from .course import get_runtime_preference
    from .course_storage import course_offline_wheelhouse
    from .course_runtime import RUNTIME_TARGETS, current_runtime_target

    root = Path(course).expanduser().resolve()
    manifest = _installed_manifest(root)
    required_python = manifest.python if manifest is not None else ""
    requirements = (
        manifest.requirements if manifest is not None else LEGACY_RUNTIME_REQUIREMENTS
    )
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
            has_extras = _has_nonstandard_requirements(requirements)
            if has_extras and wheelhouse is None:
                issues.append(
                    "Das Offlinepaket ist für diese Plattform unvollständig. "
                    "Importiere das Kurs-ZIP erneut."
                )
                hard_failure = True
        except RuntimeError as error:
            issues.append(str(error))
            hard_failure = True
    elif manifest is not None and _has_nonstandard_requirements(requirements):
        label = RUNTIME_TARGETS[target].label if target in RUNTIME_TARGETS else "dieses System"
        warnings.append(
            f"Für {label} sind keine Zusatzpakete eingebettet; eine Einrichtung "
            "oder Reparatur kann Internetzugang benötigen."
        )

    discovered = candidates if candidates is not None else discover_runtimes(root)
    by_path = {
        _executable_path(candidate.executable): candidate
        for candidate in discovered
    }
    preference = get_runtime_preference()
    if preference:
        preferred_path = _executable_path(preference)
        preferred = by_path.pop(preferred_path, None) or inspect_runtime(
            preference, "Ausgewählt"
        )
        ordered = (preferred, *by_path.values())
    else:
        ordered = tuple(by_path.values())

    matching = tuple(
        candidate for candidate in ordered
        if _matches_python(candidate, required_python)
    )
    checked: dict[str, tuple[RuntimePackageCheck, ...]] = {}
    probe_errors: dict[str, str] = {}
    ready_candidate = None
    ready_packages: tuple[RuntimePackageCheck, ...] = ()
    for candidate in matching:
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

    selected = ready_candidate or next(
        (
            candidate for candidate in matching
            if is_managed_runtime(candidate.executable, root)
        ),
        matching[0] if matching else None,
    )
    packages = ready_packages
    if selected is not None and ready_candidate is None and requirements:
        packages = checked.get(selected.executable, ())

    if selected is None:
        version_note = f" {required_python}" if required_python else ""
        issues.append(
            f"Es wurde kein geeignetes Python{version_note} gefunden. "
            "Installiere die benötigte Python-Version und versuche es erneut."
        )
    elif ready_candidate is None:
        for package in packages:
            if package.ready:
                continue
            name, expected = package.requirement.split("==", 1)
            if package.installed:
                issues.append(
                    f"{name} hat Version {package.installed}; benötigt wird {expected}."
                )
            else:
                issues.append(
                    f"{name} fehlt; benötigt wird {package.requirement}."
                )
        if selected.executable in probe_errors:
            issues.append(probe_errors[selected.executable])

    ready = ready_candidate is not None and not hard_failure
    repairable = bool(
        not ready
        and not hard_failure
        and selected is not None
        and _matches_python(selected, required_python)
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


def selected_runtime(
    course: str | Path | None = None,
    *,
    additional_requirements: tuple[str, ...] = (),
) -> RuntimeCandidate:
    """Wähle eine mit dem Kursprofil kompatible Laufzeit deterministisch aus."""
    from .course import get_runtime_preference

    required_python = None
    requirements = LEGACY_RUNTIME_REQUIREMENTS
    if course is not None:
        manifest = _installed_manifest(course)
        if manifest is not None:
            required_python = manifest.python
            requirements = manifest.requirements
    effective_requirements = tuple(
        dict.fromkeys((*requirements, *additional_requirements))
    )

    def suitable(candidate: RuntimeCandidate) -> bool:
        if not _matches_python(candidate, required_python):
            return False
        try:
            return all(
                package.ready
                for package in _package_checks(candidate, effective_requirements)
            )
        except RuntimeError:
            return False

    preference = get_runtime_preference()
    checked_paths: set[Path] = set()
    if preference:
        preferred = inspect_runtime(preference, "Ausgewählt")
        checked_paths.add(_executable_path(preferred.executable))
        if suitable(preferred):
            return preferred
    candidates = discover_runtimes(course)
    for candidate in candidates:
        if _executable_path(candidate.executable) in checked_paths:
            continue
        if suitable(candidate):
            return candidate
    version_note = f" in Version {required_python}" if required_python else ""
    package_note = (
        " mit " + ", ".join(additional_requirements)
        if additional_requirements
        else ""
    )
    raise RuntimeError(
        f"Keine geeignete Python-Laufzeit{version_note}{package_note} "
        "für das Kursprofil gefunden. "
        "Richte im Setup zuerst eine kompatible Laufzeit ein."
    )


def create_managed_runtime(
    course: str | Path,
    base_python: str | Path | RuntimeCandidate,
) -> RuntimeCandidate:
    """Erzeuge eine neue isolierte Runtime-Generation.

    Die Paketinstallation bleibt ein eigener, expliziter Schritt;
    damit löst diese Funktion weder ungefragt Downloads noch Updates aus.
    """
    base = (
        base_python
        if isinstance(base_python, RuntimeCandidate)
        else inspect_runtime(base_python, "Basis")
    )
    if not base.supported:
        raise RuntimeError("Der ausgewählte Interpreter wird von in:si nicht unterstützt.")
    manifest = _installed_manifest(course)
    if manifest is not None and not _matches_python(base, manifest.python):
        raise RuntimeError(
            f"Dieser Kurs benötigt Python {manifest.python}; ausgewählt ist "
            f"Python {base.version or 'unbekannt'}."
        )
    versions = managed_runtime_path(course) / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    environment = Path(mkdtemp(prefix="runtime-", dir=versions))
    try:
        subprocess.run(
            [*command_for(base.executable), "-m", "venv", str(environment)],
            check=True,
        )
        candidate = inspect_runtime(_python_in_environment(environment), "Kursumgebung")
        if not candidate.supported:
            raise RuntimeError(
                "Die neue Kursumgebung konnte nicht vollständig erzeugt werden."
            )
        return candidate
    except BaseException:
        shutil.rmtree(environment, ignore_errors=True)
        raise


def bundled_wheelhouse() -> Path | None:
    """Finde ein vollständiges Offline-Wheel-Verzeichnis der Suite."""
    configured = os.environ.get("INSI_WHEELHOUSE") or os.environ.get(
        "PYKIM_WHEELHOUSE"
    )
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
        from .course_storage import course_offline_wheelhouse

        course_wheels = course_offline_wheelhouse(course)
        manifest = _installed_manifest(course)
    bundled = bundled_wheelhouse()
    wheelhouses = []
    for wheels in (explicit, course_wheels, bundled):
        if wheels is None or wheels in wheelhouses:
            continue
        if not wheels.is_dir():
            raise RuntimeError("Das konfigurierte Offline-Wheel-Verzeichnis fehlt.")
        wheelhouses.append(wheels)
    requirements = (
        tuple(manifest.requirements)
        if manifest is not None
        else LEGACY_RUNTIME_REQUIREMENTS
    )
    has_nonstandard = _has_nonstandard_requirements(requirements)
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
    command.extend(requirements)
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _validate_managed_runtime(
    course: str | Path,
    candidate: RuntimeCandidate,
    *,
    action: str,
) -> None:
    """Prüfe eine neue Generation vollständig vor ihrer Aktivierung."""
    if not candidate.supported:
        raise RuntimeError(
            f"{action} wurde beendet, aber die Laufzeit ist nicht vollständig."
        )
    manifest = _installed_manifest(course)
    requirements = (
        manifest.requirements if manifest is not None else LEGACY_RUNTIME_REQUIREMENTS
    )
    packages = _package_checks(candidate, requirements)
    missing = [item.requirement for item in packages if not item.ready]
    if missing:
        raise RuntimeError(
            f"{action} hat nicht alle geforderten Paketversionen hergestellt: "
            + ", ".join(missing)
        )


def provision_managed_runtime(
    course: str | Path,
    base_python: str | Path | RuntimeCandidate,
    *,
    wheelhouse: str | Path | None = None,
) -> RuntimeCandidate:
    """Baue, prüfe und aktiviere eine neue Runtime-Generation."""
    candidate = create_managed_runtime(course, base_python)
    environment = _runtime_environment(candidate.executable)
    try:
        _install_runtime_packages(
            candidate.executable, course=course, wheelhouse=wheelhouse
        )
        ready = inspect_runtime(candidate.executable, "Kursumgebung")
        _validate_managed_runtime(course, ready, action="Die Einrichtung")
    except BaseException:
        shutil.rmtree(environment, ignore_errors=True)
        raise
    _activate_managed_runtime(course, ready.executable)
    from .course import set_runtime_preference

    set_runtime_preference(ready.executable)
    return ready


def repair_runtime(
    course: str | Path,
    *,
    wheelhouse: str | Path | None = None,
) -> RuntimeCandidate:
    """Ersetze eine defekte Runtime erst nach erfolgreichem Neuaufbau."""
    from .course import get_runtime_preference

    executable = get_runtime_preference()
    if not executable:
        raise RuntimeError("Es wurde noch keine Python-Laufzeit ausgewählt.")
    if not is_managed_runtime(executable, course):
        raise RuntimeError(
            "Nur eine von in:si verwaltete Kursumgebung kann automatisch repariert werden."
        )
    before = inspect_runtime(executable, "Ausgewählt")
    if not before.supported:
        raise RuntimeError("Die gewählte Python-Laufzeit ist nicht mehr verfügbar oder ungeeignet.")
    return provision_managed_runtime(course, before, wheelhouse=wheelhouse)


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
