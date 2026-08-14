"""Kurszertifikate und hybride Verschlüsselung für Offline-Abgaben."""

import base64
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature
from cryptography.x509.oid import NameOID

CERTIFICATE_FORMAT = "pykim-course-config-v2"
LEGACY_CERTIFICATE_FORMAT = "pykim-course-certificate-v1"
PRIVATE_KEY_FORMAT = "pykim-teacher-private-key-v1"
SUBMISSION_FORMAT = "pykim-submission-v1"
CONTENT_CONFIGURATION_OID = x509.ObjectIdentifier("1.3.6.1.4.1.58555.1.1")


@dataclass(frozen=True)
class ContentConfiguration:
    """Vom Zertifikat signierte Quelle der Unterrichtsinhalte."""

    repository: str
    branch: str
    scripts_path: str
    assignments_path: str
    trainers_path: str
    certificate_name: str = ""

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CertificateInfo:
    teacher: str
    school: str
    course: str
    valid_from: str
    valid_until: str
    fingerprint: str
    content: ContentConfiguration | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _json_bytes(data: dict[str, object]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "pykim-kurs"


def _content_configuration(value: object) -> ContentConfiguration | None:
    if value in (None, {}):
        return None
    if not isinstance(value, dict):
        raise ValueError("Die Inhaltskonfiguration muss ein Objekt sein.")
    required = {
        "repository", "branch", "scripts_path", "assignments_path", "trainers_path"
    }
    allowed = required | {"certificate_name"}
    if not required.issubset(value) or not set(value).issubset(allowed) or not all(
        isinstance(value.get(key), str) and str(value[key]).strip() for key in required
    ):
        raise ValueError("Die Inhaltskonfiguration ist unvollständig.")
    repository = str(value["repository"]).strip()
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", repository):
        raise ValueError("Das Inhaltsrepository muss eine öffentliche GitHub-HTTPS-Adresse sein.")
    branch = str(value["branch"]).strip()
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch.split("/"):
        raise ValueError("Der Inhaltsbranch ist ungültig.")
    paths = {}
    for key in ("scripts_path", "assignments_path", "trainers_path"):
        path = str(value[key]).strip().strip("/")
        if not path or path.startswith(".") or ".." in path.split("/"):
            raise ValueError(f"Der Konfigurationspfad {key} ist unsicher.")
        paths[key] = path
    certificate_name = str(value.get("certificate_name", "")).strip()
    if certificate_name and not re.fullmatch(r"[A-Za-z0-9_.-]+\.pykim-cert", certificate_name):
        raise ValueError("Der Zertifikatsname ist ungültig.")
    return ContentConfiguration(repository, branch, **paths, certificate_name=certificate_name)


def certificate_info(data: bytes | str | Path) -> CertificateInfo:
    """Prüfe das öffentliche Zertifikat und liefere seine Kursangaben."""
    raw = Path(data).read_bytes() if isinstance(data, Path) else (
        data.encode("utf-8") if isinstance(data, str) else data
    )
    document = json.loads(raw.decode("utf-8"))
    if document.get("format") == CERTIFICATE_FORMAT:
        required = {
            "format", "name", "teacher", "school", "course", "valid_from",
            "valid_until", "fingerprint", "public_key", "content",
        }
        if set(document) != required or not all(
            isinstance(document.get(key), str) and document[key].strip()
            for key in required - {"content"}
        ):
            raise ValueError("Die PyKIM-Kurskonfiguration ist unvollständig.")
        content = _content_configuration(document.get("content"))
        if content is not None and content.certificate_name != document["name"]:
            raise ValueError(
                "Zertifikatsname und Inhaltskonfiguration passen nicht zusammen."
            )
        try:
            valid_from = datetime.fromisoformat(document["valid_from"])
            valid_until = datetime.fromisoformat(document["valid_until"])
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=timezone.utc)
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Die Gültigkeit der Kurskonfiguration ist ungültig."
            ) from error
        now = datetime.now(timezone.utc)
        if now < valid_from or now > valid_until:
            raise ValueError(
                "Die Kurskonfiguration ist noch nicht oder nicht mehr gültig."
            )
        try:
            public_key = serialization.load_der_public_key(
                _unb64(document["public_key"])
            )
            public_der = public_key.public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        except (ValueError, TypeError, UnicodeEncodeError) as error:
            raise ValueError("Der öffentliche Schlüssel ist ungültig.") from error
        fingerprint = hashlib.sha256(public_der).hexdigest()
        if fingerprint != document["fingerprint"]:
            raise ValueError("Der Schlüsselfingerabdruck stimmt nicht.")
        return CertificateInfo(
            teacher=document["teacher"].strip(),
            school=document["school"].strip(),
            course=document["course"].strip(),
            valid_from=valid_from.isoformat(),
            valid_until=valid_until.isoformat(),
            fingerprint=fingerprint,
            content=content,
        )
    if document.get("format") != LEGACY_CERTIFICATE_FORMAT:
        raise ValueError("Die Datei ist kein unterstütztes PyKIM-Kurszertifikat.")
    certificate = x509.load_pem_x509_certificate(document["certificate_pem"].encode("ascii"))
    try:
        certificate.public_key().verify(
            certificate.signature,
            certificate.tbs_certificate_bytes,
            padding.PKCS1v15(),
            certificate.signature_hash_algorithm,
        )
    except InvalidSignature as error:
        raise ValueError("Die Signatur des Kurszertifikats ist ungültig.") from error
    fingerprint = certificate.fingerprint(hashes.SHA256()).hex()
    if fingerprint != document.get("fingerprint"):
        raise ValueError("Der Zertifikatsfingerabdruck stimmt nicht.")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if now < certificate.not_valid_before or now > certificate.not_valid_after:
        raise ValueError("Das Kurszertifikat ist noch nicht oder nicht mehr gültig.")
    metadata = document.get("metadata", {})
    def subject_value(oid: x509.ObjectIdentifier) -> str:
        values = certificate.subject.get_attributes_for_oid(oid)
        return values[0].value if values else ""

    signed_metadata = {
        "teacher": subject_value(NameOID.COMMON_NAME),
        "school": subject_value(NameOID.ORGANIZATION_NAME),
        "course": subject_value(NameOID.ORGANIZATIONAL_UNIT_NAME),
    }
    if any(str(metadata.get(key, "")) != value for key, value in signed_metadata.items()):
        raise ValueError("Die Kursangaben passen nicht zum signierten Zertifikat.")
    try:
        extension = certificate.extensions.get_extension_for_oid(
            CONTENT_CONFIGURATION_OID
        ).value
        signed_content_data = json.loads(extension.value.decode("utf-8"))
    except x509.ExtensionNotFound:
        signed_content_data = None
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as error:
        raise ValueError("Die signierte Inhaltskonfiguration ist ungültig.") from error
    signed_content = _content_configuration(signed_content_data)
    visible_content = _content_configuration(metadata.get("content"))
    if visible_content != signed_content:
        raise ValueError("Die Inhaltskonfiguration passt nicht zum signierten Zertifikat.")
    return CertificateInfo(
        teacher=signed_metadata["teacher"],
        school=signed_metadata["school"],
        course=signed_metadata["course"],
        valid_from=certificate.not_valid_before.isoformat(),
        valid_until=certificate.not_valid_after.isoformat(),
        fingerprint=fingerprint,
        content=signed_content,
    )


