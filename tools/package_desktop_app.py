"""Verpacke einen Windows-/Linux-Build als Release-Archiv."""

from __future__ import annotations

import argparse
import platform
import tarfile
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def project_version(project: Path) -> str:
    with (project / "pyproject.toml").open("rb") as source:
        return str(tomllib.load(source)["project"]["version"])


def architecture() -> str:
    machine = platform.machine().lower()
    return {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}.get(
        machine, machine or "unknown"
    )


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="in:si-Desktop-Build verpacken")
    parser.parse_args(arguments)
    system = platform.system()
    if system not in {"Windows", "Linux"}:
        raise SystemExit("Archive werden mit diesem Skript nur unter Windows/Linux gebaut.")

    project = Path(__file__).resolve().parents[1]
    platform_name = system.lower()
    application = project / "dist" / platform_name / "insi"
    if not application.is_dir():
        raise FileNotFoundError(
            f"{application} fehlt. Führe zuerst tools/build_desktop_app.py aus."
        )
    releases = project / "dist" / "releases" / platform_name
    releases.mkdir(parents=True, exist_ok=True)
    stem = f"insi-{project_version(project)}-{platform_name}-{architecture()}"

    if system == "Windows":
        output = releases / f"{stem}.zip"
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(application.rglob("*")):
                if path.is_file():
                    archive.write(path, Path("insi") / path.relative_to(application))
    else:
        output = releases / f"{stem}.tar.gz"
        with tarfile.open(output, "w:gz") as archive:
            archive.add(application, arcname="insi", recursive=True)

    print(f"Release-Archiv erstellt: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
