"""Atomarer Dateiaustausch für lokale und portable Kursdaten."""

import json
import os
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile


def atomic_write(target: Path, content: str | bytes) -> None:
    """Ersetze eine Datei erst nach vollständigem Schreiben im selben Ordner."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        binary = isinstance(content, bytes)
        with NamedTemporaryFile(
            "wb" if binary else "w",
            encoding=None if binary else "utf-8",
            dir=target.parent,
            prefix=".insi-write-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            # Ein entfernter Datenträger darf den ursprünglichen Fehler nicht
            # durch einen zweiten Fehler beim Aufräumen verdecken.
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)


def atomic_write_json(target: Path, document: dict[str, object]) -> None:
    atomic_write(target, json.dumps(document, ensure_ascii=False, indent=2) + "\n")
