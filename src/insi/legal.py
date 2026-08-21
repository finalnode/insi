"""Offline verfügbare Lizenz- und Rechtstexte der Anwendung."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
import sys


LEGAL_DOCUMENTS = {
    "agpl": "LICENSE",
    "scope": "LICENSING.md",
    "third-party": "THIRD_PARTY_NOTICES.md",
}


def _legal_document_candidates(filename: str) -> tuple[Path, ...]:
    """Liefere mögliche Orte in Quellbaum, Wheel und PyInstaller-Bundle."""
    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / "licenses" / filename)

    candidates.append(Path(__file__).resolve().parents[2] / filename)

    try:
        installed = distribution("insi")
    except PackageNotFoundError:
        installed = None
    if installed is not None:
        for entry in installed.files or ():
            if entry.name == filename and "licenses" in entry.parts:
                candidates.append(Path(installed.locate_file(entry)))

    return tuple(dict.fromkeys(path.resolve() for path in candidates))


def legal_document_path(document: str) -> Path:
    """Finde einen bekannten Rechtstext, ohne beliebige Pfade zu akzeptieren."""
    try:
        filename = LEGAL_DOCUMENTS[document]
    except KeyError:
        raise ValueError(f"Unbekannter Rechtstext: {document}") from None
    for candidate in _legal_document_candidates(filename):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Der mitgelieferte Rechtstext {filename} wurde nicht gefunden.")


def legal_document_text(document: str) -> str:
    """Lese einen mit der Anwendung ausgelieferten Rechtstext als UTF-8."""
    return legal_document_path(document).read_text(encoding="utf-8")


__all__ = ["LEGAL_DOCUMENTS", "legal_document_path", "legal_document_text"]
