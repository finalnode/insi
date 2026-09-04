"""Gemeinsame Sicherheitsrichtlinie für ausgeführten Lern- und Kurscode.

Die Richtlinie beschreibt die Fähigkeiten eines Starts unabhängig vom
Betriebssystem. Der Sandbox-Runner setzt sie nur mit einem verifizierten
Adapter um; andernfalls wird fremder Code nicht innerhalb von in:si gestartet.
"""

from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping


DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_MAX_OUTPUT_CHARS = 1_000_000
DEFAULT_MAX_MEMORY_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_PROCESSES = 16
DEFAULT_MAX_WRITTEN_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_CPU_SECONDS = 120.0


class CodeOrigin(str, Enum):
    """Herkunft des Codes, der von der Suite gestartet wird."""

    STUDENT = "student"
    COURSE = "course"
    BUILTIN = "builtin"


@dataclass(frozen=True)
class ExecutionPolicy:
    """Explizite Fähigkeiten und Grenzen eines Programmstarts."""

    origin: CodeOrigin
    workspace: Path
    writable_roots: tuple[Path, ...]
    readable_roots: tuple[Path, ...] = ()
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS
    max_memory_bytes: int = DEFAULT_MAX_MEMORY_BYTES
    max_processes: int = DEFAULT_MAX_PROCESSES
    max_written_bytes: int = DEFAULT_MAX_WRITTEN_BYTES
    max_cpu_seconds: float = DEFAULT_MAX_CPU_SECONDS
    allow_network: bool = False
    allow_gui: bool = False

    def __post_init__(self) -> None:
        workspace = self.workspace.expanduser().resolve()
        roots = tuple(root.expanduser().resolve() for root in self.writable_roots)
        readable = tuple(root.expanduser().resolve() for root in self.readable_roots)
        if self.timeout_seconds <= 0:
            raise ValueError("Die Laufzeitgrenze muss größer als null sein.")
        if self.max_output_chars <= 0:
            raise ValueError("Die Ausgabegrenze muss größer als null sein.")
        if self.max_memory_bytes <= 0:
            raise ValueError("Die Speichergrenze muss größer als null sein.")
        if self.max_processes <= 0:
            raise ValueError("Die Prozessgrenze muss größer als null sein.")
        if self.max_written_bytes <= 0:
            raise ValueError("Die Schreibgrenze muss größer als null sein.")
        if self.max_cpu_seconds <= 0:
            raise ValueError("Die CPU-Grenze muss größer als null sein.")
        if not roots:
            raise ValueError("Mindestens ein vorgesehener Schreibbereich ist nötig.")
        related = any(
            workspace.is_relative_to(root) or root.is_relative_to(workspace)
            for root in roots
        )
        if not related:
            raise ValueError("Der Arbeitsordner muss zu einem Schreibbereich gehören.")
        object.__setattr__(self, "workspace", workspace)
        object.__setattr__(self, "writable_roots", roots)
        object.__setattr__(self, "readable_roots", readable)


_EXACT_SECRET_NAMES = {
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "SSH_AUTH_SOCK",
    "SSH_AGENT_PID",
}
_SECRET_SUFFIXES = (
    "_ACCESS_TOKEN",
    "_API_KEY",
    "_AUTH_TOKEN",
    "_CLIENT_SECRET",
    "_PASSWORD",
    "_PRIVATE_KEY",
    "_SECRET",
)
_UNSAFE_PYTHON_ENVIRONMENT = {
    "PYTHONBREAKPOINT",
    "PYTHONINSPECT",
    "PYTHONSTARTUP",
}
_ALLOWED_ENVIRONMENT = {
    "COLORTERM",
    "COMSPEC",
    "DISPLAY",
    "LANG",
    "LANGUAGE",
    "NUMBER_OF_PROCESSORS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PULSE_SERVER",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SYSTEMROOT",
    "INSI_STAGED_APPLICATION_ROOT",
    "TERM",
    "TEMP",
    "TMP",
    "TMPDIR",
    "TZ",
    "WAYLAND_DISPLAY",
    "WINDIR",
    "XDG_RUNTIME_DIR",
}
_ALLOWED_ENVIRONMENT_PREFIXES = ("LC_", "PYXEL_", "SDL_")


