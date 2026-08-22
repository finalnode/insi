from dataclasses import dataclass

import pytest

from insi.course import approve_trainer_extension, approved_trainer_extensions
from insi.training import backends
from insi.training.backends import (
    TRAINER_FORMAT,
    backend_extensions,
    backend_names,
    get_authoring_backend,
    register_backend,
)
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


class _Distribution:
    version = "1.2.3"
    metadata = {
        "Name": "Example-Trainer",
        "Author-email": "Example Team <team@example.invalid>",
        "Home-page": "https://example.invalid/trainer",
    }


class _EntryPoint:
    name = "external-web"

    def __init__(self):
        self.dist = _Distribution()
        self.loads = 0

    def load(self):
        self.loads += 1
        return type("ExternalBackend", (_WebBackend,), {"engine": self.name})()


def _external_entrypoint(monkeypatch, tmp_path):
    candidate = _EntryPoint()
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(backends, "_BACKENDS", dict(backends._BACKENDS))
    monkeypatch.setattr(backends, "_LOADED_EXTENSIONS", set())
    monkeypatch.setattr(backends, "entry_points", lambda **_options: (candidate,))
    return candidate


def test_external_backend_metadata_is_inventoried_without_import(monkeypatch, tmp_path):
    candidate = _external_entrypoint(monkeypatch, tmp_path)

    extensions = backend_extensions()

    assert candidate.loads == 0
    assert extensions[0].engine == "external-web"
    assert extensions[0].identity == "Example-Trainer==1.2.3"
    assert extensions[0].publisher == "Example Team <team@example.invalid>"
    assert extensions[0].source == "https://example.invalid/trainer"
    assert "external-web" not in backend_names()
    assert candidate.loads == 0


def test_external_backend_loads_only_after_version_consent(monkeypatch, tmp_path):
    candidate = _external_entrypoint(monkeypatch, tmp_path)

    approve_trainer_extension("Example-Trainer==1.2.3")

    assert approved_trainer_extensions() == frozenset({"Example-Trainer==1.2.3"})
    assert "external-web" in backend_names()
    assert candidate.loads == 1
    assert "external-web" in backend_names()
    assert candidate.loads == 1


def test_new_external_backend_version_requires_new_consent(monkeypatch, tmp_path):
    candidate = _external_entrypoint(monkeypatch, tmp_path)
    approve_trainer_extension("Example-Trainer==1.2.3")
    candidate.dist.version = "1.2.4"

    assert "external-web" not in backend_names()
    assert candidate.loads == 0


def test_declared_unapproved_backend_fails_closed(monkeypatch, tmp_path):
    candidate = _external_entrypoint(monkeypatch, tmp_path)
    trainers = tmp_path / "Trainer"
    trainers.mkdir()
    (trainers / "external.yml").write_text(
        f"format: {TRAINER_FORMAT}\nengine: external-web\nexercises: []\n",
        encoding="utf-8",
    )

    with pytest.raises(PermissionError, match="Example-Trainer==1.2.3"):
        backends.load_backend_exercises(trainers)

    assert candidate.loads == 0


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


def test_legacy_numeric_format_activates_pykim_adapter_lazily(tmp_path):
    trainers = tmp_path / "Trainer"
    trainers.mkdir()
    (trainers / "legacy.yml").write_text(
        """format: 1
exercises:
  - id: alt
    title: Alt
    tests:
      - type: loop
""",
        encoding="utf-8",
    )

    activate(tmp_path)

    assert exercise_names() == ("alt",)
    assert exercise_engine("alt") == "pykim"


def test_pykim_authoring_is_exposed_through_optional_backend_contract():
    authoring = get_authoring_backend("pykim")

    source = authoring.generate_source(
        "vertrag", "Vertrag", ("loop",), optimal_lines=4
    )
    exercise = authoring.parse_source(source)

    assert exercise.name == "vertrag"
    assert "loop" in authoring.rule_kinds
    assert authoring.rule_labels["loop"]
    assert authoring.audit(exercise).valid


def test_backend_without_authoring_tools_is_rejected():
    register_backend(_WebBackend(), replace=True)

    with pytest.raises(ValueError, match="keine Autorenwerkzeuge"):
        get_authoring_backend("test-web")


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
