"""Lokale Werkzeuge für IDE, Updates und Pyxel-Ressourcen."""

import getpass
import hashlib
import platform
import shutil
import subprocess
import sys
import os
import tempfile
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

from .interpreter import command_for, python_command
from .execution_security import (
    course_code_policy,
    execution_environment,
    limited_output,
    student_policy,
)
from .progress import merge_sandbox_progress, prepare_sandbox_progress
from .sandbox import sandbox_popen, sandbox_run
from .workspace_files import sandbox_readable_roots
from tempfile import NamedTemporaryFile
from urllib.request import Request

import pykim
from . import __version__
from .network import urlopen

GITHUB_REPOSITORY = "finalnode/insi"


def system_user_name() -> str:
    """Liefere möglichst den Anzeigenamen, sonst den lokalen Kontonamen."""
    login = getpass.getuser().strip()
    if platform.system() != "Windows":
        try:
            import pwd

            full_name = pwd.getpwnam(login).pw_gecos.split(",", 1)[0].strip()
            if full_name:
                return full_name
        except (ImportError, KeyError, OSError):
            pass
    return login or "Schüler/in"


@dataclass(frozen=True)
class SystemStatus:
    python: str
    python_supported: bool
    pykim: str
    pyxel: bool
    thonny: bool
    vscode: bool
    platform: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProgramResult:
    returncode: int
    stdout: str
    stderr: str
    output_truncated: bool = False


class SourceConflictError(RuntimeError):
    """Die Datei wurde seit dem Laden außerhalb der Suite verändert."""


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _application_exists(name: str) -> bool:
    if platform.system() != "Darwin":
        return False
    return (Path("/Applications") / f"{name}.app").exists() or (
        Path.home() / "Applications" / f"{name}.app"
    ).exists()


def detected_ides() -> dict[str, str]:
    """Finde für den Unterricht typische IDEs samt startbarem Pfad."""
    from .ide import discover_ides

    return {key: item.executable for key, item in discover_ides().items()}


def system_status() -> SystemStatus:
    return SystemStatus(
        python=platform.python_version(),
        python_supported=sys.version_info >= (3, 10),
        pykim=pykim.__version__,
        pyxel=shutil.which("pyxel") is not None,
        thonny=shutil.which("thonny") is not None or _application_exists("Thonny"),
        vscode=(
            shutil.which("code") is not None
            or _application_exists("Visual Studio Code")
        ),
        platform=platform.system(),
    )


def open_path(
    path: str | Path,
    ide: str = "system",
    custom_executable: str | Path | None = None,
) -> None:
    """Öffne eine Datei oder einen Ordner mit einer bewusst gewählten Anwendung."""
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"{target} wurde nicht gefunden.")
    system = platform.system()
    if ide == "custom":
        if custom_executable is None:
            raise RuntimeError("Für die eigene IDE wurde kein Programmpfad festgelegt.")
        executable = Path(custom_executable).expanduser().resolve()
        if not executable.exists():
            raise FileNotFoundError(f"Die eingestellte IDE {executable} wurde nicht gefunden.")
        command = (
            ["open", "-a", str(executable), str(target)]
            if system == "Darwin" and executable.suffix == ".app"
            else [str(executable), str(target)]
        )
    elif ide in {"thonny", "vscode", "pycharm"}:
        from .ide import launch_ide

        python = None
        course = None
        if ide in {"vscode", "thonny"}:
            try:
                from .course import get_course_directory
                from .runtime import selected_runtime

                course = get_course_directory()
                python = selected_runtime(course).executable
            except RuntimeError:
                pass
        launch_ide(target, ide, python=python, course=course)
        return
    elif system == "Darwin":
        command = ["open", str(target)]
    elif system == "Windows":
        command = ["explorer", str(target)]
    else:
        command = ["xdg-open", str(target)]
    subprocess.Popen(command)


def open_in_preferred_ide(path: str | Path) -> None:
    """Öffne einen Pfad mit der im Lernstudio gespeicherten IDE."""
    from .course import get_ide_preference

    preference = get_ide_preference()
    open_path(path, preference["ide"], preference["path"] or None)


