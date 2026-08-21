from dataclasses import dataclass

from insi.training.backends import TRAINER_FORMAT, register_backend
from insi.training.contracts import CheckReport, CheckResult, StarterFile, Submission
from insi.training.registry import (
    activate,
    evaluate_submission,
    exercise_engine,
    exercise_names,
    exercise_starter_files,
    get_exercise,
)


@dataclass(frozen=True)
class _WebExercise:
    name: str
    title: str


class _WebBackend:
    engine = "test-web"

    def load_exercises(self, trainer_directory):
        source = trainer_directory / "test-web" / "index.yml"
        if not source.is_file():
            return {}
        return {"webseite": _WebExercise("webseite", "Webseite")}

    def evaluate(self, exercise, submission):
        passed = submission.kind == "workspace" and submission.workspace is not None
        return CheckReport(
            exercise.title,
            (CheckResult(passed, "Projekt erkannt.", "Projekt fehlt."),),
        )

    def starter_files(self, exercise):
        return (StarterFile("index.html", "<!doctype html>\n"),)


def test_explicit_pykim_engine_uses_the_new_insi_trainer_contract(tmp_path):
    trainers = tmp_path / "Trainer"
    trainers.mkdir()
    (trainers / "loop.yml").write_text(
        f"""format: {TRAINER_FORMAT}
engine: pykim
exercises:
  - id: schleife
    title: Schleife
    tests:
      - type: loop
""",
        encoding="utf-8",
    )

    activate(tmp_path)

    assert exercise_names() == ("schleife",)
    assert exercise_engine("schleife") == "pykim"
    assert get_exercise("schleife").checker("for _ in range(2):\n    pass").successful
    starter = exercise_starter_files("schleife")
    assert starter[0].relative_path == "schleife.py"
    assert 'run(check="schleife")' in starter[0].content


def test_unknown_declared_engine_is_rejected(tmp_path):
    trainers = tmp_path / "Trainer"
    trainers.mkdir()
    (trainers / "web.yml").write_text(
        f"format: {TRAINER_FORMAT}\nengine: web\nexercises: []\n",
        encoding="utf-8",
    )

    try:
        activate(tmp_path)
    except ValueError as error:
        assert "Nicht installierte Trainer-Engine: web" in str(error)
    else:
        raise AssertionError("Eine nicht installierte Engine wurde akzeptiert.")


def test_non_python_backend_evaluates_a_workspace_without_pykim_checker(tmp_path):
    register_backend(_WebBackend(), replace=True)
    trainers = tmp_path / "Trainer" / "test-web"
    trainers.mkdir(parents=True)
    (trainers / "index.yml").write_text("id: webseite\n", encoding="utf-8")

    activate(tmp_path)
    report = evaluate_submission(
        "webseite",
        Submission(kind="workspace", workspace=tmp_path),
    )

    assert report.successful
    assert exercise_starter_files("webseite")[0].relative_path == "index.html"
