import hashlib
import json
from pathlib import Path

import pytest
from packaging.requirements import Requirement

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


PROJECT = Path(__file__).parents[1]


def test_direct_project_and_build_dependencies_are_exactly_pinned():
    with (PROJECT / "pyproject.toml").open("rb") as source:
        configuration = tomllib.load(source)

    project = configuration["project"]
    dependencies = [
        *project["dependencies"],
        *project["optional-dependencies"]["test"],
        *project["optional-dependencies"]["build"],
    ]
    for raw in dependencies:
        specifiers = list(Requirement(raw).specifier)
        assert len(specifiers) == 1, raw
        assert specifiers[0].operator == "==", raw
    assert configuration["build-system"]["requires"] == ["setuptools==84.0.0"]


def test_python_support_matches_the_pinned_runtime_contract():
    from insi.runtime import MINIMUM_PYTHON

    with (PROJECT / "pyproject.toml").open("rb") as source:
        project = tomllib.load(source)["project"]
    workflow = (PROJECT / ".github/workflows/tests.yml").read_text(
        encoding="utf-8"
    )

    assert project["requires-python"] == ">=3.11"
    assert MINIMUM_PYTHON == (3, 11)
    assert 'python-version: ["3.11", "3.12", "3.13"]' in workflow
    assert '"3.10"' not in workflow


