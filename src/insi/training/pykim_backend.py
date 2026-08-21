"""PyKIM-Adapter für die fachmodulneutrale Trainer-Registry."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from pykim.trainer.definitions import load_exercises

from .backends import TRAINER_FORMAT
from .contracts import CheckReportLike, ExerciseLike, StarterFile, Submission


def normalize_pykim_document(data: object, *, source_name: str = "Trainer") -> dict:
    """Überführe alte und neue PyKIM-Dokumente in das Fachmodulformat 1."""
    if not isinstance(data, dict):
        raise ValueError(f"{source_name}: unbekanntes Trainingsformat.")
    if data.get("format") not in {1, TRAINER_FORMAT}:
        raise ValueError(f"{source_name}: unbekanntes Trainingsformat.")
    if data.get("engine") not in {None, "pykim"}:
        raise ValueError(f"{source_name}: ist keine PyKIM-Trainerdefinition.")
    normalized = dict(data)
    normalized["format"] = 1
    normalized.pop("engine", None)
    return normalized


def explicit_pykim_source(source: str) -> str:
    """Kennzeichne erzeugte Trainerdateien mit dem neuen in:si-Vertrag."""
    data = normalize_pykim_document(yaml.safe_load(source))
    data["format"] = TRAINER_FORMAT
    data = {"format": data.pop("format"), "engine": "pykim", **data}
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


class PyKIMTrainerBackend:
    engine = "pykim"

    @staticmethod
    def _documents(directory: Path) -> tuple[Path, ...]:
        result = []
        for source in sorted(directory.glob("*.yml")):
            data = yaml.safe_load(source.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(f"{source.name}: unbekanntes Trainingsformat.")
            engine = data.get("engine")
            if engine in {None, "pykim"}:
                result.append(source)
        module_directory = directory / "pykim"
        if module_directory.is_dir():
            result.extend(sorted(module_directory.glob("*.yml")))
        return tuple(result)

    def load_exercises(self, trainer_directory: Path) -> dict[str, ExerciseLike]:
        documents = self._documents(trainer_directory)
        if not documents:
            return {}
        with TemporaryDirectory(prefix="insi-trainer-pykim-") as temporary:
            target = Path(temporary)
            for index, source in enumerate(documents):
                data = yaml.safe_load(source.read_text(encoding="utf-8"))
                normalized = normalize_pykim_document(data, source_name=source.name)
                (target / f"{index:04d}-{source.name}").write_text(
                    yaml.safe_dump(normalized, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
            return load_exercises(target)

    @staticmethod
    def evaluate(
        exercise: ExerciseLike,
        submission: Submission,
    ) -> CheckReportLike:
        if submission.kind != "source":
            raise ValueError("PyKIM kann nur Python-Quelltext prüfen.")
        context = submission.context or {}
        namespace = context.get("namespace")
        if namespace is not None and not isinstance(namespace, dict):
            raise ValueError("Der PyKIM-Namensraum muss ein Dictionary sein.")
        checker = getattr(exercise, "checker", None)
        if not callable(checker):
            raise ValueError("Die PyKIM-Aufgabe besitzt keinen gültigen Prüfer.")
        return checker(submission.text, namespace)

    @staticmethod
    def starter_files(exercise: ExerciseLike) -> tuple[StarterFile, ...]:
        filename = f"{exercise.name.replace('-', '_')}.py"
        content = (
            f'"""PyKIM-Aufgabe: {exercise.name}\n\n'
            "Die Aufgabenstellung und Hilfen findest du unter in:si.\n"
            '"""\n\n'
            "from pykim import *\n\n"
            f'prepare("{exercise.name}")\n\n'
            "# Schreibe deine Lösung hier.\n\n\n"
            f'run(check="{exercise.name}")\n'
        )
        return (StarterFile(filename, content),)


backend = PyKIMTrainerBackend()

__all__ = [
    "PyKIMTrainerBackend",
    "backend",
    "explicit_pykim_source",
    "normalize_pykim_document",
]