def launch_pyxel_editor(
    resource: str | Path,
    python: str | Path | None = None,
) -> Path:
    """Starte den offiziellen Editor für Sprites, Tilemaps, Sounds und Musik."""
    if python is None:
        executable = shutil.which("pyxel")
        command = (
            [executable, "edit"]
            if executable is not None
            else [*python_command(), "-m", "pyxel", "edit"]
        )
    else:
        command = [
            *command_for(str(Path(python).expanduser().resolve())),
            "-m",
            "pyxel",
            "edit",
        ]
    target = Path(resource).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.Popen([*command, str(target)], cwd=target.parent)
    return target


def pyxel_examples() -> tuple[Path, ...]:
    """Liefere die Python-Beispiele der tatsächlich installierten Pyxel-Version."""
    try:
        import pyxel
    except ImportError:
        return ()
    directory = Path(pyxel.__file__).resolve().parent / "examples"
    try:
        return tuple(sorted(directory.glob("*.py"), key=lambda path: path.name))
    except OSError:
        return ()


def launch_pyxel_example(example: str | Path) -> Path:
    """Starte ausschließlich ein offizielles Beispiel der Pyxel-Installation."""
    available = {path.resolve() for path in pyxel_examples()}
    target = Path(example).expanduser().resolve()
    if target not in available:
        raise ValueError("Es dürfen nur mitgelieferte Pyxel-Beispiele gestartet werden.")
    executable = shutil.which("pyxel")
    command = (
        [executable, "run"]
        if executable is not None
        else [*python_command(), "-m", "pyxel", "run"]
    )
    subprocess.Popen([*command, str(target)], cwd=target.parent)
    return target


def _course_file(path: str | Path, course: str | Path) -> Path:
    """Erlaube ausführbare Dateien ausschließlich innerhalb des Kursordners."""
    target = Path(path).expanduser().resolve()
    root = Path(course).expanduser().resolve()
    if not target.is_relative_to(root):
        raise ValueError("Es dürfen nur Dateien aus dem Kursordner gestartet werden.")
    if not target.is_file():
        raise FileNotFoundError(f"{target} wurde nicht gefunden.")
    return target


def run_student_program(path: str | Path, course: str | Path) -> Path:
    """Starte eine Python-Aufgabe mit der ausgewählten Schüler-Laufzeit."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können gestartet werden.")
    from .runtime import selected_runtime

    python = selected_runtime(course).executable
    root = Path(course).expanduser().resolve()
    run_root = Path(tempfile.mkdtemp(prefix="insi-task-"))
    progress_path = run_root / "progress.json"
    baseline = prepare_sandbox_progress(progress_path, root)
    policy = student_policy(
        run_root,
        readable_roots=sandbox_readable_roots(root, target),
        writable_roots=(run_root,),
        allow_gui=True,
    )
    environment = execution_environment(
        policy,
        pythonpath=(root,),
        overrides={
            "INSI_PROGRESS_FILE": str(progress_path),
            "INSI_RUN_FILES": str(run_root),
        },
    )
    process = sandbox_popen(
        [*command_for(python), str(target)],
        policy=policy,
        cwd=run_root,
        env=environment,
    )

    def cleanup() -> None:
        process.wait()
        merge_sandbox_progress(progress_path, root, baseline_attempts=baseline)
        shutil.rmtree(run_root, ignore_errors=True)

    threading.Thread(target=cleanup, daemon=True).start()
    return target


def execute_student_program(path: str | Path, course: str | Path) -> ProgramResult:
    """Führe eine Aufgabe aus und sammle ihre vollständige Konsolenausgabe."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können gestartet werden.")
    from .runtime import selected_runtime

    root = Path(course).expanduser().resolve()
    run_root = Path(tempfile.mkdtemp(prefix="insi-task-"))
    progress_path = run_root / "progress.json"
    baseline = prepare_sandbox_progress(progress_path, root)
    policy = student_policy(
        run_root,
        readable_roots=sandbox_readable_roots(root, target),
        writable_roots=(run_root,),
    )
    environment = execution_environment(
        policy,
        pythonpath=(root,),
        overrides={
            "INSI_PROGRESS_FILE": str(progress_path),
            "INSI_RUN_FILES": str(run_root),
        },
    )
    try:
        completed = sandbox_run(
            [*command_for(selected_runtime(course).executable), str(target)],
            policy=policy,
            cwd=run_root,
            capture_output=True,
            text=True,
            env=environment,
            timeout=policy.timeout_seconds,
        )
    finally:
        merge_sandbox_progress(progress_path, root, baseline_attempts=baseline)
        shutil.rmtree(run_root, ignore_errors=True)
    stdout, stdout_truncated = limited_output(
        completed.stdout, policy.max_output_chars
    )
    stderr, stderr_truncated = limited_output(
        completed.stderr, policy.max_output_chars
    )
    return ProgramResult(
        completed.returncode,
        stdout,
        stderr,
        bool(getattr(completed, "output_truncated", False))
        or stdout_truncated
        or stderr_truncated,
    )


