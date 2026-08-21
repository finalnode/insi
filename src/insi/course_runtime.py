"""Reproduzierbarer Runtime-Vertrag und optionale Offline-Wheels für Kurse."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - nur Python 3.10
    import tomli as tomllib

from packaging.utils import canonicalize_name, parse_wheel_filename


RUNTIME_FORMAT = 1
RUNTIME_FILENAME = "runtime.toml"
RUNTIME_PYTHON = "3.11"
MAX_RUNTIME_REQUIREMENTS = 50
MAX_OFFLINE_WHEELS = 500
MAX_OFFLINE_PACKAGE_SIZE = 1024 * 1024 * 1024


@dataclass(frozen=True)
class RuntimeTarget:
    id: str
    label: str
    pip_platform: str
    python_version: str = RUNTIME_PYTHON
    implementation: str = "cp"
    abi: str = "cp311"


RUNTIME_TARGETS = {
    target.id: target
    for target in (
        RuntimeTarget("windows-x86_64-python311", "Windows x86_64", "win_amd64"),
        RuntimeTarget("macos-arm64-python311", "macOS Apple Silicon", "macosx_11_0_arm64"),
        RuntimeTarget("macos-x86_64-python311", "macOS Intel", "macosx_10_9_x86_64"),
        RuntimeTarget("linux-x86_64-python311", "Linux x86_64", "manylinux2014_x86_64"),
    )
}


@dataclass(frozen=True)
class RuntimeManifest:
    python: str
    requirements: tuple[str, ...]
    offline_targets: tuple[str, ...] = ()
    wheel_hashes: tuple[tuple[str, str], ...] = ()

    @property
    def hashes(self) -> dict[str, str]:
        return dict(self.wheel_hashes)


_REQUIREMENT = re.compile(
    r"(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)=="
    r"(?P<version>[A-Za-z0-9][A-Za-z0-9.!+_-]*)"
)


def parse_runtime_requirements(value: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Akzeptiere ausschließlich exakt gepinnte, einfache Paketanforderungen."""
    items = value.splitlines() if isinstance(value, str) else value
    result: list[str] = []
    seen: dict[str, str] = {}
    for raw in items:
        requirement = str(raw).strip()
        if not requirement or requirement.startswith("#"):
            continue
        match = _REQUIREMENT.fullmatch(requirement)
        if match is None:
            raise ValueError(
                f"Paketanforderung {requirement!r} ist nicht exakt. "
                "Verwende beispielsweise paket==1.2.3."
            )
        normalized = canonicalize_name(match.group("name"))
        canonical = f"{match.group('name')}=={match.group('version')}"
        previous = seen.get(normalized)
        if previous is not None and previous != canonical:
            raise ValueError(f"Für {match.group('name')} wurden mehrere Versionen angegeben.")
        if previous is None:
            seen[normalized] = canonical
            result.append(canonical)
    if len(result) > MAX_RUNTIME_REQUIREMENTS:
        raise ValueError("Ein Kurs enthält zu viele zusätzliche Paketanforderungen.")
    return tuple(result)


def default_runtime_requirements() -> tuple[str, ...]:
    """Fixiere die beiden von jedem PyKIM-Kurs benötigten Fachpakete."""
    requirements = []
    for distribution in ("PyKIM", "pyxel"):
        try:
            installed = version(distribution)
        except PackageNotFoundError as error:
            raise RuntimeError(
                f"{distribution} ist nicht installiert; das Runtime-Manifest "
                "kann nicht reproduzierbar erzeugt werden."
            ) from error
        requirements.append(f"{distribution}=={installed}")
    return tuple(requirements)


def combined_runtime_requirements(additional: str | tuple[str, ...] = ()) -> tuple[str, ...]:
    defaults = default_runtime_requirements()
    extra = parse_runtime_requirements(additional)
    default_versions = {
        canonicalize_name(item.split("==", 1)[0]): item for item in defaults
    }
    for item in extra:
        name = canonicalize_name(item.split("==", 1)[0])
        if name in default_versions:
            if item != default_versions[name]:
                raise ValueError(
                    f"{item} widerspricht der von in:si bereitgestellten Version "
                    f"{default_versions[name]}."
                )
            raise ValueError(
                f"{item} wird bereits von in:si bereitgestellt und muss nicht "
                "als Zusatzpaket eingetragen werden."
            )
    return parse_runtime_requirements([*defaults, *extra])