def test_build_bootstrap_uses_one_pinned_pip_version():
    requirement = (
        PROJECT / "requirements" / "build-bootstrap.txt"
    ).read_text(encoding="utf-8")
    entries = [
        line.strip()
        for line in requirement.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert entries == ["pip==26.2.1"]

    for relative in (
        ".github/workflows/tests.yml",
        ".github/workflows/build-desktop.yml",
        "tools/build_desktop_app.py",
        "tools/build_macos_app.py",
    ):
        source = (PROJECT / relative).read_text(encoding="utf-8")
        assert "build-bootstrap.txt" in source
        assert '"upgrade", "pip"' not in source


def test_pykim_version_is_pinned_across_install_and_build_paths():
    with (PROJECT / "pyproject.toml").open("rb") as source:
        dependencies = tomllib.load(source)["project"]["dependencies"]

    assert "PyKIM==0.6.0" in dependencies
    requirement = (
        PROJECT / "requirements" / "pykim-0.6.0.txt"
    ).read_text(encoding="utf-8")
    assert "PyKIM @ git+https://github.com/finalnode/PyKIM.git@" in requirement
    assert "7494db55a84e95b6dc13fc4a32a586b62fb5830d" in requirement
    assert "Pyxel==2.9.9" in requirement
    assert "PyYAML==6.0.3" in requirement
    assert "@main" not in requirement

    for relative in (
        "README.md",
        ".github/workflows/tests.yml",
        ".github/workflows/build-desktop.yml",
        "tools/build_desktop_app.py",
        "tools/build_macos_app.py",
        "tools/build_wheelhouse.py",
    ):
        source = (PROJECT / relative).read_text(encoding="utf-8")
        assert "pykim-0.6.0.txt" in source
        assert "PyKIM.git@main" not in source


def test_wheelhouse_reset_and_manifest_are_reproducible(tmp_path):
    from tools.build_wheelhouse import reset_wheelhouse, write_manifest

    output = tmp_path / "wheelhouse"
    output.mkdir()
    obsolete = output / "insi-0.6.0-py3-none-any.whl"
    obsolete.write_bytes(b"obsolete")
    preserved = output / "notes.txt"
    preserved.write_text("keep", encoding="utf-8")
    reset_wheelhouse(output)

    assert not obsolete.exists()
    assert preserved.is_file()

    wheel = output / "insi-0.7.0-py3-none-any.whl"
    wheel.write_bytes(b"current")
    requirement = tmp_path / "pykim.txt"
    requirement.write_text(
        "# fixed\nPyKIM @ git+https://example.invalid/PyKIM.git@abc123\n",
        encoding="utf-8",
    )
    manifest_path = write_manifest(output, requirement)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["format"] == 1
    assert manifest["requirements"] == [
        "PyKIM @ git+https://example.invalid/PyKIM.git@abc123"
    ]
    assert manifest["wheels"] == [
        {
            "distribution": "insi",
            "filename": wheel.name,
            "sha256": hashlib.sha256(b"current").hexdigest(),
            "size": len(b"current"),
            "version": "0.7.0",
        }
    ]


def test_wheelhouse_contains_only_the_course_runtime(monkeypatch, tmp_path):
    from tools.build_wheelhouse import main

    calls = []
    monkeypatch.setattr(
        "tools.build_wheelhouse.subprocess.run",
        lambda command, **options: calls.append((command, options)),
    )

    assert main(["--output", str(tmp_path / "wheelhouse")]) == 0
    assert len(calls) == 1
    command, options = calls[0]
    assert command[3:5] == ["wheel", "--wheel-dir"]
    assert "--requirement" in command
    assert str(PROJECT) not in command
    assert options == {"check": True}


def test_packaged_wheelhouse_is_located_and_verified(tmp_path):
    from tools.verify_packaged_wheelhouse import (
        packaged_wheelhouse,
        verified_requirements,
    )

    application = tmp_path / "insi"
    wheelhouse = application / "_internal" / "wheels"
    wheelhouse.mkdir(parents=True)
    wheel = wheelhouse / "PyKIM-0.6.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    manifest = {
        "format": 1,
        "requirements": [
            "PyKIM @ git+https://example.invalid/PyKIM.git@abc123",
            "PyYAML==6.0.3",
        ],
        "wheels": [
            {
                "distribution": "PyKIM",
                "filename": wheel.name,
                "sha256": hashlib.sha256(b"wheel").hexdigest(),
                "size": len(b"wheel"),
                "version": "0.6.0",
            }
        ],
    }
    (wheelhouse / "wheelhouse-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    assert packaged_wheelhouse(application) == wheelhouse
    assert verified_requirements(wheelhouse) == ("PyKIM==0.6.0", "PyYAML==6.0.3")


def test_packaged_wheelhouse_rejects_tampering(tmp_path):
    from tools.verify_packaged_wheelhouse import verified_requirements

    wheelhouse = tmp_path / "wheels"
    wheelhouse.mkdir()
    wheel = wheelhouse / "demo-1.0-py3-none-any.whl"
    wheel.write_bytes(b"tampered")
    (wheelhouse / "wheelhouse-manifest.json").write_text(
        json.dumps(
            {
                "format": 1,
                "requirements": ["demo==1.0"],
                "wheels": [
                    {
                        "distribution": "demo",
                        "filename": wheel.name,
                        "sha256": hashlib.sha256(b"original").hexdigest(),
                        "size": len(b"tampered"),
                        "version": "1.0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Prüfsumme"):
        verified_requirements(wheelhouse)


def test_test_extra_contains_collection_time_dependencies():
    with (PROJECT / "pyproject.toml").open("rb") as source:
        project = tomllib.load(source)["project"]
    dependencies = [
        *project["dependencies"],
        *project["optional-dependencies"]["test"],
    ]

    assert any(dependency.startswith("cryptography") for dependency in dependencies)
    assert any(dependency.startswith("Send2Trash") for dependency in dependencies)


def test_windows_build_pins_compatible_pythonnet():
    with (PROJECT / "pyproject.toml").open("rb") as source:
        dependencies = tomllib.load(source)["project"]["optional-dependencies"]["build"]

    assert "pythonnet==3.0.5; sys_platform == 'win32'" in dependencies


def test_desktop_workflow_covers_all_release_targets():
    workflow = (PROJECT / ".github/workflows/build-desktop.yml").read_text(
        encoding="utf-8"
    )

    for expected in (
        "windows-2025",
        "ubuntu-24.04",
        "macos-15-intel",
        "runner: macos-15",
        "tools/build_desktop_app.py",
        "tools/check_windows_desktop.ps1",
        "tools/check_windows_sandbox.py",
        "tools/check_linux_sandbox.py",
        "tools/check_macos_sandbox.py",
        "tools/build_macos_dmg.py --rebuild-app",
        "tools/check_release_version.py",
        "gh release upload",
        'dist/windows/insi/insi-python.exe',
        'dist/macos/insi.app/Contents/MacOS/insi-python',
        "bubblewrap",
    ):
        assert expected in workflow


def test_ci_runs_the_separate_nicegui_e2e_suite():
    workflow = (PROJECT / ".github/workflows/tests.yml").read_text(encoding="utf-8")

    assert "NiceGUI E2E" in workflow
    assert "python -m pytest -m e2e" in workflow


def test_pyinstaller_specs_are_valid_python_and_use_common_entrypoint():
    for relative in (
        "packaging/desktop/insi.spec",
        "packaging/macos/insi.spec",
    ):
        path = PROJECT / relative
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        assert 'packaging" / "app_entry.py' in source
        assert "copy_metadata" in source
        assert '"insi"' in source
        assert '"nicegui"' in source
        assert '"pywebview"' in source
        assert 'project / "LICENSE"' in source
        assert 'project / "LICENSING.md"' in source
        assert 'THIRD_PARTY_NOTICES.md' in source
        assert 'DATENSCHUTZ.md' in source
        assert 'project / "README.en.md"' in source
        assert 'project / "docs"' in source
        assert "desktop-build-manifest.json" in source


def test_packaging_infrastructure_uses_insi_names():
    assert not (PROJECT / "packaging/desktop/PyKIM.spec").exists()
    assert not (PROJECT / "packaging/macos/PyKIM.spec").exists()
    assert (PROJECT / "packaging/desktop/insi.spec").is_file()
    assert (PROJECT / "packaging/macos/insi.spec").is_file()

    sources = {
        relative: (PROJECT / relative).read_text(encoding="utf-8")
        for relative in (
            ".github/workflows/build-desktop.yml",
            "packaging/app_entry.py",
            "tools/build_desktop_app.py",
            "tools/build_macos_app.py",
            "tools/check_linux_sandbox.py",
            "tools/check_macos_sandbox.py",
            "tools/check_windows_sandbox.py",
        )
    }
    for source in sources.values():
        assert "PyKIM.spec" not in source
        assert "--pykim-python" not in source
        assert "PYKIM_DESKTOP_BUILD_ENV" not in source
        assert "PYKIM_MACOS_BUILD_ENV" not in source
    assert "INSI_DESKTOP_BUILD_ENV" in sources["tools/build_desktop_app.py"]
    assert "INSI_MACOS_BUILD_ENV" in sources["tools/build_macos_app.py"]
    assert "--insi-python" in sources["packaging/app_entry.py"]


def test_visual_markdown_editor_assets_are_declared_as_package_data():
    with (PROJECT / "pyproject.toml").open("rb") as source:
        setuptools = tomllib.load(source)["tool"]["setuptools"]
    package_data = setuptools["package-data"]["insi"]

    assert "markdown_editor.js" in package_data
    assert "vendor/toastui_editor/*.js" in package_data
    assert "vendor/toastui_editor/*.css" in package_data
    assert "vendor/toastui_editor/*.txt" in package_data
    assert "LICENSE" in setuptools["license-files"]
    assert "LICENSING.md" in setuptools["license-files"]
    assert "THIRD_PARTY_NOTICES.md" in setuptools["license-files"]
    assert "share/insi/documentation/de" in setuptools["data-files"]
    assert "share/insi/documentation/en" in setuptools["data-files"]


def test_runtime_license_audit_is_strict_and_platform_aware():
    source = (PROJECT / "tools/audit_runtime_licenses.py").read_text(
        encoding="utf-8"
    )

    assert "License-Expression" in source
    assert 'Requirement("pywebview[gtk]")' in source
    assert 'Requirement("pythonnet")' in source
    assert '"--strict"' in source
    assert '"--manifest"' in source

    entrypoint = (PROJECT / "packaging/app_entry.py").read_text(encoding="utf-8")
    assert "from insi.app import main" in entrypoint


def test_build_manifest_records_resolved_versions_without_local_paths(tmp_path):
    from tools.audit_runtime_licenses import write_build_manifest

    target = write_build_manifest(tmp_path / "desktop-build-manifest.json")
    serialized = target.read_text(encoding="utf-8")
    manifest = json.loads(serialized)
    packages = {
        item["name"].casefold(): item
        for item in manifest["packages"]
    }

    assert manifest["format"] == 1
    assert manifest["python"]
    assert manifest["platform"]
    assert packages["pykim"]["version"] == "0.6.0"
    assert packages["pykim"]["source"]["commit"] == (
        "7494db55a84e95b6dc13fc4a32a586b62fb5830d"
    )
    assert str(PROJECT) not in serialized


def test_desktop_brand_uses_safe_technical_names_and_visible_display_name():
    desktop = (PROJECT / "packaging/desktop/insi.spec").read_text(
        encoding="utf-8"
    )
    macos = (PROJECT / "packaging/macos/insi.spec").read_text(
        encoding="utf-8"
    )

    assert 'name="insi"' in desktop
    assert 'name="insi-python"' in desktop
    assert 'name="insi.app"' in macos
    assert '"CFBundleDisplayName": "in:si"' in macos
    assert 'bundle_identifier="de.simplicissima.insi"' in macos


def test_macos_build_removes_extended_attributes_and_verifies_adhoc_signature():
    app_source = (PROJECT / "tools/build_macos_app.py").read_text(encoding="utf-8")
    dmg_source = (PROJECT / "tools/build_macos_dmg.py").read_text(encoding="utf-8")

    assert '["xattr", "-cr", str(application)]' in app_source
    assert 'TemporaryDirectory(prefix="insi-macos-sign-")' in app_source
    assert '"codesign", "--verify", "--deep", "--strict"' in app_source
    assert "Der lokale .app-Ordner ist deshalb" in app_source
    assert "apply_adhoc_signature(staging / application.name)" in dmg_source
    assert '"audit_runtime_licenses.py"' in app_source


def test_windows_and_linux_builds_run_strict_license_audit():
    source = (PROJECT / "tools/build_desktop_app.py").read_text(encoding="utf-8")

    assert '"audit_runtime_licenses.py"' in source
    assert '"--strict"' in source
