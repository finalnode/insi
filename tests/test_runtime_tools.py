"""Verträge für Runtime-Auswahl, externe IDEs und Pyxel-Werkzeuge."""

import json
from pathlib import Path
import subprocess
import sys
import threading

import pykim
import pytest

from insi.course import (
    create_course,
    exercise_file,
    get_course_directory,
    get_ide_preference,
    get_runtime_preference,
    provision_course_exercises,
    set_ide_preference,
    set_runtime_preference,
    starter_source,
)
from insi.ide import (
    configure_thonny,
    configure_vscode,
    launch_ide,
    thonny_profile_directory,
)
from insi.pyxel_examples_view import copy_pyxel_example_to_course
from insi.runtime import (
    RuntimeCandidate,
    RuntimePackageCheck,
    _active_managed_python,
    _installed_python_paths,
    bundled_wheelhouse,
    create_managed_runtime,
    discover_runtimes,
    managed_runtime_path,
    provision_managed_runtime,
    repair_runtime,
    runtime_diagnostics,
    selected_runtime,
)
from insi.system import (
    PYXEL_EDITOR_LAUNCHER,
    launch_pyxel_editor,
    launch_pyxel_example,
    open_path,
    pyxel_examples,
    system_status,
    system_user_name,
)


def test_system_user_name_falls_back_to_login(monkeypatch):
    monkeypatch.setattr("insi.system.getpass.getuser", lambda: "ada")
    monkeypatch.setattr("insi.system.platform.system", lambda: "Windows")

    assert system_user_name() == "ada"


@pytest.mark.parametrize(
    ("platform_name", "launcher"),
    (("Windows", "explorer"), ("Linux", "xdg-open")),
)
def test_system_file_opening_uses_platform_launcher(
    tmp_path, monkeypatch, platform_name, launcher
):
    target = tmp_path / "aufgabe.py"
    target.write_text("print('ok')", encoding="utf-8")
    calls = []
    monkeypatch.setattr("insi.system.platform.system", lambda: platform_name)
    monkeypatch.setattr(
        "insi.system.subprocess.Popen",
        lambda command, cwd=None: calls.append(command),
    )

    open_path(target)

    assert calls == [[launcher, str(target.resolve())]]


