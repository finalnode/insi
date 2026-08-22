import hashlib
import io
import subprocess
import zipfile
from pathlib import Path

import pytest

from insi.course_archive import (
    build_course_archive,
    parse_course_archive,
)
from insi.course_storage import (
    course_offline_wheelhouse,
    install_course_runtime,
    installed_course_runtime,
)
from insi.course_builder_view import create_portable_course, ensure_course_source
from insi.course_runtime import (
    RUNTIME_FILENAME,
    RUNTIME_PYTHON,
    RuntimeManifest,
    download_offline_wheels,
    manifest_with_wheels,
    parse_runtime_manifest,
    parse_runtime_requirements,
    runtime_manifest_bytes,
)
from insi.runtime import (
    RuntimeCandidate,
    RuntimePackageCheck,
    _suite_packages,
    course_runtime_preflight,
    managed_runtime_path,
)


def course_source(tmp_path: Path) -> Path:
    source = ensure_course_source(tmp_path / "Kurs")
    (source / "Skripte" / "start.md").write_text("# Start\n", encoding="utf-8")
    return source


def test_suite_package_inventory_is_cached(monkeypatch):
    calls = []

    class Distribution:
        metadata = {"Name": "Demo"}

    monkeypatch.setattr(
        "insi.runtime.importlib.metadata.distributions",
        lambda: calls.append(True) or (Distribution(),),
    )
    _suite_packages.cache_clear()
    try:
        assert _suite_packages() == ("Demo",)
        assert _suite_packages() == ("Demo",)
        assert calls == [True]
    finally:
        _suite_packages.cache_clear()


def test_runtime_manifest_accepts_only_exact_versions_and_roundtrips():
    requirements = parse_runtime_requirements("Demo_Paket==1.2.3\nrequests==2.32.5\n")
    manifest = RuntimeManifest(RUNTIME_PYTHON, requirements)

    assert parse_runtime_manifest(runtime_manifest_bytes(manifest)) == manifest
    with pytest.raises(ValueError, match="nicht exakt"):
        parse_runtime_requirements("requests>=2")
    with pytest.raises(ValueError, match="mehrere Versionen"):
        parse_runtime_requirements(("requests==2.32.4", "requests==2.32.5"))
    incompatible = runtime_manifest_bytes(
        RuntimeManifest(
            "3.12",
            requirements,
            ("windows-x86_64-python311",),
        )
    )
    with pytest.raises(ValueError, match="passen nicht zusammen"):
        parse_runtime_manifest(incompatible)


def test_standard_course_export_stays_small_and_writes_runtime_contract(tmp_path):
    source = course_source(tmp_path)

    _, archive = create_portable_course(
        source,
        teacher="Ada",
        school="Beispielschule",
        course="Kompakter Kurs",
        runtime_python="3.12",
        runtime_requirements="DemoTrainer==1.2.3\nrequests==2.32.5",
    )

    bundle = parse_course_archive(archive.read_bytes())
    source_runtime = parse_runtime_manifest(source / RUNTIME_FILENAME)
    assert archive.stat().st_size < 1024 * 1024
    assert bundle.runtime == source_runtime
    assert bundle.runtime is not None
    assert bundle.runtime.python == "3.12"
    assert bundle.runtime.offline_targets == ()
    assert bundle.runtime.hashes == {}
    assert bundle.runtime.requirements == (
        "DemoTrainer==1.2.3",
        "requests==2.32.5",
    )


def test_offline_export_is_opt_in_and_keeps_source_manifest_compact(
    tmp_path, monkeypatch
):
    source = course_source(tmp_path)
    targets = ("windows-x86_64-python311", "linux-x86_64-python311")

    def fake_download(requirements, selected, destination, **_kwargs):
        assert requirements == ("demo==1.2.3",)
        assert selected == targets
        result = {}
        for target in selected:
            wheel = Path(destination) / target / "demo-1.2.3-py3-none-any.whl"
            wheel.parent.mkdir(parents=True)
            wheel.write_bytes(f"wheel for {target}".encode())
            result[f"wheelhouse/{target}/{wheel.name}"] = wheel
        return result

    monkeypatch.setattr(
        "insi.course_builder_view.download_offline_wheels", fake_download
    )
    _, archive = create_portable_course(
        source,
        teacher="Ada",
        school="Beispielschule",
        course="Offlinekurs",
        runtime_python=RUNTIME_PYTHON,
        runtime_requirements="demo==1.2.3",
        include_offline_packages=True,
        offline_targets=targets,
    )

    bundle = parse_course_archive(archive.read_bytes())
    assert bundle.runtime is not None
    assert bundle.runtime.offline_targets == targets
    assert set(bundle.offline_wheels) == set(bundle.runtime.hashes)
    source_runtime = parse_runtime_manifest(source / RUNTIME_FILENAME)
    assert source_runtime.offline_targets == ()
    assert source_runtime.hashes == {}


