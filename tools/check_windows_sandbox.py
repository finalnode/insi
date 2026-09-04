"""Prüfe den echten AppContainer-Runner im gebündelten Windows-Build."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path

from insi import sandbox
from insi.execution_security import execution_environment, student_policy
from insi.interpreter import python_command
from insi.sandbox import WindowsAppContainerAdapter, sandbox_run


def _progress(message: str) -> None:
    print(f"windows-sandbox-progress:{message}", flush=True)


def _run_isolation_probe(root: Path) -> None:
    readable = root / "readable"
    writable = root / "writable"
    private = root / "private"
    for directory in (readable, writable, private):
        directory.mkdir()
    secret = private / "secret.txt"
    secret.write_text("host-secret", encoding="utf-8")
    program = readable / "isolation_probe.py"
    program.write_text(
        "import json, socket\n"
        "from pathlib import Path\n"
        f"secret=Path({str(secret)!r})\n"
        "result={}\n"
        "try:\n result['read']=secret.read_text()\n"
        "except Exception:\n result['read']='blocked'\n"
        "try:\n secret.write_text('changed'); result['write']='allowed'\n"
        "except Exception:\n result['write']='blocked'\n"
        "try:\n socket.create_connection(('1.1.1.1',53),.25); result['network']='allowed'\n"
        "except Exception:\n result['network']='blocked'\n"
        "Path('inside.txt').write_text('ok')\n"
        "print(json.dumps(result))\n",
        encoding="utf-8",
    )
    policy = student_policy(
        writable,
        readable_roots=(program,),
        writable_roots=(writable,),
        timeout_seconds=15,
    )
    completed = sandbox_run(
        [*python_command(), str(program)],
        policy=policy,
        cwd=writable,
        env=execution_environment(policy),
        capture_output=True,
        text=True,
        timeout=20,
    )
    result = json.loads(completed.stdout)
    assert completed.returncode == 0, completed.stderr
    assert result == {"read": "blocked", "write": "blocked", "network": "blocked"}
    assert secret.read_text(encoding="utf-8") == "host-secret"
    assert (writable / "inside.txt").read_text(encoding="utf-8") == "ok"


def _run_process_limit_probe(root: Path) -> None:
    readable = root / "process-readable"
    writable = root / "process-writable"
    readable.mkdir()
    writable.mkdir()
    program = readable / "process_probe.py"
    program.write_text(
        "import subprocess, sys, time\n"
        "command=[sys.executable]\n"
        "if getattr(sys,'frozen',False): command.append('--pykim-python')\n"
        "command += ['-c','import time; time.sleep(20)']\n"
        "children=[subprocess.Popen(command) for _ in range(5)]\n"
        "time.sleep(20)\n",
        encoding="utf-8",
    )
    policy = student_policy(
        writable,
        readable_roots=(program,),
        writable_roots=(writable,),
        timeout_seconds=15,
        max_processes=2,
    )
    completed = sandbox_run(
        [*python_command(), str(program)],
        policy=policy,
        cwd=writable,
        env=execution_environment(policy),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode != 0
    assert (
        "Prozessgrenze" in completed.stderr
        or "WinError 1816" in completed.stderr
    ), completed.stderr


def _run_write_limit_probe(root: Path) -> None:
    readable = root / "write-readable"
    writable = root / "write-writable"
    readable.mkdir()
    writable.mkdir()
    program = readable / "write_probe.py"
    program.write_text(
        "from pathlib import Path\n"
        "import time\n"
        "Path('too-large.bin').write_bytes(b'x' * 2_000_000)\n"
        "time.sleep(20)\n",
        encoding="utf-8",
    )
    policy = student_policy(
        writable,
        readable_roots=(program,),
        writable_roots=(writable,),
        timeout_seconds=15,
        max_written_bytes=32 * 1024,
    )
    completed = sandbox_run(
        [*python_command(), str(program)],
        policy=policy,
        cwd=writable,
        env=execution_environment(policy),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode != 0
    assert "Schreibgrenze" in completed.stderr, completed.stderr


def _run_gui_probe(root: Path) -> None:
    readable = root / "gui-readable"
    writable = root / "gui-writable"
    readable.mkdir()
    writable.mkdir()
    program = readable / "gui_probe.py"
    program.write_text(
        "import pyxel\n"
        "pyxel.init(16, 16, title='in:si Sandbox-Probelauf')\n"
        "print('gui-ok', flush=True)\n"
        "pyxel.quit()\n",
        encoding="utf-8",
    )
    policy = student_policy(
        writable,
        readable_roots=(program,),
        writable_roots=(writable,),
        timeout_seconds=15,
        allow_gui=True,
    )
    completed = sandbox_run(
        [*python_command(), str(program)],
        policy=policy,
        cwd=writable,
        env=execution_environment(policy),
        capture_output=True,
        text=True,
        timeout=45,
    )
    if completed.returncode != 0:
        hosted_runner_without_opengl = (
            os.environ.get("GITHUB_ACTIONS") == "true"
            and "called glCreateShader but it was not loaded" in completed.stderr
        )
        assert hosted_runner_without_opengl, completed.stderr
        print("GUI-AppContainer gestartet; OpenGL fehlt auf dem GitHub-Windows-Runner.")
        return
    assert "gui-ok" in completed.stdout


def main() -> int:
    if platform.system() != "Windows":
        raise SystemExit("Dieser Test muss unter Windows laufen.")
    adapter = WindowsAppContainerAdapter()
    _progress("status-start")
    status = adapter.status()
    _progress("status-done")
    if not status.available:
        raise RuntimeError(status.detail)
    sandbox._adapter_override = adapter
    with sandbox._temporary_windows_probe() as root:
        _progress("isolation-start")
        _run_isolation_probe(root)
        _progress("isolation-done:process-limit-start")
        _run_process_limit_probe(root)
        _progress("process-limit-done:write-limit-start")
        _run_write_limit_probe(root)
        _progress("write-limit-done:gui-start")
        _run_gui_probe(root)
        _progress("gui-done")
    print("Windows-AppContainer-Isolation und Job-Object-Grenzen sind funktionsfähig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
