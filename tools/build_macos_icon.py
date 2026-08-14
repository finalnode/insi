"""Erzeuge aus der PNG-Masterdatei ein vollständiges macOS-ICNS."""

from __future__ import annotations

import platform
from pathlib import Path

from PIL import Image


def main() -> int:
    if platform.system() != "Darwin":
        raise SystemExit("Das macOS-Icon kann nur unter macOS erzeugt werden.")
    project = Path(__file__).resolve().parents[1]
    assets = project / "packaging" / "macos" / "assets"
    source = assets / "app-icon-master.png"
    target = assets / "app-icon.icns"
    if not source.is_file():
        raise FileNotFoundError(source)
    with Image.open(source) as image:
        image.convert("RGBA").save(target, format="ICNS")
    print(f"macOS-Icon erstellt: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
