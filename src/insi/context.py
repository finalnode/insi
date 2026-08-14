"""Explizite Abhängigkeiten und flüchtiger Zustand der NiceGUI-Anwendung."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CourseSyncState:
    """Status des laufenden oder letzten Kursabgleichs."""

    result: Any = None
    error: str = ""
    pending: bool = False

    def update(self, **values: Any) -> None:
        """Biete vorerst die bisherige ``dict.update``-Schnittstelle an."""
        for name, value in values.items():
            if not hasattr(self, name):
                raise KeyError(name)
            setattr(self, name, value)

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        setattr(self, name, value)


@dataclass(slots=True)
class CourseSelectionState:
    """Browserübergreifender Zustand der initialen Kursauswahl."""

    confirmed: bool = False

    def update(self, **values: Any) -> None:
        for name, value in values.items():
            if not hasattr(self, name):
                raise KeyError(name)
            setattr(self, name, value)

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        setattr(self, name, value)


@dataclass(slots=True)
class AppContext:
    """Alle Framework-Abhängigkeiten und der geteilte Laufzeitzustand."""

    ui: Any
    app: Any
    run: Any
    desktop: bool
    course_sync: CourseSyncState = field(default_factory=CourseSyncState)
    course_selection: CourseSelectionState = field(
        default_factory=CourseSelectionState
    )


__all__ = ["AppContext", "CourseSelectionState", "CourseSyncState"]