def student_policy(
    workspace: str | Path,
    *,
    readable_roots: tuple[str | Path, ...] = (),
    writable_roots: tuple[str | Path, ...] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    max_memory_bytes: int = DEFAULT_MAX_MEMORY_BYTES,
    max_processes: int = DEFAULT_MAX_PROCESSES,
    max_written_bytes: int = DEFAULT_MAX_WRITTEN_BYTES,
    max_cpu_seconds: float = DEFAULT_MAX_CPU_SECONDS,
    allow_gui: bool = False,
) -> ExecutionPolicy:
    """Erzeuge die verbindliche Richtlinie für einen Student Workspace."""

    root = Path(workspace).expanduser().resolve()
    writable = (root,) if writable_roots is None else tuple(
        Path(path).expanduser().resolve() for path in writable_roots
    )
    return ExecutionPolicy(
        CodeOrigin.STUDENT,
        root,
        writable,
        tuple(Path(path).expanduser().resolve() for path in readable_roots),
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
        max_memory_bytes=max_memory_bytes,
        max_processes=max_processes,
        max_written_bytes=max_written_bytes,
        max_cpu_seconds=max_cpu_seconds,
        allow_gui=allow_gui,
    )


def course_code_policy(
    workspace: str | Path,
    *,
    readable_roots: tuple[str | Path, ...] = (),
    writable_roots: tuple[str | Path, ...] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    max_memory_bytes: int = DEFAULT_MAX_MEMORY_BYTES,
    max_processes: int = DEFAULT_MAX_PROCESSES,
    max_written_bytes: int = DEFAULT_MAX_WRITTEN_BYTES,
    max_cpu_seconds: float = DEFAULT_MAX_CPU_SECONDS,
    allow_gui: bool = False,
) -> ExecutionPolicy:
    root = Path(workspace).expanduser().resolve()
    writable = (root,) if writable_roots is None else tuple(
        Path(path).expanduser().resolve() for path in writable_roots
    )
    return ExecutionPolicy(
        CodeOrigin.COURSE,
        root,
        writable,
        tuple(Path(path).expanduser().resolve() for path in readable_roots),
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
        max_memory_bytes=max_memory_bytes,
        max_processes=max_processes,
        max_written_bytes=max_written_bytes,
        max_cpu_seconds=max_cpu_seconds,
        allow_gui=allow_gui,
    )


def builtin_policy(
    workspace: str | Path,
    *,
    readable_roots: tuple[str | Path, ...] = (),
    writable_roots: tuple[str | Path, ...] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    allow_gui: bool = False,
) -> ExecutionPolicy:
    root = Path(workspace).expanduser().resolve()
    writable = (root,) if writable_roots is None else tuple(
        Path(path).expanduser().resolve() for path in writable_roots
    )
    return ExecutionPolicy(
        CodeOrigin.BUILTIN,
        root,
        writable,
        tuple(Path(path).expanduser().resolve() for path in readable_roots),
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
        allow_gui=allow_gui,
    )


def _looks_sensitive(name: str) -> bool:
    upper = name.upper()
    return upper in _EXACT_SECRET_NAMES or upper.endswith(_SECRET_SUFFIXES)


