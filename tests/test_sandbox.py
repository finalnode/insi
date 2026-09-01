import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from insi import sandbox, windows_staging
from insi.execution_security import builtin_policy, execution_environment, student_policy
from insi.sandbox import (
    BubblewrapAdapter,
    MacOSSeatbeltAdapter,
    SandboxStatus,
    SandboxUnavailableError,
    SandboxedProcess,
    prepare_launch,
    sandbox_popen,
    sandbox_run,
    WindowsAppContainerAdapter,
)
from insi.windows_sandbox_helper import decode_payload, encode_payload
from insi.windows_sandbox_helper import (
    _is_preauthorized_read,
    _preauthorized_application_root,
)
from insi.windows_paths import (
    is_windows_network_path,
)
from insi.windows_staging import (
    WindowsNetworkRunStage,
    relaunch_frozen_windows_application,
    sync_network_writebacks,
)


class UnavailableAdapter:
    name = "Nicht verfügbar"

    def status(self):
        return SandboxStatus(False, self.name, "Test", "bewusst nicht verfügbar")

    def prepare(self, *args, **kwargs):  # pragma: no cover - darf nie erreicht werden
        raise AssertionError("Ein nicht verfügbarer Adapter darf keinen Start vorbereiten.")


def test_untrusted_code_never_falls_back_to_an_unsandboxed_process(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_adapter_override", UnavailableAdapter())
    policy = student_policy(tmp_path)

    with pytest.raises(SandboxUnavailableError, match="externe IDE"):
        prepare_launch(
            [sys.executable, "-c", "print('no')"],
            cwd=tmp_path,
            environment=execution_environment(policy),
            policy=policy,
        )


def test_packaged_builtin_code_has_an_explicit_trusted_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_adapter_override", UnavailableAdapter())
    policy = builtin_policy(tmp_path)

    launch = prepare_launch(
        [sys.executable, "-c", "print('ok')"],
        cwd=tmp_path,
        environment=execution_environment(policy),
        policy=policy,
    )

    assert launch.command[0] == sys.executable
    assert launch.environment["INSI_SANDBOX"] == "trusted-local"


def test_bubblewrap_command_uses_read_only_and_writable_mounts_without_network(
    tmp_path, monkeypatch
):
    readable = tmp_path / "course"
    writable = tmp_path / "project"
    readable.mkdir()
    writable.mkdir()
    adapter = BubblewrapAdapter("/usr/bin/bwrap")
    monkeypatch.setattr(
        adapter,
        "status",
        lambda: SandboxStatus(True, "Bubblewrap", "Linux", "ok", True, True),
    )
    policy = student_policy(
        writable,
        readable_roots=(readable,),
        writable_roots=(writable,),
    )

    launch = adapter.prepare(
        ["/usr/bin/python3", str(readable / "main.py")],
        cwd=writable,
        environment={"PATH": "/usr/bin"},
        policy=policy,
    )
    command = list(launch.command)

    assert "--unshare-all" in command
    assert "--share-net" not in command
    assert "--tmpfs" not in command
    temporary = launch.cleanup_paths[0]
    assert ["--bind", str(temporary), "/tmp"] == command[
        command.index(str(temporary)) - 1:command.index(str(temporary)) + 2
    ]
    assert ["--ro-bind", str(readable), str(readable)] == command[
        command.index(str(readable)) - 1:command.index(str(readable)) + 2
    ]
    writable_index = command.index(str(writable))
    assert command[writable_index - 1] == "--bind"
    assert launch.environment["HOME"] == "/tmp/insi-home"
    assert launch.environment["INSI_SANDBOX"] == "bubblewrap"
    shutil.rmtree(temporary)


def test_bubblewrap_resolves_executable_before_entering_namespace(
    tmp_path, monkeypatch
):
    target = tmp_path / "targets" / "runtime"
    target.mkdir(parents=True)
    executable = target / "python"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    alias = tmp_path / "aliases" / "current"
    alias.parent.mkdir()
    alias.symlink_to(target, target_is_directory=True)
    writable = tmp_path / "project"
    writable.mkdir()
    adapter = BubblewrapAdapter("/usr/bin/bwrap")
    monkeypatch.setattr(
        adapter,
        "status",
        lambda: SandboxStatus(True, "Bubblewrap", "Linux", "ok", True, True),
    )
    policy = student_policy(writable, writable_roots=(writable,))

    launch = adapter.prepare(
        [str(alias / "python"), "-c", "print('ok')"],
        cwd=writable,
        environment={"PATH": "/usr/bin"},
        policy=policy,
    )
    command = list(launch.command)
    separator = command.index("--")

    assert command[separator + 1] == str(executable.resolve())
    shutil.rmtree(launch.cleanup_paths[0])


def test_bubblewrap_recreates_merged_usr_aliases(tmp_path):
    usr = tmp_path / "usr"
    binary_directory = usr / "bin"
    library_directory = usr / "lib64"
    binary_directory.mkdir(parents=True)
    library_directory.mkdir()
    binary_alias = tmp_path / "bin"
    library_alias = tmp_path / "lib64"
    binary_alias.symlink_to("usr/bin", target_is_directory=True)
    library_alias.symlink_to("usr/lib64", target_is_directory=True)

    roots, links = BubblewrapAdapter._system_layout(
        (usr, binary_alias, library_alias)
    )

    assert roots == (usr.resolve(), binary_directory.resolve(), library_directory.resolve())
    assert links == (
        ("usr/bin", str(binary_alias)),
        ("usr/lib64", str(library_alias)),
    )


def test_host_pythonpath_does_not_implicitly_mount_the_whole_course(tmp_path, monkeypatch):
    course = tmp_path / "course"
    task = course / "Aufgaben" / "task.py"
    run = tmp_path / "run"
    task.parent.mkdir(parents=True)
    task.write_text("print('ok')", encoding="utf-8")
    run.mkdir()
    adapter = BubblewrapAdapter("/usr/bin/bwrap")
    monkeypatch.setattr(
        adapter,
        "status",
        lambda: SandboxStatus(True, "Bubblewrap", "Linux", "ok", True, True),
    )
    policy = student_policy(run, readable_roots=(task,), writable_roots=(run,))

    launch = adapter.prepare(
        ["/usr/bin/python3", str(task)],
        cwd=run,
        environment={"PATH": "/usr/bin", "PYTHONPATH": str(course)},
        policy=policy,
    )
    command = list(launch.command)
    read_only_sources = {
        Path(command[index + 1])
        for index, value in enumerate(command[:-2])
        if value == "--ro-bind"
    }

    assert task.resolve() in read_only_sources
    assert course.resolve() not in read_only_sources
    shutil.rmtree(launch.cleanup_paths[0])


def test_windows_adapter_wraps_student_command_in_validated_broker_payload(
    tmp_path, monkeypatch
):
    readable = tmp_path / "course" / "task.py"
    runtime = tmp_path / "runtime" / "insi.exe"
    writable = tmp_path / "project"
    readable.parent.mkdir()
    readable.write_text("print('ok')", encoding="utf-8")
    runtime.parent.mkdir()
    runtime.write_bytes(b"runner")
    writable.mkdir()
    adapter = WindowsAppContainerAdapter()
    monkeypatch.setattr(
        adapter,
        "status",
        lambda: SandboxStatus(
            True,
            "Windows AppContainer",
            "Windows",
            "ok",
            True,
            True,
            True,
        ),
    )
    monkeypatch.setattr(sandbox, "python_command", lambda: ["insi-python.exe"])
    policy = student_policy(
        writable,
        readable_roots=(readable,),
        writable_roots=(writable,),
        max_processes=3,
        max_memory_bytes=64 * 1024 * 1024,
    )

    launch = adapter.prepare(
        [str(runtime), str(readable)],
        cwd=writable,
        environment={"PATH": "C:\\Windows\\System32"},
        policy=policy,
    )

    assert launch.command[:4] == (
        "insi-python.exe",
        "-m",
        "insi.windows_sandbox_helper",
        "--payload",
    )
    payload = decode_payload(launch.command[4])
    assert payload["command"] == [str(runtime), str(readable)]
    assert str(runtime.resolve()) in payload["readable_roots"]
    assert str(readable.resolve()) in payload["readable_roots"]
    assert payload["writable_roots"] == [str(writable.resolve())]
    assert payload["limits"]["max_processes"] == 3
    assert payload["limits"]["max_memory_bytes"] == 64 * 1024 * 1024
    assert payload["environment"]["INSI_SANDBOX"] == "windows-appcontainer"
    assert launch.environment["INSI_SANDBOX"] == "windows-appcontainer-broker"
    assert launch.violation_file is not None
    assert payload["violation_file"] == str(launch.violation_file)
    launch.violation_file.unlink()


def test_windows_probe_cleanup_retries_transient_file_lock(tmp_path, monkeypatch):
    path = tmp_path / "probe"
    path.mkdir()
    calls = []
    real_rmtree = shutil.rmtree

    def transient_rmtree(target):
        calls.append(Path(target))
        if len(calls) == 1:
            raise PermissionError(32, "Datei wird von einem anderen Prozess verwendet")
        real_rmtree(target)

    monkeypatch.setattr(sandbox.shutil, "rmtree", transient_rmtree)

    assert sandbox._remove_tree_with_retries(path, attempts=2, delay_seconds=0)
    assert calls == [path, path]
    assert not path.exists()


def test_windows_onefile_child_reuses_parent_extraction(
    tmp_path, monkeypatch
):
    bundle = tmp_path / "onefile-extraction"
    bundle_library = bundle / "library"
    system_root = tmp_path / "system"
    executable = tmp_path / "application" / "insi.exe"
    bundle_library.mkdir(parents=True)
    system_root.mkdir()
    executable.parent.mkdir()
    executable.touch()
    monkeypatch.setattr(sandbox.sys, "platform", "win32")
    monkeypatch.setattr(sandbox.sys, "frozen", True, raising=False)
    monkeypatch.setattr(sandbox.sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr(sandbox.sys, "executable", str(executable))
    monkeypatch.setattr(
        BubblewrapAdapter,
        "_runtime_roots",
        staticmethod(lambda _command, _environment: (bundle, bundle_library, system_root)),
    )

    roots = WindowsAppContainerAdapter._runtime_roots([str(executable)], {})

    assert bundle in roots
    assert bundle_library in roots
    assert system_root in roots
    assert executable.resolve() in roots


def test_windows_adapter_refuses_network_capability(tmp_path, monkeypatch):
    adapter = WindowsAppContainerAdapter()
    monkeypatch.setattr(
        adapter,
        "status",
        lambda: SandboxStatus(True, adapter.name, "Windows", "ok"),
    )
    policy = student_policy(tmp_path)
    object.__setattr__(policy, "allow_network", True)

    with pytest.raises(SandboxUnavailableError, match="Netzwerkfähigkeiten"):
        adapter.prepare(
            [sys.executable, "-c", "pass"],
            cwd=tmp_path,
            environment={},
            policy=policy,
        )


@pytest.mark.parametrize(
    "path",
    (
        r"\\server\share\insi\insi.exe",
        "//server/share/course",
        r"\\?\UNC\server\share\course",
    ),
)
def test_windows_network_paths_are_detected_without_touching_the_share(path):
    assert is_windows_network_path(path)


@pytest.mark.parametrize("path", (r"C:\insi\insi.exe", r"D:\PyKIM-Kurs"))
def test_local_windows_paths_are_not_mistaken_for_unc_paths(path):
    assert not is_windows_network_path(path)


def test_packaged_windows_network_launch_is_staged_and_relaunched(tmp_path, monkeypatch):
    calls = []
    source = tmp_path / "network" / "insi"
    source.mkdir(parents=True)
    (source / "insi.exe").write_bytes(b"portable-build")
    (source / "_internal").mkdir()
    (source / "_internal" / "library.zip").write_bytes(b"runtime")
    local_app_data = tmp_path / "local"

    class Process:
        pass

    monkeypatch.setattr(windows_staging.sys, "platform", "win32")
    monkeypatch.setattr(
        windows_staging,
        "is_windows_network_path",
        lambda path: str(path) == str(source / "insi.exe"),
    )
    monkeypatch.setattr(
        windows_staging.subprocess,
        "Popen",
        lambda command, **options: calls.append((command, options)) or Process(),
    )

    with pytest.raises(SystemExit) as exit_info:
        relaunch_frozen_windows_application(
            source / "insi.exe",
            arguments=("--test",),
            environment={"LOCALAPPDATA": str(local_app_data)},
        )

    assert exit_info.value.code == 0
    assert len(calls) == 1
    command, options = calls[0]
    assert command[1:] == ["--test"]
    assert Path(command[0]).is_file()
    assert Path(command[0]).parent.is_relative_to(local_app_data)
    assert (Path(command[0]).parent / "_internal" / "library.zip").is_file()
    assert options["cwd"] == Path(command[0]).parent
    assert options["env"]["INSI_STAGED_FROM_NETWORK"] == str(source / "insi.exe")
    assert options["env"]["INSI_STAGED_APPLICATION_ROOT"] == str(
        Path(command[0]).parent
    )
    assert options["env"]["PYINSTALLER_RESET_ENVIRONMENT"] == "1"
    assert (Path(command[0]).parent / ".insi-appcontainer-access").is_file()


def test_packaged_windows_cache_changes_with_distribution_identity(tmp_path):
    source = tmp_path / "network" / "insi"
    source.mkdir(parents=True)
    executable = source / "insi.exe"
    executable.write_bytes(b"unchanged-launcher")
    (source / "_internal").mkdir()
    identity = source / windows_staging.APPLICATION_IDENTITY_FILE
    local_app_data = tmp_path / "local"

    identity.write_text("1" * 64, encoding="ascii")
    first = windows_staging.stage_application_directory(
        executable,
        environment={"LOCALAPPDATA": str(local_app_data)},
    )
    identity.write_text("2" * 64, encoding="ascii")
    second = windows_staging.stage_application_directory(
        executable,
        environment={"LOCALAPPDATA": str(local_app_data)},
    )

    assert first.parent != second.parent
    assert first.read_bytes() == second.read_bytes() == b"unchanged-launcher"


def test_packaged_windows_onefile_cache_is_reused_without_internal_directory(
    tmp_path,
):
    source = tmp_path / "network" / "insi"
    source.mkdir(parents=True)
    executable = source / "insi.exe"
    executable.write_bytes(b"onefile-build")
    local_app_data = tmp_path / "local"

    first = windows_staging.stage_application_directory(
        executable,
        environment={"LOCALAPPDATA": str(local_app_data)},
    )
    second = windows_staging.stage_application_directory(
        executable,
        environment={"LOCALAPPDATA": str(local_app_data)},
    )

    assert first == second
    assert first.read_bytes() == b"onefile-build"
    assert not (first.parent / "_internal").exists()


def test_staged_application_root_skips_only_validated_read_grants(tmp_path):
    application = tmp_path / "staged-app"
    internal = application / "_internal"
    internal.mkdir(parents=True)
    marker = application / ".insi-appcontainer-access"
    marker.write_text("S-1-15-2-1", encoding="ascii")
    runtime = internal / "python311.dll"
    runtime.touch()
    project = tmp_path / "project"
    project.mkdir()

    root = _preauthorized_application_root(
        {"INSI_STAGED_APPLICATION_ROOT": str(application)}
    )

    assert root == application.resolve()
    assert _is_preauthorized_read(runtime, root)
    assert not _is_preauthorized_read(project, root)
    marker.write_text("invalid", encoding="ascii")
    assert _preauthorized_application_root(
        {"INSI_STAGED_APPLICATION_ROOT": str(application)}
    ) is None


def test_staged_application_access_is_granted_once_without_a_window(
    tmp_path, monkeypatch
):
    calls = []
    application = tmp_path / "staged-app"
    application.mkdir()
    monkeypatch.setattr(windows_staging.os, "name", "nt")
    monkeypatch.setattr(windows_staging.subprocess, "CREATE_NO_WINDOW", 8, raising=False)

    class Completed:
        returncode = 0

    monkeypatch.setattr(
        windows_staging.subprocess,
        "run",
        lambda command, **options: calls.append((command, options)) or Completed(),
    )

    windows_staging._grant_staged_application_access(application)

    command, options = calls[0]
    assert command[:3] == ["icacls", str(application), "/grant:r"]
    assert "*S-1-15-2-1:(OI)(CI)RX" in command
    assert "/T" not in command
    assert options["creationflags"] == 8
    assert options["check"] is True
    assert (application / ".insi-appcontainer-access").read_text(
        encoding="ascii"
    ) == "S-1-15-2-1"


def test_staged_application_sets_inherited_access_before_copy(tmp_path, monkeypatch):
    source = tmp_path / "network" / "insi"
    source.mkdir(parents=True)
    executable = source / "insi.exe"
    executable.write_bytes(b"portable-build")
    (source / "_internal").mkdir()
    events = []
    real_copytree = windows_staging.shutil.copytree
    real_grant = windows_staging._grant_staged_application_access

    def grant(directory):
        events.append("grant")
        real_grant(directory)

    def copytree(*args, **kwargs):
        events.append("copy")
        return real_copytree(*args, **kwargs)

    monkeypatch.setattr(windows_staging, "_grant_staged_application_access", grant)
    monkeypatch.setattr(windows_staging.shutil, "copytree", copytree)

    windows_staging.stage_application_directory(
        executable,
        environment={"LOCALAPPDATA": str(tmp_path / "local")},
    )

    assert events[:2] == ["grant", "copy"]


def test_packaged_network_python_runner_waits_for_local_child(tmp_path, monkeypatch):
    source = tmp_path / "network" / "insi"
    source.mkdir(parents=True)
    (source / "insi.exe").write_bytes(b"portable-build")
    (source / "_internal").mkdir()
    calls = []

    class Completed:
        returncode = 7

    monkeypatch.setattr(windows_staging.sys, "platform", "win32")
    monkeypatch.setattr(
        windows_staging,
        "is_windows_network_path",
        lambda path: str(path) == str(source / "insi.exe"),
    )
    monkeypatch.setattr(
        windows_staging.subprocess,
        "run",
        lambda command, **options: calls.append((command, options)) or Completed(),
    )

    with pytest.raises(SystemExit) as exit_info:
        relaunch_frozen_windows_application(
            source / "insi.exe",
            arguments=("--pykim-python", "-c", "print('ok')"),
            environment={"LOCALAPPDATA": str(tmp_path / "local")},
        )

    assert exit_info.value.code == 7
    assert calls[0][0][1:] == ["--pykim-python", "-c", "print('ok')"]
    assert calls[0][1]["check"] is False


def test_windows_network_run_stage_copies_and_syncs_writable_files(tmp_path, monkeypatch):
    source = tmp_path / "network-project"
    source.mkdir()
    (source / "main.py").write_text("print('before')", encoding="utf-8")
    local_app_data = tmp_path / "local"
    monkeypatch.setattr(
        windows_staging,
        "is_windows_network_path",
        lambda value: Path(value).is_relative_to(source),
    )
    stage = WindowsNetworkRunStage({"LOCALAPPDATA": str(local_app_data)})

    staged = stage.stage_path(source, writable=True)
    (staged / "main.py").write_text("print('after')", encoding="utf-8")
    (staged / "removed.py").write_text("remove me", encoding="utf-8")
    sync_network_writebacks(stage.writebacks)
    stage = WindowsNetworkRunStage({"LOCALAPPDATA": str(local_app_data)})
    staged = stage.stage_path(source, writable=True)
    (staged / "removed.py").unlink()
    (staged / "result.txt").write_text("ok", encoding="utf-8")
    sync_network_writebacks(stage.writebacks)

    assert (source / "main.py").read_text(encoding="utf-8") == "print('after')"
    assert (source / "result.txt").read_text(encoding="utf-8") == "ok"
    assert not (source / "removed.py").exists()


def test_windows_network_stage_preserves_path_relationships_and_environment(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(windows_staging.os, "pathsep", ";")
    stage = WindowsNetworkRunStage({"LOCALAPPDATA": str(tmp_path)})
    course = r"\\server\share\courses\pykim"
    target = course + r"\Aufgaben\quadrat.py"

    assert stage.local_path(target).is_relative_to(stage.local_path(course))
    mapped = stage.map_environment(
        {
            "PYKIM_COURSE_DIR": course,
            "PYTHONPATH": course + r";C:\Python\Lib",
        }
    )

    assert mapped["PYKIM_COURSE_DIR"] == str(stage.local_path(course))
    assert mapped["PYTHONPATH"].split(";") == [
        str(stage.local_path(course)),
        r"C:\Python\Lib",
    ]


def test_windows_network_sync_does_not_overwrite_concurrent_change(tmp_path, monkeypatch):
    source = tmp_path / "network-project"
    source.mkdir()
    target = source / "main.py"
    target.write_text("before", encoding="utf-8")
    other = source / "other.txt"
    other.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(
        windows_staging,
        "is_windows_network_path",
        lambda value: Path(value).is_relative_to(source),
    )
    stage = WindowsNetworkRunStage({"LOCALAPPDATA": str(tmp_path / "local")})
    staged = stage.stage_path(source, writable=True)
    (staged / "main.py").write_text("sandbox", encoding="utf-8")
    (staged / "other.txt").unlink()
    target.write_text("network", encoding="utf-8")

    with pytest.raises(OSError, match="nicht überschrieben"):
        sync_network_writebacks(stage.writebacks)

    assert target.read_text(encoding="utf-8") == "network"
    assert other.read_text(encoding="utf-8") == "keep"


def test_sandboxed_process_syncs_staged_network_writes_before_cleanup(tmp_path):
    source = tmp_path / "network"
    staged_root = tmp_path / "stage"
    staged = staged_root / "project"
    source.mkdir()
    staged.mkdir(parents=True)
    (source / "result.txt").write_text("before", encoding="utf-8")
    (staged / "result.txt").write_text("before", encoding="utf-8")
    writeback = windows_staging.NetworkWriteback(
        source,
        staged,
        {"result.txt": windows_staging._file_digest(staged / "result.txt")},
    )
    policy = student_policy(staged)
    native = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"from pathlib import Path; Path({str(staged / 'result.txt')!r}).write_text('after')",
        ]
    )
    process = SandboxedProcess(
        native,
        policy,
        baseline_written_bytes=0,
        cleanup_paths=(staged_root,),
        monitored_writable_roots=(staged,),
        writebacks=(writeback,),
    )

    process.wait(timeout=5)

    assert (source / "result.txt").read_text(encoding="utf-8") == "after"
    assert not staged_root.exists()


def test_windows_broker_payload_rejects_tampering_and_invalid_limits(tmp_path):
    payload = {
        "version": 1,
        "profile": "de.simplicissima.insi.test",
        "command": ["python.exe", "-c", "pass"],
        "cwd": str(tmp_path),
        "environment": {},
        "readable_roots": [],
        "writable_roots": [str(tmp_path)],
        "allow_gui": False,
        "limits": {
            "timeout_seconds": 1,
            "max_cpu_seconds": 1,
            "max_memory_bytes": 1024,
            "max_processes": 1,
            "max_written_bytes": 1024,
        },
    }

    assert decode_payload(encode_payload(payload)) == payload
    payload["limits"]["max_processes"] = 0
    with pytest.raises(ValueError, match="max_processes"):
        decode_payload(encode_payload(payload))
    with pytest.raises(ValueError, match="Ungültige"):
        decode_payload("nicht-base64!")


def test_platform_adapter_selects_windows_appcontainer(monkeypatch):
    monkeypatch.setattr(sandbox, "_adapter_override", None)
    monkeypatch.setattr(sandbox, "_default_adapter", None)
    monkeypatch.setattr(sandbox.platform, "system", lambda: "Windows")

    assert isinstance(sandbox._platform_adapter(), WindowsAppContainerAdapter)


def test_platform_adapter_selects_macos_seatbelt(monkeypatch):
    monkeypatch.setattr(sandbox, "_adapter_override", None)
    monkeypatch.setattr(sandbox, "_default_adapter", None)
    monkeypatch.setattr(sandbox.platform, "system", lambda: "Darwin")

    assert isinstance(sandbox._platform_adapter(), MacOSSeatbeltAdapter)


def test_macos_adapter_builds_fail_closed_profile_and_private_environment(
    tmp_path, monkeypatch
):
    readable = tmp_path / "course"
    writable = tmp_path / "project"
    readable.mkdir()
    writable.mkdir()
    adapter = MacOSSeatbeltAdapter("/usr/bin/sandbox-exec")
    monkeypatch.setattr(
        adapter,
        "status",
        lambda: SandboxStatus(True, adapter.name, "Darwin", "ok", True, True, True, True),
    )
    policy = student_policy(
        writable,
        readable_roots=(readable,),
        writable_roots=(writable,),
    )

    launch = adapter.prepare(
        [sys.executable, str(readable / "main.py")],
        cwd=writable,
        environment={"PATH": "/usr/bin"},
        policy=policy,
    )

    profile = launch.command[2]
    assert launch.command[:2] == ("/usr/bin/sandbox-exec", "-p")
    assert "(deny default)" in profile
    assert "(allow process-exec process-fork)" in profile
    assert "(allow network*)" not in profile
    assert "(allow mach-lookup)" not in profile
    assert f'(subpath "{readable.resolve()}")' in profile
    assert f'(subpath "{writable.resolve()}")' in profile
    assert launch.environment["INSI_SANDBOX"] == "macos-seatbelt"
    assert launch.environment["HOME"] == str(launch.cleanup_paths[0])
    shutil.rmtree(launch.cleanup_paths[0])


def test_macos_adapter_adds_gui_and_explicit_network_capabilities(
    tmp_path, monkeypatch
):
    adapter = MacOSSeatbeltAdapter("/usr/bin/sandbox-exec")
    monkeypatch.setattr(
        adapter,
        "status",
        lambda: SandboxStatus(True, adapter.name, "Darwin", "ok", True, True, True, True),
    )
    policy = student_policy(tmp_path, allow_gui=True)
    object.__setattr__(policy, "allow_network", True)

    launch = adapter.prepare(
        [sys.executable, "-c", "pass"],
        cwd=tmp_path,
        environment={},
        policy=policy,
    )

    assert "(allow network*)" in launch.command[2]
    assert "(allow mach-lookup)" in launch.command[2]
    assert "(allow iokit-open)" in launch.command[2]
    shutil.rmtree(launch.cleanup_paths[0])


def test_macos_temporary_home_is_removed_after_process_exit(tmp_path):
    temporary = tmp_path / "temporary-home"
    temporary.mkdir()
    policy = student_policy(tmp_path)
    native = subprocess.Popen([sys.executable, "-c", "pass"])
    process = SandboxedProcess(
        native,
        policy,
        baseline_written_bytes=0,
        cleanup_paths=(temporary,),
    )

    process.wait(timeout=5)

    assert not temporary.exists()


def test_macos_temporary_home_counts_towards_write_limit(tmp_path):
    temporary = tmp_path / "temporary-home"
    temporary.mkdir()
    policy = student_policy(tmp_path, max_written_bytes=1024)
    native = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import time; "
            f"Path({str(temporary / 'large.bin')!r}).write_bytes(b'x' * 200000); "
            "time.sleep(30)",
        ]
    )
    process = SandboxedProcess(
        native,
        policy,
        baseline_written_bytes=0,
        cleanup_paths=(temporary,),
        monitored_writable_roots=(*policy.writable_roots, temporary),
    )

    process.wait(timeout=5)

    assert process.violation_reason is not None
    assert "Schreibgrenze" in process.violation_reason
    assert not temporary.exists()


