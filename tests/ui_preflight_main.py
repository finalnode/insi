"""Registriere einen Kurs mit zunächst reparaturbedürftiger Laufzeit."""

import json
import sys
from pathlib import Path
from tempfile import mkdtemp

from insi.app import main
from insi.course import create_course
from insi.runtime import (
    RuntimeCandidate,
    RuntimePackageCheck,
    RuntimePreflight,
)
import insi.course_selection_view as selection_view


course = Path(mkdtemp(prefix="insi-ui-preflight-")) / "runtimekurs"
create_course(course, "Ada")
setup = {
    "format": "insi-course-setup-v1",
    "name": "ui-runtimekurs.insi-setup",
    "teacher": "in:si-Test",
    "school": "Testschule",
    "course": "UI-Runtimekurs",
    "repository": "",
    "branch": "main",
    "scripts_path": "Skripte",
    "assignments_path": "Aufgaben",
    "trainers_path": "Trainer",
}
(course / ".pykim").mkdir(exist_ok=True)
(course / ".pykim" / "course.insi-setup").write_text(
    json.dumps(setup), encoding="utf-8"
)

candidate = RuntimeCandidate(
    sys.executable,
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "UI-Testumgebung",
    True,
    True,
    True,
)
state = {"ready": False}


def preflight(_course):
    if state["ready"]:
        return RuntimePreflight(
            True,
            candidate,
            "3.11",
            "macos-arm64-python311",
            (RuntimePackageCheck("PyKIM==0.6.0", "0.6.0", True),),
            (),
            (),
            False,
            False,
            (),
        )
    return RuntimePreflight(
        False,
        candidate,
        "3.11",
        "macos-arm64-python311",
        (RuntimePackageCheck("PyKIM==0.6.0", "0.5.0", False),),
        ("PyKIM hat Version 0.5.0; benötigt wird 0.6.0.",),
        (),
        False,
        True,
        (),
    )


def repair(_course):
    state["ready"] = True
    return candidate


selection_view.course_runtime_preflight = preflight
selection_view.repair_runtime = repair
selection_view.activate_installed_course_content = lambda _course: None

main(show=False, native=False, arguments=[])
