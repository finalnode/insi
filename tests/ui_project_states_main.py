"""Registriere in:si mit einem Projekt für die Projektstand-Simulation."""

import json
from pathlib import Path
from tempfile import mkdtemp

from insi.app import main
from insi.course import create_course
from insi.projects import create_project


course = Path(mkdtemp(prefix="insi-ui-project-states-")) / "projektkurs"
create_course(course, "Ada")
setup = {
    "format": "insi-course-setup-v1",
    "name": "ui-projektkurs.insi-setup",
    "teacher": "in:si-Test",
    "school": "Testschule",
    "course": "UI-Projektkurs",
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
create_project(course, "Versionsprojekt", "pyxel")


main(show=False, native=False, arguments=[])