@pytest.mark.parametrize(
    ("value", "expected"),
    [("01:02", 62.0), ("1:02:03", 3723.0), ("2-01:02:03", 176523.0)],
)
def test_macos_ps_cpu_time_parser(value, expected):
    assert sandbox._darwin_cpu_seconds(value) == expected


def test_sandboxed_process_imports_native_broker_violation_reason(tmp_path):
    violation_file = tmp_path / "violation.txt"
    violation_file.write_text("Prozessgrenze überschritten.", encoding="utf-8")
    policy = student_policy(tmp_path)
    native = subprocess.Popen([sys.executable, "-c", "pass"])
    process = SandboxedProcess(
        native,
        policy,
        baseline_written_bytes=0,
        violation_file=violation_file,
    )

    process.wait(timeout=5)

    assert process.violation_reason == "Prozessgrenze überschritten."
    assert not violation_file.exists()


def test_windows_process_termination_falls_back_after_invalid_console_handle(
    monkeypatch,
):
    events = []

    class NativeProcess:
        pid = 123

        @staticmethod
        def poll():
            return None

        @staticmethod
        def send_signal(_signal):
            raise SystemError("invalid Windows console handle")

        @staticmethod
        def terminate():
            events.append("terminate")

    process = object.__new__(SandboxedProcess)
    process._process = NativeProcess()
    monkeypatch.setattr(sandbox.os, "name", "nt")
    monkeypatch.setattr(sandbox.signal, "CTRL_BREAK_EVENT", 1, raising=False)

    process.terminate_tree()

    assert events == ["terminate"]


