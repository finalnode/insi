"""Lokale Auswertung verschlüsselter Abgaben durch die Lehrkraft."""

import csv
import html
import json
from collections import defaultdict
from pathlib import Path

from .crypto import decrypt_payload
from .fingerprints import code_fingerprints


def decrypt_submission(
    submission: str | Path, private_key: str | Path, password: str
) -> dict[str, object]:
    envelope = json.loads(Path(submission).read_text(encoding="utf-8"))
    payload = decrypt_payload(envelope, Path(private_key).read_bytes(), password)
    for exercise in payload.get("exercises", []):
        if not isinstance(exercise, dict):
            continue
        recomputed = code_fingerprints(str(exercise.get("source", ""))).as_dict()
        exercise["fingerprints_verified"] = recomputed == exercise.get("fingerprints")
        exercise["teacher_fingerprints"] = recomputed
    return payload


def create_teacher_report(
    submissions: list[str | Path],
    private_key: str | Path,
    password: str,
    output_directory: str | Path,
) -> tuple[Path, Path]:
    records = [decrypt_submission(path, private_key, password) for path in submissions]
    output = Path(output_directory).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    similarities: dict[tuple[str, str], list[str]] = defaultdict(list)
    for record in records:
        student = str(record.get("identity", {}).get("student_name", "Unbekannt"))
        for exercise in record.get("exercises", []):
            if not exercise.get("result"):
                continue
            fingerprint = exercise.get("teacher_fingerprints", {}).get("structural_sha256")
            if fingerprint:
                similarities[(exercise["exercise"], fingerprint)].append(student)

    csv_path = output / "pykim-leistungsuebersicht.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Name", "Bearbeitet", "Bestanden", "Gesamt", "Exportiert"])
        for record in records:
            summary = record.get("summary", {})
            writer.writerow([
                record.get("identity", {}).get("student_name", ""),
                summary.get("attempted", 0),
                summary.get("completed", 0),
                summary.get("total", 0),
                record.get("exported_at", ""),
            ])

    rows = []
    details = []
    for record in records:
        identity = record.get("identity", {})
        summary = record.get("summary", {})
        student_name = str(identity.get("student_name", ""))
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(identity.get('student_name', '')))}</td>"
            f"<td>{summary.get('attempted', 0)}</td>"
            f"<td>{summary.get('completed', 0)} / {summary.get('total', 0)}</td>"
            f"<td>{html.escape(str(record.get('exported_at', '')))}</td>"
            "</tr>"
        )
        exercise_details = []
        for exercise in record.get("exercises", []):
            result = exercise.get("result") or {}
            status = (
                f"{result.get('passed', 0)} / {result.get('total', 0)} Tests"
                if result
                else "nicht getestet"
            )
            verified = "ja" if exercise.get("fingerprints_verified") else "nein"
            exercise_details.append(
                "<details><summary>"
                f"{html.escape(str(exercise.get('exercise', '')))} – {status}"
                "</summary>"
                f"<p>Fingerprints neu geprüft: <strong>{verified}</strong></p>"
                f"<pre>{html.escape(str(exercise.get('source', '')))}</pre>"
                "</details>"
            )
        details.append(
            f"<section><h2>{html.escape(student_name)}</h2>"
            + "".join(exercise_details)
            + "</section>"
        )
    similarity_items = []
    for (exercise, _fingerprint), students in sorted(similarities.items()):
        if len(students) > 1:
            names = ", ".join(html.escape(name) for name in students)
            similarity_items.append(
                f"<li><strong>{html.escape(exercise)}</strong>: {names} "
                "(gleicher Strukturhash; nur manueller Hinweis)</li>"
            )
    html_path = output / "pykim-bericht.html"
    html_path.write_text(
        "<!doctype html><meta charset='utf-8'><title>PyKIM-Bericht</title>"
        "<h1>PyKIM-Leistungsübersicht</h1>"
        "<table border='1' cellpadding='6'><tr><th>Name</th><th>Bearbeitet</th>"
        "<th>Bestanden</th><th>Exportiert</th></tr>"
        + "".join(rows)
        + "</table><h2>Ähnlichkeitshinweise</h2><p>Kein Plagiatsnachweis.</p><ul>"
        + "".join(similarity_items)
        + "</ul><h1>Abgaben und Quellcodes</h1>"
        + "".join(details),
        encoding="utf-8",
    )
    return csv_path, html_path
