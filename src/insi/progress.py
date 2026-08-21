"""Synchronisierbarer Lernfortschritt im jeweiligen Kursordner."""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from .training.contracts import CheckReportLike

from .course import get_course_directory


SANDBOX_PROGRESS_ENV = "INSI_PROGRESS_FILE"
MAX_SANDBOX_ATTEMPTS_PER_RUN = 100
MAX_SANDBOX_ATTEMPT_BYTES = 1024 * 1024


def _empty_progress() -> dict[str, object]:
    return {"format": 1, "attempts": [], "journal": {}, "answers": {}, "hints": {}}


def progress_file(course: Path | None = None) -> Path | None:
    sandbox_target = os.environ.get(SANDBOX_PROGRESS_ENV)
    if sandbox_target:
        return Path(sandbox_target).expanduser().resolve()
    course = get_course_directory() if course is None else course
    return None if course is None else course / ".pykim" / "progress.json"


def prepare_sandbox_progress(target: str | Path, course: str | Path) -> int:
    """Kopiere den Lernstand in einen privaten Laufbereich und liefere die Versuchszahl."""

    destination = Path(target).expanduser().resolve()
    data = load_progress(Path(course).expanduser().resolve())
    attempts = data.get("attempts", [])
    baseline = len(attempts) if isinstance(attempts, list) else 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return baseline


def merge_sandbox_progress(
    source: str | Path,
    course: str | Path,
    *,
    baseline_attempts: int,
) -> int:
    """Übernimm ausschließlich neue Trainer-Versuche aus einem Sandboxlauf."""

    path = Path(source).expanduser().resolve()
    try:
        sandbox_data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return 0
    sandbox_attempts = sandbox_data.get("attempts", []) if isinstance(sandbox_data, dict) else []
    if not isinstance(sandbox_attempts, list):
        return 0
    additions = sandbox_attempts[max(0, baseline_attempts):][
        :MAX_SANDBOX_ATTEMPTS_PER_RUN
    ]
    if not additions:
        return 0
    course_path = Path(course).expanduser().resolve()
    current = load_progress(course_path)
    attempts = current.setdefault("attempts", [])
    if not isinstance(attempts, list):
        attempts = current["attempts"] = []
    valid_additions = []
    for item in additions:
        if not isinstance(item, dict):
            continue
        exercise = item.get("exercise")
        passed = item.get("passed")
        tests = item.get("tests")
        if (
            not isinstance(exercise, str)
            or not exercise.strip()
            or len(exercise) > 200
            or not isinstance(passed, bool)
            or not isinstance(tests, list)
            or len(tests) > 500
        ):
            continue
        try:
            encoded = json.dumps(item, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError):
            continue
        if len(encoded) > MAX_SANDBOX_ATTEMPT_BYTES:
            continue
        valid_additions.append(item)
    attempts.extend(valid_additions)
    _save(current, course_path)
    return len(valid_additions)


def load_progress(course: Path | None = None) -> dict[str, object]:
    target = progress_file(course)
    if target is None or not target.exists():
        return _empty_progress()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else _empty_progress()
    except (OSError, ValueError):
        return _empty_progress()


def _save(data: dict[str, object], course: Path | None = None) -> None:
    target = progress_file(course)
    if target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    # Schreiben und Ersetzen verhindert halbe JSON-Dateien bei Abbruch oder Sync.
    with NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, delete=False
    ) as temporary:
        json.dump(data, temporary, ensure_ascii=False, indent=2)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)