def test_frozen_windows_children_reset_the_pyinstaller_environment(monkeypatch):
    monkeypatch.setattr(sandbox.sys, "frozen", True, raising=False)
    monkeypatch.setattr(sandbox.sys, "platform", "win32")

    environment = sandbox._independent_frozen_environment({"PATH": "runtime"})

    assert environment == {
        "PATH": "runtime",
        "PYINSTALLER_RESET_ENVIRONMENT": "1",
    }


def test_internal_windows_onefile_children_reuse_the_extracted_runtime(monkeypatch):
    monkeypatch.setattr(sandbox.sys, "frozen", True, raising=False)
    monkeypatch.setattr(sandbox.sys, "platform", "win32")
    monkeypatch.setenv("_PYI_ARCHIVE_FILE", "insi.exe")
    monkeypatch.setenv("_PYI_APPLICATION_HOME_DIR", "runtime")
    monkeypatch.setenv("INSI_PREAUTHORIZED_RUNTIME_ROOT", "runtime")

    environment = sandbox._reused_frozen_environment({
        "PATH": "runtime",
        "PYINSTALLER_RESET_ENVIRONMENT": "1",
    })

    assert environment == {
        "PATH": "runtime",
        "_PYI_ARCHIVE_FILE": "insi.exe",
        "_PYI_APPLICATION_HOME_DIR": "runtime",
        "INSI_PREAUTHORIZED_RUNTIME_ROOT": "runtime",
    }


