import json
import hashlib

import pytest

from insi.course import create_course
from insi.submission.cli import parser
from insi.submission.crypto import (
    certificate_info,
    decrypt_payload,
    generate_course_credentials,
)
from insi.submission.export import (
    build_submission_payload,
    create_encrypted_submission,
    install_course_certificate,
)
from insi.submission.fingerprints import code_fingerprints
from insi.submission.teacher import create_teacher_report, decrypt_submission


def test_fingerprints_ignore_formatting_and_variable_names():
    first = """distance = 5
for step in range(distance):
    right(step)
"""
    formatted = "distance=5\n\nfor step in range(distance):\n  right(step)\n"
    renamed = "width = 5\nfor index in range(width):\n    right(index)\n"

    first_hashes = code_fingerprints(first)
    formatted_hashes = code_fingerprints(formatted)
    renamed_hashes = code_fingerprints(renamed)

    assert first_hashes.exact_sha256 != formatted_hashes.exact_sha256
    assert first_hashes.canonical_sha256 == formatted_hashes.canonical_sha256
    assert first_hashes.structural_sha256 == renamed_hashes.structural_sha256
    assert first_hashes.structural_sha256 != code_fingerprints(renamed.replace("5", "6")).structural_sha256


def test_invalid_python_receives_no_structural_fingerprint():
    result = code_fingerprints("for x in:")

    assert not result.syntax_valid
    assert result.structural_sha256 is None
    assert result.canonical_sha256


def test_certificate_export_decrypt_and_tamper_detection(tmp_path, monkeypatch):
    credentials = tmp_path / "credentials"
    certificate, private_key = generate_course_credentials(
        credentials,
        teacher="Frau Beispiel",
        school="OSZ KIM",
        course="Informatik 11A",
        password="sehr-geheim",
        valid_days=30,
    )
    info = certificate_info(certificate)
    assert info.course == "Informatik 11A"
    assert info.teacher == "Frau Beispiel"

    course = tmp_path / "course"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    create_course(course, "Ada Lovelace")
    install_course_certificate(certificate.read_bytes(), course)
    submission = create_encrypted_submission(course)
    payload = decrypt_submission(submission, private_key, "sehr-geheim")

    assert payload["identity"] == {"student_name": "Ada Lovelace"}
    assert payload["summary"]["total"] == 11
    assert len(payload["exercises"]) == 11
    assert all(item["fingerprints_verified"] for item in payload["exercises"])

    envelope = json.loads(submission.read_text(encoding="utf-8"))
    envelope["ciphertext"] = envelope["ciphertext"][:-2] + "AA"
    with pytest.raises(Exception):
        decrypt_payload(envelope, private_key.read_bytes(), "sehr-geheim")


def test_certificate_contains_hashed_content_repository_configuration(tmp_path, monkeypatch):
    certificate, _private_key = generate_course_credentials(
        tmp_path,
        teacher="Frau Beispiel",
        school="OSZ KIM",
        course="Python Beta",
        password="sehr-geheim",
        content_repository="https://github.com/finalnode/PyKIM_Kurs.git",
        content_branch="beta",
    )

    info = certificate_info(certificate)

    assert info.content is not None
    assert info.content.repository == "https://github.com/finalnode/PyKIM_Kurs.git"
    assert info.content.branch == "beta"
    assert info.content.scripts_path == "Skripte"
    assert info.content.assignments_path == "Aufgaben"
    assert info.content.trainers_path == "Trainer"
    assert info.content.certificate_name == "python-beta.pykim-cert"
    authorization = tmp_path / "certificates/python-beta.pykim-cert"
    assert authorization.is_file()
    assert authorization.read_text(encoding="ascii").strip() == (
        "sha256:" + hashlib.sha256(certificate.read_bytes()).hexdigest()
    )

    document = json.loads(certificate.read_text(encoding="utf-8"))
    document["content"]["branch"] = "main"
    changed = json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")
    changed_info = certificate_info(changed)
    monkeypatch.setattr(
        "insi.updates._download",
        lambda *_args: authorization.read_bytes(),
    )
    from insi.updates import verify_certificate_authorization

    with pytest.raises(ValueError, match="nicht zugelassen"):
        verify_certificate_authorization(changed, changed_info.content)


