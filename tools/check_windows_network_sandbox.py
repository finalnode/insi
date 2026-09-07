"""Prüfe AppContainer-Staging und Rücksynchronisierung auf einer SMB-Freigabe."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from insi.execution_security import execution_environment, student_policy
from insi.interpreter import python_command
from insi.sandbox import sandbox_run


def run(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    readable = root / "readable"
    project = root / "project"
    readable.mkdir(exist_ok=True)
    project.mkdir(exist_ok=True)
    source = readable / "network_task.py"
    input_file = readable / "input.txt"
    result_file = project / "result.txt"
    removed_file = project / "remove-me.txt"
    input_file.write_text("network-ok", encoding="utf-8")
    removed_file.write_text("old", encoding="utf-8")
    source.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path('result.txt').write_text(Path(sys.argv[1]).read_text(encoding='utf-8'), encoding='utf-8')\n"
        "Path('remove-me.txt').unlink()\n"
        "print('sandbox-network-ok')\n",
        encoding="utf-8",
    )
    policy = student_policy(
        project,
        readable_roots=(source, input_file),
        writable_roots=(project,),
        timeout_seconds=30,
    )
    completed = sandbox_run(
        [*python_command(), str(source), str(input_file)],
        policy=policy,
        cwd=project,
        env=execution_environment(policy),
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    if completed.stdout.strip() != "sandbox-network-ok":
        raise RuntimeError(f"Unerwartete Sandboxausgabe: {completed.stdout!r}")
    if result_file.read_text(encoding="utf-8") != "network-ok":
        raise RuntimeError("Die Ausgabedatei wurde nicht ins Netzlaufwerk synchronisiert.")
    if removed_file.exists():
        raise RuntimeError("Eine erlaubte Löschung wurde nicht ins Netzlaufwerk synchronisiert.")
    print("Windows-Netzwerkstaging und Rücksynchronisierung erfolgreich.")


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    options = parser.parse_args(arguments)
    if os.name != "nt":
        raise RuntimeError("Dieser Test benötigt Windows.")
    run(options.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
