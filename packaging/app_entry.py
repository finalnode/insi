"""Gemeinsamer Einstiegspunkt der gebündelten Desktop-App."""

from __future__ import annotations

import faulthandler
import multiprocessing
import os
import platform
import runpy
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from insi.windows_staging import (
    prepare_onefile_runtime_for_appcontainer,
    relaunch_frozen_windows_application,
)


_DESKTOP_LOG = None
_ONEFILE_READY_ENV = "INSI_ONEFILE_BOOTSTRAP_READY"
_ONEFILE_CONTINUE_ENV = "INSI_ONEFILE_BOOTSTRAP_CONTINUE"


def restore_standard_streams() -> None:
    """Verbinde einen fensterlosen PyInstaller-Prozess wieder mit seinen Pipes."""
    if sys.stdout is None:
        sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)


def complete_onefile_bootstrap() -> None:
    """Melde dem Sandboxbroker das Ende der vertrauenswürdigen Entpackphase."""
    ready_value = os.environ.pop(_ONEFILE_READY_ENV, "")
    continue_value = os.environ.pop(_ONEFILE_CONTINUE_ENV, "")
    if not ready_value and not continue_value:
        return
    if not ready_value or not continue_value:
        raise RuntimeError("Der Windows-Onefile-Start-Handshake ist unvollständig.")
    ready = Path(ready_value)
    continuation = Path(continue_value)
    ready.write_text("ready", encoding="ascii")
    deadline = time.monotonic() + 45
    while not continuation.is_file():
        if time.monotonic() >= deadline:
            raise RuntimeError("Der Windows-Sandboxbroker hat den Start nicht freigegeben.")
        time.sleep(0.02)


def configure_desktop_logging() -> Path:
    """Aktiviere das Log auch im gespawnten nativen Fensterprozess."""
    global _DESKTOP_LOG
    log_directory = Path.home() / ".pykim" / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / f"desktop-app-{platform.system().lower()}.log"
    _DESKTOP_LOG = log_file.open("a", encoding="utf-8", buffering=1)
    sys.stdout = _DESKTOP_LOG
    sys.stderr = _DESKTOP_LOG
    faulthandler.enable(_DESKTOP_LOG)
    print(
        f"\n[{datetime.now().isoformat()}] PyKIM-Prozess startet "
        f"(PID {os.getpid()}, Argumente: {sys.argv!r})"
    )
    return log_file


def run_python(arguments: list[str]) -> int:
    """Führe Schülercode mit dem in der App enthaltenen Python aus."""
    args = list(arguments)
    if args and args[0] == "-u":
        args.pop(0)
    if len(args) >= 2 and args[0] == "-c":
        sys.argv = ["-c", *args[2:]]
        namespace = {"__name__": "__main__", "__package__": None}
        exec(compile(args[1], "<string>", "exec"), namespace, namespace)
        return 0
    if len(args) >= 2 and args[0] == "-m":
        sys.argv = [args[1], *args[2:]]
        runpy.run_module(args[1], run_name="__main__", alter_sys=True)
        return 0
    if args and Path(args[0]).suffix.lower() == ".py":
        script = Path(args[0]).expanduser().resolve()
        sys.argv = [str(script), *args[1:]]
        runpy.run_path(str(script), run_name="__main__")
        return 0
    raise SystemExit(
        "Der eingebettete Interpreter erwartet -c CODE, -m MODUL oder eine .py-Datei."
    )


def run_app() -> None:
    """Starte die Suite und schreibe Absturzdetails in ein lokales Log."""
    from insi.app import main

    print(f"[{datetime.now().isoformat()}] in:si startet")
    try:
        # Desktop-Starter können eigene Argumente ergänzen. Die App startet
        # deshalb bewusst im nativen Modus ohne Auswertung dieser Argumente.
        main(arguments=[], native=True)
    except BaseException:
        traceback.print_exc(file=_DESKTOP_LOG)
        raise


if __name__ == "__main__":
    # Der sichtbare Start darf auf SMB/WebDAV liegen. Der AppContainer selbst
    # bleibt netzwerklos: Die portable Distribution wird einmalig lokal
    # gespiegelt und mit unveränderten Argumenten transparent fortgesetzt.
    relaunch_frozen_windows_application()
    prepare_onefile_runtime_for_appcontainer()
    # multiprocessing.freeze_support() übernimmt den nativen Fensterprozess,
    # bevor run_app() erreicht wird. Das Log muss deshalb bereits hier stehen.
    if "--pykim-python" not in sys.argv:
        configure_desktop_logging()
    multiprocessing.freeze_support()
    if len(sys.argv) > 1 and sys.argv[1] == "--pykim-python":
        restore_standard_streams()
        complete_onefile_bootstrap()
        status = run_python(sys.argv[2:])
        sys.stdout.flush()
        sys.stderr.flush()
        raise SystemExit(status)
    run_app()
