"""Prüfe 0.7-Migrationen mit dem echten Dateisystem des paketierten Python."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from insi.data_migrations import (
    COURSE_DATA_MARKER,
    LOCAL_SETTINGS_FORMAT,
    migrate_course_data,
    migrate_local_settings,
)


def main() -> None:
    with TemporaryDirectory(prefix="insi-migration-check-") as directory:
        root = Path(directory)
        settings = root / "config.json"
        original_settings = b'{"course_directory": "C:/Kurse", "unknown": true}\n'
        settings.write_bytes(original_settings)
        assert migrate_local_settings(settings).changed == ("config.json",)
        backup = root / "backups/migrations/0.7-to-0.8/config.json"
        assert backup.read_bytes() == original_settings
        assert json.loads(settings.read_bytes()) == {
            "format": LOCAL_SETTINGS_FORMAT,
            **json.loads(original_settings),
        }
        assert migrate_local_settings(settings).changed == ()
        assert backup.read_bytes() == original_settings

        course = root / "course"
        internal = course / ".pykim"
        internal.mkdir(parents=True)
        (course / ".pykim-course.json").write_text('{"format": 1}', encoding="utf-8")
        progress = internal / "progress.json"
        original_progress = b'{"attempts": [], "journal": {"lesson": "keep"}}\n'
        progress.write_bytes(original_progress)
        assert migrate_course_data(course).version == 1
        backup = internal / "backups/migrations/0.7-to-0.8/progress.json"
        assert backup.read_bytes() == original_progress
        assert json.loads(progress.read_bytes()) == {
            **json.loads(original_progress),
            "format": 1,
            "answers": {},
            "hints": {},
        }
        assert (internal / COURSE_DATA_MARKER).is_file()
        assert migrate_course_data(course).changed == ()
        assert backup.read_bytes() == original_progress
    print("Einstellungen und Lernstand: Migration, Originalbackup und Wiederholung OK")


if __name__ == "__main__":
    main()