def execution_environment(
    policy: ExecutionPolicy,
    *,
    pythonpath: tuple[str | Path, ...] = (),
    overrides: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Erzeuge eine kompatible Umgebung ohne typische Zugangsdaten.

    Es wird nur eine kleine Kompatibilitätsliste für Sprache, Terminal und
    grafische Sitzungen übernommen. HOME, D-Bus, Agenten, Proxys und der
    Host-PYTHONPATH werden nicht an Lerncode weitergereicht.
    """

    environment = {
        name: value
        for name, value in os.environ.items()
        if (
            name in _ALLOWED_ENVIRONMENT
            or name.startswith(_ALLOWED_ENVIRONMENT_PREFIXES)
        )
        and not _looks_sensitive(name)
        and name not in _UNSAFE_PYTHON_ENVIRONMENT
    }
    paths = [str(Path(path).expanduser().resolve()) for path in pythonpath]
    # Auch ein nicht installiertes Entwickler-Checkout muss den optionalen
    # in:si-Trainer-Provider in Kindprozessen auflösen können. In gebündelten
    # Apps zeigt derselbe Pfad auf das PyInstaller-Paketverzeichnis.
    paths.append(str(Path(__file__).resolve().parents[1]))
    if paths:
        environment["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    else:
        environment.pop("PYTHONPATH", None)
    environment["PYTHONUNBUFFERED"] = "1"
    environment["PYKIM_CODE_ORIGIN"] = policy.origin.value
    # PyKIM bleibt von der Host-Anwendung unabhängig. in:si übergibt jedem
    # Kindprozess deshalb ausschließlich lokale, bereits ausgewählte Pfade.
    try:
        from .course import get_course_directory
        from .library import PACKAGED_CONTENT_ROOT
        from .updates import active_content_root

        course = get_course_directory()
        if course is not None:
            environment["PYKIM_COURSE_DIR"] = str(course)
            from .workspace_files import course_files_directory

            environment["INSI_COURSE_FILES"] = str(course_files_directory(course))
        from .workspace_files import global_files_directory

        environment["INSI_GLOBAL_FILES"] = str(global_files_directory())
        selected_content = str(active_content_root(PACKAGED_CONTENT_ROOT))
        environment["PYKIM_CONTENT_DIR"] = selected_content
        environment["PYKIM_TRAINER_PROVIDER"] = "insi.training.provider:provider"
    except (OSError, ValueError):
        # Diagnose- und Autorenwerkzeuge dürfen auch ohne eingerichteten Kurs
        # mit der explizit übergebenen Prozessumgebung laufen.
        pass
    if overrides:
        environment.update(
            {str(name): str(value) for name, value in overrides.items()}
        )
    return environment


def popen_isolation_options() -> dict[str, object]:
    """Starte Code in einer eigenen Prozessgruppe für zuverlässiges Stoppen."""

    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def terminate_process(process: subprocess.Popen[object], *, force: bool = False) -> None:
    """Beende nach Möglichkeit die ganze für den Start erzeugte Prozessgruppe."""

    if process.poll() is not None:
        return
    terminate_tree = getattr(process, "terminate_tree", None)
    if callable(terminate_tree):
        terminate_tree(force=force)
        return
    if os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)
            return
        except (OSError, ProcessLookupError):
            pass
    if force:
        process.kill()
    else:
        process.terminate()


def limited_output(value: str, limit: int) -> tuple[str, bool]:
    """Begrenze gespeicherte Ausgabe und markiere sichtbare Kürzungen."""

    if len(value) <= limit:
        return value, False
    marker = "\n… Ausgabe wurde aus Sicherheitsgründen gekürzt.\n"
    return value[: max(0, limit - len(marker))] + marker, True


__all__ = [
    "CodeOrigin",
    "DEFAULT_MAX_CPU_SECONDS",
    "DEFAULT_MAX_MEMORY_BYTES",
    "ExecutionPolicy",
    "DEFAULT_MAX_OUTPUT_CHARS",
    "DEFAULT_MAX_PROCESSES",
    "DEFAULT_MAX_WRITTEN_BYTES",
    "DEFAULT_TIMEOUT_SECONDS",
    "builtin_policy",
    "course_code_policy",
    "execution_environment",
    "limited_output",
    "popen_isolation_options",
    "student_policy",
    "terminate_process",
]
