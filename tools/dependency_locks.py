"""Wähle den reproduzierbaren Dependency-Lock eines Desktop-Ziels."""

from __future__ import annotations

import platform
from pathlib import Path


LOCK_NAMES = {
    ("windows", "amd64"): "windows-x86_64-python311.txt",
    ("windows", "x86_64"): "windows-x86_64-python311.txt",
    ("linux", "amd64"): "linux-x86_64-python311.txt",
    ("linux", "x86_64"): "linux-x86_64-python311.txt",
    ("darwin", "amd64"): "macos-x86_64-python311.txt",
    ("darwin", "x86_64"): "macos-x86_64-python311.txt",
    ("darwin", "aarch64"): "macos-arm64-python311.txt",
    ("darwin", "arm64"): "macos-arm64-python311.txt",
}


def dependency_lock(
    project: Path,
    *,
    system: str | None = None,
    machine: str | None = None,
) -> Path:
    """Liefere den eingecheckten Lock für die aktuelle Buildplattform."""

    key = (
        (system or platform.system()).casefold(),
        (machine or platform.machine()).casefold(),
    )
    try:
        name = LOCK_NAMES[key]
    except KeyError:
        raise RuntimeError(
            f"Kein Desktop-Dependency-Lock für {key[0]}/{key[1]} vorhanden."
        ) from None
    target = project / "requirements" / "locks" / name
    if not target.is_file():
        raise RuntimeError(f"Desktop-Dependency-Lock fehlt: {target}")
    return target
