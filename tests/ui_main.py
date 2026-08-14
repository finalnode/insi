"""Registriere in:si mit einem isolierten Kurs für die User-Simulation."""

import json
from pathlib import Path
from tempfile import mkdtemp

from insi.app import main
from insi.course import create_course


course = Path(mkdtemp(prefix="insi-ui-course-")) / "standardkurs"
create_course(course, "Ada")
setup = {
    "format": "pykim-course-setup-v1",
    "name": "ui-standardkurs.pykim-setup",
    "teacher": "in:si-Test",
    "school": "Testschule",
    "course": "UI-Standardkurs",
    "repository": "",
    "branch": "main",
    "scripts_path": "Skripte",
    "assignments_path": "Aufgaben",
    "trainers_path": "Trainer",
}
(course / ".pykim").mkdir(exist_ok=True)
(course / ".pykim" / "course.pykim-setup").write_text(
    json.dumps(setup),
    encoding="utf-8",
)


main(show=False, native=False, arguments=[])
