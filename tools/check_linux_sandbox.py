"""Prüfe den echten Bubblewrap-Runner im gebündelten oder lokalen Linux-Build."""

from __future__ import annotations

import argparse
import json
import os
import platform
import tempfile
from pathlib import Path

from insi import sandbox
from insi.execution_security import execution_environment, student_policy
from insi.interpreter import python_command
from insi.sandbox import BubblewrapAdapter, sandbox_run


def _run_program(
    root: Path,
    name: str,
    source: str,
    *,
    max_processes: int = 16,
    max_memory_bytes: int = 512 * 1024 * 1024,
    max_written_bytes: int = 100 * 1024 * 1024,
    max_cpu_seconds: float = 120,
    allow_gui: bool = False,
):
    readable = root / f"{name}-readable"
    writable = root / f"{name}-writable"
    readable.mkdir()
    writable.mkdir()
    program = readable / f"{name}.py"
    program.write_text(source, encoding="utf-8")
    policy = student_policy(
        writable,
        readable_roots=(program,),
        writable_roots=(writable,),
        timeout_seconds=20,
        max_processes=max_processes,
        max_memory_bytes=max_memory_bytes,
        max_written_bytes=max_written_bytes,
        max_cpu_seconds=max_cpu_seconds,
        allow_gui=allow_gui,
    )
    completed = sandbox_run(
        [*python_command(), str(program)],
        policy=policy,
        cwd=writable,
        env=execution_environment(policy),
        capture_output=True,
        text=True,
        timeout=25,
    )
    return completed, writable


def _run_isolation_probe(root: Path) -> None:
    private = root / "private"
    private.mkdir()
    secret = private / "secret.txt"
    secret.write_text("host-secret", encoding="utf-8")
    host_network_namespace = os.readlink("/proc/self/ns/net")
    host_pid_namespace = os.readlink("/proc/self/ns/pid")
    source = (
        "import json,os,socket,subprocess,sys\n"
        "from pathlib import Path\n"
        f"secret=Path({str(secret)!r})\n"
        "result={}\n"
        "try:\n result['read']=secret.read_text()\n"
        "except Exception:\n result['read']='blocked'\n"
        "try:\n secret.write_text('changed'); result['write']='allowed'\n"
        "except Exception:\n result['write']='blocked'\n"
        "try:\n socket.create_connection(('1.1.1.1',53),.25); result['network']='allowed'\n"
        "except Exception:\n result['network']='blocked'\n"
        "result['network_namespace']=os.readlink('/proc/self/ns/net')\n"
        "result['pid_namespace']=os.readlink('/proc/self/ns/pid')\n"
        "result['visible_pids']=len([p for p in Path('/proc').iterdir() if p.name.isdigit()])\n"
        "command=[sys.executable]\n"
        "if getattr(sys,'frozen',False): command.append('--pykim-python')\n"
        "child=subprocess.run([*command,'-c','print(\"child-ok\")'],capture_output=True,text=True)\n"
        "result['child']=child.stdout.strip()\n"
        "Path('inside.txt').write_text('ok')\n"
        "print(json.dumps(result))\n"
    )
    completed, writable = _run_program(root, "isolation", source)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["read"] == "blocked"
    assert result["write"] == "blocked"
    assert result["network"] == "blocked"
    assert result["network_namespace"] != host_network_namespace
    assert result["pid_namespace"] != host_pid_namespace
    assert result["visible_pids"] <= 4
    assert result["child"] == "child-ok"
    assert secret.read_text(encoding="utf-8") == "host-secret"
    assert (writable / "inside.txt").read_text(encoding="utf-8") == "ok"


def _run_process_limit_probe(root: Path) -> None:
    source = (
        "import subprocess,sys,time\n"
        "command=[sys.executable]\n"
        "if getattr(sys,'frozen',False): command.append('--pykim-python')\n"
        "command += ['-c','import time; time.sleep(20)']\n"
        "children=[subprocess.Popen(command) for _ in range(5)]\n"
        "time.sleep(20)\n"
    )
    completed, _ = _run_program(root, "process", source, max_processes=3)
    assert completed.returncode != 0
    assert "Prozessgrenze" in completed.stderr, completed.stderr


def _run_memory_limit_probe(root: Path) -> None:
    source = "import time\ndata=bytearray(160 * 1024 * 1024)\ntime.sleep(20)\n"
    completed, _ = _run_program(
        root, "memory", source, max_memory_bytes=96 * 1024 * 1024
    )
    assert completed.returncode != 0
    assert "Arbeitsspeichergrenze" in completed.stderr, completed.stderr


def _run_cpu_limit_probe(root: Path) -> None:
    source = "value=0\nwhile True:\n value += 1\n"
    completed, _ = _run_program(root, "cpu", source, max_cpu_seconds=1)
    assert completed.returncode != 0
    assert "CPU-Zeitgrenze" in completed.stderr, completed.stderr


def _run_write_limit_probe(root: Path) -> None:
    source = (
        "from pathlib import Path\n"
        "import time\n"
        "Path('/tmp/too-large.bin').write_bytes(b'x' * 2_000_000)\n"
        "time.sleep(20)\n"
    )
    completed, _ = _run_program(
        root, "write", source, max_written_bytes=32 * 1024
    )
    assert completed.returncode != 0
    assert "Schreibgrenze" in completed.stderr, completed.stderr


def _run_gui_probe(root: Path) -> None:
    source = (
        "import pyxel\n"
        "pyxel.init(16,16,title='in:si Bubblewrap-Probelauf')\n"
        "print('gui-ok',flush=True)\n"
        "pyxel.quit()\n"
    )
    completed, _ = _run_program(root, "gui", source, allow_gui=True)
    assert completed.returncode == 0, completed.stderr
    assert "gui-ok" in completed.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Zusätzlich ein echtes Pyxel-Fenster über die Wayland-Sitzung prüfen.",
    )
    arguments = parser.parse_args()
    if platform.system() != "Linux":
        raise SystemExit("Dieser Test muss unter Linux laufen.")
    adapter = BubblewrapAdapter()
    status = adapter.status()
    if not status.available:
        raise RuntimeError(status.detail)
    if arguments.gui and not status.gui_available:
        raise RuntimeError("Für den GUI-Test fehlt eine geschützte Wayland-Sitzung.")
    sandbox._adapter_override = adapter
    with tempfile.TemporaryDirectory(prefix="insi-linux-sandbox-ci-") as temporary:
        root = Path(temporary)
        _run_isolation_probe(root)
        _run_process_limit_probe(root)
        _run_memory_limit_probe(root)
        _run_cpu_limit_probe(root)
        _run_write_limit_probe(root)
        if arguments.gui:
            _run_gui_probe(root)
    print("Linux-Bubblewrap-Isolation und dynamische Ressourcengrenzen sind funktionsfähig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
