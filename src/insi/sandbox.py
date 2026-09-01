"""Betriebssystemsandbox und deterministische Prozessaufsicht für Lerncode."""

from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import warnings
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import IO, Any, Mapping, Protocol, Sequence

from .execution_security import CodeOrigin, ExecutionPolicy, popen_isolation_options
from .interpreter import python_command
from .windows_sandbox_helper import PAYLOAD_VERSION, encode_payload, windows_api_available
from .windows_paths import is_windows_network_path
from .windows_staging import (
    NetworkWriteback,
    WindowsNetworkRunStage,
    environment_has_network_path,
    sync_network_writebacks,
)


class SandboxUnavailableError(RuntimeError):
    """Die geforderte Schutzstufe kann auf diesem System nicht hergestellt werden."""


@dataclass(frozen=True)
class SandboxStatus:
    available: bool
    adapter: str
    platform: str
    detail: str
    filesystem_isolated: bool = False
    network_isolated: bool = False
    process_supervised: bool = True
    gui_available: bool = False

    @property
    def summary(self) -> str:
        if self.available:
            return f"Geschützte Ausführung aktiv: {self.adapter}."
        return (
            "Geschützte Ausführung ist nicht verfügbar; Fremdcode kann nur "
            "in einer externen IDE gestartet werden."
        )


@dataclass(frozen=True)
class PreparedLaunch:
    command: tuple[str, ...]
    cwd: Path
    environment: Mapping[str, str]
    adapter: str
    violation_file: Path | None = None
    cleanup_paths: tuple[Path, ...] = ()
    writebacks: tuple[NetworkWriteback, ...] = ()
    monitored_writable_roots: tuple[Path, ...] = ()


class SandboxAdapter(Protocol):
    name: str

    def status(self) -> SandboxStatus: ...

    def prepare(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        policy: ExecutionPolicy,
    ) -> PreparedLaunch: ...