def test_teacher_cli_accepts_certificate_validity():
    options = parser().parse_args([
        "keygen",
        "--teacher", "Frau Beispiel",
        "--school", "OSZ KIM",
        "--course", "Python 11A",
        "--output", "kurszugang",
        "--valid-days", "365",
        "--content-repository", "https://github.com/finalnode/PyKIM_Kurs.git",
    ])

    assert options.valid_days == 365
    assert options.content_branch == "main"


def test_wrong_teacher_key_reports_both_fingerprints(tmp_path):
    certificate, _ = generate_course_credentials(
        tmp_path / "first",
        teacher="Frau A",
        school="OSZ KIM",
        course="Kurs A",
        password="sehr-geheim",
    )
    _, wrong_key = generate_course_credentials(
        tmp_path / "second",
        teacher="Herr B",
        school="OSZ KIM",
        course="Kurs B",
        password="noch-geheimer",
    )
    from insi.submission.crypto import encrypt_payload

    envelope = encrypt_payload({"test": True}, certificate.read_bytes())
    with pytest.raises(ValueError, match="Erwarteter Fingerabdruck.*verwendeter Fingerabdruck"):
        decrypt_payload(envelope, wrong_key.read_bytes(), "noch-geheimer")


def test_external_certificate_is_checked_on_import_and_export(tmp_path, monkeypatch):
    from insi.updates import TrainerVerification

    certificate, _ = generate_course_credentials(
        tmp_path / "keys",
        teacher="Frau Beispiel",
        school="OSZ KIM",
        course="Python 11A",
        password="sehr-geheim",
        content_repository="https://github.com/finalnode/PyKIM_Kurs.git",
    )
    checks = []
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates.verify_certificate_authorization",
        lambda data, configuration, **kwargs: (
            checks.append((data, configuration, kwargs))
            or TrainerVerification(True, False)
        ),
    )
    monkeypatch.setattr(
        "insi.updates.sync_certificate_content",
        lambda _configuration: tmp_path / "content",
    )
    course = tmp_path / "course"
    create_course(course, "Ada")

    install_course_certificate(certificate.read_bytes(), course)
    create_encrypted_submission(course, tmp_path / "exports")

    assert len(checks) == 2
    assert checks[0][1].certificate_name == "python-11a.pykim-cert"
    assert checks[1][2] == {"allow_offline": False}


def test_submission_payload_excludes_journal_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course, "Grace")

    assert "journal" not in build_submission_payload(course)
    assert "journal" in build_submission_payload(course, include_journal=True)


def test_submission_payload_never_falls_back_to_system_user(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("getpass.getuser", lambda: "private-login")
    course = tmp_path / "course"
    create_course(course)

    payload = build_submission_payload(course)

    assert payload["identity"] == {"student_name": ""}
    assert "private-login" not in json.dumps(payload)


def test_teacher_report_reads_moodle_download_folder(tmp_path, monkeypatch):
    certificate, private_key = generate_course_credentials(
        tmp_path / "keys",
        teacher="Herr Test",
        school="OSZ KIM",
        course="GK Python",
        password="bericht-passwort",
    )
    submissions = []
    for index, name in enumerate(("Ada", "Bob"), start=1):
        config = tmp_path / f"config-{index}"
        monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))
        course = tmp_path / f"course-{index}"
        create_course(course, name)
        install_course_certificate(certificate.read_bytes(), course)
        submissions.append(create_encrypted_submission(course, tmp_path / "moodle" / name))

    csv_path, html_path = create_teacher_report(
        submissions,
        private_key,
        "bericht-passwort",
        tmp_path / "report",
    )

    assert "Ada" in csv_path.read_text(encoding="utf-8")
    report = html_path.read_text(encoding="utf-8")
    assert "Ähnlichkeitshinweise" in report
    assert "Kein Plagiatsnachweis" in report
    assert "Abgaben und Quellcodes" in report


def test_teacher_cli_exposes_all_offline_commands():
    keygen = parser().parse_args([
        "keygen", "--teacher", "T", "--school", "S", "--course", "C", "--output", "."
        , "--content-repository", "https://github.com/finalnode/PyKIM_Kurs.git",
        "--content-branch", "beta",
    ])
    assert keygen.command == "keygen"
    assert keygen.content_branch == "beta"
    assert parser().parse_args([
        "decrypt", "x.pykim-abgabe", "--key", "key", "--output", "out.json"
    ]).command == "decrypt"
    assert parser().parse_args([
        "report", ".", "--key", "key", "--output", "report"
    ]).command == "report"
