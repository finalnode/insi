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
        "tools/build_macos_dmg.py --rebuild-app",
        "tools/check_release_version.py",
        "gh release upload",
        'dist/windows/insi/insi-python.exe',
        'dist/macos/insi.app/Contents/MacOS/insi-python',
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
    assert 'name="insi-python"' in desktop
    assert 'name="insi.app"' in macos
    assert '"CFBundleDisplayName": "in:si"' in macos
    assert 'bundle_identifier="de.simplicissima.insi"' in macos
