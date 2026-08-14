"""Erzeuge aus den eingebauten Inhalten ein eigenständiges Kursrepository."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "insi"
TARGET = ROOT / "kurs"


VALIDATOR = r'''"""Validiere Kursstruktur und erzeuge reproduzierbare SHA-256-Hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TESTS = {
    "pixels", "no-extra-pixels", "pixel-count", "square", "position",
    "positions", "pixel-names", "visibility", "audio", "loop",
    "nested-loop", "parallel", "condition", "function", "calls",
    "class", "methods", "super-init",
}


def content_files() -> list[Path]:
    result = []
    for folder, suffix in (("Skripte", ".md"), ("Aufgaben", ".md"), ("Trainer", ".yml")):
        result.extend(
            path for path in (ROOT / folder).rglob(f"*{suffix}")
            if path.is_file()
            and not any(part.startswith("_") for part in path.relative_to(ROOT).parts)
        )
    return sorted(result)


def validate() -> None:
    seen = set()
    trainers = [path for path in content_files() if path.is_relative_to(ROOT / "Trainer")]
    for trainer in trainers:
        definition = yaml.safe_load(trainer.read_text(encoding="utf-8"))
        exercise_id = definition.get("id") if isinstance(definition, dict) else None
        if not isinstance(exercise_id, str) or exercise_id in seen:
            raise ValueError(f"Ungültige oder doppelte Aufgabenkennung: {exercise_id!r}")
        seen.add(exercise_id)
        assignments = [
            path for path in content_files()
            if path.is_relative_to(ROOT / "Aufgaben") and path.stem == exercise_id
        ]
        if len(assignments) != 1:
            raise ValueError(f"Aufgabe fehlt oder ist nicht eindeutig: {exercise_id}.")
        if definition.get("format") != 1 or definition.get("id") != exercise_id:
            raise ValueError(f"Trainerkennung stimmt nicht: {trainer}")
        tests = definition.get("tests")
        if not isinstance(tests, list) or not tests:
            raise ValueError(f"{trainer} benötigt mindestens einen Test.")
        unknown = {test.get("type") for test in tests} - ALLOWED_TESTS
        if unknown:
            raise ValueError(f"Unbekannte Prüftypen in {trainer}: {sorted(unknown)}")


def trainer_hashes() -> dict[str, object]:
    files = {
        path.relative_to(ROOT).as_posix(): {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size": path.stat().st_size,
        }
        for path in content_files()
        if path.is_relative_to(ROOT / "Trainer")
    }
    return {
        "format": 1,
        "algorithm": "sha256",
        "scope": "trainer",
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-hashes", action="store_true")
    options = parser.parse_args()
    validate()
    rendered = json.dumps(trainer_hashes(), ensure_ascii=False, indent=2) + "\n"
    target = ROOT / ".pykim" / "trainer-hashes.json"
    if options.write_hashes:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    elif not target.is_file() or target.read_text(encoding="utf-8") != rendered:
        raise SystemExit(".pykim/trainer-hashes.json ist nicht aktuell.")
    print(
        f"Kursinhalt gültig: {len(content_files())} sichtbare Dateien, "
        f"{len(trainer_hashes()['files'])} Trainer"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


WORKFLOW = '''name: Kursinhalte prüfen

on:
  push:
    branches: [main, beta]
    paths-ignore:
      - .pykim/trainer-hashes.json
  pull_request:
    branches: [main, beta]

permissions:
  contents: write

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install "PyYAML>=6,<7"
      - run: python tools/validate_content.py --write-hashes
      - name: Hashliste zurückschreiben
        if: github.event_name == 'push'
        run: |
          if git diff --quiet -- .pykim/trainer-hashes.json; then exit 0; fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add .pykim/trainer-hashes.json
          git commit -m "chore: Inhaltshashes aktualisieren"
          git push
'''


README = '''# PyKIM-Kursinhalte

Öffentliche Skripte, Aufgabenstellungen und deklarative Trainerdefinitionen
für in:si und das PyKIM-Modul.

- `main` enthält den stabilen Unterrichtsstand.
- `beta` dient zur Erprobung neuer und geänderter Inhalte.
- Automatisch geprüfte Aufgaben besitzen eine gleichnamige Datei unter `Trainer/`.
- Dateien und Ordner, deren Name mit `_` beginnt, werden von der Suite ignoriert.
- `.pykim/trainer-hashes.json` wird durch GitHub Actions erzeugt und nicht von Hand gepflegt.

Nach Änderungen kann lokal geprüft werden:

```bash
python -m pip install "PyYAML>=6,<7"
python tools/validate_content.py --write-hashes
```

Schülerlösungen, Musterlösungen, Zertifikate, Schlüssel und personenbezogene
Daten gehören nicht in dieses Repository.
'''


def main() -> int:
    if TARGET.exists():
        raise SystemExit(f"Ziel existiert bereits: {TARGET}")
    TARGET.mkdir()
    shutil.copytree(SOURCE / "Skripte", TARGET / "Skripte")
    shutil.copytree(SOURCE / "Aufgaben", TARGET / "Aufgaben")
    shutil.copy2(ROOT / "LICENSE", TARGET / "LICENSE")

    payload = yaml.safe_load(
        (SOURCE / "Trainer" / "definitions.yml").read_text(encoding="utf-8")
    )
    trainer = TARGET / "Trainer"
    trainer.mkdir()
    definitions = payload["exercises"]
    for definition in definitions:
        target = trainer / f"{definition['id']}.yml"
        target.write_text(
            yaml.safe_dump(
                {"format": 1, **definition}, allow_unicode=True, sort_keys=False
            ),
            encoding="utf-8",
        )

    (TARGET / "README.md").write_text(README, encoding="utf-8")
    (TARGET / ".gitignore").write_text(".DS_Store\n__pycache__/\n", encoding="utf-8")
    workflow = TARGET / ".github" / "workflows"
    workflow.mkdir(parents=True)
    (workflow / "validate.yml").write_text(WORKFLOW, encoding="utf-8")
    tools = TARGET / "tools"
    tools.mkdir()
    (tools / "validate_content.py").write_text(VALIDATOR, encoding="utf-8")

    # Dieselbe Logik wie im künftigen Workflow bereits für den ersten Commit ausführen.
    import subprocess

    subprocess.run(
        ["python", str(tools / "validate_content.py"), "--write-hashes"],
        cwd=TARGET,
        check=True,
    )
    print(f"Kursrepository vorbereitet: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
