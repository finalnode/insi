"""Inventarisiere die installierte Laufzeit-Lizenzkette von in:si."""

from __future__ import annotations

import argparse
from collections import deque
from importlib import metadata
from pathlib import Path
import sys

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


PROJECT = Path(__file__).resolve().parents[1]


def _license_name(package: metadata.PackageMetadata) -> str:
    expression = (package.get("License-Expression") or "").strip()
    if expression:
        return expression

    classifiers = package.get_all("Classifier") or []
    osi = [item.rsplit(" :: ", 1)[-1] for item in classifiers if "License :: OSI Approved" in item]
    if osi:
        return " / ".join(sorted(set(osi)))

    value = (package.get("License") or "").strip()
    first_line = value.splitlines()[0].strip() if value else ""
    lowered = first_line.casefold()
    known = (
        ("mit", "MIT"),
        ("apache", "Apache"),
        ("bsd", "BSD"),
        ("mozilla public license", "MPL"),
        ("mpl", "MPL"),
        ("isc", "ISC"),
        ("python software foundation", "PSF"),
        ("lgpl", "LGPL"),
    )
    for marker, label in known:
        if marker in lowered:
            return first_line if len(first_line) <= 80 else label
    return first_line if 0 < len(first_line) <= 80 else "UNKNOWN"


def _requirement_applies(requirement: Requirement, extras: frozenset[str]) -> bool:
    if requirement.marker is None:
        return True
    environment = default_environment()
    for extra in extras or frozenset({""}):
        if requirement.marker.evaluate({**environment, "extra": extra}):
            return True
    return False


def runtime_distributions() -> tuple[metadata.Distribution, ...]:
    with (PROJECT / "pyproject.toml").open("rb") as source:
        project = tomllib.load(source)["project"]

    queue: deque[tuple[Requirement, frozenset[str]]] = deque()
    for raw in project["dependencies"]:
        requirement = Requirement(raw)
        if _requirement_applies(requirement, frozenset()):
            queue.append((requirement, frozenset(requirement.extras)))

    # These are runtime inputs of platform-specific desktop builds even though
    # their installation is initiated by the build extra.
    if sys.platform.startswith("linux"):
        queue.append((Requirement("pywebview[gtk]"), frozenset({"gtk"})))
    elif sys.platform == "win32":
        queue.append((Requirement("pythonnet"), frozenset()))

    found: dict[str, metadata.Distribution] = {}
    enabled_extras: dict[str, frozenset[str]] = {}
    while queue:
        requirement, requested_extras = queue.popleft()
        name = canonicalize_name(requirement.name)
        merged_extras = enabled_extras.get(name, frozenset()) | requested_extras
        if name in found and merged_extras == enabled_extras[name]:
            continue
        try:
            installed = metadata.distribution(requirement.name)
        except metadata.PackageNotFoundError:
            raise RuntimeError(
                f"Die Laufzeitabhängigkeit {requirement.name} ist nicht installiert."
            ) from None
        found[name] = installed
        enabled_extras[name] = merged_extras
        for raw in installed.requires or ():
            child = Requirement(raw)
            if _requirement_applies(child, merged_extras):
                queue.append((child, frozenset(child.extras)))

    return tuple(sorted(found.values(), key=lambda item: canonicalize_name(item.metadata["Name"])))


def markdown_report(distributions: tuple[metadata.Distribution, ...]) -> str:
    rows = ["| Paket | Version | Lizenzangabe |", "|---|---:|---|"]
    for installed in distributions:
        package = installed.metadata
        rows.append(
            f"| {package['Name']} | {installed.version} | {_license_name(package)} |"
        )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true", help="bei unbekannten Lizenzangaben fehlschlagen"
    )
    options = parser.parse_args()
    installed = runtime_distributions()
    report = markdown_report(installed)
    print(report)
    if options.strict and "UNKNOWN" in report:
        print("Mindestens eine Laufzeitlizenz konnte nicht bestimmt werden.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
