"""Baue eine frische Kurs-Runtime ausschließlich aus einem App-Wheelhouse."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

MANIFEST_NAME = "wheelhouse-manifest.json"


def normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.casefold())


def packaged_wheelhouse(application: Path) -> Path:
    """Finde genau ein in die fertige Anwendung eingebettetes Wheelhouse."""
    manifests = tuple(application.rglob(MANIFEST_NAME))
    if len(manifests) != 1:
        raise RuntimeError(
            f"Erwartet wurde genau ein {MANIFEST_NAME} in {application}, "
            f"gefunden wurden {len(manifests)}."
        )
    return manifests[0].parent


def verified_requirements(wheelhouse: Path) -> tuple[str, ...]:
    """Prüfe das Manifest und liefere offline auflösbare Hauptanforderungen."""
    manifest_path = wheelhouse / MANIFEST_NAME
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if document.get("format") != 1:
        raise RuntimeError("Das Wheelhouse-Manifest verwendet ein unbekanntes Format.")

    versions: dict[str, str] = {}
    declared_files: set[str] = set()
    for item in document.get("wheels", ()):
        filename = str(item["filename"])
        wheel = wheelhouse / filename
        if not wheel.is_file():
            raise RuntimeError(f"Das deklarierte Wheel fehlt: {filename}")
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            raise RuntimeError(f"Die Prüfsumme stimmt nicht: {filename}")
        if wheel.stat().st_size != item.get("size"):
            raise RuntimeError(f"Die Dateigröße stimmt nicht: {filename}")
        name = normalized_name(str(item["distribution"]))
        versions[name] = str(item["version"])
        declared_files.add(filename)

    actual_files = {path.name for path in wheelhouse.glob("*.whl")}
    if actual_files != declared_files:
        raise RuntimeError("Manifest und tatsächlicher Wheelbestand weichen voneinander ab.")

    requirements = []
    for raw in document.get("requirements", ()):
        requirement = str(raw).strip()
        direct_reference = re.fullmatch(
            r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*@\s*\S+", requirement
        )
        if direct_reference:
            name = direct_reference.group(1)
            version = versions.get(normalized_name(name))
            if version is None:
                raise RuntimeError(
                    f"Für {name} fehlt ein paketiertes Wheel."
                )
            requirements.append(f"{name}=={version}")
        else:
            requirements.append(requirement)
    if not requirements:
        raise RuntimeError("Das Wheelhouse-Manifest enthält keine Anforderungen.")
    return tuple(requirements)


def verify_runtime(application: Path) -> None:
    """Installiere und importiere die Kursabhängigkeiten ohne Netzwerkzugriff."""
    wheelhouse = packaged_wheelhouse(application)
    requirements = verified_requirements(wheelhouse)
    with tempfile.TemporaryDirectory(prefix="insi-offline-runtime-") as temporary:
        environment = Path(temporary) / "runtime"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                *requirements,
            ],
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.metadata, pykim, pyxel, yaml; "
                "print('Offline-Runtime bereit:', pykim.__version__, "
                "importlib.metadata.version('pyxel'))",
            ],
            check=True,
        )


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Paketiertes in:si-Wheelhouse ohne Netzwerk neu installieren"
    )
    parser.add_argument("application", type=Path, help="fertiger App-/Payload-Ordner")
    options = parser.parse_args(arguments)
    application = options.application.expanduser().resolve()
    if not application.is_dir():
        raise FileNotFoundError(f"Der Anwendungspfad fehlt: {application}")
    verify_runtime(application)
    print(f"Paketiertes Offline-Wheelhouse geprüft: {application}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
