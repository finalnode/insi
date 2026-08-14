"""Gemeinsame Sicherheitsrichtlinie für ausgeführten Lern- und Kurscode.

Die Richtlinie ist bewusst ehrlich: Ein getrennter Prozess ist noch keine
Sandbox. Sie reduziert heute unbeabsichtigte Datenweitergabe und begrenzt
Laufzeit sowie Ausgabe. Echte Dateisystem- und Netzwerkgrenzen werden später
von betriebssystemspezifischen Adaptern umgesetzt.
"""

from __future__ import annotations

import os
import platform
import signal
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping


DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_MAX_OUTPUT_CHARS = 1_000_000


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
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS
    allow_network: bool = True

    def __post_init__(self) -> None:
        workspace = self.workspace.expanduser().resolve()
        roots = tuple(root.expanduser().resolve() for root in self.writable_roots)
        if self.timeout_seconds <= 0:
            raise ValueError("Die Laufzeitgrenze muss größer als null sein.")
        if self.max_output_chars <= 0:
            raise ValueError("Die Ausgabegrenze muss größer als null sein.")
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


@dataclass(frozen=True)
class ExecutionProtection:
    """Tatsächlich aktive Schutzmerkmale der aktuellen Implementierung."""

    process_separated: bool
    environment_sanitized: bool
    runtime_limited: bool
    output_limited: bool
    filesystem_isolated: bool
    network_isolated: bool
    os_sandbox_active: bool
    platform: str

    @property
    def summary(self) -> str:
        if self.os_sandbox_active:
            return "Betriebssystem-Sandbox aktiv."
        return (
            "Prozess begrenzt; Dateisystem und Netzwerk sind noch nicht durch "
            "eine Betriebssystem-Sandbox isoliert."
        )


ACTIVE_PROTECTION = ExecutionProtection(
    process_separated=True,
    environment_sanitized=True,
    runtime_limited=True,
    output_limited=True,
    filesystem_isolated=False,
    network_isolated=False,
    os_sandbox_active=False,
    platform=platform.system() or "Unbekannt",
)


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


def student_policy(
    workspace: str | Path,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
) -> ExecutionPolicy:
    """Erzeuge die heutige Richtlinie für einen Student Workspace.

    Der Schreibbereich ist bereits für einen späteren Sandbox-Adapter
    festgelegt. Ohne aktiven Adapter ist er noch keine technische Grenze.
    Dadurch können Projekte später innerhalb des Workspaces etwa SQLite-Dateien
    verwenden, ohne pauschal schreibgeschützt zu werden.
    """

    root = Path(workspace).expanduser().resolve()
    return ExecutionPolicy(
        CodeOrigin.STUDENT,
        root,
        (root,),
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
    )


def course_code_policy(
    workspace: str | Path,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
) -> ExecutionPolicy:
    root = Path(workspace).expanduser().resolve()
    return ExecutionPolicy(
        CodeOrigin.COURSE,
        root,
        (root,),
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
    )


def builtin_policy(
    workspace: str | Path,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
) -> ExecutionPolicy:
    root = Path(workspace).expanduser().resolve()
    return ExecutionPolicy(
        CodeOrigin.BUILTIN,
        root,
        (root,),
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
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

    HOME und grafische Sitzungsvariablen bleiben vorerst erhalten, weil Pyxel
    und native Fenster sie benötigen. Das ist ausdrücklich keine
    Dateisystemisolation.
    """

    environment = {
        name: value
        for name, value in os.environ.items()
        if not _looks_sensitive(name) and name not in _UNSAFE_PYTHON_ENVIRONMENT
    }
    paths = [str(Path(path).expanduser().resolve()) for path in pythonpath]
    existing = environment.get("PYTHONPATH", "")
    paths.extend(part for part in existing.split(os.pathsep) if part)
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
    "ACTIVE_PROTECTION",
    "CodeOrigin",
    "ExecutionPolicy",
    "ExecutionProtection",
    "builtin_policy",
    "course_code_policy",
    "execution_environment",
    "limited_output",
    "popen_isolation_options",
    "student_policy",
    "terminate_process",
]
