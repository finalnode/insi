#!/usr/bin/env python3
"""Erzeuge ein offline nutzbares ZIP aus Kursrepository und Setupdatei."""

from __future__ import annotations

import argparse
from pathlib import Path

from insi.course_archive import build_course_archive
from insi.course_setup import setup_info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="lokaler Kursrepository-Ordner")
    parser.add_argument("setup", type=Path, help="passende .insi-setup-Datei")
    parser.add_argument("--output", type=Path, help="Ziel-ZIP")
    options = parser.parse_args()

    setup = setup_info(options.setup)
    output = options.output or Path(f"{Path(setup.name).stem}.zip")
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(build_course_archive(options.source, options.setup))
    print(output)


if __name__ == "__main__":
    main()