def record_attempt(
    exercise: str,
    report: CheckReportLike,
    source: str = "",
    *,
    course: Path | None = None,
) -> bool:
    """Speichere einen Trainerlauf; ohne Kurskonfiguration geschieht nichts."""
    target = progress_file(course)
    if target is None:
        return False
    data = load_progress(course)
    attempts = data.setdefault("attempts", [])
    if not isinstance(attempts, list):
        attempts = data["attempts"] = []
    optimization = report.optimization
    attempts.append(
        {
            "exercise": exercise,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": report.passed,
            "total": len(report.results),
            "successful": report.successful,
            "optimization": None if optimization is None else {
                "score": optimization.score,
                "maximum": optimization.maximum,
            },
            "tests": [
                {
                    "index": index,
                    "passed": result.passed,
                    "message": result.message,
                    "hint": result.hint if not result.passed else "",
                }
                for index, result in enumerate(report.results, start=1)
            ],
            "source": source,
        }
    )
    _save(data, course)
    return True


def save_journal_entry(
    exercise: str,
    text: str,
    *,
    course: Path | None = None,
) -> None:
    data = load_progress(course)
    journal = data.setdefault("journal", {})
    if not isinstance(journal, dict):
        journal = data["journal"] = {}
    journal[exercise] = {
        "text": text,
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    _save(data, course)


def save_task_answer(
    task: str,
    text: str,
    *,
    course: Path | None = None,
) -> None:
    """Speichere eine freie Antwort auf eine Aufgabe ohne Trainer."""
    data = load_progress(course)
    answers = data.setdefault("answers", {})
    if not isinstance(answers, dict):
        answers = data["answers"] = {}
    answers[task] = {
        "text": text,
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    _save(data, course)


def revealed_hint_count(task: str, *, course: Path | None = None) -> int:
    data = load_progress(course)
    hints = data.get("hints", {})
    value = hints.get(task, 0) if isinstance(hints, dict) else 0
    return max(0, value) if isinstance(value, int) and not isinstance(value, bool) else 0


def save_revealed_hint_count(
    task: str,
    count: int,
    *,
    course: Path | None = None,
) -> None:
    """Merke, wie viele gestufte Hinweise bereits geöffnet wurden."""
    data = load_progress(course)
    hints = data.setdefault("hints", {})
    if not isinstance(hints, dict):
        hints = data["hints"] = {}
    hints[task] = max(0, int(count))
    _save(data, course)


def remove_packaged_example_attempts(course: Path | None = None) -> int:
    """Entferne irrtümlich erfasste Musterlösungen und sichere den alten Stand."""
    target = progress_file(course)
    if target is None or not target.exists():
        return 0
    from .examples import example_programs

    example_sources = {example.source for example in example_programs()}
    data = load_progress(course)
    attempts = data.get("attempts", [])
    if not isinstance(attempts, list):
        return 0
    retained = [
        attempt
        for attempt in attempts
        if not isinstance(attempt, dict) or attempt.get("source") not in example_sources
    ]
    removed = len(attempts) - len(retained)
    if removed:
        backup = target.with_name("progress.before-example-cleanup.json")
        if not backup.exists():
            shutil.copy2(target, backup)
        data["attempts"] = retained
        _save(data, course)
    return removed


def clear_exercise_progress(exercise: str, course: Path | None = None) -> int:
    """Entferne Versuche und geöffnete Hinweise einer Aufgabe mit Backup."""
    target = progress_file(course)
    if target is None or not target.exists():
        return 0
    data = load_progress(course)
    attempts = data.get("attempts", [])
    if not isinstance(attempts, list):
        return 0
    retained = [
        attempt
        for attempt in attempts
        if not isinstance(attempt, dict) or attempt.get("exercise") != exercise
    ]
    removed = len(attempts) - len(retained)
    hints = data.get("hints", {})
    removed_hint = False
    if isinstance(hints, dict):
        for key in tuple(hints):
            if key == exercise or key.endswith(f"/{exercise}"):
                del hints[key]
                removed_hint = True
    if removed or removed_hint:
        backup_directory = target.parent / "backups"
        backup_directory.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        shutil.copy2(target, backup_directory / f"progress-{exercise}-{stamp}.json")
        data["attempts"] = retained
        _save(data, course)
    return removed