def test_ide_preference_is_saved_without_losing_course_directory(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    custom_ide = tmp_path / "MyEditor.app"
    custom_ide.mkdir()

    create_course(course)
    assert set_ide_preference("custom", str(custom_ide)) == {
        "ide": "custom",
        "path": str(custom_ide.resolve()),
    }
    assert get_ide_preference()["ide"] == "custom"
    assert get_course_directory() == course.resolve()

    with pytest.raises(ValueError, match="nicht gefunden"):
        set_ide_preference("custom", str(tmp_path / "missing"))


def test_runtime_preference_is_saved_without_losing_other_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    create_course(tmp_path / "course")
    set_ide_preference("system")

    assert set_runtime_preference(python) == str(python.resolve())
    assert get_runtime_preference() == str(python.resolve())
    assert get_ide_preference()["ide"] == "system"
    assert get_course_directory() == (tmp_path / "course").resolve()


def test_runtime_discovery_includes_current_suite_python(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    candidates = discover_runtimes()

    current_path = str(Path(__import__("sys").executable).absolute())
    current = next(item for item in candidates if item.executable == current_path)
    assert current.supported
    assert current.has_package("PyKIM") and current.has_package("Pyxel")
    assert selected_runtime().executable == current.executable


def test_runtime_selection_honors_feature_specific_package_version(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    old = RuntimeCandidate("/python-old", "3.14.1", "Alt", True, ("Pyxel",))
    current = RuntimeCandidate("/python-current", "3.14.1", "Aktuell", True, ("Pyxel",))
    monkeypatch.setattr(
        "insi.runtime.discover_runtimes", lambda _course=None: (old, current)
    )
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda candidate, requirements: tuple(
            RuntimePackageCheck(
                requirement,
                "2.8.0" if candidate is old else "2.9.9",
                candidate is current,
            )
            for requirement in requirements
        ),
    )

    selected = selected_runtime(
        additional_requirements=("Pyxel==2.9.9",)
    )

    assert selected is current


def test_runtime_discovery_probes_independent_interpreters_in_parallel(
    tmp_path, monkeypatch
):
    first = tmp_path / "python-a"
    second = tmp_path / "python-b"
    first.write_text("", encoding="utf-8")
    second.write_text("", encoding="utf-8")
    barrier = threading.Barrier(2, timeout=2)

    monkeypatch.setattr(
        "insi.runtime._candidate_paths",
        lambda _course: [(first, "A"), (second, "B")],
    )

    def inspect(executable, source):
        barrier.wait()
        return RuntimeCandidate(str(executable), "3.14.1", source, True, ())

    monkeypatch.setattr("insi.runtime.inspect_runtime", inspect)

    candidates = discover_runtimes()

    assert [item.source for item in candidates] == ["A", "B"]


def test_managed_runtime_is_local_and_stable(tmp_path, monkeypatch):
    local = tmp_path / "local-runtimes"
    monkeypatch.setenv("PYKIM_RUNTIME_DIR", str(local))
    course = tmp_path / "synced" / "course"

    first = managed_runtime_path(course)
    second = managed_runtime_path(course)

    assert first == second
    assert first.parent == local
    assert not first.is_relative_to(course)


def test_managed_runtime_generation_is_a_real_isolated_venv(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.setenv("INSI_RUNTIME_DIR", str(tmp_path / "runtimes"))

    candidate = create_managed_runtime(course, sys.executable)

    environment = Path(candidate.executable).parent.parent
    assert candidate.supported
    assert environment.parent == managed_runtime_path(course) / "versions"
    assert (environment / "pyvenv.cfg").is_file()
    assert _active_managed_python(course) is None


def test_managed_runtime_marker_rejects_paths_outside_course_root(
    tmp_path, monkeypatch
):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.setenv("INSI_RUNTIME_DIR", str(tmp_path / "runtimes"))
    root = managed_runtime_path(course)
    root.mkdir(parents=True)
    outside = tmp_path / "outside" / "bin" / "python"
    outside.parent.mkdir(parents=True)
    outside.write_text("", encoding="utf-8")
    (root / "active.json").write_text(
        json.dumps({"environment": "../../outside"}), encoding="utf-8"
    )

    assert _active_managed_python(course) is None


def test_runtime_discovery_scans_conda_pyenv_and_uv(tmp_path, monkeypatch):
    home = tmp_path / "home"
    expected = {
        home / "miniconda3" / "envs" / "kurs" / "bin" / "python",
        home / ".pyenv" / "versions" / "3.12.4" / "bin" / "python",
        home / ".local" / "share" / "uv" / "python" / "cpython-3.13" / "bin" / "python3",
    }
    for executable in expected:
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("", encoding="utf-8")
    monkeypatch.setattr("insi.runtime.Path.home", lambda: home)
    monkeypatch.setattr("insi.runtime.platform.system", lambda: "Linux")
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)

    found = {path for path, _ in _installed_python_paths()}

    assert expected <= found


def test_provisioned_runtime_installs_package_and_becomes_preferred(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.setenv("INSI_RUNTIME_DIR", str(tmp_path / "runtimes"))
    python = managed_runtime_path(course) / "versions" / "test" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    calls = []
    ready = RuntimeCandidate(
        str(python), "3.13.1", "Kursumgebung", True, ("PyKIM", "Pyxel")
    )
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.runtime.create_managed_runtime", lambda *args: ready)
    monkeypatch.setattr("insi.runtime.bundled_wheelhouse", lambda: None)
    monkeypatch.setattr("insi.runtime.inspect_runtime", lambda *args: ready)
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda _candidate, requirements: tuple(
            RuntimePackageCheck(item, item.split("==", 1)[1], True)
            for item in requirements
        ),
    )
    monkeypatch.setattr(
        "insi.runtime.subprocess.run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    result = provision_managed_runtime(course, python)

    assert result == ready
    assert calls[0][0] == [
        str(python),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "PyKIM==0.6.0",
        "Pyxel==2.9.9",
        "PyYAML==6.0.3",
    ]
    assert get_runtime_preference() == str(python.resolve())
    marker = json.loads(
        (managed_runtime_path(course) / "active.json").read_text(encoding="utf-8")
    )
    assert marker == {"environment": "versions/test"}


def test_failed_runtime_repair_preserves_active_generation(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.setenv("INSI_RUNTIME_DIR", str(tmp_path / "runtimes"))
    root = managed_runtime_path(course)
    old_python = root / "versions" / "old" / "bin" / "python"
    new_python = root / "versions" / "new" / "bin" / "python"
    for executable in (old_python, new_python):
        executable.parent.mkdir(parents=True)
        executable.write_text("", encoding="utf-8")
    (root / "active.json").write_text(
        json.dumps({"environment": "versions/old"}), encoding="utf-8"
    )
    set_runtime_preference(old_python)
    old = RuntimeCandidate(
        str(old_python), "3.13.1", "Kursumgebung", True, ("PyKIM", "Pyxel")
    )
    new = RuntimeCandidate(
        str(new_python), "3.13.1", "Kursumgebung", True, ("PyKIM", "Pyxel")
    )
    bases = []
    monkeypatch.setattr("insi.runtime.inspect_runtime", lambda *args: old)
    monkeypatch.setattr(
        "insi.runtime.create_managed_runtime",
        lambda _course, base: bases.append(base) or new,
    )
    monkeypatch.setattr(
        "insi.runtime._install_runtime_packages",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("abgebrochen")),
    )

    with pytest.raises(RuntimeError, match="abgebrochen"):
        repair_runtime(course)

    assert old_python.is_file()
    assert not new_python.parent.parent.exists()
    assert bases == [old]
    assert get_runtime_preference() == str(old_python.resolve())
    assert json.loads((root / "active.json").read_text(encoding="utf-8")) == {
        "environment": "versions/old"
    }


def test_successful_runtime_repair_activates_new_generation(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    monkeypatch.setenv("INSI_RUNTIME_DIR", str(tmp_path / "runtimes"))
    root = managed_runtime_path(course)
    old_python = root / "versions" / "old" / "bin" / "python"
    new_python = root / "versions" / "new" / "bin" / "python"
    for executable in (old_python, new_python):
        executable.parent.mkdir(parents=True)
        executable.write_text("", encoding="utf-8")
    (root / "active.json").write_text(
        json.dumps({"environment": "versions/old"}), encoding="utf-8"
    )
    set_runtime_preference(old_python)
    old = RuntimeCandidate(
        str(old_python), "3.13.1", "Kursumgebung", True, ("PyKIM", "Pyxel")
    )
    new = RuntimeCandidate(
        str(new_python), "3.13.1", "Kursumgebung", True, ("PyKIM", "Pyxel")
    )
    bases = []
    monkeypatch.setattr(
        "insi.runtime.inspect_runtime",
        lambda executable, *_args: (
            old if Path(executable) == old_python else new
        ),
    )
    monkeypatch.setattr(
        "insi.runtime.create_managed_runtime",
        lambda _course, base: bases.append(base) or new,
    )
    monkeypatch.setattr(
        "insi.runtime._install_runtime_packages", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "insi.runtime._package_checks",
        lambda _candidate, requirements: tuple(
            RuntimePackageCheck(item, item.split("==", 1)[1], True)
            for item in requirements
        ),
    )

    assert repair_runtime(course) == new

    assert old_python.is_file()
    assert new_python.is_file()
    assert bases == [old]
    assert get_runtime_preference() == str(new_python.resolve())
    assert json.loads((root / "active.json").read_text(encoding="utf-8")) == {
        "environment": "versions/new"
    }


def test_runtime_install_uses_bundled_wheels_offline(tmp_path, monkeypatch):
    wheelhouse = tmp_path / "wheels"
    wheelhouse.mkdir()
    (wheelhouse / "PyKIM-0.6.0-py3-none-any.whl").write_text("", encoding="utf-8")
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    calls = []
    monkeypatch.setenv("PYKIM_WHEELHOUSE", str(wheelhouse))
    monkeypatch.setattr(
        "insi.runtime.subprocess.run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    from insi.runtime import _install_runtime_packages
    _install_runtime_packages(python)

    assert bundled_wheelhouse() == wheelhouse
    assert "--no-index" in calls[0][0]
    assert calls[0][0][calls[0][0].index("--find-links") + 1] == str(wheelhouse)
    assert calls[0][0][-3:] == ["PyKIM==0.6.0", "Pyxel==2.9.9", "PyYAML==6.0.3"]


def test_runtime_diagnostics_does_not_contain_student_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    report = runtime_diagnostics(tmp_path / "course")

    assert set(report) == {
        "platform", "selected", "wheelhouse", "candidates", "preflight"
    }
    assert all("executable" in item for item in report["candidates"])
    assert "issues" in report["preflight"]


def test_repair_refuses_to_modify_external_python(tmp_path, monkeypatch):
    python = tmp_path / "external" / "python"
    python.parent.mkdir()
    python.write_text("", encoding="utf-8")
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    set_runtime_preference(python)

    with pytest.raises(RuntimeError, match="verwaltete Kursumgebung"):
        repair_runtime(tmp_path / "course")


def test_vscode_workspace_uses_selected_runtime_and_preserves_settings(tmp_path):
    settings_directory = tmp_path / ".vscode"
    settings_directory.mkdir()
    settings = settings_directory / "settings.json"
    settings.write_text('{"editor.formatOnSave": true}', encoding="utf-8")
    python = tmp_path / "runtime" / "bin" / "python"

    settings_path, extensions_path = configure_vscode(tmp_path, python)
    data = json.loads(settings_path.read_text(encoding="utf-8"))

    assert data["editor.formatOnSave"] is True
    assert data["python.defaultInterpreterPath"] == str(python.resolve())
    assert data["python.terminal.activateEnvironment"] is True
    assert "ms-python.python" in extensions_path.read_text(encoding="utf-8")


def test_launch_vscode_configures_workspace_before_opening(tmp_path, monkeypatch):
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        "insi.ide.discover_ides",
        lambda: {"vscode": __import__("insi.ide", fromlist=["IDEInstallation"]).IDEInstallation(
            "vscode", "Visual Studio Code", "/usr/bin/code"
        )},
    )
    monkeypatch.setattr("insi.ide.subprocess.Popen", lambda command: calls.append(command))

    launch_ide(tmp_path, "vscode", python=python)

    assert calls == [["/usr/bin/code", str(tmp_path.resolve())]]
    settings = json.loads((tmp_path / ".vscode" / "settings.json").read_text())
    assert settings["python.defaultInterpreterPath"] == str(python.resolve())


def test_thonny_uses_isolated_pykim_profile_and_selected_runtime(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    python = tmp_path / "runtime" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))

    profile = configure_thonny(course, python)
    configuration = (profile / "configuration.ini").read_text(encoding="utf-8")

    assert profile == thonny_profile_directory(course)
    assert "backend_name = LocalCPython" in configuration
    assert f"executable = {python.resolve()}" in configuration
    assert "single_instance = False" in configuration


def test_launch_thonny_passes_dedicated_user_directory(tmp_path, monkeypatch):
    course = tmp_path / "course"
    course.mkdir()
    python = tmp_path / "python"
    python.write_text("", encoding="utf-8")
    calls = []
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.ide.discover_ides",
        lambda: {"thonny": __import__("insi.ide", fromlist=["IDEInstallation"]).IDEInstallation(
            "thonny", "Thonny", "/usr/bin/thonny"
        )},
    )
    monkeypatch.setattr(
        "insi.ide.subprocess.Popen",
        lambda command, env=None: calls.append((command, env)),
    )

    launch_ide(course, "thonny", python=python, course=course)

    assert calls[0][0] == ["/usr/bin/thonny", str(course.resolve())]
    assert calls[0][1]["THONNY_USER_DIR"] == str(thonny_profile_directory(course))


def test_exercise_file_finds_the_generated_starter(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course)
    provision_course_exercises(course)

    assert exercise_file("treppe-5") == course / "Aufgaben" / "imperativ" / "treppe_5.py"
    assert exercise_file("gibt-es-nicht") is None


def test_starter_prepares_declarative_task_world_before_student_code():
    source = starter_source("rote-pixel-sammeln")

    assert 'prepare("rote-pixel-sammeln")' in source
    assert source.index('prepare("rote-pixel-sammeln")') < source.index(
        "# Schreibe deine Lösung hier."
    )


def test_system_status_reports_versions_and_tools(monkeypatch):
    monkeypatch.setattr("insi.system.shutil.which", lambda name: f"/bin/{name}")

    status = system_status()

    assert status.pykim == pykim.__version__
    assert status.python_supported
    assert status.pyxel and status.thonny and status.vscode


def test_launch_pyxel_editor_opens_requested_official_editor(tmp_path, monkeypatch):
    calls = []

    class RunningProcess:
        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired("pyxel-editor", timeout)

    monkeypatch.setattr("insi.system.python_command", lambda: ["/runtime/python"])
    monkeypatch.setattr(
        "insi.system.subprocess.Popen",
        lambda command, cwd=None, **_options: (
            calls.append((command, cwd)) or RunningProcess()
        ),
    )
    resource = tmp_path / "assets" / "game.pyxres"

    assert launch_pyxel_editor(resource, editor="music") == resource
    assert resource.parent.exists()
    command, cwd = calls[0]
    assert command[:2] == ["/runtime/python", "-c"]
    assert command[-2:] == [str(resource), "music"]
    assert "edit_pyxel_resource" in command[2]
    assert cwd == resource.parent


def test_launch_pyxel_editor_rejects_unknown_editor(tmp_path):
    with pytest.raises(ValueError, match="Unbekannter Pyxel-Editor"):
        launch_pyxel_editor(tmp_path / "game.pyxres", editor="video")


def test_launch_pyxel_editor_preserves_virtualenv_symlink_and_reports_failure(
    tmp_path, monkeypatch
):
    interpreter = tmp_path / "venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to("/usr/bin/python3")
    calls = []

    class FailedProcess:
        def wait(self, timeout=None):
            return 1

    def fail(command, cwd=None, stdout=None, **_options):
        calls.append(command)
        stdout.write("ModuleNotFoundError: No module named 'pyxel'\n")
        stdout.flush()
        return FailedProcess()

    monkeypatch.setattr("insi.system.subprocess.Popen", fail)

    with pytest.raises(RuntimeError, match="No module named 'pyxel'"):
        launch_pyxel_editor(tmp_path / "game.pyxres", python=interpreter)

    assert calls[0][0] == str(interpreter.absolute())


def test_pyxel_tools_use_bundled_python_without_global_command(tmp_path, monkeypatch):
    import pyxel

    package = tmp_path / "pyxel"
    examples = package / "examples"
    examples.mkdir(parents=True)
    example = examples / "01_hello.py"
    example.write_text("import pyxel", encoding="utf-8")
    monkeypatch.setattr(pyxel, "__file__", str(package / "__init__.py"))
    monkeypatch.setattr("insi.system.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "insi.system.python_command",
        lambda: ["/Applications/insi.app/Contents/MacOS/insi-python", "--insi-python"],
    )
    calls = []

    class RunningProcess:
        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired("pyxel-editor", timeout)

    monkeypatch.setattr(
        "insi.system.subprocess.Popen",
        lambda command, cwd=None, **_options: (
            calls.append((command, cwd)) or RunningProcess()
        ),
    )
    resource = tmp_path / "assets" / "game.pyxres"

    assert launch_pyxel_editor(resource, editor="image") == resource
    assert launch_pyxel_example(example) == example
    runner = "/Applications/insi.app/Contents/MacOS/insi-python"
    assert calls == [
        (
            [
                runner,
                "--insi-python",
                "-c",
                PYXEL_EDITOR_LAUNCHER,
                str(resource),
                "image",
            ],
            resource.parent,
        ),
        (
            [runner, "--insi-python", "-m", "pyxel", "run", str(example)],
            example.parent,
        ),
    ]


def test_frozen_python_runner_keeps_windows_executable_suffix(tmp_path, monkeypatch):
    from insi.interpreter import command_for

    suite = tmp_path / "insi.exe"
    runner = tmp_path / "insi-python.exe"
    runner.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(suite))

    assert command_for(str(suite)) == [str(runner), "--insi-python"]


def test_frozen_python_runner_uses_old_switch_only_for_legacy_bundle(
    tmp_path,
    monkeypatch,
):
    from insi.interpreter import command_for

    suite = tmp_path / "PyKIM.exe"
    legacy_runner = tmp_path / "PyKIM Python.exe"
    legacy_runner.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(suite))

    assert command_for(str(suite)) == [str(legacy_runner), "--pykim-python"]


