"""Schlanke Kurskonfiguration ohne Schlüssel oder Verschlüsselungsdaten."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


SETUP_FORMAT = "pykim-course-setup-v1"
SETUP_FILENAME = "course.pykim-setup"


@dataclass(frozen=True)
class CourseSetup:
    name: str
    teacher: str
    school: str
    course: str
    repository: str
    branch: str
    scripts_path: str
    assignments_path: str
    trainers_path: str

    @property
    def certificate_name(self) -> str:
        """Kompatibilität für den vorhandenen Inhalts-Synchronisierer."""
        return self.name

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "pykim-kurs"


def _safe_path(value: object, label: str) -> str:
    path = str(value).strip().strip("/")
    if not path or path.startswith(".") or ".." in path.split("/"):
        raise ValueError(f"Der Konfigurationspfad {label} ist unsicher.")
    return path


def setup_info(data: bytes | str | Path) -> CourseSetup:
    raw = Path(data).read_bytes() if isinstance(data, Path) else (
        data.encode("utf-8") if isinstance(data, str) else data
    )
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Die Datei ist keine gültige PyKIM-Setupdatei.") from error
    required = {
        "format", "name", "teacher", "school", "course", "repository", "branch",
        "scripts_path", "assignments_path", "trainers_path",
    }
    if not isinstance(document, dict) or set(document) != required:
        raise ValueError("Die PyKIM-Setupdatei ist unvollständig.")
    if document.get("format") != SETUP_FORMAT:
        raise ValueError("Die Datei ist keine unterstützte PyKIM-Setupdatei.")
    nonempty = required - {"repository"}
    if (
        not all(isinstance(document.get(key), str) for key in required)
        or not all(document[key].strip() for key in nonempty)
    ):
        raise ValueError("Die PyKIM-Setupdatei enthält leere Angaben.")
    name = document["name"].strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.pykim-setup", name):
        raise ValueError("Der Name der Setupdatei ist ungültig.")
    repository = document["repository"].strip()
    if repository and not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", repository):
        raise ValueError("Das Kursrepository muss eine öffentliche GitHub-HTTPS-Adresse sein.")
    branch = document["branch"].strip()
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch.split("/"):
        raise ValueError("Der Inhaltsbranch ist ungültig.")
    return CourseSetup(
        name=name,
        teacher=document["teacher"].strip(),
        school=document["school"].strip(),
        course=document["course"].strip(),
        repository=repository,
        branch=branch,
        scripts_path=_safe_path(document["scripts_path"], "scripts_path"),
        assignments_path=_safe_path(document["assignments_path"], "assignments_path"),
        trainers_path=_safe_path(document["trainers_path"], "trainers_path"),
    )


def course_setup_path(course: str | Path) -> Path:
    return Path(course).expanduser().resolve() / ".pykim" / SETUP_FILENAME


def course_setup_info(course: str | Path) -> CourseSetup | None:
    path = course_setup_path(course)
    return setup_info(path) if path.is_file() else None


def _write_course_setup(data: bytes, course: str | Path) -> None:
    target = course_setup_path(course)
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", dir=target.parent, delete=False) as temporary:
        temporary.write(data)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)


def _managed_course_directory(
    info: CourseSetup,
    base_directory: str | Path | None,
    *,
    collision: str,
) -> Path:
    if collision not in {"reuse", "copy"}:
        raise ValueError("Unbekannte Behandlung eines vorhandenen Kurses.")
    base = (
        Path(base_directory).expanduser().resolve()
        if base_directory is not None
        else Path.home() / "PyKIM-Kurse"
    )
    candidate = (base / Path(info.name).stem).resolve()
    if collision == "reuse" or not candidate.exists():
        return candidate
    index = 2
    while True:
        alternative = candidate.with_name(f"{candidate.name}-{index}")
        if not alternative.exists():
            return alternative
        index += 1


def course_import_target(
    info: CourseSetup,
    base_directory: str | Path | None = None,
) -> Path:
    """Liefere den regulären Zielordner, um Namenskollisionen vorab anzuzeigen."""
    return _managed_course_directory(info, base_directory, collision="reuse")


def install_course_setup(data: bytes, course: str | Path) -> CourseSetup:
    """Lese, synchronisiere und installiere eine Kurs-Setupdatei."""
    info = setup_info(data)
    if not info.repository:
        raise ValueError(
            "Diese lokale Setupdatei gehört in ein Kurs-ZIP und besitzt keine "
            "Onlinequelle. Importiere stattdessen das exportierte ZIP."
        )
    from .updates import sync_certificate_content

    target = sync_certificate_content(info)
    _write_course_setup(data, course)
    from .course_archive import write_course_content_source

    write_course_content_source(course, "repository")
    from .course import provision_course_exercises
    from .registries import activate_content_registries

    activate_content_registries(
        target,
        trainers_path=info.trainers_path,
        assignments_path=info.assignments_path,
    )
    provision_course_exercises(course)
    return info


def install_new_course_setup(
    data: bytes,
    *,
    base_directory: str | Path | None = None,
    collision: str = "reuse",
) -> tuple[CourseSetup, Path]:
    """Lege aus einer hochgeladenen Setupdatei einen lokal bekannten Kurs an."""
    info = setup_info(data)
    if not info.repository:
        raise ValueError(
            "Diese lokale Setupdatei gehört in ein Kurs-ZIP und besitzt keine "
            "Onlinequelle. Importiere stattdessen das exportierte ZIP."
        )
    course = _managed_course_directory(
        info, base_directory, collision=collision
    )

    # Erst vollständig synchronisieren; ein ungültiger oder nicht erreichbarer
    # Kurs wird dadurch nicht als halbfertiger Eintrag registriert.
    from .updates import sync_certificate_content

    target = sync_certificate_content(info)
    _write_course_setup(data, course)
    from .course_archive import write_course_content_source

    write_course_content_source(course, "repository")

    from .course import create_course, provision_course_exercises

    create_course(course)
    from .registries import activate_content_registries

    activate_content_registries(
        target,
        trainers_path=info.trainers_path,
        assignments_path=info.assignments_path,
    )
    provision_course_exercises(course)
    return info, course


def install_new_course_archive(
    data: bytes,
    *,
    base_directory: str | Path | None = None,
    collision: str = "copy",
) -> tuple[CourseSetup, Path]:
    """Installiere einen geprüften ZIP-Snapshot vollständig ohne Netzwerk."""
    from .course_archive import (
        install_course_archive_content,
        parse_course_archive,
        write_course_content_source,
    )

    bundle = parse_course_archive(data)
    course = _managed_course_directory(
        bundle.setup, base_directory, collision=collision
    )
    target = install_course_archive_content(bundle)
    _write_course_setup(bundle.setup_data, course)
    write_course_content_source(
        course, "archive", content_version=bundle.revision
    )

    from .course import create_course, provision_course_exercises

    create_course(course)
    from .registries import activate_content_registries

    activate_content_registries(
        target,
        trainers_path=bundle.setup.trainers_path,
        assignments_path=bundle.setup.assignments_path,
    )
    provision_course_exercises(course)
    return bundle.setup, course


def install_course_archive(data: bytes, course: str | Path) -> CourseSetup:
    """Aktiviere einen ZIP-Snapshot in einem bestehenden Student Workspace."""
    from .course_archive import (
        install_course_archive_content,
        parse_course_archive,
        write_course_content_source,
    )

    bundle = parse_course_archive(data)
    target = install_course_archive_content(bundle)
    _write_course_setup(bundle.setup_data, course)
    write_course_content_source(
        course, "archive", content_version=bundle.revision
    )
    from .course import provision_course_exercises

    from .registries import activate_content_registries

    activate_content_registries(
        target,
        trainers_path=bundle.setup.trainers_path,
        assignments_path=bundle.setup.assignments_path,
    )
    provision_course_exercises(course)
    return bundle.setup


def sync_installed_course_content(
    course: str | Path | None = None,
    *,
    timeout: float = 20.0,
):
    """Gleiche den eingerichteten Kurs beim App-Start mit seinem Repository ab."""
    from .course import get_course_directory, provision_course_exercises
    from .library import PACKAGED_CONTENT_ROOT
    from .updates import TrainerVerification, active_content_root, sync_certificate_content

    selected = get_course_directory() if course is None else Path(course).expanduser().resolve()
    if selected is None:
        return TrainerVerification(False, False, "Kein Kursordner eingerichtet.")
    info = course_setup_info(selected)
    if info is None:
        return TrainerVerification(False, False, "Keine Kurs-Setupdatei installiert.")

    from .course_archive import course_content_source

    source = course_content_source(selected)
    if source.get("type") == "archive":
        activate_installed_course_content(selected)
        return TrainerVerification(
            False,
            False,
            "Lokales Kursarchiv ist aktiv; es ist kein Online-Abgleich nötig.",
        )

    previous = active_content_root(PACKAGED_CONTENT_ROOT)
    target = sync_certificate_content(info, timeout=timeout)

    activate_installed_course_content(selected)
    updated = previous.resolve() != target.resolve()
    return TrainerVerification(
        True,
        updated,
        "Kursinhalte wurden aktualisiert." if updated else "Kursinhalte sind aktuell.",
    )


def activate_installed_course_content(course: str | Path) -> None:
    """Aktiviere den bereits lokal geprüften Kursstand ohne Netzwerkzugriff."""
    from .course import provision_course_exercises

    selected = Path(course).expanduser().resolve()
    from .library import PACKAGED_CONTENT_ROOT
    from .registries import activate_content_registries
    from .updates import active_content_root

    info = course_setup_info(selected)
    root = active_content_root(PACKAGED_CONTENT_ROOT)
    activate_content_registries(
        root,
        trainers_path=getattr(info, "trainers_path", "Trainer"),
        assignments_path=getattr(info, "assignments_path", "Aufgaben"),
    )
    provision_course_exercises(selected)


def verify_installed_course_setup(course: str | Path, *, allow_offline: bool = False):
    path = course_setup_path(course)
    if not path.is_file():
        raise FileNotFoundError("Importiere zuerst die Setupdatei deiner Lehrkraft.")
    data = path.read_bytes()
    info = setup_info(data)
    # Die Setupdatei ist momentan reine Konfiguration. Eine kryptografische
    # Vertrauensprüfung wird später als getrennte Schicht ergänzt.
    from .updates import TrainerVerification

    return info, TrainerVerification(False, False)


def generate_course_setup(
    output_directory: str | Path,
    *,
    teacher: str,
    school: str,
    course: str,
    repository: str = "",
    branch: str = "main",
    scripts_path: str = "Skripte",
    assignments_path: str = "Aufgaben",
    trainers_path: str = "Trainer",
) -> Path:
    """Erzeuge eine schlanke Setupdatei ohne Schlüssel oder Hashfreigabe."""
    name = f"{_slug(course)}.pykim-setup"
    document = {
        "format": SETUP_FORMAT,
        "name": name,
        "teacher": teacher,
        "school": school,
        "course": course,
        "repository": repository,
        "branch": branch,
        "scripts_path": scripts_path,
        "assignments_path": assignments_path,
        "trainers_path": trainers_path,
    }
    data = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    setup_info(data)
    root = Path(output_directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    setup_path = root / name
    setup_path.write_bytes(data)
    return setup_path