def test_windows_probe_preserves_staged_application_root():
    source = Path(sandbox.__file__).read_text(encoding="utf-8")

    assert "STAGED_APPLICATION_ENV," in source


def test_windows_broker_declares_fail_closed_kernel_controls():
    source = (
        Path(__file__).parents[1] / "src/insi/windows_sandbox_helper.py"
    ).read_text(encoding="utf-8")

    for expected in (
        "PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES",
        "PROC_THREAD_ATTRIBUTE_HANDLE_LIST",
        "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
        "JOB_OBJECT_LIMIT_ACTIVE_PROCESS",
        "JOB_OBJECT_LIMIT_JOB_MEMORY",
        "CreateAppContainerProfile",
        "AssignProcessToJobObject",
    ):
        assert expected in source
    assert "GetAppContainerFolderPath(\n            self.sid_string" in source
    assert 'self._icacls(parent, ["/grant:r", f"*{self.sid_string}:RX"])' in source
    assert 'if not self.payload["allow_gui"]:' in source
    assert 'creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)' in source
    assert "is_windows_network_path(path)" in source
    assert 'bootstrap_continue.write_text("continue"' in source
    assert "if recursive:" in source


@pytest.mark.parametrize(
    ("metrics", "fragment"),
    [
        ((17, 0, 0.0), "Prozessgrenze"),
        ((1, 2 * 1024 * 1024, 0.0), "Arbeitsspeichergrenze"),
        ((1, 0, 121.0), "CPU-Zeitgrenze"),
    ],
)
def test_supervisor_kills_the_process_tree_on_resource_violation(
    tmp_path, monkeypatch, metrics, fragment
):
    monkeypatch.setattr(sandbox, "_process_metrics", lambda _pid: metrics)
    policy = student_policy(
        tmp_path,
        max_processes=16,
        max_memory_bytes=1024 * 1024,
    )
    process = sandbox_popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        policy=policy,
        cwd=tmp_path,
        env=execution_environment(policy),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    process.wait(timeout=5)

    assert process.violation_reason is not None
    assert fragment in process.violation_reason


