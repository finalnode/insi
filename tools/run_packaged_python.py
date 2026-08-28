"""Führe den internen Python-Modus einer gebündelten App synchron aus."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(runner: Path, arguments: list[str]) -> int:
    """Warte auf den GUI-Starter und reiche Ausgabe sowie Exitcode weiter."""
    completed = subprocess.run(
        [str(runner), "--pykim-python", *arguments],
        check=False,
        timeout=180,
    )
    return completed.returncode


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runner", type=Path)
    parser.add_argument("runner_arguments", nargs=argparse.REMAINDER)
    options = parser.parse_args(arguments)
    runner_arguments = options.runner_arguments
    if runner_arguments[:1] == ["--"]:
        runner_arguments = runner_arguments[1:]
    if not options.runner.is_file():
        raise FileNotFoundError(options.runner)
    return run(options.runner, runner_arguments)


if __name__ == "__main__":
    raise SystemExit(main())