def test_list_and_launch_installed_pyxel_example(tmp_path, monkeypatch):
    import pyxel

    package = tmp_path / "pyxel"
    examples = package / "examples"
    examples.mkdir(parents=True)
    first = examples / "01_hello.py"
    second = examples / "02_game.py"
    first.write_text("import pyxel", encoding="utf-8")
    second.write_text("import pyxel", encoding="utf-8")
    monkeypatch.setattr(pyxel, "__file__", str(package / "__init__.py"))
    monkeypatch.setattr(
        "insi.system.shutil.which",
        lambda name: "/usr/local/bin/pyxel" if name == "pyxel" else None,
    )
    calls = []
    monkeypatch.setattr(
        "insi.system.subprocess.Popen",
        lambda command, cwd=None: calls.append((command, cwd)),
    )

    assert pyxel_examples() == (first, second)
    assert launch_pyxel_example(second) == second
    assert calls == [
        (["/usr/local/bin/pyxel", "run", str(second)], second.parent)
    ]
    with pytest.raises(ValueError, match="mitgelieferte"):
        launch_pyxel_example(tmp_path / "fremd.py")


def test_copy_pyxel_example_creates_project_with_assets(tmp_path, monkeypatch):
    import pyxel

    package = tmp_path / "installed" / "pyxel"
    examples = package / "examples"
    assets = examples / "assets"
    assets.mkdir(parents=True)
    example = examples / "02_jump_game.py"
    example.write_text('import pyxel\npyxel.load("assets/game.pyxres")\n', encoding="utf-8")
    (assets / "game.pyxres").write_bytes(b"resource")
    monkeypatch.setattr(pyxel, "__file__", str(package / "__init__.py"))
    course = tmp_path / "course"
    course.mkdir()

    target, created = copy_pyxel_example_to_course(example, course)
    same_target, created_again = copy_pyxel_example_to_course(example, course)

    assert created
    assert not created_again
    assert same_target == target
    assert target.read_text(encoding="utf-8") == example.read_text(encoding="utf-8")
    assert (target.parent / "assets" / "game.pyxres").read_bytes() == b"resource"
    metadata = json.loads((target.parent / "projekt.json").read_text(encoding="utf-8"))
    assert metadata["kind"] == "pyxel"
    assert metadata["resources"] == ""
