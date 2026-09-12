"""Erzeuge die Offline-Pakete für die aktuelle Plattform und Python-Version."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

from packaging.utils import parse_wheel_filename


MANIFEST_NAME = "wheelhouse-manifest.json"


def reset_wheelhouse(output: Path) -> None:
    """Entferne alte Buildartefakte, ohne andere Dateien im Ziel anzufassen."""
    output.mkdir(parents=True, exist_ok=True)
    for wheel in output.glob("*.whl"):
        wheel.unlink()
    (output / MANIFEST_NAME).unlink(missing_ok=True)


def write_manifest(output: Path, pykim_requirements: Path) -> Path:
    """Dokumentiere den exakt erzeugten, plattformspezifischen Paketbestand."""
    requirements = [
        line.strip()
        for line in pykim_requirements.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    wheels = []
    for wheel in sorted(output.glob("*.whl")):
        distribution, version, _, _ = parse_wheel_filename(wheel.name)
        wheels.append(
            {
                "distribution": str(distribution),
                "filename": wheel.name,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                "size": wheel.stat().st_size,
                "version": str(version),
            }
        )
    manifest = {
        "format": 1,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "requirements": requirements,
        "wheels": wheels,
    }
    target = output / MANIFEST_NAME
    target.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="in:si-Offline-Wheelhouse bauen")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/wheelhouse"),
        help="Zielordner (Standard: dist/wheelhouse)",
    )
    options = parser.parse_args(arguments)
    project = Path(__file__).resolve().parents[1]
    pykim_requirements = project / "requirements" / "pykim-0.6.0.txt"
    output = options.output.expanduser().resolve()
    reset_wheelhouse(output)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--wheel-dir",
            str(output),
            "--requirement",
            str(pykim_requirements),
        ],
        check=True,
    )
    manifest = write_manifest(output, pykim_requirements)
    print(f"Offline-Wheelhouse erstellt: {output}")
    print(f"Paketmanifest erstellt: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
