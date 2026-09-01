from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


PROJECT = Path(__file__).parents[1]


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
        "tools/check_windows_network_start.ps1",
        "tools/check_linux_sandbox.py",
        "tools/check_macos_sandbox.py",
        "tools/build_macos_dmg.py --rebuild-app",
        "tools/check_release_version.py",
        "gh release upload",
        'dist/windows/insi/insi.exe',
        'dist/macos/insi.app/Contents/MacOS/insi-python',
        "bubblewrap",
    ):
        assert expected in workflow


def test_pyinstaller_specs_are_valid_python_and_use_common_entrypoint():
    for relative in (
        "packaging/desktop/PyKIM.spec",
        "packaging/macos/PyKIM.spec",
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

    entrypoint = (PROJECT / "packaging/app_entry.py").read_text(encoding="utf-8")
    assert "from insi.app import main" in entrypoint


def test_desktop_brand_uses_safe_technical_names_and_visible_display_name():
    desktop = (PROJECT / "packaging/desktop/PyKIM.spec").read_text(
        encoding="utf-8"
    )
    macos = (PROJECT / "packaging/macos/PyKIM.spec").read_text(
        encoding="utf-8"
    )

    assert 'name="insi"' in desktop
    assert 'if system == "Windows"' in desktop
    assert "analysis.binaries" in desktop
    assert "analysis.datas" in desktop
    assert 'name="insi.app"' in macos
    assert '"CFBundleDisplayName": "in:si"' in macos
    assert 'bundle_identifier="de.simplicissima.insi"' in macos


def test_windows_build_uses_one_executable_for_app_and_internal_python():
    workflow = (PROJECT / ".github/workflows/build-desktop.yml").read_text(
        encoding="utf-8"
    )

    assert "tools/run_packaged_python.py dist/windows/insi/insi.exe" in workflow
    assert "run_packaged_python.py dist/windows/insi/insi-python.exe" not in workflow
    assert "Einzelnen Windows-Starter prüfen" in workflow
    assert "Windows-Netzlaufwerk, Staging und Rücksynchronisierung prüfen" in workflow

    entrypoint = (PROJECT / "packaging/app_entry.py").read_text(encoding="utf-8")
    assert "relaunch_frozen_windows_application()" in entrypoint
    assert "complete_onefile_bootstrap()" in entrypoint
    network_check = (PROJECT / "tools/check_windows_network_start.ps1").read_text(
        encoding="utf-8"
    )
    assert "tools/check_windows_network_sandbox.py" in network_check
    assert "New-SmbShare" in network_check
    build_script = (PROJECT / "tools/build_desktop_app.py").read_text(
        encoding="utf-8"
    )
    assert 'onefile = destination / "insi.exe"' in build_script
    assert "onefile.replace(application / onefile.name)" in build_script


def test_desktop_build_identity_covers_the_complete_distribution(tmp_path):
    from tools.build_desktop_app import write_application_identity

    application = tmp_path / "insi"
    internal = application / "_internal"
    internal.mkdir(parents=True)
    (application / "insi.exe").write_bytes(b"unchanged-launcher")
    library = internal / "library.zip"
    library.write_bytes(b"first-runtime")

    first = write_application_identity(application)
    library.write_bytes(b"second-runtime")
    second = write_application_identity(application)

    assert first != second
    assert (application / ".insi-build-id").read_text(encoding="ascii") == second


def test_packaged_python_checker_waits_and_returns_child_status(
    monkeypatch, tmp_path, capsys
):
    from tools import run_packaged_python

    runner = tmp_path / "insi.exe"
    runner.touch()
    calls = []

    class Completed:
        returncode = 7

    def run(command, **options):
        options["stdout"].write(b"ok\ninvalid:\xfc\n")
        options["stderr"].write(b"warn\n")
        calls.append((command, options))
        return Completed()

    monkeypatch.setattr(run_packaged_python.subprocess, "run", run)

    assert run_packaged_python.run(runner, ["-c", "print('ok')"]) == 7
    command, options = calls[0]
    assert command == [str(runner), "--pykim-python", "-c", "print('ok')"]
    assert options["check"] is False
    assert options["timeout"] == 180
    assert options["stdout"] is not options["stderr"]
    assert capsys.readouterr() == ("ok\ninvalid:\\xfc\n", "warn\n")


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
