"""Registry austauschbarer Trainer-Engines."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
import re

import yaml

from .contracts import (
    CheckReportLike,
    ExerciseLike,
    FingerprintProfile,
    StarterFile,
    Submission,
    TrainerAuthoringBackend,
    TrainerBackend,
)


TRAINER_FORMAT = "insi-trainer-v1"
TRAINER_BACKEND_ENTRYPOINT = "insi.trainer_backends"
DEFAULT_FINGERPRINT_PROFILE = FingerprintProfile("insi-python-ast-v1")
_ENGINE_NAME = re.compile(r"[a-z][a-z0-9-]*")
_BACKENDS: dict[str, TrainerBackend] = {}
_LOADED_EXTENSIONS: set[str] = set()


@dataclass(frozen=True)
class BackendExtension:
    engine: str
    package: str
    version: str
    publisher: str
    source: str
    entrypoint: object

    @property
    def identity(self) -> str:
        return f"{self.package}=={self.version}"


def backend_extensions() -> tuple[BackendExtension, ...]:
    """Inventarisiere Fachmodule ausschließlich aus Distributionsmetadaten."""
    result = []
    for candidate in entry_points(group=TRAINER_BACKEND_ENTRYPOINT):
        engine = str(candidate.name).strip().casefold()
        if not _ENGINE_NAME.fullmatch(engine):
            continue
        distribution = getattr(candidate, "dist", None)
        metadata = getattr(distribution, "metadata", {})
        package = str(metadata.get("Name", "") if metadata else "").strip()
        version = str(getattr(distribution, "version", "")).strip()
        if not package or not version:
            continue
        publisher = str(
            metadata.get("Author-email", "") or metadata.get("Author", "")
        ).strip()
        source = str(metadata.get("Home-page", "")).strip()
        if not source and hasattr(metadata, "get_all"):
            project_urls = metadata.get_all("Project-URL") or []
            source = str(project_urls[0]).split(",", 1)[-1].strip() if project_urls else ""
        result.append(
            BackendExtension(
                engine, package, version, publisher, source, candidate
            )
        )
    return tuple(sorted(result, key=lambda item: (item.engine, item.identity.casefold())))


class BackendConsentRequired(PermissionError):
    """Ein Kurs benötigt installierte, aber noch nicht freigegebene Module."""

    def __init__(self, extensions: tuple[BackendExtension, ...]):
        self.extensions = extensions
        details = ", ".join(
            f"{extension.engine} ({extension.identity})" for extension in extensions
        )
        super().__init__("Nicht freigegebenes externes Fachmodul: " + details)


def register_backend(backend: TrainerBackend, *, replace: bool = False) -> None:
    engine = str(backend.engine).strip().casefold()
    if not _ENGINE_NAME.fullmatch(engine):
        raise ValueError("Die Trainer-Engine benötigt eine sichere Kennung.")
    if engine in _BACKENDS and not replace:
        raise ValueError(f"Die Trainer-Engine {engine!r} ist bereits registriert.")
    _BACKENDS[engine] = backend


def _load_entrypoints() -> None:
    from insi.course import approved_trainer_extensions

    approved = approved_trainer_extensions()
    for extension in backend_extensions():
        if extension.identity not in approved or extension.identity in _LOADED_EXTENSIONS:
            continue
        backend = extension.entrypoint.load()
        backend = backend() if isinstance(backend, type) else backend
        register_backend(backend)
        _LOADED_EXTENSIONS.add(extension.identity)


def backend_names() -> tuple[str, ...]:
    _load_entrypoints()
    return tuple(sorted(_BACKENDS))


def get_backend(engine: str) -> TrainerBackend:
    normalized = engine.casefold()
    if normalized == "pykim" and normalized not in _BACKENDS:
        from .pykim_backend import backend as pykim_backend

        register_backend(pykim_backend)
    _load_entrypoints()
    try:
        return _BACKENDS[normalized]
    except KeyError:
        raise ValueError(
            f"Für die Trainer-Engine {engine!r} ist kein Fachmodul installiert."
        ) from None


def get_authoring_backend(engine: str) -> TrainerAuthoringBackend:
    """Liefere die optionalen Autorenfunktionen einer Trainer-Engine."""
    backend = get_backend(engine)
    if not isinstance(backend, TrainerAuthoringBackend):
        raise ValueError(
            f"Die Trainer-Engine {engine!r} bietet keine Autorenwerkzeuge an."
        )
    return backend


def fingerprint_profile(engine: str) -> FingerprintProfile:
    """Liefere die AST-Normalisierung einer Engine oder den neutralen Standard."""
    profile = getattr(get_backend(engine), "fingerprint_profile", None)
    if profile is None:
        return DEFAULT_FINGERPRINT_PROFILE
    if not isinstance(profile, FingerprintProfile):
        raise TypeError(
            f"Die Trainer-Engine {engine!r} liefert ein ungültiges Fingerprint-Profil."
        )
    return profile


def declared_engines(path: str | Path) -> frozenset[str]:
    """Lese explizite Engineangaben, ohne Fachmoduldaten zu interpretieren."""
    directory = Path(path)
    result: set[str] = set()
    for source in sorted(directory.glob("*.yml")):
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        engine = data.get("engine")
        if engine is not None:
            if not isinstance(engine, str) or not _ENGINE_NAME.fullmatch(engine):
                raise ValueError(f"{source.name}: ungültige Trainer-Engine.")
            result.add(engine)
        elif data.get("format") == 1 and isinstance(data.get("exercises"), list):
            # Das historische numerische Format ist eindeutig der eingebaute
            # PyKIM-Adapter und bleibt ohne pauschalen Registry-Import lesbar.
            result.add("pykim")
    for child in directory.iterdir() if directory.is_dir() else ():
        if child.is_dir() and _ENGINE_NAME.fullmatch(child.name):
            result.add(child.name)
    return frozenset(result)


def load_backend_exercises(path: str | Path) -> tuple[dict[str, ExerciseLike], dict[str, str]]:
    directory = Path(path)
    if not directory.is_dir():
        return {}, {}
    declared = declared_engines(directory)
    if "pykim" in declared:
        get_backend("pykim")
    available = set(backend_names())
    missing = sorted(declared - available - {"core"})
    if missing:
        blocked = tuple(
            extension
            for extension in backend_extensions()
            if extension.engine in missing
        )
        if blocked:
            raise BackendConsentRequired(blocked)
        raise ValueError(
            "Nicht installierte Trainer-Engine: " + ", ".join(missing)
        )
    exercises: dict[str, ExerciseLike] = {}
    engines: dict[str, str] = {}
    for engine in sorted(available):
        loaded = get_backend(engine).load_exercises(directory)
        duplicate = sorted(set(exercises) & set(loaded))
        if duplicate:
            raise ValueError(f"Die Aufgabenkennung {duplicate[0]!r} ist doppelt.")
        exercises.update(loaded)
        engines.update({name: engine for name in loaded})
    return exercises, engines


def starter_files(engine: str, exercise: ExerciseLike) -> tuple[StarterFile, ...]:
    return get_backend(engine).starter_files(exercise)


def evaluate(
    engine: str,
    exercise: ExerciseLike,
    submission: Submission,
) -> CheckReportLike:
    """Lasse ausschließlich die zuständige Fachmodul-Engine prüfen."""
    return get_backend(engine).evaluate(exercise, submission)


__all__ = [
    "TRAINER_BACKEND_ENTRYPOINT",
    "TRAINER_FORMAT",
    "BackendExtension",
    "BackendConsentRequired",
    "backend_extensions",
    "backend_names",
    "declared_engines",
    "evaluate",
    "fingerprint_profile",
    "get_backend",
    "get_authoring_backend",
    "load_backend_exercises",
    "register_backend",
    "starter_files",
]
