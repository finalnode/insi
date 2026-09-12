"""Erzeuge einen pip-Constraint-Lock aus einem Desktop-Buildmanifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from packaging.utils import canonicalize_name


# Diese Werkzeuge werden unabhängig festgelegt oder von der isolierten
# Buildumgebung bereitgestellt. Sie gehören nicht zur App-Abhängigkeitskette.
EXCLUDED_PACKAGES = frozenset({"insi", "pip", "setuptools", "wheel"})


def lock_lines(manifest: dict[str, object]) -> tuple[str, ...]:
    """Formatiere die eindeutigen aufgelösten Drittanbieterpakete."""

    if manifest.get("format") != 1 or not isinstance(manifest.get("packages"), list):
        raise ValueError("Unbekanntes Desktop-Buildmanifest.")
    resolved: dict[str, str] = {}
    display_names: dict[str, str] = {}
    sources: dict[str, dict[str, str]] = {}
    for item in manifest["packages"]:
        if not isinstance(item, dict):
            raise ValueError("Ungültiger Paketeintrag im Desktop-Buildmanifest.")
        name = str(item.get("name", "")).strip()
        version = str(item.get("version", "")).strip()
        canonical = canonicalize_name(name)
        if not name or not version or canonical in EXCLUDED_PACKAGES:
            continue
        if canonical in resolved and resolved[canonical] != version:
            raise ValueError(f"Widersprüchliche Versionen für {name}.")
        resolved[canonical] = version
        display_names[canonical] = name
        source = item.get("source")
        if isinstance(source, dict):
            sources[canonical] = {key: str(value) for key, value in source.items()}

    lines = []
    for canonical in sorted(resolved):
        name = display_names[canonical]
        source = sources.get(canonical, {})
        url = source.get("url", "")
        commit = source.get("commit", "")
        if source.get("vcs") == "git" and url.startswith(("https://", "http://")) and commit:
            lines.append(f"{name} @ git+{url}@{commit}")
        else:
            lines.append(f"{name}=={resolved[canonical]}")
    if not lines:
        raise ValueError("Das Desktop-Buildmanifest enthält keine sperrbaren Pakete.")
    return tuple(lines)


def write_lock(manifest_path: Path, target: Path, reference: str) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    header = [
        "# Aus dem plattformspezifischen Desktop-Buildmanifest erzeugt.",
        f"# Referenz: {reference}",
        "# pip, setuptools, wheel und das lokale Editable-Projekt sind bewusst ausgenommen.",
        "",
    ]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join((*header, *lock_lines(manifest), "")), encoding="utf-8")
    return target


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--reference", required=True)
    options = parser.parse_args(arguments)
    result = write_lock(options.manifest, options.target, options.reference)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
