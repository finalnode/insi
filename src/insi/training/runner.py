"""Führe eine kursgebundene Prüfung aus und protokolliere den Versuch."""

import os

from .contracts import CheckReportLike, Submission
from .feedback import print_report
from .registry import evaluate_submission
from insi.progress import record_attempt


def check_exercise(
    name: str,
    source: str,
    namespace: dict[str, object] | None = None,
) -> CheckReportLike:
    report = evaluate_submission(
        name,
        Submission(kind="source", text=source, context={"namespace": namespace}),
    )
    print_report(report)
    if os.environ.get("PYKIM_PROGRESS_MODE") == "disabled":
        return report
    try:
        record_attempt(name, report, source)
    except OSError as error:
        print(f"\nHinweis: Der Lernfortschritt konnte nicht gespeichert werden: {error}")
    return report


__all__ = ["check_exercise"]