def _existing_roots(paths: Sequence[str | Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    for value in paths:
        try:
            path = Path(value).expanduser().resolve()
        except (OSError, RuntimeError, ValueError):
            continue
        if path.exists() and path not in result:
            result.append(path)
    return tuple(result)


def _independent_frozen_environment(
    environment: Mapping[str, str],
) -> dict[str, str]:
    """Starte dieselbe PyInstaller-EXE als eigenständige neue Instanz."""
    child = dict(environment)
    if getattr(sys, "frozen", False) and sys.platform == "win32":
        child["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return child


def _remove_tree_with_retries(
    path: Path,
    *,
    attempts: int = 6,
    delay_seconds: float = 0.1,
) -> bool:
    """Entferne einen unter Windows kurzzeitig belegten temporären Baum."""
    for attempt in range(attempts):
        try:
            shutil.rmtree(path)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            if attempt + 1 < attempts:
                time.sleep(delay_seconds)
    return False


@contextmanager
def _temporary_windows_probe():
    """Räume den AppContainer-Probeordner trotz kurzer Fremdsperren auf."""
    path = Path(tempfile.mkdtemp(prefix="insi-win-sandbox-probe-"))
    try:
        yield path
    finally:
        if not _remove_tree_with_retries(path):
            warnings.warn(
                f"Temporärer Windows-Sandbox-Probeordner bleibt vorläufig bestehen: {path}",
                RuntimeWarning,
                stacklevel=2,
            )
            threading.Thread(
                target=_remove_tree_with_retries,
                args=(path,),
                kwargs={"attempts": 20, "delay_seconds": 0.5},
                name="insi-windows-probe-cleanup",
                daemon=True,
            ).start()


class BubblewrapAdapter:
    name = "Bubblewrap"

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("bwrap") or ""
        self._status: SandboxStatus | None = None

    def status(self) -> SandboxStatus:
        if self._status is not None:
            return self._status
        system = platform.system() or "Unbekannt"
        if system != "Linux":
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                "Bubblewrap steht nur unter Linux zur Verfügung.",
            )
            return self._status
        if not self.executable:
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                "Das Programm bwrap wurde nicht gefunden.",
            )
            return self._status
        runtime = os.environ.get("XDG_RUNTIME_DIR", "")
        wayland = os.environ.get("WAYLAND_DISPLAY", "")
        gui_available = bool(
            runtime and wayland and (Path(runtime) / wayland).exists()
        )
        try:
            with tempfile.TemporaryDirectory(
                prefix="insi-linux-sandbox-probe-"
            ) as temporary:
                root = Path(temporary).resolve()
                writable = root / "writable"
                private = root / "private"
                writable.mkdir()
                private.mkdir()
                secret = private / "secret.txt"
                secret.write_text("host-secret", encoding="utf-8")
                host_network_namespace = os.readlink("/proc/self/ns/net")
                host_pid_namespace = os.readlink("/proc/self/ns/pid")
                runner = python_command()
                command = [
                    *runner,
                    "-c",
                    (
                        "import json,os,socket,subprocess\n"
                        "from pathlib import Path\n"
                        f"secret=Path({str(secret)!r})\n"
                        f"runner={runner!r}\n"
                        "result={}\n"
                        "try:\n result['secret']=secret.read_text()\n"
                        "except Exception:\n result['secret']='blocked'\n"
                        "try:\n secret.write_text('changed'); result['outside_write']='allowed'\n"
                        "except Exception:\n result['outside_write']='blocked'\n"
                        "try:\n socket.create_connection(('1.1.1.1',53),.25); result['network']='allowed'\n"
                        "except Exception:\n result['network']='blocked'\n"
                        "result['network_namespace']=os.readlink('/proc/self/ns/net')\n"
                        "result['pid_namespace']=os.readlink('/proc/self/ns/pid')\n"
                        "child=subprocess.run([*runner,'-c','print(\"child-ok\")'],capture_output=True,text=True)\n"
                        "result['child']=child.stdout.strip()\n"
                        "Path('inside.txt').write_text('ok')\n"
                        "print(json.dumps(result))\n"
                    ),
                ]
                probe_policy = ExecutionPolicy(
                    CodeOrigin.STUDENT,
                    writable,
                    (writable,),
                    timeout_seconds=10,
                    max_output_chars=20_000,
                    max_memory_bytes=256 * 1024 * 1024,
                    max_processes=4,
                    max_written_bytes=1024 * 1024,
                    max_cpu_seconds=5,
                )
                launch = self._prepare_unchecked(
                    command,
                    cwd=writable,
                    environment=os.environ,
                    policy=probe_policy,
                )
                try:
                    probe = subprocess.run(
                        launch.command,
                        cwd=launch.cwd,
                        env=launch.environment,
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )
                finally:
                    for path in launch.cleanup_paths:
                        shutil.rmtree(path, ignore_errors=True)
                lines = [line for line in probe.stdout.splitlines() if line.strip()]
                result = json.loads(lines[-1]) if lines else {}
                passed = (
                    probe.returncode == 0
                    and result.get("secret") == "blocked"
                    and result.get("outside_write") == "blocked"
                    and result.get("network") == "blocked"
                    and result.get("network_namespace") != host_network_namespace
                    and result.get("pid_namespace") != host_pid_namespace
                    and result.get("child") == "child-ok"
                    and secret.read_text(encoding="utf-8") == "host-secret"
                    and (writable / "inside.txt").read_text(encoding="utf-8") == "ok"
                )
                if not passed:
                    message = (probe.stderr or probe.stdout).strip()
                    raise RuntimeError(
                        message or "Der Isolationstest lieferte ein falsches Ergebnis."
                    )
        except (
            OSError,
            RuntimeError,
            ValueError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
        ) as error:
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                f"Bubblewrap-Isolationstest fehlgeschlagen: {error}",
            )
            return self._status
        self._status = SandboxStatus(
            True,
            self.name,
            system,
            "Dateisystem-, Prozess- und Netzwerkisolation wurden erfolgreich geprüft."
            + (
                " Geschützte Grafik ist über Wayland verfügbar."
                if gui_available
                else " Für Grafikstarts fehlt eine geschützte Wayland-Sitzung."
            ),
            filesystem_isolated=True,
            network_isolated=True,
            gui_available=gui_available,
        )
        return self._status

    @staticmethod
    def _runtime_roots(command: Sequence[str], environment: Mapping[str, str]) -> tuple[Path, ...]:
        candidates: list[str | Path] = []
        if command:
            executable = shutil.which(command[0]) or command[0]
            path = Path(executable).expanduser()
            if path.exists():
                resolved = path.resolve()
                candidates.extend((path.parent, resolved.parent, resolved.parent.parent))
        candidates.extend(
            (
                Path(sys.prefix),
                Path(sys.base_prefix),
                Path(__file__).resolve().parents[1],
            )
        )
        return _existing_roots(candidates)

    @staticmethod
    def _resolved_command(command: Sequence[str]) -> tuple[str, ...]:
        if not command:
            return ()
        executable = shutil.which(str(command[0])) or str(command[0])
        try:
            executable = str(Path(executable).expanduser().resolve(strict=True))
        except (OSError, RuntimeError):
            executable = str(command[0])
        return (executable, *(str(argument) for argument in command[1:]))

    @staticmethod
    def _system_layout(
        paths: Sequence[str | Path] = (
            "/usr",
            "/bin",
            "/sbin",
            "/lib",
            "/lib64",
            "/etc",
        ),
    ) -> tuple[tuple[Path, ...], tuple[tuple[str, str], ...]]:
        roots: list[Path] = []
        links: list[tuple[str, str]] = []
        for value in paths:
            path = Path(value).expanduser()
            try:
                if path.is_symlink():
                    links.append((os.readlink(path), str(path)))
                resolved = path.resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if resolved not in roots:
                roots.append(resolved)
        return tuple(roots), tuple(links)

    @staticmethod
    def _gui_roots(environment: Mapping[str, str]) -> tuple[Path, ...]:
        candidates: list[Path] = []
        runtime = environment.get("XDG_RUNTIME_DIR")
        if runtime:
            runtime_path = Path(runtime)
            for name in (
                environment.get("WAYLAND_DISPLAY", ""),
                "pipewire-0",
                "pulse/native",
            ):
                if name:
                    candidates.append(runtime_path / name)
        return _existing_roots(candidates)

    def prepare(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        policy: ExecutionPolicy,
    ) -> PreparedLaunch:
        status = self.status()
        if not status.available:
            raise SandboxUnavailableError(status.detail)
        if policy.allow_gui and not status.gui_available:
            raise SandboxUnavailableError(
                "Geschützte Grafikstarts benötigen eine Wayland-Sitzung. "
                "Öffne das Programm stattdessen in der externen IDE."
            )
        return self._prepare_unchecked(
            command,
            cwd=cwd,
            environment=environment,
            policy=policy,
        )

    def _prepare_unchecked(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        policy: ExecutionPolicy,
    ) -> PreparedLaunch:
        writable = _existing_roots(policy.writable_roots)
        if len(writable) != len(policy.writable_roots):
            raise ValueError("Alle freigegebenen Schreibbereiche müssen vorhanden sein.")
        readable = _existing_roots(
            (*policy.readable_roots, *self._runtime_roots(command, environment))
        )
        system_roots, system_links = self._system_layout()
        temporary = Path(tempfile.mkdtemp(prefix="insi-linux-sandbox-run-")).resolve()
        home = temporary / "insi-home"
        home.mkdir()
        try:
            arguments = [
                self.executable,
                "--unshare-all",
                "--cap-drop", "ALL",
                "--die-with-parent",
                "--new-session",
                "--proc", "/proc",
                "--dev", "/dev",
                "--bind", str(temporary), "/tmp",
            ]
            if policy.allow_network:
                arguments.append("--share-net")
            mounted: set[Path] = set()
            for root in (*system_roots, *readable):
                if root in mounted or any(root.is_relative_to(item) for item in mounted):
                    continue
                arguments.extend(("--ro-bind", str(root), str(root)))
                mounted.add(root)
            for target, alias in system_links:
                arguments.extend(("--symlink", target, alias))
            if policy.allow_gui:
                for root in self._gui_roots(environment):
                    arguments.extend(("--ro-bind", str(root), str(root)))
            for root in writable:
                arguments.extend(("--bind", str(root), str(root)))
            arguments.extend(
                ("--chdir", str(cwd), "--", *self._resolved_command(command))
            )
            child_environment = dict(environment)
            child_environment.update(
                {
                    "HOME": "/tmp/insi-home",
                    "TMPDIR": "/tmp",
                    "TEMP": "/tmp",
                    "TMP": "/tmp",
                    "XDG_CACHE_HOME": "/tmp/insi-home/.cache",
                    "XDG_CONFIG_HOME": "/tmp/insi-home/.config",
                    "XDG_DATA_HOME": "/tmp/insi-home/.local/share",
                    "INSI_SANDBOX": "bubblewrap",
                }
            )
            return PreparedLaunch(
                tuple(arguments),
                cwd,
                child_environment,
                self.name,
                cleanup_paths=(temporary,),
            )
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise


class WindowsAppContainerAdapter:
    """Windows-AppContainer mit einem Job Object in einem separaten Broker."""

    name = "Windows AppContainer"

    def __init__(self) -> None:
        self._status: SandboxStatus | None = None

    @staticmethod
    def _runtime_roots(
        command: Sequence[str], environment: Mapping[str, str]
    ) -> tuple[Path, ...]:
        roots = list(BubblewrapAdapter._runtime_roots(command, environment))
        if command:
            executable = Path(
                shutil.which(str(command[0])) or command[0]
            ).expanduser()
            try:
                executable = executable.resolve()
            except (OSError, RuntimeError):
                pass
            # Der PyInstaller-Starter öffnet sein eingebettetes Archiv nach dem
            # Prozessstart erneut. Dafür braucht auch die einzelne EXE selbst
            # eine explizite Lesefreigabe und nicht nur ihr Elternverzeichnis.
            if executable.is_file():
                roots.append(executable)
            for candidate in (executable.parent.parent, executable.parent):
                configuration = candidate / "pyvenv.cfg"
                if not configuration.is_file():
                    continue
                roots.append(candidate)
                try:
                    for line in configuration.read_text(encoding="utf-8").splitlines():
                        key, separator, value = line.partition("=")
                        if separator and key.strip().lower() == "home":
                            home = Path(value.strip()).expanduser().resolve()
                            roots.extend((home, home.parent))
                            break
                except (OSError, RuntimeError, UnicodeError):
                    continue
        return _existing_roots(roots)

    @staticmethod
    def _broker_command(payload: Mapping[str, Any]) -> tuple[str, ...]:
        return (
            *python_command(),
            "-m",
            "insi.windows_sandbox_helper",
            "--payload",
            encode_payload(payload),
        )

    def _payload(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        policy: ExecutionPolicy,
        violation_file: Path | None = None,
    ) -> dict[str, Any]:
        readable = _existing_roots(
            (*policy.readable_roots, *self._runtime_roots(command, environment))
        )
        writable = _existing_roots(policy.writable_roots)
        if len(writable) != len(policy.writable_roots):
            raise ValueError("Alle freigegebenen Schreibbereiche müssen vorhanden sein.")
        child_environment = _independent_frozen_environment(environment)
        child_environment["INSI_SANDBOX"] = "windows-appcontainer"
        payload: dict[str, Any] = {
            "version": PAYLOAD_VERSION,
            "profile": f"de.simplicissima.insi.sandbox.{uuid.uuid4().hex}",
            "command": [str(item) for item in command],
            "cwd": str(cwd),
            "environment": child_environment,
            "readable_roots": [str(path) for path in readable],
            "writable_roots": [str(path) for path in writable],
            "allow_gui": policy.allow_gui,
            "limits": {
                "timeout_seconds": policy.timeout_seconds,
                "max_cpu_seconds": policy.max_cpu_seconds,
                "max_memory_bytes": policy.max_memory_bytes,
                "max_processes": policy.max_processes,
                "max_written_bytes": policy.max_written_bytes,
            },
        }
        if violation_file is not None:
            payload["violation_file"] = str(violation_file)
        return payload

    def status(self) -> SandboxStatus:
        if self._status is not None:
            return self._status
        system = platform.system() or "Unbekannt"
        if system != "Windows" or os.name != "nt":
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                "Windows AppContainer steht nur unter Windows zur Verfügung.",
            )
            return self._status
        available, detail = windows_api_available()
        if not available:
            self._status = SandboxStatus(False, self.name, system, detail)
            return self._status
        try:
            with _temporary_windows_probe() as root:
                writable = root / "writable"
                private = root / "private"
                writable.mkdir()
                private.mkdir()
                secret = private / "secret.txt"
                secret.write_text("host-secret", encoding="utf-8")
                probe_code = (
                    "import json,socket\n"
                    "from pathlib import Path\n"
                    f"secret=Path({str(secret)!r})\n"
                    "result={}\n"
                    "try:\n result['secret']=secret.read_text()\n"
                    "except Exception:\n result['secret']='blocked'\n"
                    "try:\n socket.create_connection(('1.1.1.1',53),.25); result['network']='allowed'\n"
                    "except Exception:\n result['network']='blocked'\n"
                    "Path('inside.txt').write_text('ok')\n"
                    "print(json.dumps(result))\n"
                )
                command = [*python_command(), "-c", probe_code]
                probe_environment = _independent_frozen_environment({
                    name: os.environ[name]
                    for name in ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR")
                    if name in os.environ
                })
                probe_environment["PYTHONUNBUFFERED"] = "1"
                probe_policy = ExecutionPolicy(
                    CodeOrigin.STUDENT,
                    writable,
                    (writable,),
                    timeout_seconds=10,
                    max_output_chars=20_000,
                    max_memory_bytes=256 * 1024 * 1024,
                    max_processes=4,
                    max_written_bytes=1024 * 1024,
                    max_cpu_seconds=5,
                )
                payload = self._payload(
                    command,
                    cwd=writable,
                    environment=probe_environment,
                    policy=probe_policy,
                )
                probe = subprocess.run(
                    self._broker_command(payload),
                    cwd=writable,
                    env=_independent_frozen_environment(os.environ),
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                lines = [line for line in probe.stdout.splitlines() if line.strip()]
                result = __import__("json").loads(lines[-1]) if lines else {}
                passed = (
                    probe.returncode == 0
                    and result == {"secret": "blocked", "network": "blocked"}
                    and secret.read_text(encoding="utf-8") == "host-secret"
                    and (writable / "inside.txt").read_text(encoding="utf-8") == "ok"
                )
                if not passed:
                    message = (probe.stderr or probe.stdout).strip()
                    raise RuntimeError(message or "Der Isolationstest lieferte ein falsches Ergebnis.")
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                f"Windows-AppContainer-Probelauf fehlgeschlagen: {error}",
            )
            return self._status
        self._status = SandboxStatus(
            True,
            self.name,
            system,
            "AppContainer-Datei- und Netzwerkisolation sowie Job Object wurden erfolgreich geprüft.",
            filesystem_isolated=True,
            network_isolated=True,
            gui_available=True,
        )
        return self._status

    def prepare(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        policy: ExecutionPolicy,
    ) -> PreparedLaunch:
        status = self.status()
        if not status.available:
            raise SandboxUnavailableError(status.detail)
        if policy.allow_network:
            raise SandboxUnavailableError(
                "Netzwerkfähigkeiten für den Windows-AppContainer sind nicht freigegeben."
            )
        stage: WindowsNetworkRunStage | None = None
        mapped_command = tuple(map(str, command))
        mapped_cwd = cwd
        mapped_environment = dict(environment)
        mapped_policy = policy
        network_values = (
            cwd,
            *policy.readable_roots,
            *policy.writable_roots,
            *(command[:1] if command else ()),
        )
        if (
            any(is_windows_network_path(value) for value in network_values)
            or environment_has_network_path(environment)
        ):
            stage = WindowsNetworkRunStage(environment)
            try:
                mapped_readable = tuple(
                    stage.stage_path(path) for path in policy.readable_roots
                )
                mapped_writable = tuple(
                    stage.stage_path(path, writable=True)
                    for path in policy.writable_roots
                )
                if is_windows_network_path(cwd):
                    stage.stage_path(cwd, writable=cwd in policy.writable_roots)
                if command and is_windows_network_path(command[0]):
                    stage.stage_path(Path(command[0]).parent)
                mapped_command = tuple(
                    str(stage.map_path(item))
                    if is_windows_network_path(item)
                    else str(item)
                    for item in command
                )
                mapped_cwd = stage.map_path(cwd)
                mapped_environment = stage.map_environment(environment)
                mapped_policy = replace(
                    policy,
                    workspace=stage.map_path(policy.workspace),
                    readable_roots=mapped_readable,
                    writable_roots=mapped_writable,
                )
            except Exception:
                shutil.rmtree(stage.root, ignore_errors=True)
                raise
        descriptor, filename = tempfile.mkstemp(prefix="insi-win-sandbox-status-")
        os.close(descriptor)
        violation_file = Path(filename)
        try:
            payload = self._payload(
                mapped_command,
                cwd=mapped_cwd,
                environment=mapped_environment,
                policy=mapped_policy,
                violation_file=violation_file,
            )
        except Exception:
            violation_file.unlink(missing_ok=True)
            if stage is not None:
                shutil.rmtree(stage.root, ignore_errors=True)
            raise
        broker_environment = _independent_frozen_environment(mapped_environment)
        broker_environment["INSI_SANDBOX"] = "windows-appcontainer-broker"
        return PreparedLaunch(
            self._broker_command(payload),
            mapped_cwd,
            broker_environment,
            self.name,
            violation_file,
            (stage.root,) if stage is not None else (),
            stage.writebacks if stage is not None else (),
            mapped_policy.writable_roots,
        )


