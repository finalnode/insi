"""Registry austauschbarer Trainer-Engines."""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path
import re

import yaml

from .contracts import (
    CheckReportLike,
    ExerciseLike,
    StarterFile,
    Submission,
    TrainerBackend,
)


TRAINER_FORMAT = "insi-trainer-v1"
TRAINER_BACKEND_ENTRYPOINT = "insi.trainer_backends"
_ENGINE_NAME = re.compile(r"[a-z][a-z0-9-]*")
_BACKENDS: dict[str, TrainerBackend] = {}
_ENTRYPOINTS_LOADED = False


def register_backend(backend: TrainerBackend, *, replace: bool = False) -> None:
    engine = str(backend.engine).strip().casefold()
    if not _ENGINE_NAME.fullmatch(engine):
        raise ValueError("Die Trainer-Engine benötigt eine sichere Kennung.")
    if engine in _BACKENDS and not replace:
        raise ValueError(f"Die Trainer-Engine {engine!r} ist bereits registriert.")
    _BACKENDS[engine] = backend


def _load_entrypoints() -> None:
    global _ENTRYPOINTS_LOADED
    if _ENTRYPOINTS_LOADED:
        return
    _ENTRYPOINTS_LOADED = True
    for candidate in entry_points(group=TRAINER_BACKEND_ENTRYPOINT):
        backend = candidate.load()
        backend = backend() if isinstance(backend, type) else backend
        register_backend(backend)


def backend_names() -> tuple[str, ...]:
    _load_entrypoints()
    return tuple(sorted(_BACKENDS))


def get_backend(engine: str) -> TrainerBackend:
    _load_entrypoints()
    try:
        return _BACKENDS[engine.casefold()]
    except KeyError:
        raise ValueError(
            f"Für die Trainer-Engine {engine!r} ist kein Fachmodul installiert."
        ) from None


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
    for child in directory.iterdir() if directory.is_dir() else ():
        if child.is_dir() and _ENGINE_NAME.fullmatch(child.name):
            result.add(child.name)
    return frozenset(result)


def load_backend_exercises(path: str | Path) -> tuple[dict[str, ExerciseLike], dict[str, str]]:
    directory = Path(path)
    if not directory.is_dir():
        return {}, {}
    available = set(backend_names())
    missing = sorted(declared_engines(directory) - available - {"core"})
    if missing:
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
    "backend_names",
    "declared_engines",
    "evaluate",
    "get_backend",
    "load_backend_exercises",
    "register_backend",
    "starter_files",
]
