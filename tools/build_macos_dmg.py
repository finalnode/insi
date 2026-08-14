"""Erzeuge ein komprimiertes macOS-DMG für in:si."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def project_version(project: Path) -> str:
    with (project / "pyproject.toml").open("rb") as source:
        return str(tomllib.load(source)["project"]["version"])


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="in:si als macOS-DMG bauen")
    parser.add_argument(
        "--rebuild-app",
        action="store_true",
        help="vorher den vollständigen .app-Bundle neu bauen",
    )
    options = parser.parse_args(arguments)
    if platform.system() != "Darwin":
        raise SystemExit("Das DMG muss unter macOS gebaut werden.")

    project = Path(__file__).resolve().parents[1]
    application = project / "dist" / "macos" / "insi.app"
    if options.rebuild_app:
        subprocess.run(
            [sys.executable, str(project / "tools" / "build_macos_app.py")],
            cwd=project,
            check=True,
        )
    if not application.is_dir():
        raise FileNotFoundError(
            "insi.app fehlt. Führe zuerst tools/build_macos_app.py aus."
        )

    architecture = platform.machine() or "unknown"
    output = (
        project
        / "dist"
        / "macos"
        / f"insi-{project_version(project)}-macos-{architecture}.dmg"
    )
    with tempfile.TemporaryDirectory(prefix="pykim-dmg-") as temporary:
        staging = Path(temporary) / "insi"
        staging.mkdir()
        shutil.copytree(
            application,
            staging / application.name,
            symlinks=True,
        )
        os.symlink("/Applications", staging / "Applications")
        subprocess.run(
            [
                "hdiutil",
                "create",
                "-volname",
                "in:si",
                "-srcfolder",
                str(staging),
                "-ov",
                "-format",
                "UDZO",
                str(output),
            ],
            cwd=project,
            check=True,
        )
    print(f"macOS-DMG erstellt: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