def runtime_manifest_bytes(manifest: RuntimeManifest) -> bytes:
    requirements = ", ".join(json.dumps(item) for item in manifest.requirements)
    targets = ", ".join(json.dumps(item) for item in manifest.offline_targets)
    lines = [
        f"format = {RUNTIME_FORMAT}",
        f"python = {json.dumps(manifest.python)}",
        f"requirements = [{requirements}]",
        f"offline_targets = [{targets}]",
        "",
        "[wheel_hashes]",
    ]
    lines.extend(
        f"{json.dumps(name)} = {json.dumps(digest)}"
        for name, digest in sorted(manifest.wheel_hashes)
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse_runtime_manifest(data: bytes | str | Path) -> RuntimeManifest:
    raw = Path(data).read_bytes() if isinstance(data, Path) else (
        data.encode("utf-8") if isinstance(data, str) else data
    )
    try:
        document = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError("Das Runtime-Manifest ist kein gültiges TOML.") from error
    required = {"format", "python", "requirements", "offline_targets", "wheel_hashes"}
    if not isinstance(document, dict) or set(document) != required:
        raise ValueError("Das Runtime-Manifest ist unvollständig.")
    if document.get("format") != RUNTIME_FORMAT:
        raise ValueError("Das Runtime-Manifest verwendet ein unbekanntes Format.")
    python_version = document.get("python")
    if not isinstance(python_version, str) or not re.fullmatch(r"3\.\d+", python_version):
        raise ValueError("Das Runtime-Manifest enthält keine gültige Python-Version.")
    raw_requirements = document.get("requirements")
    raw_targets = document.get("offline_targets")
    raw_hashes = document.get("wheel_hashes")
    if not isinstance(raw_requirements, list) or not all(
        isinstance(item, str) for item in raw_requirements
    ):
        raise ValueError("requirements muss eine Liste exakter Paketversionen sein.")
    requirements = parse_runtime_requirements(raw_requirements)
    if not isinstance(raw_targets, list) or not all(isinstance(item, str) for item in raw_targets):
        raise ValueError("offline_targets muss eine Liste unterstützter Ziele sein.")
    targets = tuple(raw_targets)
    if len(targets) != len(set(targets)) or any(target not in RUNTIME_TARGETS for target in targets):
        raise ValueError("Das Runtime-Manifest enthält unbekannte oder doppelte Zielplattformen.")
    if any(
        RUNTIME_TARGETS[target].python_version != python_version
        for target in targets
    ):
        raise ValueError(
            "Python-Version und eingebettete Zielplattformen passen nicht zusammen."
        )
    if not isinstance(raw_hashes, dict):
        raise ValueError("wheel_hashes muss eine Tabelle sein.")
    hashes: list[tuple[str, str]] = []
    for name, digest in raw_hashes.items():
        path = PurePosixPath(name)
        if (
            not isinstance(name, str)
            or path.is_absolute()
            or ".." in path.parts
            or len(path.parts) != 3
            or path.parts[0] != "wheelhouse"
            or path.parts[1] not in targets
            or path.suffix.casefold() != ".whl"
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValueError(f"Ungültiger Offline-Wheeleintrag: {name!r}")
        hashes.append((name, digest))
    if len(hashes) > MAX_OFFLINE_WHEELS:
        raise ValueError("Das Runtime-Manifest enthält zu viele Offline-Wheels.")
    return RuntimeManifest(python_version, requirements, targets, tuple(sorted(hashes)))


def write_runtime_manifest(path: str | Path, manifest: RuntimeManifest) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(runtime_manifest_bytes(manifest))
    return target


def current_runtime_target() -> str | None:
    system = platform.system()
    machine = platform.machine().casefold()
    architecture = "arm64" if machine in {"arm64", "aarch64"} else "x86_64"
    prefix = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(system)
    candidate = f"{prefix}-{architecture}-python311" if prefix else ""
    return candidate if candidate in RUNTIME_TARGETS else None


def download_offline_wheels(
    requirements: tuple[str, ...],
    targets: tuple[str, ...],
    destination: str | Path,
    *,
    python: str | Path = sys.executable,
) -> dict[str, Path]:
    """Lade die vollständige Wheel-Kette für explizit gewählte Ziele."""
    requirements = parse_runtime_requirements(requirements)
    if not requirements:
        raise ValueError("Gib mindestens ein zusätzliches Paket für den Offline-Export an.")
    if not targets or len(targets) != len(set(targets)):
        raise ValueError("Wähle mindestens eine eindeutige Zielplattform aus.")
    unknown = set(targets) - set(RUNTIME_TARGETS)
    if unknown:
        raise ValueError("Unbekannte Zielplattform: " + ", ".join(sorted(unknown)))
    root = Path(destination).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    provided = default_runtime_requirements()
    provided_names = {
        canonicalize_name(requirement.split("==", 1)[0])
        for requirement in provided
    }
    constraints = root / "provided-by-insi.txt"
    constraints.write_text("\n".join(provided) + "\n", encoding="utf-8")
    result: dict[str, Path] = {}
    for target_name in targets:
        target = RUNTIME_TARGETS[target_name]
        output = root / target.id
        output.mkdir(parents=True, exist_ok=True)
        command = [
            str(Path(python).expanduser().resolve()), "-m", "pip", "download",
            "--only-binary=:all:", "--dest", str(output),
            "--platform", target.pip_platform,
            "--python-version", target.python_version.replace(".", ""),
            "--implementation", target.implementation,
            "--abi", target.abi,
            "--constraint", str(constraints),
            *requirements,
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode:
            message = completed.stderr.strip() or completed.stdout.strip() or "Paketdownload fehlgeschlagen."
            raise RuntimeError(f"Offline-Pakete für {target.label} fehlen: {message}")
        wheels = tuple(sorted(output.iterdir()))
        if not wheels or any(path.suffix.casefold() != ".whl" for path in wheels):
            raise RuntimeError(f"Für {target.label} wurden nicht ausschließlich Wheels aufgelöst.")
        for wheel in wheels:
            try:
                name, _, _, _ = parse_wheel_filename(wheel.name)
            except ValueError as error:
                raise RuntimeError(f"Ungültiger Wheel-Dateiname: {wheel.name}") from error
            if canonicalize_name(name) in provided_names:
                wheel.unlink()
                continue
            relative = f"wheelhouse/{target.id}/{wheel.name}"
            result[relative] = wheel
    if len(result) > MAX_OFFLINE_WHEELS:
        raise ValueError("Der Offline-Export enthält zu viele Wheels.")
    if sum(path.stat().st_size for path in result.values()) > MAX_OFFLINE_PACKAGE_SIZE:
        raise ValueError("Die zusätzlichen Offline-Pakete sind größer als 1 GB.")
    return result


def manifest_with_wheels(
    requirements: tuple[str, ...],
    targets: tuple[str, ...],
    wheels: dict[str, Path],
) -> RuntimeManifest:
    hashes = tuple(
        (name, hashlib.sha256(path.read_bytes()).hexdigest())
        for name, path in sorted(wheels.items())
    )
    return RuntimeManifest(RUNTIME_PYTHON, requirements, targets, hashes)


__all__ = [
    "MAX_OFFLINE_PACKAGE_SIZE",
    "MAX_OFFLINE_WHEELS",
    "RUNTIME_FILENAME",
    "RUNTIME_PYTHON",
    "RUNTIME_TARGETS",
    "RuntimeManifest",
    "RuntimeTarget",
    "combined_runtime_requirements",
    "current_runtime_target",
    "default_runtime_requirements",
    "download_offline_wheels",
    "manifest_with_wheels",
    "parse_runtime_manifest",
    "parse_runtime_requirements",
    "runtime_manifest_bytes",
    "write_runtime_manifest",
]
