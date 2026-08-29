"""Portable Kursordner für Schule, Zuhause und eingebundene Laufwerke."""

import json
import os
import shutil
from pathlib import Path

from .data_migrations import LOCAL_SETTINGS_FORMAT

COURSE_ENV = "PYKIM_COURSE_DIR"
CONFIG_DIR_ENV = "PYKIM_CONFIG_DIR"

SECTIONS = {
    "Aufgaben/imperativ": (
        "quadrat-5", "treppe-5", "punktlinie-8", "vier-quadrate",
        "schachbrett-8", "tonleiter-c-dur", "rhythmus-motiv",
        "farben-melodie", "interaktive-steuerung",
    ),
    "Aufgaben/oop": ("mehrere-pixel", "musik-pixel-klasse"),
}


def _config_directory() -> Path:
    configured = os.environ.get(CONFIG_DIR_ENV)
    return Path(configured).expanduser() if configured else Path.home() / ".pykim"


def configuration_file() -> Path:
    return _config_directory() / "config.json"


def _load_config() -> dict[str, object]:
    try:
        data = json.loads(configuration_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return {}


def _save_config(data: dict[str, object]) -> None:
    config_file = configuration_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    data.setdefault("format", LOCAL_SETTINGS_FORMAT)
    config_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_course_directory() -> Path | None:
    """Liefere den konfigurierten Kursordner, ohne ihn anzulegen."""
    environment = os.environ.get(COURSE_ENV)
    if environment:
        return Path(environment).expanduser().resolve()
    try:
        data = _load_config()
        value = data.get("course_directory")
        return Path(value).expanduser().resolve() if value else None
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return None


def get_course_directories() -> tuple[Path, ...]:
    """Liefere alle lokal bekannten Kursordner, inklusive alter Konfiguration."""
    environment = os.environ.get(COURSE_ENV)
    if environment:
        return (Path(environment).expanduser().resolve(),)
    data = _load_config()
    values = data.get("course_directories", [])
    candidates = list(values) if isinstance(values, list) else []
    legacy = data.get("course_directory")
    if isinstance(legacy, str) and legacy:
        candidates.insert(0, legacy)
    result: list[Path] = []
    for value in candidates:
        if not isinstance(value, str) or not value:
            continue
        path = Path(value).expanduser().resolve()
        if path not in result:
            result.append(path)
    return tuple(result)


def set_course_directory(path: str | Path) -> Path:
    """Merke lokal, wo der portable Kursordner liegt."""
    course = Path(path).expanduser().resolve()
    data = _load_config()
    data["course_directory"] = str(course)
    known = [str(item) for item in get_course_directories() if item != course]
    data["course_directories"] = [str(course), *known]
    _save_config(data)
    return course


def clear_course_selection() -> None:
    """Löse die aktuelle Auswahl, ohne bekannte Kurse zu vergessen."""
    if os.environ.get(COURSE_ENV):
        return
    data = _load_config()
    data.pop("course_directory", None)
    _save_config(data)


def course_name_confirmation_matches(value: object, expected: str) -> bool:
    """Prüfe den aktuellen Eingabewert ohne verzögerten UI-Zustand."""
    return isinstance(value, str) and value == expected


def approved_trainer_extensions() -> frozenset[str]:
    """Liefere explizit freigegebene Fachmodule als ``Paket==Version``."""
    values = _load_config().get("approved_trainer_extensions", [])
    if not isinstance(values, list):
        return frozenset()
    return frozenset(value for value in values if isinstance(value, str) and value)


def approve_trainer_extension(identity: str) -> None:
    """Merke die bewusste Zustimmung genau für diese Paketversion."""
    if "==" not in identity or not all(part.strip() for part in identity.split("==", 1)):
        raise ValueError("Die Fachmodulfreigabe benötigt Paket und Version.")
    data = _load_config()
    approved = set(approved_trainer_extensions())
    approved.add(identity)
    data["approved_trainer_extensions"] = sorted(approved)
    _save_config(data)


def forget_course_directory(path: str | Path) -> None:
    """Entferne einen Kurs aus der lokalen Auswahl, ohne Dateien anzufassen."""
    if os.environ.get(COURSE_ENV):
        raise RuntimeError("Ein per Umgebungsvariable gesetzter Kurs kann nicht entfernt werden.")
    course = Path(path).expanduser().resolve()
    data = _load_config()
    known = [
        str(item) for item in get_course_directories()
        if item != course
    ]
    data["course_directories"] = known
    if data.get("course_directory") == str(course):
        data.pop("course_directory", None)
    _save_config(data)


def validate_registered_course(path: str | Path) -> Path:
    """Validiere Kennung und Setup eines lokal registrierten Kurses."""
    course = Path(path).expanduser().resolve()
    if course not in get_course_directories():
        raise ValueError("Der Ordner ist kein lokal registrierter PyKIM-Kurs.")
    if course in {Path.home().resolve(), Path(course.anchor)}:
        raise ValueError("Dieser Ordner darf nicht gelöscht werden.")
    if not (course / ".pykim-course.json").is_file():
        raise ValueError("Im Ordner fehlt die PyKIM-Kurskennung.")
    from .course_setup import LEGACY_SETUP_FILENAME, SETUP_FILENAME

    setup_directory = course / ".pykim"
    if not any(
        (setup_directory / name).is_file()
        for name in (SETUP_FILENAME, LEGACY_SETUP_FILENAME)
    ):
        raise ValueError("Im Ordner fehlt die in:si-Setupdatei.")
    return course


def trash_course(path: str | Path) -> None:
    """Verschiebe einen eindeutig erkannten PyKIM-Kurs in den Systempapierkorb."""
    course = validate_registered_course(path)
    try:
        from send2trash import send2trash
    except ImportError as error:
        raise RuntimeError("Die Papierkorb-Unterstützung ist nicht installiert.") from error
    send2trash(str(course))
    forget_course_directory(course)


def get_ide_preference() -> dict[str, str]:
    """Liefere die lokal gewählte IDE und gegebenenfalls ihren eigenen Pfad."""
    data = _load_config()
    ide = data.get("preferred_ide", "system")
    executable = data.get("custom_ide_path", "")
    return {
        "ide": ide if isinstance(ide, str) else "system",
        "path": executable if isinstance(executable, str) else "",
    }


def set_ide_preference(ide: str, custom_path: str = "") -> dict[str, str]:
    """Speichere genau eine bevorzugte IDE für spätere Öffnen-Aktionen."""
    allowed = {"system", "thonny", "vscode", "pycharm", "custom"}
    if ide not in allowed:
        raise ValueError(f"Unbekannte IDE-Auswahl: {ide}")
    path = str(Path(custom_path).expanduser().resolve()) if custom_path.strip() else ""
    if ide == "custom" and not path:
        raise ValueError("Für eine eigene IDE muss ein Programmpfad angegeben werden.")
    if ide == "custom" and not Path(path).exists():
        raise ValueError("Der angegebene IDE-Pfad wurde nicht gefunden.")
    data = _load_config()
    data["preferred_ide"] = ide
    data["custom_ide_path"] = path
    _save_config(data)
    return {"ide": ide, "path": path}


def get_runtime_preference() -> str:
    """Liefere den lokal gewählten Schüler-Interpreter."""
    value = _load_config().get("student_python", "")
    return value if isinstance(value, str) else ""


def set_runtime_preference(executable: str | Path) -> str:
    """Speichere einen vorhandenen Python-Interpreter für Schülerprogramme."""
    path = Path(os.path.abspath(Path(executable).expanduser()))
    if not path.is_file():
        raise ValueError("Der ausgewählte Python-Interpreter wurde nicht gefunden.")
    data = _load_config()
    data["student_python"] = str(path)
    _save_config(data)
    return str(path)


def get_student_name(course: str | Path | None = None) -> str:
    """Lese den im portablen Kursordner hinterlegten Namen."""
    selected = get_course_directory() if course is None else Path(course).expanduser().resolve()
    if selected is None:
        return ""
    try:
        data = json.loads((selected / ".pykim-course.json").read_text(encoding="utf-8"))
        value = data.get("student_name", "") if isinstance(data, dict) else ""
        return value.strip() if isinstance(value, str) else ""
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return ""


def starter_source(exercise_name: str) -> str:
    """Erzeuge den kompatiblen PyKIM-Starter auch vor Registry-Aktivierung."""
    return (
        f'"""PyKIM-Aufgabe: {exercise_name}\n\n'
        "Die Aufgabenstellung und Hilfen findest du unter in:si.\n"
        '"""\n\n'
        "from pykim import *\n\n"
        f'prepare("{exercise_name}")\n\n'
        "# Schreibe deine Lösung hier.\n\n\n"
        f'run(check="{exercise_name}")\n'
    )


def exercise_file(exercise_name: str, course: Path | None = None) -> Path | None:
    course = get_course_directory() if course is None else course
    if course is None:
        return None
    filename = f"{exercise_name.replace('-', '_')}.py"
    return next(course.rglob(filename), None)


def reset_exercise_file(exercise_name: str, course: str | Path) -> Path:
    """Sichere eine Schülerdatei und setze sie auf den Starter zurück."""
    root = Path(course).expanduser().resolve()
    target = exercise_file(exercise_name, root)
    if target is None or not target.is_file():
        raise FileNotFoundError(f"Die Aufgabe {exercise_name} wurde nicht gefunden.")
    backup_directory = root / ".pykim" / "backups"
    backup_directory.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    import shutil

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    shutil.copy2(target, backup_directory / f"{target.stem}-{stamp}.py")
    target.write_text(starter_source(exercise_name), encoding="utf-8")
    return target


def create_course(path: str | Path, student_name: str = "") -> dict[str, object]:
    """Lege fehlende Kursdateien an und überschreibe keine Lösungen."""
    course = Path(path).expanduser().resolve()
    course.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    existing: list[str] = []

    for section in SECTIONS:
        section_directory = course / section
        section_directory.mkdir(parents=True, exist_ok=True)
    # Aufgaben werden erst nach dem Import einer Kurs-Setupdatei provisioniert.
    # Der alte Ordner bleibt für bereits angelegte Kopien erhalten. Neue
    # Projekte werden strukturiert unter ``Projekte`` gespeichert.
    (course / "eigene_projekte").mkdir(exist_ok=True)
    (course / "Projekte").mkdir(exist_ok=True)
    from .extensions import ensure_extension_module
    ensure_extension_module(course)
    metadata = course / ".pykim-course.json"
    if not metadata.exists():
        metadata_data = {"format": 1, "student_name": student_name, "course": "PyKIM"}
        metadata.write_text(
            json.dumps(metadata_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        created.append(metadata.name)
    elif student_name.strip():
        try:
            metadata_data = json.loads(metadata.read_text(encoding="utf-8"))
            if not isinstance(metadata_data, dict):
                metadata_data = {"format": 1, "course": "PyKIM"}
        except (OSError, ValueError, TypeError):
            metadata_data = {"format": 1, "course": "PyKIM"}
        metadata_data["student_name"] = student_name.strip()
        metadata.write_text(
            json.dumps(metadata_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    set_course_directory(course)
    return {"path": str(course), "created": created, "existing": existing}


def provision_course_exercises(path: str | Path) -> dict[str, list[str]]:
    """Lege Starterdateien ausschließlich aus dem aktivierten Kursinhalt an."""
    from .library import PARADIGMS, task_documents
    from insi.training.registry import exercise_names, exercise_starter_files

    course = Path(path).expanduser().resolve()
    trainable = set(exercise_names())
    created: list[str] = []
    existing: list[str] = []
    for paradigm in PARADIGMS:
        section_directory = course / "Aufgaben" / paradigm
        section_directory.mkdir(parents=True, exist_ok=True)
        for document in task_documents(paradigm):
            exercise = document.name
            if exercise not in trainable:
                continue
            for starter in exercise_starter_files(exercise):
                relative = Path(starter.relative_path)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("Die Trainer-Engine lieferte einen unsicheren Starterpfad.")
                target = section_directory / relative
                if target.exists():
                    existing.append(str(target.relative_to(course)))
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                legacy = next(
                    (candidate for candidate in course.rglob(target.name) if candidate != target),
                    None,
                )
                if legacy is not None and len(relative.parts) == 1:
                    shutil.copy2(legacy, target)
                else:
                    target.write_text(starter.content, encoding="utf-8")
                created.append(str(target.relative_to(course)))
    return {"created": created, "existing": existing}
