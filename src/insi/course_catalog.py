"""Geprüfter Katalog frei verfügbarer PyKIM-Kurse."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from urllib.request import Request

from . import __version__

from .course_setup import CourseSetup, setup_info
from .network import urlopen


CATALOG_URL = (
    "https://raw.githubusercontent.com/finalnode/insi/main/"
    "src/insi/course_catalog.json"
)
PACKAGED_CATALOG = Path(__file__).with_name("course_catalog.json")


@dataclass(frozen=True)
class CatalogCourse:
    id: str
    description: str
    level: str
    tags: tuple[str, ...]
    setup: CourseSetup
    setup_data: bytes


def parse_course_catalog(data: bytes) -> tuple[CatalogCourse, ...]:
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Der Kurskatalog ist kein gültiges JSON.") from error
    courses = document.get("courses") if isinstance(document, dict) else None
    if not isinstance(document, dict) or document.get("format") != 1 or not isinstance(courses, list):
        raise ValueError("Der Kurskatalog hat ein unbekanntes Format.")
    result = []
    seen = set()
    for entry in courses:
        if not isinstance(entry, dict) or set(entry) != {
            "id", "description", "level", "tags", "setup"
        }:
            raise ValueError("Der Kurskatalog enthält einen unvollständigen Eintrag.")
        identifier = entry["id"]
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in seen
            or not isinstance(entry["description"], str)
            or not isinstance(entry["level"], str)
            or not isinstance(entry["tags"], list)
            or not entry["tags"]
            or not all(
                isinstance(tag, str) and tag.strip() for tag in entry["tags"]
            )
            or len(set(entry["tags"])) != len(entry["tags"])
            or not isinstance(entry["setup"], dict)
        ):
            raise ValueError("Der Kurskatalog enthält ungültige oder doppelte Einträge.")
        setup_data = json.dumps(entry["setup"], ensure_ascii=False).encode("utf-8")
        parsed_setup = setup_info(setup_data)
        if not parsed_setup.repository:
            raise ValueError("Ein öffentlicher Kurs benötigt ein GitHub-Repository.")
        result.append(CatalogCourse(
            identifier,
            entry["description"].strip(),
            entry["level"].strip(),
            tuple(tag.strip() for tag in entry["tags"]),
            parsed_setup,
            setup_data,
        ))
        seen.add(identifier)
    return tuple(result)


def load_course_catalog(*, online: bool = True, timeout: float = 5.0) -> tuple[CatalogCourse, ...]:
    """Lade den globalen Katalog; bei Netzproblemen gilt die eingebaute Liste."""
    if online:
        request = Request(CATALOG_URL, headers={"User-Agent": f"insi/{__version__}"})
        try:
            with urlopen(request, timeout=timeout) as response:
                return parse_course_catalog(response.read())
        except (OSError, ValueError):
            pass
    return parse_course_catalog(PACKAGED_CATALOG.read_bytes())


__all__ = ["CatalogCourse", "load_course_catalog", "parse_course_catalog"]
