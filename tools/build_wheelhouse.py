"""Erzeuge die Offline-Pakete für die aktuelle Plattform und Python-Version."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PyKIM-Offline-Wheelhouse bauen")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/wheelhouse"),
        help="Zielordner (Standard: dist/wheelhouse)",
    )
    options = parser.parse_args(arguments)
    project = Path(__file__).resolve().parents[1]
    output = options.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--wheel-dir",
            str(output),
            "git+https://github.com/finalnode/PyKIM.git@main",
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--wheel-dir",
            str(output),
            "--find-links",
            str(output),
            str(project),
        ],
        check=True,
    )
    print(f"Offline-Wheelhouse erstellt: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
