"""Fachmodulneutrale Verträge für Aufgaben, Abgaben und Rückmeldungen."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, runtime_checkable


@dataclass(frozen=True)
class Submission:
    """Eine prüfbare Abgabe – vom Quelltext bis zum ganzen Projektartefakt."""

    kind: str
    text: str = ""
    workspace: Path | None = None
    entrypoint: Path | None = None
    context: Mapping[str, object] | None = None


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    success: str
    failure: str
    hint: str = ""

    @property
    def message(self) -> str:
        return self.success if self.passed else self.failure


@dataclass(frozen=True)
class OptimizationResult:
    score: int
    tips: tuple[str, ...] = ()
    maximum: int = 100


@dataclass(frozen=True)
class CheckReport:
    title: str
    results: tuple[CheckResult, ...]
    optimization: OptimizationResult | None = None

    @property
    def passed(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def successful(self) -> bool:
        return self.passed == len(self.results)


@runtime_checkable
class CheckResultLike(Protocol):
    passed: bool
    message: str
    hint: str


@runtime_checkable
class OptimizationLike(Protocol):
    score: int
    tips: tuple[str, ...]
    maximum: int


@runtime_checkable
class CheckReportLike(Protocol):
    title: str
    results: tuple[CheckResultLike, ...]
    optimization: OptimizationLike | None

    @property
    def passed(self) -> int: ...

    @property
    def successful(self) -> bool: ...


@runtime_checkable
class ExerciseLike(Protocol):
    name: str
    title: str


@dataclass(frozen=True)
class StarterFile:
    """Von einer Trainer-Engine vorgeschlagene Datei relativ zur Aufgabe."""

    relative_path: str
    content: str


class TrainerBackend(Protocol):
    """Erweiterungspunkt eines Fachmoduls für deklarative Trainerdaten."""

    engine: str

    def load_exercises(self, trainer_directory: Path) -> dict[str, ExerciseLike]: ...

    def evaluate(
        self,
        exercise: ExerciseLike,
        submission: Submission,
    ) -> CheckReportLike: ...

    def starter_files(self, exercise: ExerciseLike) -> tuple[StarterFile, ...]: ...


__all__ = [
    "CheckReport",
    "CheckReportLike",
    "CheckResult",
    "CheckResultLike",
    "ExerciseLike",
    "OptimizationLike",
    "OptimizationResult",
    "StarterFile",
    "Submission",
    "TrainerBackend",
]
