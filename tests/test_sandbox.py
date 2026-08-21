import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from insi import sandbox
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
    writable = tmp_path / "project"
    readable.parent.mkdir()
    readable.write_text("print('ok')", encoding="utf-8")
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
        ["course-python.exe", str(readable)],
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
    assert payload["command"] == ["course-python.exe", str(readable)]
    assert str(readable.resolve()) in payload["readable_roots"]
    assert payload["writable_roots"] == [str(writable.resolve())]
    assert payload["limits"]["max_processes"] == 3
    assert payload["limits"]["max_memory_bytes"] == 64 * 1024 * 1024
    assert payload["environment"]["INSI_SANDBOX"] == "windows-appcontainer"
    assert launch.environment["INSI_SANDBOX"] == "windows-appcontainer-broker"
    assert launch.violation_file is not None
    assert payload["violation_file"] == str(launch.violation_file)
    launch.violation_file.unlink()


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


def test_windows_broker_payload_rejects_tampering_and_invalid_limits(tmp_path):
    payload = {
        "version": 1,
        "profile": "de.simplicissima.insi.test",
        "command": ["python.exe", "-c", "pass"],
        "cwd": str(tmp_path),
        "environment": {},
        "readable_roots": [],
        "writable_roots": [str(tmp_path)],
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