def execute_script_example(source: str, timeout: int = 15) -> ProgramResult:
    """Führe ein freigegebenes Skriptbeispiel isoliert als temporäre Datei aus."""
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".py", prefix="pykim-script-", delete=False
        ) as temporary:
            temporary.write(source.rstrip() + "\n")
            temporary_path = Path(temporary.name)
        policy = course_code_policy(temporary_path.parent, timeout_seconds=timeout)
        # Pyxel kann den Prozess beim Schließen des Fensters sehr direkt
        # beenden. Ungepufferte Ausgabe verhindert, dass vorherige print()-
        # Ausgaben dabei noch im stdout-Puffer liegen und verloren gehen.
        environment = execution_environment(
            policy,
            overrides={"PYKIM_PROGRESS_MODE": "disabled"},
        )
        try:
            completed = sandbox_run(
                [*python_command(), "-u", str(temporary_path)],
                policy=policy,
                cwd=temporary_path.parent,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=environment,
            )
            stdout, stdout_truncated = limited_output(
                completed.stdout, policy.max_output_chars
            )
            stderr, stderr_truncated = limited_output(
                completed.stderr, policy.max_output_chars
            )
            return ProgramResult(
                completed.returncode,
                stdout,
                stderr,
                bool(getattr(completed, "output_truncated", False))
                or stdout_truncated
                or stderr_truncated,
            )
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout or ""
            stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr or ""
            message = "Das Beispiel wurde nach 15 Sekunden automatisch beendet."
            return ProgramResult(124, stdout, f"{stderr}\n{message}".strip())
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def read_student_source(path: str | Path, course: str | Path) -> str:
    """Lese eine Python-Aufgabe ausschließlich innerhalb des Kursordners."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können bearbeitet werden.")
    return target.read_text(encoding="utf-8")


def save_student_source(
    path: str | Path,
    source: str,
    course: str | Path,
    *,
    expected_hash: str | None = None,
) -> Path:
    """Speichere eine Schülerdatei atomar, ohne andere lokale Dateien freizugeben."""
    target = _course_file(path, course)
    if target.suffix.lower() != ".py":
        raise ValueError("Nur Python-Dateien mit der Endung .py können bearbeitet werden.")
    current = target.read_text(encoding="utf-8")
    if expected_hash is not None and source_hash(current) != expected_hash:
        raise SourceConflictError(
            "Die Datei wurde außerhalb der Suite verändert. Lade sie neu, bevor du speicherst."
        )
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(source)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return target


def install_or_repair_pyxel() -> subprocess.CompletedProcess[str]:
    """Installiere die von PyKIM unterstützte Pyxel-Version nach Bestätigung."""
    return subprocess.run(
        [*python_command(), "-m", "pip", "install", "--upgrade", "pyxel>=2.2,<3"],
        check=True,
        capture_output=True,
        text=True,
    )


def github_version(timeout: float = 5.0) -> dict[str, object]:
    """Lies die Version des main-Branches ohne etwas zu installieren."""
    url = f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/main/pyproject.toml"
    request = Request(url, headers={"User-Agent": f"insi/{__version__}"})
    with urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8")
    try:
        import tomllib
    except ImportError:  # Python 3.10
        import tomli as tomllib
    remote = tomllib.loads(text)["project"]["version"]
    return {
        "installed": __version__,
        "github": remote,
        "different": remote != __version__,
        "url": f"https://github.com/{GITHUB_REPOSITORY}",
    }


def update_from_github() -> subprocess.CompletedProcess[str]:
    """Installiere nach expliziter Bestätigung den aktuellen main-Branch."""
    url = f"git+https://github.com/{GITHUB_REPOSITORY}.git#subdirectory=insi"
    return subprocess.run(
        [*python_command(), "-m", "pip", "install", "--upgrade", url],
        check=True,
        capture_output=True,
        text=True,
    )