def generate_course_credentials(
    output_directory: str | Path,
    *,
    teacher: str,
    school: str,
    course: str,
    password: str,
    valid_days: int = 730,
    content_repository: str = "",
    content_branch: str = "main",
    scripts_path: str = "Skripte",
    assignments_path: str = "Aufgaben",
    trainers_path: str = "Trainer",
) -> tuple[Path, Path]:
    """Erzeuge öffentliches Schülerzertifikat und verschlüsselten Lehrerschlüssel."""
    if len(password) < 8:
        raise ValueError("Das Passwort für den privaten Schlüssel benötigt mindestens 8 Zeichen.")
    if not all(value.strip() for value in (teacher, school, course)):
        raise ValueError("Lehrkraft, Schule und Kurs müssen angegeben werden.")
    stem = _slug(course)
    certificate_name = f"{stem}.pykim-cert"
    content = _content_configuration(
        None if not content_repository.strip() else {
            "repository": content_repository,
            "branch": content_branch,
            "scripts_path": scripts_path,
            "assignments_path": assignments_path,
            "trainers_path": trainers_path,
            "certificate_name": certificate_name,
        }
    )
    root = Path(output_directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    public_der = key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    fingerprint = hashlib.sha256(public_der).hexdigest()
    certificate_document = {
        "format": CERTIFICATE_FORMAT,
        "name": certificate_name,
        "teacher": teacher.strip(),
        "school": school.strip(),
        "course": course.strip(),
        "valid_from": (now - timedelta(minutes=5)).isoformat(),
        "valid_until": (now + timedelta(days=valid_days)).isoformat(),
        "fingerprint": fingerprint,
        "public_key": _b64(public_der),
        "content": None if content is None else content.as_dict(),
    }
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password.encode("utf-8")),
    )
    private_document = {
        "format": PRIVATE_KEY_FORMAT,
        "fingerprint": fingerprint,
        "course": course.strip(),
        "encrypted_private_key_pem": private_pem.decode("ascii"),
    }
    certificate_path = root / certificate_name
    private_path = root / f"{stem}.pykim-private-key"
    certificate_path.write_text(json.dumps(certificate_document, ensure_ascii=False, indent=2), encoding="utf-8")
    private_path.write_text(json.dumps(private_document, ensure_ascii=False, indent=2), encoding="utf-8")
    if content is not None:
        authorization_path = root / "certificates" / certificate_name
        authorization_path.parent.mkdir(parents=True, exist_ok=True)
        authorization_path.write_text(
            "sha256:" + hashlib.sha256(certificate_path.read_bytes()).hexdigest() + "\n",
            encoding="ascii",
        )
    try:
        os.chmod(private_path, 0o600)
    except OSError:
        pass
    return certificate_path, private_path


