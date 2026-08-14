"""Qualitätsprüfung für ausführbare Codeblöcke im didaktischen Skript."""

import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .execution_security import (
    course_code_policy,
    execution_environment,
    popen_isolation_options,
)
from .interpreter import python_command

from .library import PARADIGMS, script_chapters

PYKIM_CALLS = {
    "animate", "down", "get_color", "get_position", "get_x", "get_y", "hide", "left",
    "paint", "paint_stop", "play_pause", "play_tone", "right",
    "run", "set_color", "set_position", "set_x", "set_y", "show", "speed", "up",
}


@dataclass(frozen=True)
class ScriptBlockAudit:
    source: str
    path: Path
    line: int
    kind: str
    runnable: bool
    reason: str


def _call_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


def classify_script_block(source: str, path: Path, line: int) -> ScriptBlockAudit:
    """Entscheide, ob ein Block als eigenständiges Programm sinnvoll startbar ist."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return ScriptBlockAudit(source, path, line, "invalid", False, str(error))

    calls = _call_names(tree)
    imports_pykim = any(
        (isinstance(node, ast.ImportFrom) and node.module == "pykim")
        or (
            isinstance(node, ast.Import)
            and any(alias.name == "pykim" for alias in node.names)
        )
        for node in ast.walk(tree)
    )
    imports_pyxel = any(
        isinstance(node, ast.Import)
        and any(alias.name == "pyxel" for alias in node.names)
        for node in ast.walk(tree)
    )
    if "input" in calls:
        return ScriptBlockAudit(
            source, path, line, "interactive-input", False,
            "input() kann in der Suite nicht beantwortet werden.",
        )
    if any(isinstance(node, ast.Pass) for node in ast.walk(tree)):
        return ScriptBlockAudit(
            source, path, line, "incomplete", False,
            "Der Block enthält noch pass und ist absichtlich unvollständig.",
        )
    if imports_pyxel:
        runnable = "run" in calls
        return ScriptBlockAudit(
            source, path, line, "pyxel", runnable,
            "Vollständiges Pyxel-Programm." if runnable else "pyxel.run(...) fehlt.",
        )
    if imports_pykim:
        runnable = "run" in calls
        return ScriptBlockAudit(
            source, path, line, "pykim", runnable,
            "Vollständiges PyKIM-Programm." if runnable else "run() oder world.run(...) fehlt.",
        )
    if calls & PYKIM_CALLS:
        return ScriptBlockAudit(
            source, path, line, "fragment", False,
            "Der Ausschnitt verwendet PyKIM ohne vollständigen Import und run().",
        )
    if "print" in calls:
        return ScriptBlockAudit(
            source, path, line, "console", True, "Eigenständiges Konsolenprogramm.",
        )
    return ScriptBlockAudit(
        source, path, line, "fragment", False,
        "Der Ausschnitt erzeugt allein keine sichtbare Ausgabe.",
    )


def annotated_script_blocks() -> tuple[ScriptBlockAudit, ...]:
    """Liefere die Qualitätsdaten aller derzeit mit @button:run markierten Blöcke."""
    audits = []
    for paradigm in PARADIGMS:
        for chapter in script_chapters(paradigm):
            lines = chapter.content.splitlines()
            for index, line in enumerate(lines):
                if line.strip() != "@button:run":
                    continue
                cursor = index + 1
                while cursor < len(lines) and (
                    lines[cursor].startswith("@button:") or not lines[cursor].strip()
                ):
                    cursor += 1
                if cursor >= len(lines) or lines[cursor].strip() != "```python":
                    audits.append(
                        ScriptBlockAudit("", chapter.path, index + 1, "invalid", False, "Python-Block fehlt.")
                    )
                    continue
                end = cursor + 1
                while end < len(lines) and lines[end].strip() != "```":
                    end += 1
                source = "\n".join(lines[cursor + 1:end]).rstrip()
                audits.append(classify_script_block(source, chapter.path, cursor + 2))
    return tuple(audits)


def run_headless(audit: ScriptBlockAudit, timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    """Führe ein freigegebenes Konsolen-/PyKIM-Programm ohne Grafikfenster aus."""
    if not audit.runnable or audit.kind == "pyxel":
        raise ValueError("Nur freigegebene Konsolen- und PyKIM-Blöcke sind fensterlos prüfbar.")
    policy = course_code_policy(audit.path.parent, timeout_seconds=timeout)
    environment = execution_environment(
        policy,
        overrides={
            "PYKIM_HEADLESS": "1",
            "PYKIM_PROGRESS_MODE": "disabled",
        },
    )
    return subprocess.run(
        [*python_command(), "-c", audit.source],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=environment,
        **popen_isolation_options(),
    )


__all__ = [
    "ScriptBlockAudit", "annotated_script_blocks", "classify_script_block", "run_headless",
]
