"""Baue ein deterministisches, hashgeprüftes PyKIM-Inhaltspaket."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PyKIM-Inhaltspaket bauen")
    parser.add_argument("--version", default="2026.08.1")
    options = parser.parse_args(arguments)
    project = Path(__file__).resolve().parents[1]
    guide = project / "src" / "insi"
    paths = sorted(
        [
            path
            for folder in (guide / "Skripte", guide / "Aufgaben")
            for path in folder.rglob("*.md")
        ]
        + list((guide / "Trainer").rglob("*.yml"))
    )
    files = {
        path.relative_to(guide).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    output_directory = project / "dist" / "content"
    output_directory.mkdir(parents=True, exist_ok=True)
    archive = output_directory / f"pykim-content-{options.version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in paths:
            info = zipfile.ZipInfo(path.relative_to(guide).as_posix())
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, path.read_bytes())
    manifest = {
        "format": 1,
        "content_version": options.version,
        "minimum_app_version": "0.3.0",
        "package_url": (
            "https://github.com/finalnode/insi/releases/download/"
            f"content-{options.version}/{archive.name}"
        ),
        "package_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "files": files,
    }
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (project / "content-manifest.json").write_text(rendered, encoding="utf-8")
    (guide / "content-manifest.json").write_text(rendered, encoding="utf-8")
    print(f"Inhaltspaket: {archive}")
    print(f"Manifest: {project / 'content-manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