def encrypt_payload(payload: dict[str, object], certificate_data: bytes) -> dict[str, object]:
    document = json.loads(certificate_data.decode("utf-8"))
    info = certificate_info(certificate_data)
    if document.get("format") == CERTIFICATE_FORMAT:
        public_key = serialization.load_der_public_key(
            _unb64(document["public_key"])
        )
    else:
        certificate = x509.load_pem_x509_certificate(
            document["certificate_pem"].encode("ascii")
        )
        public_key = certificate.public_key()
    header = {
        "format": SUBMISSION_FORMAT,
        "encryption": "RSA-OAEP-SHA256+AES-256-GCM",
        "key_id": info.fingerprint,
        "course": info.course,
    }
    content_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ciphertext = AESGCM(content_key).encrypt(nonce, _json_bytes(payload), _json_bytes(header))
    encrypted_key = public_key.encrypt(
        content_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return {**header, "encrypted_key": _b64(encrypted_key), "nonce": _b64(nonce), "ciphertext": _b64(ciphertext)}


def decrypt_payload(
    envelope: dict[str, object], private_key_data: bytes, password: str
) -> dict[str, object]:
    private_document = json.loads(private_key_data.decode("utf-8"))
    if private_document.get("format") != PRIVATE_KEY_FORMAT:
        raise ValueError("Die Datei ist kein unterstützter PyKIM-Lehrerschlüssel.")
    if envelope.get("format") != SUBMISSION_FORMAT:
        raise ValueError("Die Datei ist keine unterstützte PyKIM-Abgabe.")
    if envelope.get("key_id") != private_document.get("fingerprint"):
        raise ValueError(
            "Die Abgabe wurde nicht mit dem Zertifikat dieses Kurses verschlüsselt. "
            f"Erwarteter Fingerabdruck: {private_document.get('fingerprint', 'unbekannt')}; "
            f"verwendeter Fingerabdruck: {envelope.get('key_id', 'unbekannt')}."
        )
    key = serialization.load_pem_private_key(
        private_document["encrypted_private_key_pem"].encode("ascii"),
        password=password.encode("utf-8"),
    )
    content_key = key.decrypt(
        _unb64(str(envelope["encrypted_key"])),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    header = {name: envelope[name] for name in ("format", "encryption", "key_id", "course")}
    plaintext = AESGCM(content_key).decrypt(
        _unb64(str(envelope["nonce"])),
        _unb64(str(envelope["ciphertext"])),
        _json_bytes(header),
    )
    result = json.loads(plaintext.decode("utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Der entschlüsselte Inhalt ist ungültig.")
    return result
