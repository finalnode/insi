"""Verträge der UI-freien Setup-Aufbereitung."""

from insi.runtime import RuntimeCandidate, RuntimePreflight
from insi.setup_view import SetupRuntimeSnapshot, runtime_candidate_options


def candidate(path: str, version: str, *, supported: bool = True) -> RuntimeCandidate:
    return RuntimeCandidate(path, version, "System", supported, ())


def test_runtime_options_describe_candidates_against_course_contract():
    ready = candidate("/ready/python", "3.12.4")
    wrong_version = candidate("/old/python", "3.11.9")
    unsupported = candidate("/unsupported/python", "3.9.20", supported=False)
    preflight = RuntimePreflight(
        True, ready, "3.12", None, (), (), (), False, False, ()
    )

    options = runtime_candidate_options(
        SetupRuntimeSnapshot(False, (ready, wrong_version, unsupported), preflight)
    )

    assert options[ready.executable].endswith("· bereit")
    assert options[wrong_version.executable].endswith("· Kurs benötigt Python 3.12")
    assert options[unsupported.executable].endswith("· Python-Version ungeeignet")


def test_runtime_options_report_missing_course_profile():
    runtime = candidate("/python", "3.12.4")
    preflight = RuntimePreflight(
        False, None, "3.12", None, (), ("Paket fehlt",), (), False, True, (runtime,)
    )

    assert runtime_candidate_options(
        SetupRuntimeSnapshot(False, (runtime,), preflight)
    )[runtime.executable].endswith("· Kursprofil nicht erfüllt")