def test_offline_export_requires_explicit_package_and_target(tmp_path):
    source = course_source(tmp_path)
    common = {
        "teacher": "Ada",
        "school": "Beispielschule",
        "course": "Offlinekurs",
        "runtime_python": RUNTIME_PYTHON,
        "include_offline_packages": True,
    }
    with pytest.raises(ValueError, match="Kurspaket"):
        create_portable_course(
            source,
            runtime_requirements=(),
            offline_targets=("windows-x86_64-python311",),
            **common,
        )
    with pytest.raises(ValueError, match="Zielplattform"):
        create_portable_course(
            source,
            runtime_requirements="demo==1.2.3",
            **common,
        )


def test_pip_download_uses_selected_python311_platform(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        destination = Path(command[command.index("--dest") + 1])
        (destination / "demo-1.2.3-py3-none-any.whl").write_bytes(b"wheel")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("insi.course_runtime.subprocess.run", fake_run)
    wheels = download_offline_wheels(
        ("demo==1.2.3",),
        ("windows-x86_64-python311",),
        tmp_path,
        python=Path("/usr/bin/python3"),
    )

    command = calls[0][0]
    assert command[command.index("--platform") + 1] == "win_amd64"
    assert command[command.index("--python-version") + 1] == "311"
    assert "--only-binary=:all:" in command
    assert "--constraint" not in command
    assert command[-1] == "demo==1.2.3"
    assert set(wheels) == {
        "wheelhouse/windows-x86_64-python311/demo-1.2.3-py3-none-any.whl"
    }


def test_archive_rejects_a_tampered_offline_wheel(tmp_path):
    source = course_source(tmp_path)
    from insi.course_setup import generate_course_setup

    setup = generate_course_setup(
        source, teacher="Ada", school="Schule", course="Manipulationstest"
    )
    target = "windows-x86_64-python311"
    wheel = tmp_path / "demo-1.2.3-py3-none-any.whl"
    wheel.write_bytes(b"original")
    name = f"wheelhouse/{target}/{wheel.name}"
    manifest = manifest_with_wheels(
        RUNTIME_PYTHON,
        ("PyKIM==0.6.0", "pyxel==2.9.9", "demo==1.2.3"),
        (target,),
        {name: wheel},
    )
    original = build_course_archive(
        source,
        setup,
        runtime_manifest=runtime_manifest_bytes(manifest),
        offline_wheels={name: wheel},
    )
    changed = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as source_zip, zipfile.ZipFile(
        changed, "w", compression=zipfile.ZIP_DEFLATED
    ) as output:
        for member in source_zip.infolist():
            data = b"changed" if member.filename == name else source_zip.read(member)
            output.writestr(member, data)

    with pytest.raises(ValueError, match="Prüfsumme"):
        parse_course_archive(changed.getvalue())


def test_installed_offline_runtime_is_versioned_and_used_by_pip(tmp_path, monkeypatch):
    course = tmp_path / "course"
    target = "windows-x86_64-python311"
    wheel_name = f"wheelhouse/{target}/demo-1.2.3-py3-none-any.whl"
    wheel_data = b"course wheel"
    manifest = RuntimeManifest(
        RUNTIME_PYTHON,
        ("PyKIM==0.6.0", "pyxel==2.9.9", "demo==1.2.3"),
        (target,),
        ((wheel_name, hashlib.sha256(wheel_data).hexdigest()),),
    )
    root = install_course_runtime(
        runtime_manifest_bytes(manifest),
        course,
        revision="archive-test",
        offline_wheels={wheel_name: wheel_data},
    )
    app_wheels = tmp_path / "app-wheels"
    app_wheels.mkdir()
    (app_wheels / "PyKIM-0.6.0-py3-none-any.whl").write_bytes(b"app")
    python = tmp_path / "python"
    python.write_bytes(b"")
    calls = []
    monkeypatch.setattr("insi.course_storage.current_runtime_target", lambda: target)
    monkeypatch.setattr("insi.course_runtime.current_runtime_target", lambda: target)
    monkeypatch.setattr("insi.runtime.bundled_wheelhouse", lambda: app_wheels)
    monkeypatch.setattr(
        "insi.runtime.subprocess.run",
        lambda command, **kwargs: calls.append((command, kwargs))
        or subprocess.CompletedProcess(command, 0, "", ""),
    )

    from insi.runtime import _install_runtime_packages

    _install_runtime_packages(python, course=course)
    command = calls[0][0]
    assert installed_course_runtime(course) == (manifest, root)
    assert course_offline_wheelhouse(course, target) == root / "wheelhouse" / target
    assert "--no-index" in command
    assert command.count("--find-links") == 2
    assert "pyxel==2.9.9" in command
    assert "demo==1.2.3" in command
    assert "PyKIM==0.6.0" in command
    (root / "wheelhouse" / target / "demo-1.2.3-py3-none-any.whl").write_bytes(
        b"tampered"
    )
    with pytest.raises(RuntimeError, match="Prüfsummen"):
        course_offline_wheelhouse(course, target)


def test_repository_runtime_activation_replaces_and_clears_contract(tmp_path):
    from insi.course_setup import _activate_repository_runtime

    course = tmp_path / "course"
    content = tmp_path / ("a" * 40)
    content.mkdir()
    manifest = RuntimeManifest(
        RUNTIME_PYTHON,
        ("PyKIM==0.6.0", "pyxel==2.9.9"),
    )
    (content / RUNTIME_FILENAME).write_bytes(runtime_manifest_bytes(manifest))

    _activate_repository_runtime(content, course)
    assert installed_course_runtime(course)[0] == manifest
    (content / RUNTIME_FILENAME).unlink()
    _activate_repository_runtime(content, course)
    assert installed_course_runtime(course) is None


def test_course_preflight_accepts_exact_python_and_package_versions(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    manifest = RuntimeManifest(
        "3.11",
        ("PyKIM==0.6.0", "pyxel==2.9.9"),
    )
    install_course_runtime(
        runtime_manifest_bytes(manifest), course, revision="ready"
    )
    python = tmp_path / "python311"
    python.write_bytes(b"")
    candidate = RuntimeCandidate(
        str(python), "3.11.9", "Test", True, ("PyKIM", "Pyxel")
    )
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda _candidate, requirements: tuple(
            RuntimePackageCheck(item, item.split("==", 1)[1], True)
            for item in requirements
        ),
    )

    report = course_runtime_preflight(course, candidates=(candidate,))

    assert report.ready
    assert report.candidate == candidate
    assert report.required_python == "3.11"
    assert all(package.ready for package in report.packages)
    assert not report.issues


def test_course_preflight_reuses_discovered_preferred_runtime(tmp_path, monkeypatch):
    from insi.course import set_runtime_preference

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    python = tmp_path / "python"
    python.write_bytes(b"")
    set_runtime_preference(python)
    candidate = RuntimeCandidate(
        str(python.resolve()), "3.13.1", "System", True, ("PyKIM", "Pyxel")
    )
    monkeypatch.setattr(
        "insi.runtime.inspect_runtime",
        lambda *_args: pytest.fail("bevorzugte Runtime wurde doppelt geprüft"),
    )
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda _candidate, requirements: tuple(
            RuntimePackageCheck(item, item.split("==", 1)[1], True)
            for item in requirements
        ),
    )

    report = course_runtime_preflight(course, candidates=(candidate,))

    assert report.ready
    assert report.candidate is candidate


