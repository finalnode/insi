"""Python-Aufrufe innerhalb der normalen und der gebündelten Suite."""

from __future__ import annotations

import sys
from pathlib import Path

EMBEDDED_PYTHON_NAME = "insi-python"


def command_for(executable: str) -> list[str]:
    """Ergänze bei der eingefrorenen Suite deren Interpreter-Schalter."""
    command = [executable]
    if (
        getattr(sys, "frozen", False)
        and executable == sys.executable
    ):
        executable_path = Path(sys.executable)
        runner = executable_path.with_name(
            f"{EMBEDDED_PYTHON_NAME}{executable_path.suffix}"
        )
        # Alte PyKIM-Suite-Bundles bleiben startbar, bis sie durch einen
        # in:si-Build ersetzt wurden.
        legacy_runner = executable_path.with_name(
            f"PyKIM Python{executable_path.suffix}"
        )
        if runner.is_file():
            command = [str(runner), "--insi-python"]
        elif legacy_runner.is_file():
            command = [str(legacy_runner), "--pykim-python"]
        else:
            command = [str(Path(sys.executable)), "--insi-python"]
    return command


def python_command() -> list[str]:
    """Liefere den Einstieg zum eingebetteten oder normalen Interpreter."""
    return command_for(sys.executable)
