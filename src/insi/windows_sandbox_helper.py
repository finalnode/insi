"""Vertrauenswürdiger Windows-Broker für AppContainer-Lernprozesse.

Das Modul wird als separater, normaler in:si-Prozess gestartet. Es richtet den
AppContainer und das Job Object ein, startet darin ausschließlich den
übergebenen Lernprozess und hält das Job-Handle bis zu dessen Ende offen.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any, Mapping


PAYLOAD_VERSION = 1
MAX_PAYLOAD_BYTES = 64 * 1024


def encode_payload(payload: Mapping[str, Any]) -> str:
    """Kodiere eine kleine, nicht geheime Brokerkonfiguration."""

    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("Die Windows-Sandboxkonfiguration ist zu groß.")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_payload(value: str) -> dict[str, Any]:
    """Dekodiere und validiere die äußere Form einer Brokerkonfiguration."""

    try:
        raw = base64.b64decode(value.encode("ascii"), altchars=b"-_", validate=True)
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Ungültige Windows-Sandboxkonfiguration.") from error
    if len(raw) > MAX_PAYLOAD_BYTES or not isinstance(data, dict):
        raise ValueError("Ungültige Windows-Sandboxkonfiguration.")
    if data.get("version") != PAYLOAD_VERSION:
        raise ValueError("Nicht unterstützte Windows-Sandboxkonfiguration.")
    command = data.get("command")
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) and item for item in command
    ):
        raise ValueError("Der Windows-Sandboxbefehl fehlt oder ist ungültig.")
    for name in ("cwd", "profile"):
        if not isinstance(data.get(name), str) or not data[name]:
            raise ValueError(f"Das Windows-Sandboxfeld {name} fehlt.")
    for name in ("readable_roots", "writable_roots"):
        roots = data.get(name)
        if not isinstance(roots, list) or not all(
            isinstance(item, str) and item for item in roots
        ):
            raise ValueError(f"Das Windows-Sandboxfeld {name} ist ungültig.")
    environment = data.get("environment")
    if not isinstance(environment, dict) or not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in environment.items()
    ):
        raise ValueError("Die Windows-Sandboxumgebung ist ungültig.")
    violation_file = data.get("violation_file")
    if violation_file is not None and (
        not isinstance(violation_file, str) or not violation_file
    ):
        raise ValueError("Die Windows-Sandbox-Statusdatei ist ungültig.")
    limits = data.get("limits")
    if not isinstance(limits, dict):
        raise ValueError("Die Windows-Sandboxgrenzen fehlen.")
    for name in (
        "timeout_seconds",
        "max_cpu_seconds",
        "max_memory_bytes",
        "max_processes",
        "max_written_bytes",
    ):
        value = limits.get(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"Die Windows-Sandboxgrenze {name} ist ungültig.")
    return data


def windows_api_available() -> tuple[bool, str]:
    """Prüfe die für AppContainer und Job Objects nötigen Systemfunktionen."""

    if os.name != "nt":
        return False, "Der Windows-Broker kann nur unter Windows laufen."
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        userenv = ctypes.WinDLL("userenv", use_last_error=True)
        advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        for library, names in (
            (
                kernel32,
                (
                    "CreateJobObjectW",
                    "SetInformationJobObject",
                    "AssignProcessToJobObject",
                    "InitializeProcThreadAttributeList",
                    "UpdateProcThreadAttribute",
                    "CreateProcessW",
                ),
            ),
            (
                userenv,
                (
                    "CreateAppContainerProfile",
                    "DeriveAppContainerSidFromAppContainerName",
                    "DeleteAppContainerProfile",
                    "GetAppContainerFolderPath",
                ),
            ),
            (advapi32, ("ConvertSidToStringSidW",)),
        ):
            for name in names:
                getattr(library, name)
    except (AttributeError, OSError) as error:
        return False, f"Windows-AppContainer-API fehlt: {error}"
    if shutil.which("icacls") is None:
        return False, "Das Windows-Werkzeug icacls wurde nicht gefunden."
    return True, "Windows-AppContainer- und Job-Object-APIs sind vorhanden."


def _directory_size(roots: list[Path], *, stop_after: int) -> int:
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
                if total > stop_after:
                    return total
        except (FileNotFoundError, OSError):
            continue
    return total


if os.name == "nt":
    ULONG_PTR = ctypes.c_size_t
    SIZE_T = ctypes.c_size_t

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class STARTUPINFOEXW(ctypes.Structure):
        _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", wintypes.LPVOID)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    class SECURITY_CAPABILITIES(ctypes.Structure):
        _fields_ = [
            ("AppContainerSid", wintypes.LPVOID),
            ("Capabilities", wintypes.LPVOID),
            ("CapabilityCount", wintypes.DWORD),
            ("Reserved", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "ReadOperationCount",
            "WriteOperationCount",
            "OtherOperationCount",
            "ReadTransferCount",
            "WriteTransferCount",
            "OtherTransferCount",
        )]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", SIZE_T),
            ("MaximumWorkingSetSize", SIZE_T),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ULONG_PTR),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", SIZE_T),
            ("JobMemoryLimit", SIZE_T),
            ("PeakProcessMemoryUsed", SIZE_T),
            ("PeakJobMemoryUsed", SIZE_T),
        ]

    class JOBOBJECT_ASSOCIATE_COMPLETION_PORT(ctypes.Structure):
        _fields_ = [("CompletionKey", wintypes.LPVOID), ("CompletionPort", wintypes.HANDLE)]


class _WindowsBroker:
    ERROR_ALREADY_EXISTS_HRESULT = 0x800700B7
    ERROR_INSUFFICIENT_BUFFER = 122
    WAIT_OBJECT_0 = 0
    WAIT_TIMEOUT = 258
    INFINITE = 0xFFFFFFFF
    STARTF_USESTDHANDLES = 0x00000100
    EXTENDED_STARTUPINFO_PRESENT = 0x00080000
    CREATE_SUSPENDED = 0x00000004
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    CREATE_UNICODE_ENVIRONMENT = 0x00000400
    CREATE_NO_WINDOW = 0x08000000
    PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009
    PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
    HANDLE_FLAG_INHERIT = 0x00000001
    JOB_OBJECT_LIMIT_JOB_TIME = 0x00000004
    JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
    JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
    JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JOB_OBJECT_BASIC_UI_RESTRICTIONS = 4
    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION = 7
    JOB_OBJECT_UILIMIT_ALL = 0x000000FF
    JOB_OBJECT_MSG_END_OF_JOB_TIME = 1
    JOB_OBJECT_MSG_ACTIVE_PROCESS_LIMIT = 3
    JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT = 9
    JOB_OBJECT_MSG_JOB_MEMORY_LIMIT = 10

    def __init__(self, payload: Mapping[str, Any]) -> None:
        if os.name != "nt":
            raise RuntimeError("Der Windows-Broker kann nur unter Windows laufen.")
        self.payload = payload
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.userenv = ctypes.WinDLL("userenv", use_last_error=True)
        self.advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        self.ole32 = ctypes.WinDLL("ole32", use_last_error=True)
        self.sid = wintypes.LPVOID()
        self.sid_string = ""
        self.profile_folder: Path | None = None
        self.granted: list[Path] = []
        self.job: int | None = None
        self.completion_port: int | None = None
        self.process_handle: int | None = None
        self.thread_handle: int | None = None
        self.attribute_buffer: Any = None
        self._configure_signatures()

    def _configure_signatures(self) -> None:
        self.userenv.CreateAppContainerProfile.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.LPVOID),
        ]
        self.userenv.CreateAppContainerProfile.restype = wintypes.LONG
        self.userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(wintypes.LPVOID),
        ]
        self.userenv.DeriveAppContainerSidFromAppContainerName.restype = wintypes.LONG
        self.userenv.DeleteAppContainerProfile.argtypes = [wintypes.LPCWSTR]
        self.userenv.DeleteAppContainerProfile.restype = wintypes.LONG
        self.userenv.GetAppContainerFolderPath.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(wintypes.LPWSTR),
        ]
        self.userenv.GetAppContainerFolderPath.restype = wintypes.LONG
        self.advapi32.ConvertSidToStringSidW.argtypes = [
            wintypes.LPVOID,
            ctypes.POINTER(wintypes.LPWSTR),
        ]
        self.advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
        self.advapi32.FreeSid.argtypes = [wintypes.LPVOID]
        self.advapi32.FreeSid.restype = wintypes.LPVOID
        self.kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        self.kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        self.kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
        ]
        self.kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel32.TerminateJobObject.restype = wintypes.BOOL
        self.kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel32.TerminateProcess.restype = wintypes.BOOL
        self.kernel32.CreateIoCompletionPort.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
            ULONG_PTR,
            wintypes.DWORD,
        ]
        self.kernel32.CreateIoCompletionPort.restype = wintypes.HANDLE
        self.kernel32.GetQueuedCompletionStatus.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(ULONG_PTR),
            ctypes.POINTER(wintypes.LPVOID),
            wintypes.DWORD,
        ]
        self.kernel32.GetQueuedCompletionStatus.restype = wintypes.BOOL
        self.kernel32.InitializeProcThreadAttributeList.argtypes = [
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(SIZE_T),
        ]
        self.kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
        self.kernel32.UpdateProcThreadAttribute.argtypes = [
            wintypes.LPVOID,
            wintypes.DWORD,
            ULONG_PTR,
            wintypes.LPVOID,
            SIZE_T,
            wintypes.LPVOID,
            wintypes.LPVOID,
        ]
        self.kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
        self.kernel32.DeleteProcThreadAttributeList.argtypes = [wintypes.LPVOID]
        self.kernel32.DeleteProcThreadAttributeList.restype = None
        self.kernel32.CreateProcessW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            wintypes.LPVOID,
            wintypes.LPVOID,
            wintypes.BOOL,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.LPCWSTR,
            ctypes.POINTER(STARTUPINFOW),
            ctypes.POINTER(PROCESS_INFORMATION),
        ]
        self.kernel32.CreateProcessW.restype = wintypes.BOOL
        self.kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
        self.kernel32.GetStdHandle.restype = wintypes.HANDLE
        self.kernel32.SetHandleInformation.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self.kernel32.SetHandleInformation.restype = wintypes.BOOL
        self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel32.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        self.kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
        self.kernel32.ResumeThread.restype = wintypes.DWORD
        self.kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
        self.kernel32.LocalFree.restype = wintypes.HLOCAL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.ole32.CoTaskMemFree.argtypes = [wintypes.LPVOID]
        self.ole32.CoTaskMemFree.restype = None

    @staticmethod
    def _hresult_value(value: int) -> int:
        return ctypes.c_uint32(value).value

    @staticmethod
    def _check_bool(result: int, operation: str) -> None:
        if not result:
            raise ctypes.WinError(ctypes.get_last_error(), operation)

    def _create_profile(self) -> None:
        profile = str(self.payload["profile"])
        result = self.userenv.CreateAppContainerProfile(
            profile,
            "in:si Lernprozess",
            "Temporäre, eingeschränkte Ausführung von Lerncode",
            None,
            0,
            ctypes.byref(self.sid),
        )
        if self._hresult_value(result) == self.ERROR_ALREADY_EXISTS_HRESULT:
            result = self.userenv.DeriveAppContainerSidFromAppContainerName(
                profile, ctypes.byref(self.sid)
            )
        if result < 0:
            raise OSError(f"AppContainer-Profil konnte nicht erzeugt werden (0x{self._hresult_value(result):08X}).")

        sid_text = wintypes.LPWSTR()
        self._check_bool(
            self.advapi32.ConvertSidToStringSidW(self.sid, ctypes.byref(sid_text)),
            "ConvertSidToStringSidW",
        )
        try:
            self.sid_string = sid_text.value
        finally:
            self.kernel32.LocalFree(ctypes.cast(sid_text, wintypes.HLOCAL))

        folder_text = wintypes.LPWSTR()
        result = self.userenv.GetAppContainerFolderPath(profile, ctypes.byref(folder_text))
        if result < 0:
            raise OSError(f"AppContainer-Ordner konnte nicht bestimmt werden (0x{self._hresult_value(result):08X}).")
        try:
            self.profile_folder = Path(folder_text.value)
        finally:
            self.ole32.CoTaskMemFree(ctypes.cast(folder_text, wintypes.LPVOID))

    def _icacls(self, path: Path, arguments: list[str], *, check: bool = True) -> None:
        command = ["icacls", str(path), *arguments, "/C", "/Q"]
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        if check and completed.returncode:
            raise OSError(f"Dateifreigabe für den AppContainer fehlgeschlagen: {path}")

    def _grant_path(self, path: Path, *, writable: bool) -> None:
        resolved = path.resolve(strict=True)
        rights = "(OI)(CI)M" if writable and resolved.is_dir() else (
            "M" if writable else "(OI)(CI)RX" if resolved.is_dir() else "RX"
        )
        arguments = ["/grant:r", f"*{self.sid_string}:{rights}"]
        if resolved.is_dir():
            arguments.append("/T")
        self.granted.append(resolved)
        self._icacls(resolved, arguments)

    def _grant_filesystem(self) -> None:
        readable = [Path(item) for item in self.payload["readable_roots"]]
        writable = [Path(item) for item in self.payload["writable_roots"]]
        for root in readable:
            self._grant_path(root, writable=False)
        for root in writable:
            self._grant_path(root, writable=True)

    def _create_job(self) -> None:
        limits = self.payload["limits"]
        job = self.kernel32.CreateJobObjectW(None, None)
        if not job:
            raise ctypes.WinError(ctypes.get_last_error(), "CreateJobObjectW")
        self.job = job
        information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        information.BasicLimitInformation.LimitFlags = (
            self.JOB_OBJECT_LIMIT_JOB_TIME
            | self.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
            | self.JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION
            | self.JOB_OBJECT_LIMIT_JOB_MEMORY
            | self.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        information.BasicLimitInformation.PerJobUserTimeLimit = int(
            float(limits["max_cpu_seconds"]) * 10_000_000
        )
        information.BasicLimitInformation.ActiveProcessLimit = int(limits["max_processes"])
        information.JobMemoryLimit = int(limits["max_memory_bytes"])
        self._check_bool(
            self.kernel32.SetInformationJobObject(
                job,
                self.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                ctypes.byref(information),
                ctypes.sizeof(information),
            ),
            "SetInformationJobObject",
        )
        ui_limits = wintypes.DWORD(self.JOB_OBJECT_UILIMIT_ALL)
        self._check_bool(
            self.kernel32.SetInformationJobObject(
                job,
                self.JOB_OBJECT_BASIC_UI_RESTRICTIONS,
                ctypes.byref(ui_limits),
                ctypes.sizeof(ui_limits),
            ),
            "SetInformationJobObject(UI)",
        )

        invalid_handle = ctypes.c_void_p(-1).value
        port = self.kernel32.CreateIoCompletionPort(invalid_handle, None, 0, 1)
        if not port:
            raise ctypes.WinError(ctypes.get_last_error(), "CreateIoCompletionPort")
        self.completion_port = port
        association = JOBOBJECT_ASSOCIATE_COMPLETION_PORT(None, port)
        self._check_bool(
            self.kernel32.SetInformationJobObject(
                job,
                self.JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION,
                ctypes.byref(association),
                ctypes.sizeof(association),
            ),
            "SetInformationJobObject(CompletionPort)",
        )

    def _environment_block(self) -> Any:
        environment = dict(self.payload["environment"])
        if self.profile_folder is not None:
            temp = self.profile_folder / "Temp"
            temp.mkdir(parents=True, exist_ok=True)
            environment.update(
                {
                    "HOME": str(self.profile_folder),
                    "LOCALAPPDATA": str(self.profile_folder),
                    "TEMP": str(temp),
                    "TMP": str(temp),
                    "INSI_SANDBOX": "windows-appcontainer",
                }
            )
        block = "\0".join(
            f"{key}={value}" for key, value in sorted(environment.items(), key=lambda item: item[0].upper())
        ) + "\0\0"
        return ctypes.create_unicode_buffer(block)

    def _startup_information(self) -> tuple[Any, Any, STARTUPINFOEXW]:
        size = SIZE_T()
        result = self.kernel32.InitializeProcThreadAttributeList(
            None, 2, 0, ctypes.byref(size)
        )
        if result or ctypes.get_last_error() != self.ERROR_INSUFFICIENT_BUFFER:
            raise ctypes.WinError(ctypes.get_last_error(), "InitializeProcThreadAttributeList(size)")
        self.attribute_buffer = ctypes.create_string_buffer(size.value)
        pointer = ctypes.cast(self.attribute_buffer, wintypes.LPVOID)
        self._check_bool(
            self.kernel32.InitializeProcThreadAttributeList(
                pointer, 2, 0, ctypes.byref(size)
            ),
            "InitializeProcThreadAttributeList",
        )
        capabilities = SECURITY_CAPABILITIES(self.sid, None, 0, 0)
        self._check_bool(
            self.kernel32.UpdateProcThreadAttribute(
                pointer,
                0,
                self.PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
                ctypes.byref(capabilities),
                ctypes.sizeof(capabilities),
                None,
                None,
            ),
            "UpdateProcThreadAttribute(AppContainer)",
        )
        standard_handles = (
            self.kernel32.GetStdHandle(wintypes.DWORD(-10 & 0xFFFFFFFF)),
            self.kernel32.GetStdHandle(wintypes.DWORD(-11 & 0xFFFFFFFF)),
            self.kernel32.GetStdHandle(wintypes.DWORD(-12 & 0xFFFFFFFF)),
        )
        invalid_handle = ctypes.c_void_p(-1).value
        if any(handle in (None, 0, invalid_handle) for handle in standard_handles):
            raise OSError("Der Windows-Sandboxbroker besitzt keine gültigen Standardkanäle.")
        handle_array = (wintypes.HANDLE * len(standard_handles))(*standard_handles)
        for handle in standard_handles:
            self._check_bool(
                self.kernel32.SetHandleInformation(
                    handle,
                    self.HANDLE_FLAG_INHERIT,
                    self.HANDLE_FLAG_INHERIT,
                ),
                "SetHandleInformation",
            )
        self._check_bool(
            self.kernel32.UpdateProcThreadAttribute(
                pointer,
                0,
                self.PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
                handle_array,
                ctypes.sizeof(handle_array),
                None,
                None,
            ),
            "UpdateProcThreadAttribute(HandleList)",
        )
        startup = STARTUPINFOEXW()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.StartupInfo.dwFlags = self.STARTF_USESTDHANDLES
        (
            startup.StartupInfo.hStdInput,
            startup.StartupInfo.hStdOutput,
            startup.StartupInfo.hStdError,
        ) = standard_handles
        startup.lpAttributeList = pointer
        return capabilities, handle_array, startup

    def _launch(self) -> None:
        _capabilities, handle_array, startup = self._startup_information()
        command_line = ctypes.create_unicode_buffer(
            subprocess.list2cmdline(list(self.payload["command"]))
        )
        environment = self._environment_block()
        process = PROCESS_INFORMATION()
        flags = (
            self.EXTENDED_STARTUPINFO_PRESENT
            | self.CREATE_SUSPENDED
            | self.CREATE_NEW_PROCESS_GROUP
            | self.CREATE_UNICODE_ENVIRONMENT
            | self.CREATE_NO_WINDOW
        )
        try:
            self._check_bool(
                self.kernel32.CreateProcessW(
                    None,
                    command_line,
                    None,
                    None,
                    True,
                    flags,
                    environment,
                    str(self.payload["cwd"]),
                    ctypes.byref(startup.StartupInfo),
                    ctypes.byref(process),
                ),
                "CreateProcessW(AppContainer)",
            )
        finally:
            for handle in handle_array:
                self.kernel32.SetHandleInformation(
                    handle,
                    self.HANDLE_FLAG_INHERIT,
                    0,
                )
        self.process_handle = process.hProcess
        self.thread_handle = process.hThread
        self._check_bool(
            self.kernel32.AssignProcessToJobObject(self.job, process.hProcess),
            "AssignProcessToJobObject",
        )
        if self.kernel32.ResumeThread(process.hThread) == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error(), "ResumeThread")

    def _completion_violation(self) -> str | None:
        if not self.completion_port:
            return None
        message = wintypes.DWORD()
        key = ULONG_PTR()
        overlapped = wintypes.LPVOID()
        result = self.kernel32.GetQueuedCompletionStatus(
            self.completion_port,
            ctypes.byref(message),
            ctypes.byref(key),
            ctypes.byref(overlapped),
            0,
        )
        if not result:
            return None
        return {
            self.JOB_OBJECT_MSG_END_OF_JOB_TIME: "CPU-Zeitgrenze überschritten.",
            self.JOB_OBJECT_MSG_ACTIVE_PROCESS_LIMIT: "Prozessgrenze überschritten.",
            self.JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT: "Arbeitsspeichergrenze überschritten.",
            self.JOB_OBJECT_MSG_JOB_MEMORY_LIMIT: "Arbeitsspeichergrenze überschritten.",
        }.get(message.value)

    def _wait(self) -> tuple[int, str | None]:
        limits = self.payload["limits"]
        writable = [Path(item) for item in self.payload["writable_roots"]]
        if self.profile_folder is not None:
            writable.append(self.profile_folder)
        baseline = _directory_size(writable, stop_after=2**63 - 1)
        max_written = int(limits["max_written_bytes"])
        started = time.monotonic()
        violation: str | None = None
        while True:
            result = self.kernel32.WaitForSingleObject(self.process_handle, 100)
            candidate = self._completion_violation()
            if candidate is not None:
                violation = candidate
            if violation is None and time.monotonic() - started > float(limits["timeout_seconds"]):
                violation = "Laufzeitgrenze überschritten."
            if violation is None:
                current = _directory_size(
                    writable,
                    stop_after=baseline + max_written,
                )
                if current - baseline > max_written:
                    violation = "Schreibgrenze überschritten."
            if violation is not None:
                self.kernel32.TerminateJobObject(self.job, 1)
                self.kernel32.WaitForSingleObject(self.process_handle, 3000)
                break
            if result == self.WAIT_OBJECT_0:
                break
            if result != self.WAIT_TIMEOUT:
                raise ctypes.WinError(ctypes.get_last_error(), "WaitForSingleObject")
        exit_code = wintypes.DWORD()
        self._check_bool(
            self.kernel32.GetExitCodeProcess(self.process_handle, ctypes.byref(exit_code)),
            "GetExitCodeProcess",
        )
        return exit_code.value, violation

    def _cleanup(self) -> None:
        if self.job:
            self.kernel32.TerminateJobObject(self.job, 1)
        if self.process_handle:
            self.kernel32.TerminateProcess(self.process_handle, 1)
        if self.attribute_buffer is not None:
            try:
                self.kernel32.DeleteProcThreadAttributeList(
                    ctypes.cast(self.attribute_buffer, wintypes.LPVOID)
                )
            except (AttributeError, OSError):
                pass
        for handle in (self.thread_handle, self.process_handle, self.completion_port, self.job):
            if handle:
                self.kernel32.CloseHandle(handle)
        for path in reversed(self.granted):
            try:
                self._icacls(path, ["/remove:g", f"*{self.sid_string}", "/T"] if path.is_dir() else ["/remove:g", f"*{self.sid_string}"], check=False)
            except (OSError, subprocess.SubprocessError):
                pass
        if self.payload.get("profile"):
            try:
                self.userenv.DeleteAppContainerProfile(str(self.payload["profile"]))
            except (AttributeError, OSError):
                pass
        if self.sid:
            try:
                self.advapi32.FreeSid(self.sid)
            except (AttributeError, OSError):
                pass

    def run(self) -> int:
        try:
            self._create_profile()
            self._grant_filesystem()
            self._create_job()
            self._launch()
            exit_code, violation = self._wait()
            if violation:
                status_file = self.payload.get("violation_file")
                if status_file:
                    Path(str(status_file)).write_text(violation, encoding="utf-8")
                else:
                    print(
                        f"Das Programm wurde beendet: {violation}",
                        file=sys.stderr,
                        flush=True,
                    )
                return 1
            return int(exit_code)
        finally:
            self._cleanup()


def run_payload(payload: Mapping[str, Any]) -> int:
    available, detail = windows_api_available()
    if not available:
        raise RuntimeError(detail)
    return _WindowsBroker(payload).run()


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interner in:si-Windows-Sandboxbroker")
    parser.add_argument("--payload", required=True)
    options = parser.parse_args(arguments)
    try:
        payload = decode_payload(options.payload)
        return run_payload(payload)
    except KeyboardInterrupt:
        return 130
    except BaseException as error:
        print(f"Windows-Sandbox konnte nicht gestartet werden: {error}", file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "MAX_PAYLOAD_BYTES",
    "PAYLOAD_VERSION",
    "decode_payload",
    "encode_payload",
    "main",
    "run_payload",
    "windows_api_available",
]
