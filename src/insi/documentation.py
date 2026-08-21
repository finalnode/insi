"""Mit der App ausgelieferte, offline lesbare Kurzdokumentation."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
import sys


DOCUMENTATION_PAGES = {
    "de": (
        "de/erste-schritte.md",
        "de/lehrkraefte-und-kurse.md",
        "de/datenschutz-und-sicherheit.md",
    ),
    "en": (
        "en/getting-started.md",
        "en/teachers-and-courses.md",
        "en/privacy-and-security.md",
    ),
}


def _documentation_candidates(relative: str) -> tuple[Path, ...]:
    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / "documentation" / "docs" / relative)

    candidates.append(Path(__file__).resolve().parents[2] / "docs" / relative)

    try:
        installed = distribution("insi")
    except PackageNotFoundError:
        installed = None
    if installed is not None:
        suffix = f"share/insi/documentation/{relative}"
        for entry in installed.files or ():
            if entry.as_posix().endswith(suffix):
                candidates.append(Path(installed.locate_file(entry)))

    return tuple(dict.fromkeys(path.resolve() for path in candidates))


def documentation_text(language: str) -> str:
    """Verbinde die bekannten Seiten einer Sprache zu einer Offline-Ansicht."""
    try:
        pages = DOCUMENTATION_PAGES[language]
    except KeyError:
        raise ValueError(f"Unbekannte Dokumentsprache: {language}") from None

    contents: list[str] = []
    for relative in pages:
        path = next(
            (
                candidate
                for candidate in _documentation_candidates(relative)
                if candidate.is_file()
            ),
            None,
        )
        if path is None:
            raise FileNotFoundError(
                f"Die mitgelieferte Dokumentationsseite {relative} fehlt."
            )
        contents.append(path.read_text(encoding="utf-8").strip())
    return "\n\n---\n\n".join(contents) + "\n"


__all__ = ["DOCUMENTATION_PAGES", "documentation_text"]