def test_course_preflight_accepts_manifest_without_standard_training_engine(
    tmp_path, monkeypatch
):
    """Das Runtime-Modell darf Kurse nicht implizit an PyKIM koppeln."""
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    manifest = RuntimeManifest("3.11", ("DemoTrainer==1.2.3",))
    install_course_runtime(runtime_manifest_bytes(manifest), course, revision="generic")
    python = tmp_path / "python311"
    python.write_bytes(b"")
    candidate = RuntimeCandidate(
        str(python), "3.11.9", "Test", True, ("DemoTrainer",)
    )
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda _candidate, requirements: tuple(
            RuntimePackageCheck(item, item.split("==", 1)[1], True)
            for item in requirements
        ),
    )

    report = course_runtime_preflight(course, candidates=(candidate,))

    assert report.ready
    assert report.candidate == candidate
    assert report.packages == (
        RuntimePackageCheck("DemoTrainer==1.2.3", "1.2.3", True),
    )


def test_course_preflight_marks_managed_package_mismatch_as_repairable(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("PYKIM_RUNTIME_DIR", str(tmp_path / "runtimes"))
    course = tmp_path / "course"
    manifest = RuntimeManifest(
        "3.11",
        ("PyKIM==0.6.0", "pyxel==2.9.9"),
    )
    install_course_runtime(
        runtime_manifest_bytes(manifest), course, revision="mismatch"
    )
    python = managed_runtime_path(course) / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"")
    candidate = RuntimeCandidate(
        str(python), "3.11.9", "Kursumgebung", True, ("PyKIM", "Pyxel")
    )
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda *_args: (
            RuntimePackageCheck("PyKIM==0.6.0", "0.5.0", False),
            RuntimePackageCheck("pyxel==2.9.9", "2.9.9", True),
        ),
    )

    report = course_runtime_preflight(course, candidates=(candidate,))

    assert not report.ready
    assert report.repairable
    assert "Version 0.5.0" in " ".join(report.issues)


