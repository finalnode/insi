"""Baue die eigenständige in:si-App unter Windows oder Linux."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def environment_python(environment: Path) -> Path:
    if platform.system() == "Windows":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="in:si für Windows/Linux bauen")
    parser.add_argument("--skip-wheelhouse", action="store_true")
    parser.add_argument("--skip-clean", action="store_true")
    options = parser.parse_args(arguments)

    system = platform.system()
    if system not in {"Windows", "Linux"}:
        raise SystemExit("Dieser Build ist nur für Windows und Linux vorgesehen.")

    project = Path(__file__).resolve().parents[1]
    platform_name = system.lower()
    if os.environ.get("PYKIM_DESKTOP_BUILD_ENV") != "1":
        environment = project / "build" / f"{platform_name}-venv"
        python = environment_python(environment)
        if not python.is_file():
            subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run(
            [
                str(python), "-m", "pip", "install",
                "git+https://github.com/finalnode/PyKIM.git@main",
            ],
            check=True,
        )
        subprocess.run(
            [str(python), "-m", "pip", "install", "-e", f"{project}[build]"],
            check=True,
        )
        child_environment = os.environ.copy()
        child_environment["PYKIM_DESKTOP_BUILD_ENV"] = "1"
        return subprocess.run(
            [str(python), str(Path(__file__).resolve()), *sys.argv[1:]],
            cwd=project,
            env=child_environment,
        ).returncode

    if not options.skip_wheelhouse:
        subprocess.run(
            [sys.executable, str(project / "tools" / "build_wheelhouse.py")],
            cwd=project,
            check=True,
        )

    work = project / "build" / platform_name
    destination = project / "dist" / platform_name
    if not options.skip_clean:
        for directory in (work, destination):
            if directory.exists():
                shutil.rmtree(directory)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(destination),
        "--workpath",
        str(work),
    ]
    if not options.skip_clean:
        command.append("--clean")
    command.append(str(project / "packaging" / "desktop" / "PyKIM.spec"))
    subprocess.run(command, cwd=project, check=True)

    application = destination / "insi"
    if not application.is_dir():
        raise RuntimeError("PyInstaller hat keinen App-Ordner erzeugt.")
    print(f"{system}-App erstellt: {application}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
