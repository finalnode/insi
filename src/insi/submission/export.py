"""Zusammenstellen und Verschlüsseln eines portablen Lernstandexports."""

import json
import os
import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import pykim
import insi
from insi.course import exercise_file, get_student_name
from insi.progress import load_progress
from insi.system import system_user_name
from insi.training.registry import exercise_names

from .crypto import CertificateInfo, certificate_info, encrypt_payload
from .fingerprints import code_fingerprints


def course_certificate_path(course: str | Path) -> Path:
    return Path(course).expanduser().resolve() / ".pykim" / "submission-certificate.pykim-cert"


def install_course_certificate(data: bytes, course: str | Path) -> CertificateInfo:
    """Prüfe und speichere das öffentliche Zertifikat im portablen Kursordner."""
    info = certificate_info(data)
    if info.content is not None:
        from insi.updates import (
            sync_certificate_content,
            verify_certificate_authorization,
        )

        verify_certificate_authorization(data, info.content)
        sync_certificate_content(info.content)
    target = course_certificate_path(course)
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", dir=target.parent, delete=False) as temporary:
        temporary.write(data)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, target)
    return info


def course_certificate_info(course: str | Path) -> CertificateInfo | None:
    target = course_certificate_path(course)
    if not target.exists():
        return None
    return certificate_info(target)


def verify_installed_course_certificate(
    course: str | Path, *, allow_offline: bool = False
):
    """Prüfe das installierte Zertifikat erneut gegen sein Kurs-Repository."""
    target = course_certificate_path(course)
    if not target.is_file():
        raise FileNotFoundError("Importiere zuerst das Zertifikat deiner Lehrkraft.")
    data = target.read_bytes()
    info = certificate_info(data)
    if info.content is None:
        raise ValueError("Das Kurszertifikat enthält keine externe Inhaltsquelle.")
    from insi.updates import verify_certificate_authorization

    return info, verify_certificate_authorization(
        data, info.content, allow_offline=allow_offline
    )


def _latest_attempts(progress: dict[str, object]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    attempts = progress.get("attempts", [])
    if isinstance(attempts, list):
        for attempt in attempts:
            if isinstance(attempt, dict) and isinstance(attempt.get("exercise"), str):
                result[attempt["exercise"]] = attempt
    return result


def build_submission_payload(
    course: str | Path, *, include_journal: bool = False
) -> dict[str, object]:
    root = Path(course).expanduser().resolve()
    progress = load_progress(root)
    latest = _latest_attempts(progress)
    exercises = []
    for name in exercise_names():
        path = exercise_file(name, root)
        source = path.read_text(encoding="utf-8") if path and path.exists() else ""
        attempt = latest.get(name)
        exercises.append(
            {
                "exercise": name,
                "source": source,
                "fingerprints": code_fingerprints(source).as_dict(),
                "result": None if attempt is None else {
                    "timestamp": attempt.get("timestamp"),
                    "passed": attempt.get("passed", 0),
                    "total": attempt.get("total", 0),
                    "successful": bool(attempt.get("successful")),
                    "optimization": attempt.get("optimization"),
                    "tests": attempt.get("tests", []),
                },
            }
        )
    completed = sum(
        bool(item["result"] and item["result"].get("successful")) for item in exercises
    )
    payload: dict[str, object] = {
        "format": "pykim-learning-record-v1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "identity": {
            "student_name": get_student_name(root) or system_user_name(),
            "system_name": system_user_name(),
        },
        "environment": {
            "insi": insi.__version__,
            "pykim": pykim.__version__,
            "python": platform.python_version(),
            "platform": platform.system(),
        },
        "summary": {
            "completed": completed,
            "total": len(exercises),
            "attempted": sum(item["result"] is not None for item in exercises),
        },
        "exercises": exercises,
    }
    if include_journal:
        payload["journal"] = progress.get("journal", {})
        payload["answers"] = progress.get("answers", {})
    return payload


def create_encrypted_submission(
    course: str | Path,
    output_directory: str | Path | None = None,
    *,
    include_journal: bool = False,
) -> Path:
    root = Path(course).expanduser().resolve()
    certificate_path = course_certificate_path(root)
    if not certificate_path.exists():
        raise FileNotFoundError("Importiere zuerst das Zertifikat deiner Lehrkraft.")
    info = certificate_info(certificate_path)
    if info.content is not None:
        verify_installed_course_certificate(root, allow_offline=False)
    payload = build_submission_payload(root, include_journal=include_journal)
    envelope = encrypt_payload(payload, certificate_path.read_bytes())
    destination = (
        Path(output_directory).expanduser().resolve()
        if output_directory is not None
        else root / "abgaben"
    )
    destination.mkdir(parents=True, exist_ok=True)
    identity = payload["identity"]
    name = re.sub(r"[^a-z0-9]+", "-", str(identity["student_name"]).casefold()).strip("-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = destination / f"{name or 'lernstand'}-{timestamp}.pykim-abgabe"
    target.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
