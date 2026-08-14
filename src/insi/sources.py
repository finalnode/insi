"""Gebündelte Herkunfts- und Verantwortungsangaben der Lernumgebung."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .course_setup import CourseSetup
from .library import PACKAGED_CONTENT_ROOT, task_sources
from .updates import active_content_root


APPLICATION_SOURCE_URL = "https://github.com/finalnode/insi"
APPLICATION_LICENSE_URL = "https://github.com/finalnode/insi/blob/main/LICENSE"


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Eine sichtbare Quellenangabe mit optionaler Webressource."""

    label: str
    url: str = ""
    kind: str = "material"


def _web_url(value: str) -> str:
    """Akzeptiere für klickbare Ressourcen ausschließlich HTTP(S)-Adressen."""
    candidate = value.strip()
    parsed = urlparse(candidate)
    return candidate if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def _course_task_sources(setup: CourseSetup) -> tuple[SourceReference, ...]:
    root = active_content_root(PACKAGED_CONTENT_ROOT)
    directory = root / setup.assignments_path
    if not directory.is_dir():
        return ()
    references: list[SourceReference] = []
    for path in sorted(directory.rglob("*.md")):
        relative = path.relative_to(directory)
        if any(part.startswith("_") for part in relative.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for source in task_sources(content):
            references.append(
                SourceReference(source.label, _web_url(source.url), "assignment")
            )
    return tuple(references)


def source_references(setup: CourseSetup | None) -> tuple[SourceReference, ...]:
    """Sammle Software-, Kurs- und Aufgabenquellen ohne Dubletten."""
    references = [
        SourceReference("Quellcode von in:si und PyKIM", APPLICATION_SOURCE_URL, "software"),
        SourceReference("MIT-Lizenz von in:si und PyKIM", APPLICATION_LICENSE_URL, "license"),
    ]
    if setup is not None:
        if setup.repository:
            references.append(
                SourceReference(
                    f"Kursquelle: {setup.course}",
                    _web_url(setup.repository.removesuffix(".git")),
                    "course",
                )
            )
        references.extend(_course_task_sources(setup))

    unique: list[SourceReference] = []
    seen: set[tuple[str, str]] = set()
    for reference in references:
        key = (reference.label.casefold(), reference.url)
        if key not in seen:
            seen.add(key)
            unique.append(reference)
    return tuple(unique)


__all__ = ["SourceReference", "source_references"]