def test_course_preflight_offers_only_matching_base_python(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    install_course_runtime(
        runtime_manifest_bytes(
            RuntimeManifest("3.11", ("PyKIM==0.6.0", "pyxel==2.9.9"))
        ),
        course,
        revision="python-version",
    )
    matching = tmp_path / "python311"
    wrong = tmp_path / "python313"
    matching.write_bytes(b"")
    wrong.write_bytes(b"")
    candidates = (
        RuntimeCandidate(str(wrong), "3.13.4", "Falsch", True, ("PyKIM", "Pyxel")),
        RuntimeCandidate(str(matching), "3.11.9", "Passend", True, ()),
    )
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda _candidate, requirements: tuple(
            RuntimePackageCheck(item, "", False) for item in requirements
        ),
    )

    report = course_runtime_preflight(course, candidates=candidates)

    assert not report.ready
    assert [item.executable for item in report.provision_candidates] == [str(matching)]
    assert "PyKIM fehlt" in " ".join(report.issues)


def test_course_preflight_blocks_tampered_offline_packages(tmp_path, monkeypatch):
    from insi.course_runtime import current_runtime_target

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    target = current_runtime_target()
    assert target is not None
    course = tmp_path / "course"
    wheel_name = f"wheelhouse/{target}/demo-1.2.3-py3-none-any.whl"
    data = b"valid"
    manifest = RuntimeManifest(
        "3.11",
        ("PyKIM==0.6.0", "pyxel==2.9.9", "demo==1.2.3"),
        (target,),
        ((wheel_name, hashlib.sha256(data).hexdigest()),),
    )
    root = install_course_runtime(
        runtime_manifest_bytes(manifest),
        course,
        revision="offline",
        offline_wheels={wheel_name: data},
    )
    (root / wheel_name).write_bytes(b"tampered")

    report = course_runtime_preflight(course, candidates=())

    assert not report.ready
    assert not report.repairable
    assert not report.provision_candidates
    assert "Prüfsummen" in " ".join(report.issues)


def test_course_preflight_blocks_unsupported_platform(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    manifest = RuntimeManifest(
        "3.11", ("PyKIM==0.6.0", "pyxel==2.9.9")
    )
    install_course_runtime(
        runtime_manifest_bytes(manifest), course, revision="platform"
    )
    python = tmp_path / "python311"
    python.write_bytes(b"")
    candidate = RuntimeCandidate(
        str(python), "3.11.9", "Test", True, ("PyKIM", "Pyxel")
    )
    monkeypatch.setattr("insi.course_runtime.current_runtime_target", lambda: None)
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda _candidate, requirements: tuple(
            RuntimePackageCheck(item, item.split("==", 1)[1], True)
            for item in requirements
        ),
    )

    report = course_runtime_preflight(course, candidates=(candidate,))

    assert not report.ready
    assert not report.repairable
    assert not report.provision_candidates
    assert "Betriebssystem und Architektur" in report.summary