class MacOSSeatbeltAdapter:
    """Nativer macOS-Runner mit einem pro Start erzeugten Seatbelt-Profil."""

    name = "macOS Seatbelt"

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or (
            "/usr/bin/sandbox-exec" if Path("/usr/bin/sandbox-exec").is_file() else ""
        )
        self._status: SandboxStatus | None = None

    @staticmethod
    def _profile_path(path: Path) -> str:
        rule = "subpath" if path.is_dir() else "literal"
        return f"({rule} {json.dumps(str(path))})"

    @staticmethod
    def _runtime_roots(
        command: Sequence[str], environment: Mapping[str, str]
    ) -> tuple[Path, ...]:
        return BubblewrapAdapter._runtime_roots(command, environment)

    @staticmethod
    def _system_roots() -> tuple[Path, ...]:
        return _existing_roots(
            (
                "/System",
                "/usr/bin",
                "/usr/lib",
                "/usr/share",
                "/bin",
                "/sbin",
                "/Library/Apple",
                "/private/var/db/timezone",
            )
        )

    def _profile(
        self,
        *,
        readable: Sequence[Path],
        writable: Sequence[Path],
        allow_network: bool,
        allow_gui: bool,
    ) -> str:
        read_rules = "\n    ".join(
            self._profile_path(path)
            for path in _existing_roots((*self._system_roots(), *readable, *writable))
        )
        write_rules = "\n    ".join(
            self._profile_path(path) for path in _existing_roots(writable)
        )
        lines = [
            "(version 1)",
            "(deny default)",
            '(import "system.sb")',
            "(allow process-exec process-fork)",
            "(allow process-info* signal (target self) (target children))",
            "(allow file-read-metadata)",
            "(allow file-test-existence)",
            "(allow sysctl-read)",
            "(allow file-read* file-map-executable",
            f"    {read_rules})",
            "(allow file-write*",
            f"    {write_rules})",
            "(allow file-read* file-write*",
            '    (literal "/dev/null")',
            '    (literal "/dev/random")',
            '    (literal "/dev/urandom")',
            '    (literal "/dev/zero"))',
        ]
        if allow_network:
            lines.append("(allow network*)")
        if allow_gui:
            # Cocoa, SDL/Pyxel und CoreAudio sprechen über Mach, IOKit und
            # POSIX-IPC mit den Diensten der aktuellen grafischen Sitzung.
            # Datei-, Netzwerk- und Prozessrechte bleiben davon unberührt.
            lines.extend(
                (
                    "(allow mach-lookup)",
                    "(allow ipc-posix*)",
                    "(allow iokit-open)",
                    "(allow user-preference-read)",
                )
            )
        return "\n".join(lines)

    @staticmethod
    def _child_environment(
        environment: Mapping[str, str], temporary: Path
    ) -> dict[str, str]:
        child = dict(environment)
        child.update(
            {
                "HOME": str(temporary),
                "TMPDIR": str(temporary),
                "TEMP": str(temporary),
                "TMP": str(temporary),
                "XDG_CACHE_HOME": str(temporary / ".cache"),
                "XDG_CONFIG_HOME": str(temporary / ".config"),
                "XDG_DATA_HOME": str(temporary / ".local" / "share"),
                "INSI_SANDBOX": "macos-seatbelt",
            }
        )
        return child

    def status(self) -> SandboxStatus:
        if self._status is not None:
            return self._status
        system = platform.system() or "Unbekannt"
        if system != "Darwin":
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                "Der Seatbelt-Runner steht nur unter macOS zur Verfügung.",
            )
            return self._status
        if not self.executable or not Path(self.executable).is_file():
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                "Das macOS-Systemprogramm sandbox-exec wurde nicht gefunden.",
            )
            return self._status
        try:
            with tempfile.TemporaryDirectory(
                prefix="insi-macos-sandbox-probe-"
            ) as temporary:
                root = Path(temporary).resolve()
                writable = root / "writable"
                private = root / "private"
                runtime = root / "runtime"
                writable.mkdir()
                private.mkdir()
                runtime.mkdir()
                secret = private / "secret.txt"
                secret.write_text("host-secret", encoding="utf-8")
                runner = python_command()
                command = [
                    *runner,
                    "-c",
                    (
                        "import json,socket,subprocess,sys\n"
                        "from pathlib import Path\n"
                        f"secret=Path({str(secret)!r})\n"
                        "result={}\n"
                        "try:\n result['secret']=secret.read_text()\n"
                        "except Exception:\n result['secret']='blocked'\n"
                        "try:\n secret.write_text('changed'); result['outside_write']='allowed'\n"
                        "except Exception:\n result['outside_write']='blocked'\n"
                        "try:\n socket.create_connection(('127.0.0.1',9),.25); result['network']='allowed'\n"
                        "except Exception:\n result['network']='blocked'\n"
                        f"runner={runner!r}\n"
                        "child=subprocess.run([*runner,'-c','print(\"child-ok\")'],capture_output=True,text=True)\n"
                        "result['child']=child.stdout.strip()\n"
                        "Path('inside.txt').write_text('ok')\n"
                        "print(json.dumps(result))\n"
                    ),
                ]
                readable = self._runtime_roots(command, os.environ)
                profile = self._profile(
                    readable=readable,
                    writable=(writable, runtime),
                    allow_network=False,
                    allow_gui=False,
                )
                probe = subprocess.run(
                    [self.executable, "-p", profile, *command],
                    cwd=writable,
                    env=self._child_environment(os.environ, runtime),
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                lines = [line for line in probe.stdout.splitlines() if line.strip()]
                result = json.loads(lines[-1]) if lines else {}
                expected = {
                    "secret": "blocked",
                    "outside_write": "blocked",
                    "network": "blocked",
                    "child": "child-ok",
                }
                passed = (
                    probe.returncode == 0
                    and result == expected
                    and secret.read_text(encoding="utf-8") == "host-secret"
                    and (writable / "inside.txt").read_text(encoding="utf-8") == "ok"
                )
                if not passed:
                    message = (probe.stderr or probe.stdout).strip()
                    raise RuntimeError(
                        message or "Der Isolationstest lieferte ein falsches Ergebnis."
                    )
        except (
            OSError,
            RuntimeError,
            ValueError,
            json.JSONDecodeError,
            subprocess.SubprocessError,
        ) as error:
            self._status = SandboxStatus(
                False,
                self.name,
                system,
                f"macOS-Seatbelt-Probelauf fehlgeschlagen: {error}",
            )
            return self._status
        self._status = SandboxStatus(
            True,
            self.name,
            system,
            "Seatbelt-Datei-, Netzwerk- und Prozessisolation wurden erfolgreich geprüft.",
            filesystem_isolated=True,
            network_isolated=True,
            gui_available=True,
        )
        return self._status

    def prepare(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        policy: ExecutionPolicy,
    ) -> PreparedLaunch:
        status = self.status()
        if not status.available:
            raise SandboxUnavailableError(status.detail)
        writable = _existing_roots(policy.writable_roots)
        if len(writable) != len(policy.writable_roots):
            raise ValueError("Alle freigegebenen Schreibbereiche müssen vorhanden sein.")
        readable = _existing_roots(
            (*policy.readable_roots, *self._runtime_roots(command, environment))
        )
        temporary = Path(tempfile.mkdtemp(prefix="insi-macos-sandbox-run-")).resolve()
        try:
            profile = self._profile(
                readable=readable,
                writable=(*writable, temporary),
                allow_network=policy.allow_network,
                allow_gui=policy.allow_gui,
            )
            child_environment = self._child_environment(environment, temporary)
            return PreparedLaunch(
                (self.executable, "-p", profile, *map(str, command)),
                cwd,
                child_environment,
                self.name,
                cleanup_paths=(temporary,),
            )
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise


class _TrustedLocalAdapter:
    """Nur für mit dem Release ausgelieferten und geprüften Programmcode."""

    name = "Vertrauenswürdiger lokaler Start"

    def status(self) -> SandboxStatus:
        return SandboxStatus(
            True,
            self.name,
            platform.system() or "Unbekannt",
            "Nur für mitgelieferten Release-Code.",
            gui_available=True,
        )

    def prepare(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        policy: ExecutionPolicy,
    ) -> PreparedLaunch:
        child_environment = dict(environment)
        child_environment["INSI_SANDBOX"] = "trusted-local"
        return PreparedLaunch(tuple(map(str, command)), cwd, child_environment, self.name)


class _TestAdapter(_TrustedLocalAdapter):
    """Test-Double; wird ausschließlich durch Tests explizit eingesetzt."""

    name = "Testadapter"


_adapter_override: SandboxAdapter | None = None
_default_adapter: SandboxAdapter | None = None


def _platform_adapter() -> SandboxAdapter:
    global _default_adapter
    if _adapter_override is not None:
        return _adapter_override
    if _default_adapter is None:
        system = platform.system()
        if system == "Windows":
            _default_adapter = WindowsAppContainerAdapter()
        elif system == "Darwin":
            _default_adapter = MacOSSeatbeltAdapter()
        else:
            _default_adapter = BubblewrapAdapter()
    return _default_adapter


def sandbox_status() -> SandboxStatus:
    return _platform_adapter().status()


def prepare_launch(
    command: Sequence[str],
    *,
    cwd: str | Path,
    environment: Mapping[str, str],
    policy: ExecutionPolicy,
) -> PreparedLaunch:
    root = Path(cwd).expanduser().resolve()
    adapter = _platform_adapter()
    status = adapter.status()
    if not status.available:
        if policy.origin is CodeOrigin.BUILTIN:
            adapter = _TrustedLocalAdapter()
        else:
            raise SandboxUnavailableError(
                status.detail
                + " Nutze für dieses Programm die konfigurierte externe IDE."
            )
    return adapter.prepare(
        command,
        cwd=root,
        environment=environment,
        policy=policy,
    )


def _directory_size(roots: Sequence[Path], *, stop_after: int | None = None) -> int:
    total = 0
    seen: set[tuple[int, int]] = set()
    for root in roots:
        try:
            entries = (root,) if root.is_file() else root.rglob("*")
            for entry in entries:
                try:
                    stat = entry.stat(follow_symlinks=False)
                except (FileNotFoundError, OSError):
                    continue
                if not entry.is_file() or entry.is_symlink():
                    continue
                identity = (stat.st_dev, stat.st_ino)
                if identity in seen:
                    continue
                seen.add(identity)
                total += stat.st_size
                if stop_after is not None and total > stop_after:
                    return total
        except (FileNotFoundError, OSError):
            continue
    return total


def _linux_process_metrics(root_pid: int) -> tuple[int, int, float]:
    """Liefere Prozessanzahl, RSS und CPU-Zeit des Linux-Prozessbaums."""

    if platform.system() != "Linux" or not Path("/proc").is_dir():
        return 1, 0, 0.0
    parents: dict[int, int] = {}
    rss: dict[int, int] = {}
    cpu_ticks: dict[int, int] = {}
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            stat_text = (item / "stat").read_text(encoding="utf-8")
            fields = stat_text[stat_text.rfind(")") + 2:].split()
            pid = int(item.name)
            parents[pid] = int(fields[1])
            cpu_ticks[pid] = int(fields[11]) + int(fields[12])
            status_text = (item / "status").read_text(encoding="utf-8")
            rss_line = next(
                (line for line in status_text.splitlines() if line.startswith("VmRSS:")),
                "VmRSS: 0 kB",
            )
            rss[pid] = int(rss_line.split()[1]) * 1024
        except (FileNotFoundError, OSError, ValueError, IndexError):
            continue
    tree = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if parent in tree and pid not in tree:
                tree.add(pid)
                changed = True
    ticks_per_second = int(os.sysconf("SC_CLK_TCK"))
    return (
        len(tree),
        sum(rss.get(pid, 0) for pid in tree),
        sum(cpu_ticks.get(pid, 0) for pid in tree) / max(1, ticks_per_second),
    )


def _darwin_cpu_seconds(value: str) -> float:
    """Wandle die von macOS-ps gelieferte [[Tage-]Stunden:]Minuten:Sekunden-Zeit um."""

    days = 0
    clock = value.strip()
    if "-" in clock:
        day_text, clock = clock.split("-", 1)
        days = int(day_text)
    parts = [float(part) for part in clock.split(":")]
    seconds = parts.pop()
    if parts:
        seconds += parts.pop() * 60
    if parts:
        seconds += parts.pop() * 3600
    return days * 86400 + seconds


def _darwin_process_metrics(root_pid: int) -> tuple[int, int, float]:
    """Liefere Prozessanzahl, RSS und CPU-Zeit des macOS-Prozessbaums."""

    if platform.system() != "Darwin":
        return 1, 0, 0.0
    try:
        output = subprocess.run(
            ["/bin/ps", "-axo", "pid=,ppid=,rss=,time="],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return 1, 0, 0.0
    parents: dict[int, int] = {}
    rss: dict[int, int] = {}
    cpu: dict[int, float] = {}
    for line in output.splitlines():
        try:
            pid_text, parent_text, rss_text, cpu_text = line.split()
            pid = int(pid_text)
            parents[pid] = int(parent_text)
            rss[pid] = int(rss_text) * 1024
            cpu[pid] = _darwin_cpu_seconds(cpu_text)
        except (ValueError, IndexError):
            continue
    tree = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if parent in tree and pid not in tree:
                tree.add(pid)
                changed = True
    return len(tree), sum(rss.get(pid, 0) for pid in tree), sum(
        cpu.get(pid, 0.0) for pid in tree
    )


def _process_metrics(root_pid: int) -> tuple[int, int, float]:
    if platform.system() == "Linux":
        return _linux_process_metrics(root_pid)
    if platform.system() == "Darwin":
        return _darwin_process_metrics(root_pid)
    return 1, 0, 0.0


class SandboxedProcess:
    """Popen-kompatibler Prozess mit Ressourcenaufsicht und Abbruchgrund."""

    def __init__(
        self,
        process: subprocess.Popen[Any],
        policy: ExecutionPolicy,
        *,
        baseline_written_bytes: int,
        violation_file: Path | None = None,
        cleanup_paths: Sequence[Path] = (),
        monitored_writable_roots: Sequence[Path] | None = None,
        writebacks: Sequence[NetworkWriteback] = (),
    ) -> None:
        self._process = process
        self.policy = policy
        self.violation_reason: str | None = None
        self._baseline_written_bytes = baseline_written_bytes
        self._monitored_writable_roots = tuple(
            monitored_writable_roots or policy.writable_roots
        )
        self._violation_file = violation_file
        self._cleanup_paths = tuple(cleanup_paths)
        self._writebacks = tuple(writebacks)
        self._cleanup_lock = threading.Lock()
        self.output_truncated = False
        self._supervisor = threading.Thread(target=self._supervise, daemon=True)
        self._supervisor.start()

    def _supervise(self) -> None:
        while self._process.poll() is None:
            process_count, memory, cpu_seconds = _process_metrics(self._process.pid)
            reason = None
            if process_count > self.policy.max_processes:
                reason = (
                    f"Prozessgrenze überschritten ({process_count} statt maximal "
                    f"{self.policy.max_processes})."
                )
            elif memory > self.policy.max_memory_bytes:
                reason = (
                    "Arbeitsspeichergrenze überschritten "
                    f"({memory // (1024 * 1024)} MB statt maximal "
                    f"{self.policy.max_memory_bytes // (1024 * 1024)} MB)."
                )
            elif cpu_seconds > self.policy.max_cpu_seconds:
                reason = (
                    "CPU-Zeitgrenze überschritten "
                    f"({cpu_seconds:.1f} s statt maximal "
                    f"{self.policy.max_cpu_seconds:g} s)."
                )
            else:
                current = _directory_size(
                    self._monitored_writable_roots,
                    stop_after=self._baseline_written_bytes + self.policy.max_written_bytes,
                )
                growth = max(0, current - self._baseline_written_bytes)
                if growth > self.policy.max_written_bytes:
                    reason = (
                        "Schreibgrenze überschritten "
                        f"({growth // (1024 * 1024)} MB statt maximal "
                        f"{self.policy.max_written_bytes // (1024 * 1024)} MB)."
                    )
            if reason is not None:
                self.violation_reason = reason
                self.terminate_tree(force=True)
                return
            time.sleep(0.2)
        self._refresh_violation()

    def _cleanup(self) -> None:
        if self._process.poll() is None:
            return
        with self._cleanup_lock:
            paths = self._cleanup_paths
            writebacks = self._writebacks
            self._cleanup_paths = ()
            self._writebacks = ()
            if not paths and not writebacks:
                return
            try:
                sync_network_writebacks(writebacks)
            except OSError as error:
                if self.violation_reason is None:
                    self.violation_reason = f"Netzwerk-Synchronisierung fehlgeschlagen: {error}"
            finally:
                for path in paths:
                    shutil.rmtree(path, ignore_errors=True)

    def _refresh_violation(self) -> None:
        path = self._violation_file
        if self._process.poll() is None:
            return
        self._cleanup()
        if path is None:
            return
        self._violation_file = None
        try:
            reason = path.read_text(encoding="utf-8")[:2000].strip()
            if reason and self.violation_reason is None:
                self.violation_reason = reason
        except (FileNotFoundError, OSError, UnicodeError):
            pass
        finally:
            path.unlink(missing_ok=True)

    @property
    def pid(self) -> int:
        return self._process.pid

    @property
    def returncode(self) -> int | None:
        self._refresh_violation()
        return self._process.returncode

    @property
    def stdout(self) -> IO[Any] | None:
        return self._process.stdout

    @property
    def stderr(self) -> IO[Any] | None:
        return self._process.stderr

    def poll(self) -> int | None:
        result = self._process.poll()
        self._refresh_violation()
        return result

    def wait(self, timeout: float | None = None) -> int:
        result = self._process.wait(timeout=timeout)
        self._refresh_violation()
        return result

    def communicate(self, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        result = self._process.communicate(*args, **kwargs)
        self._refresh_violation()
        return result

    def communicate_bounded(
        self,
        *,
        timeout: float | None = None,
    ) -> tuple[str, str, bool, bool]:
        """Lese beide Ausgabeströme begrenzt und beende bei Ausgabeüberlauf."""

        buffers: dict[str, list[str]] = {"stdout": [], "stderr": []}
        lengths = {"stdout": 0, "stderr": 0}
        lock = threading.Lock()

        def read_stream(stream: IO[Any] | None, name: str) -> None:
            if stream is None:
                return
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    break
                if isinstance(chunk, bytes):
                    chunk = chunk.decode(errors="replace")
                should_kill = False
                with lock:
                    remaining = self.policy.max_output_chars - lengths[name]
                    if remaining > 0:
                        buffers[name].append(chunk[:remaining])
                        lengths[name] += min(len(chunk), remaining)
                    if len(chunk) > remaining:
                        self.output_truncated = True
                        if self.violation_reason is None:
                            self.violation_reason = (
                                "Ausgabegrenze überschritten "
                                f"(maximal {self.policy.max_output_chars} Zeichen pro Kanal)."
                            )
                            should_kill = True
                if should_kill:
                    self.terminate_tree(force=True)
            stream.close()

        readers = [
            threading.Thread(target=read_stream, args=(self.stdout, "stdout"), daemon=True),
            threading.Thread(target=read_stream, args=(self.stderr, "stderr"), daemon=True),
        ]
        for reader in readers:
            reader.start()
        timed_out = False
        try:
            self.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            self.terminate_tree()
            try:
                self.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.terminate_tree(force=True)
                self.wait()
        for reader in readers:
            reader.join(timeout=5)
        return (
            "".join(buffers["stdout"]),
            "".join(buffers["stderr"]),
            timed_out,
            self.output_truncated,
        )

    def terminate(self) -> None:
        self.terminate_tree()

    def kill(self) -> None:
        self.terminate_tree(force=True)

    def terminate_tree(self, *, force: bool = False) -> None:
        if self._process.poll() is not None:
            return
        if os.name != "nt":
            try:
                os.killpg(self._process.pid, 9 if force else 15)
                return
            except (OSError, ProcessLookupError):
                pass
        elif not force:
            try:
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
                return
            except (OSError, SystemError, ValueError):
                pass
        self._process.kill() if force else self._process.terminate()


def sandbox_popen(
    command: Sequence[str],
    *,
    policy: ExecutionPolicy,
    cwd: str | Path,
    env: Mapping[str, str],
    **kwargs: Any,
) -> SandboxedProcess:
    prepared = prepare_launch(command, cwd=cwd, environment=env, policy=policy)
    monitored_writable_roots = (
        prepared.monitored_writable_roots
        or (*policy.writable_roots, *prepared.cleanup_paths)
    )
    baseline = _directory_size(monitored_writable_roots)
    options = popen_isolation_options()
    options.update(kwargs)
    if prepared.adapter == WindowsAppContainerAdapter.name:
        options.setdefault("stdin", subprocess.DEVNULL)
        options.setdefault("stdout", subprocess.DEVNULL)
        options.setdefault("stderr", subprocess.DEVNULL)
    try:
        process = subprocess.Popen(
            list(prepared.command),
            cwd=prepared.cwd,
            env=dict(prepared.environment),
            **options,
        )
    except Exception:
        if prepared.violation_file is not None:
            prepared.violation_file.unlink(missing_ok=True)
        for path in prepared.cleanup_paths:
            shutil.rmtree(path, ignore_errors=True)
        raise
    return SandboxedProcess(
        process,
        policy,
        baseline_written_bytes=baseline,
        violation_file=prepared.violation_file,
        cleanup_paths=prepared.cleanup_paths,
        monitored_writable_roots=monitored_writable_roots,
        writebacks=prepared.writebacks,
    )


def sandbox_run(
    command: Sequence[str],
    *,
    policy: ExecutionPolicy,
    cwd: str | Path,
    env: Mapping[str, str],
    input: str | bytes | None = None,
    capture_output: bool = False,
    timeout: float | None = None,
    check: bool = False,
    text: bool = False,
    **kwargs: Any,
) -> subprocess.CompletedProcess[Any]:
    if capture_output:
        kwargs.setdefault("stdout", subprocess.PIPE)
        kwargs.setdefault("stderr", subprocess.PIPE)
    process = sandbox_popen(
        command,
        policy=policy,
        cwd=cwd,
        env=env,
        text=text,
        **kwargs,
    )
    if input is not None:
        raise ValueError("Sandboxläufe mit Standardeingabe werden nicht unterstützt.")
    if capture_output:
        stdout, stderr, timed_out, _truncated = process.communicate_bounded(
            timeout=timeout
        )
        if timed_out:
            raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
    else:
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.terminate_tree(force=True)
            process.wait()
            raise
        stdout = stderr = None
    if capture_output and process.violation_reason:
        stderr = (
            f"{stderr or ''}\nDas Programm wurde beendet: "
            f"{process.violation_reason}"
        ).strip()
    completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    completed.output_truncated = process.output_truncated
    completed.limit_reason = process.violation_reason
    if check and completed.returncode:
        raise subprocess.CalledProcessError(
            completed.returncode, command, output=stdout, stderr=stderr
        )
    return completed


__all__ = [
    "BubblewrapAdapter",
    "MacOSSeatbeltAdapter",
    "PreparedLaunch",
    "SandboxStatus",
    "SandboxUnavailableError",
    "SandboxedProcess",
    "WindowsAppContainerAdapter",
    "prepare_launch",
    "sandbox_popen",
    "sandbox_run",
    "sandbox_status",
]
