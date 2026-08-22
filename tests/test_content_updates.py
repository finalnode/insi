"""Verträge für App-, Inhalts- und zertifikatsgebundene Updates."""

import hashlib
import io
import json
import zipfile
from urllib.error import HTTPError

import pytest

from insi.library import (
    PACKAGED_CONTENT_ROOT,
    script_chapters,
    script_code_examples,
    task_document,
)
from insi.submission.crypto import ContentConfiguration
from insi.system import github_version
from insi.updates import (
    active_content_root,
    check_app_update,
    check_content_update,
    check_updates,
    format_content_version,
    install_content_update,
    sync_certificate_content,
    verify_certificate_authorization,
    verify_certificate_trainers,
)


def test_content_overlay_can_replace_scripts_without_touching_packaged_files(
    tmp_path, monkeypatch
):
    overlay = tmp_path / "overlay"
    chapter = overlay / "Skripte" / "imperativ" / "00_neu.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("# Aktualisiertes Kapitel\n", encoding="utf-8")
    nested = overlay / "Skripte" / "imperativ" / "unterricht" / "01_mehr.md"
    nested.parent.mkdir()
    nested.write_text("# Weiteres Kapitel\n", encoding="utf-8")
    hidden = overlay / "Skripte" / "imperativ" / "_entwuerfe" / "alt.md"
    hidden.parent.mkdir()
    hidden.write_text("# Unsichtbar\n", encoding="utf-8")
    (overlay / "Skripte" / "imperativ" / "README.md").write_text(
        "# Repository-Dokumentation\n", encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONTENT_DIR", str(overlay))

    assert active_content_root(PACKAGED_CONTENT_ROOT) == overlay
    assert [item.title for item in script_chapters("imperativ")] == [
        "Aktualisiertes Kapitel",
        "Weiteres Kapitel",
    ]


def test_bundled_content_manifest_matches_all_markdown_files():
    manifest = json.loads(
        (PACKAGED_CONTENT_ROOT / "content-manifest.json").read_text(encoding="utf-8")
    )
    expected = manifest["files"]
    actual = {
        path.relative_to(PACKAGED_CONTENT_ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for folder, pattern in (
            ("Skripte", "*.md"),
            ("Aufgaben", "*.md"),
            ("Trainer", "*.yml"),
        )
        for path in (PACKAGED_CONTENT_ROOT / folder).rglob(pattern)
    }

    assert expected == actual


def test_content_update_is_hash_checked_and_activated_atomically(tmp_path, monkeypatch):
    source = io.BytesIO()
    content = b"# Neues Kapitel\n"
    with zipfile.ZipFile(source, "w") as bundle:
        bundle.writestr("Skripte/imperativ/01_neu.md", content)
    archive = source.getvalue()
    manifest = {
        "content_version": "2099.1",
        "package_url": "https://example.invalid/content.zip",
        "package_sha256": hashlib.sha256(archive).hexdigest(),
        "files": {
            "Skripte/imperativ/01_neu.md": hashlib.sha256(content).hexdigest()
        },
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return archive

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.updates.urlopen", lambda request, timeout: Response())

    installed = install_content_update(manifest)

    assert (installed / "Skripte/imperativ/01_neu.md").read_bytes() == content
    assert active_content_root(PACKAGED_CONTENT_ROOT) == installed


def test_content_update_rejects_changed_archive(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b"manipuliert"

    monkeypatch.setattr("insi.updates.urlopen", lambda request, timeout: Response())
    with pytest.raises(ValueError, match="Prüfsumme"):
        install_content_update(
            {
                "content_version": "2099.2",
                "package_url": "https://example.invalid/content.zip",
                "package_sha256": "0" * 64,
                "files": {"Skripte/imperativ/x.md": "0" * 64},
            }
        )


def test_content_update_falls_back_to_hash_checked_raw_files(tmp_path, monkeypatch):
    content = b"# Fallback-Kapitel\n"
    name = "Skripte/imperativ/01_fallback.md"
    manifest = {
        "content_version": "2099.3",
        "package_url": "https://example.invalid/content.zip",
        "package_sha256": "0" * 64,
        "files": {name: hashlib.sha256(content).hexdigest()},
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return content

    def open_with_failed_archive(request, timeout):
        if request.full_url == manifest["package_url"]:
            raise ConnectionResetError("release server closed the connection")
        assert request.full_url.endswith(name)
        return Response()

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.updates.urlopen", open_with_failed_archive)

    installed = install_content_update(manifest)

    assert (installed / name).read_bytes() == content


def test_damaged_active_content_falls_back_to_packaged_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    version = "2099.3"
    root = tmp_path / "config" / "content" / "versions" / version
    chapter = root / "Skripte" / "imperativ" / "x.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("beschädigt", encoding="utf-8")
    (root / "content-manifest.json").write_text(
        json.dumps(
            {
                "content_version": version,
                "files": {"Skripte/imperativ/x.md": "0" * 64},
            }
        ),
        encoding="utf-8",
    )
    marker = tmp_path / "config" / "content" / "active.json"
    marker.write_text(json.dumps({"content_version": version}), encoding="utf-8")

    assert active_content_root(PACKAGED_CONTENT_ROOT) == PACKAGED_CONTENT_ROOT
    assert task_document("quadrat-5").paradigm == "imperativ"
    assert task_document("musik-pixel-klasse").paradigm == "oop"
    assert len(script_code_examples()) >= 50


def test_github_version_reads_remote_pyproject(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'[project]\nname = "PyKIM"\nversion = "9.9.9"\n'

    monkeypatch.setattr("insi.system.urlopen", lambda request, timeout: Response())

    info = github_version()

    assert info["github"] == "9.9.9"
    assert info["different"]


def test_release_update_selects_matching_macos_architecture(monkeypatch):
    monkeypatch.setattr("insi.updates.platform.machine", lambda: "x86_64")
    monkeypatch.setattr(
        "insi.updates._json_url",
        lambda url, timeout: {
            "tag_name": "v9.9.9",
            "html_url": "https://example.invalid/release",
            "assets": [
                {
                    "name": "insi-9.9.9-macos-arm64.dmg",
                    "browser_download_url": "https://example.invalid/arm.dmg",
                },
                {
                    "name": "insi-9.9.9-macos-x86_64.dmg",
                    "browser_download_url": "https://example.invalid/intel.dmg",
                },
            ],
        },
    )

    update = check_app_update()

    assert update.newer
    assert update.download_url.endswith("intel.dmg")


def test_content_update_compares_bundled_manifest(tmp_path, monkeypatch):
    packaged = tmp_path / "guide"
    packaged.mkdir()
    (packaged / "content-manifest.json").write_text(
        json.dumps({"content_version": "2026.08.1"}), encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url",
        lambda url, timeout: {
            "content_version": "2026.08.2",
            "minimum_app_version": "0.2.0",
        },
    )

    update = check_content_update(packaged)

    assert update.installed == "2026.08.1"
    assert update.newer
    assert update.compatible


def test_content_version_is_displayed_as_german_date():
    assert format_content_version("2026.08.1") == "01.08.2026"
    assert format_content_version("commit-abc") == "commit-abc"


def repository_api(revision, files):
    """Erzeuge Commit- und Git-Baum-Antworten für Synchronisationstests."""

    def response(url, _timeout):
        if "/commits/" in url:
            return {"sha": revision() if callable(revision) else revision}
        if "/git/trees/" in url:
            return {
                "truncated": False,
                "tree": [
                    {"path": name, "type": "blob"}
                    for name in files
                ],
            }
        raise AssertionError(f"Unerwartete API-URL: {url}")

    return response


def test_certificate_content_sync_downloads_individual_hashed_files(
    tmp_path, monkeypatch
):
    files = {
        "Skripte/imperativ/01_start.md": b"# Start\n",
        "Skripte/_backup/00_alt.md": b"# Alt\n",
        "Skripte/imperativ/_entwurf.md": b"# Entwurf\n",
        "Aufgaben/imperativ/quadrat-5.md": b"# Quadrat\n",
        "Trainer/quadrat-5.yml": (
            b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
            b"  - type: square\n    start: [50, 50]\n    side: 5\n"
        ),
    }
    index = {
        "format": 1,
        "scope": "trainer",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in files.items()
            if name.startswith("Trainer/")
        },
    }
    revision = "a" * 40
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.updates._json_url", repository_api(revision, files))

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("insi.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )

    target = sync_certificate_content(configuration)

    assert target.name == revision
    assert (target / "Skripte/imperativ/01_start.md").read_bytes() == files[
        "Skripte/imperativ/01_start.md"
    ]
    assert not (target / "Skripte/_backup/00_alt.md").exists()
    assert not (target / "Skripte/imperativ/_entwurf.md").exists()
    assert not (target / "content.yml").exists()
    assert active_content_root(PACKAGED_CONTENT_ROOT) == target


def test_certificate_authorization_uses_same_named_repository_hash(monkeypatch):
    certificate = b'{"format":"test-certificate"}'
    expected = hashlib.sha256(certificate).hexdigest()
    requested = []
    monkeypatch.setattr(
        "insi.updates._download",
        lambda url, _timeout: requested.append(url)
        or f"sha256:{expected}\n".encode("ascii"),
    )
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
        "python-11a.pykim-cert",
    )

    result = verify_certificate_authorization(certificate, configuration)

    assert result.checked_online
    assert requested == [
        "https://raw.githubusercontent.com/finalnode/PyKIM_Kurs/main/"
        "certificates/python-11a.pykim-cert"
    ]


def test_certificate_authorization_rejects_unlisted_certificate(monkeypatch):
    monkeypatch.setattr(
        "insi.updates._download",
        lambda *_args: b"sha256:" + b"0" * 64,
    )
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
        "python-11a.pykim-cert",
    )

    with pytest.raises(ValueError, match="nicht zugelassen"):
        verify_certificate_authorization(b"anderes Zertifikat", configuration)


def test_trainer_verification_ignores_remote_assignment_only_changes(
    tmp_path, monkeypatch
):
    files = {
        "Skripte/imperativ/01_start.md": b"# Start\n",
        "Aufgaben/imperativ/quadrat-5.md": b"# Alte Aufgabe\n",
        "Trainer/quadrat-5.yml": (
            b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
            b"  - type: square\n    start: [50, 50]\n    side: 5\n"
        ),
    }
    index = {
        "format": 1,
        "scope": "trainer",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in files.items()
            if name.startswith("Trainer/")
        },
    }
    revision = "b" * 40
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.updates._json_url", repository_api(revision, files))

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("insi.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )
    sync_certificate_content(configuration)

    files["Aufgaben/imperativ/quadrat-5.md"] = b"# Neue Aufgabenformulierung\n"
    result = verify_certificate_trainers(configuration)

    assert result.checked_online
    assert not result.updated


def test_trainer_verification_replaces_changed_trainer_data(tmp_path, monkeypatch):
    old_trainer = (
        b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
        b"  - type: square\n    start: [50, 50]\n    side: 5\n"
    )
    new_trainer = old_trainer.replace(b"side: 5", b"side: 6")
    files = {
        "Skripte/imperativ/01_start.md": b"# Start\n",
        "Aufgaben/imperativ/quadrat-5.md": b"# Quadrat\n",
        "Trainer/quadrat-5.yml": old_trainer,
    }

    def index():
        return {
            "format": 1,
            "scope": "trainer",
            "files": {
                name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
                for name, data in files.items()
                if name.startswith("Trainer/")
            },
        }

    revisions = iter(("c" * 40, "d" * 40))
    current_revision = [next(revisions)]
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url",
        repository_api(lambda: current_revision[0], files),
    )

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index()).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("insi.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )
    sync_certificate_content(configuration)

    files["Trainer/quadrat-5.yml"] = new_trainer
    current_revision[0] = next(revisions)
    result = verify_certificate_trainers(configuration)

    assert result.checked_online
    assert result.updated
    assert (
        active_content_root(PACKAGED_CONTENT_ROOT) / "Trainer/quadrat-5.yml"
    ).read_bytes() == new_trainer


def test_missing_first_release_is_treated_as_current(tmp_path, monkeypatch):
    packaged = tmp_path / "guide"
    packaged.mkdir()
    (packaged / "content-manifest.json").write_text(
        json.dumps({"content_version": "2026.08.1"}), encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url",
        lambda url, timeout: (_ for _ in ()).throw(
            HTTPError(url, 404, "Not Found", None, None)
        ),
    )

    status = check_updates(packaged)

    assert status.error == ""
    assert status.app is not None and not status.app.newer
    assert status.content is not None and not status.content.newer