def test_supervisor_kills_a_program_that_exceeds_its_write_budget(tmp_path):
    policy = student_policy(tmp_path, max_written_bytes=1024)
    process = sandbox_popen(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import time; "
            "Path('large.bin').write_bytes(b'x' * 200000); time.sleep(30)",
        ],
        policy=policy,
        cwd=tmp_path,
        env=execution_environment(policy),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    process.wait(timeout=5)

    assert process.violation_reason is not None
    assert "Schreibgrenze" in process.violation_reason


@pytest.mark.skipif(
    platform.system() != "Linux" or shutil.which("bwrap") is None,
    reason="Der echte Bubblewrap-Test läuft nur auf Linux mit bwrap.",
)
def test_real_bubblewrap_hides_host_files_and_network(tmp_path, monkeypatch):
    adapter = BubblewrapAdapter()
    status = adapter.status()
    if not status.available:
        if os.environ.get("CI"):
            pytest.fail(status.detail)
        pytest.skip(status.detail)
    monkeypatch.setattr(sandbox, "_adapter_override", adapter)
    readable = tmp_path / "readable"
    writable = tmp_path / "writable"
    private = tmp_path / "private"
    readable.mkdir()
    writable.mkdir()
    private.mkdir()
    secret = private / "secret.txt"
    secret.write_text("host-secret", encoding="utf-8")
    program = readable / "probe.py"
    program.write_text(
        "import json, socket\n"
        "from pathlib import Path\n"
        f"secret = Path({str(secret)!r})\n"
        "result = {}\n"
        "try:\n result['secret'] = secret.read_text()\n"
        "except Exception:\n result['secret'] = 'blocked'\n"
        "try:\n secret.write_text('changed'); result['outside_write'] = 'allowed'\n"
        "except Exception:\n result['outside_write'] = 'blocked'\n"
        "try:\n socket.create_connection(('1.1.1.1', 53), .25); result['network'] = 'allowed'\n"
        "except Exception:\n result['network'] = 'blocked'\n"
        "Path('inside.txt').write_text('ok')\n"
        "print(json.dumps(result))\n",
        encoding="utf-8",
    )
    policy = student_policy(
        writable,
        readable_roots=(readable,),
        writable_roots=(writable,),
    )
    completed = sandbox_run(
        [sys.executable, str(program)],
        policy=policy,
        cwd=writable,
        env=execution_environment(policy),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "secret": "blocked",
        "outside_write": "blocked",
        "network": "blocked",
    }
    assert secret.read_text(encoding="utf-8") == "host-secret"
    assert (writable / "inside.txt").read_text(encoding="utf-8") == "ok"
