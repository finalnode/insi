#!/usr/bin/env python3
"""Erzeuge das kleine Browser-Favicon aus dem in:si-App-Icon."""

from pathlib import Path

from PIL import Image


project = Path(__file__).resolve().parents[1]
source = project / "packaging" / "macos" / "assets" / "app-icon-master.png"
target = project / "src" / "insi" / "assets" / "app-icon-64.png"
target.parent.mkdir(parents=True, exist_ok=True)
with Image.open(source) as image:
    image.thumbnail((64, 64), Image.Resampling.LANCZOS)
    image.save(target, format="PNG", optimize=True)
print(target)
