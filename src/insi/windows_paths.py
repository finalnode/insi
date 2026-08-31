"""Schnelle Erkennung nichtlokaler Windows-Pfade ohne Dateizugriff."""

from __future__ import annotations

import ctypes
import ntpath
import os
import sys
from typing import Union


PathValue = Union[str, os.PathLike[str]]
DRIVE_REMOTE = 4


def is_windows_network_path(value: PathValue) -> bool:
    """Erkenne UNC-Pfade und unter Windows auch verbundene Netzlaufwerke.

    Die lexikalische UNC-Prüfung erfolgt absichtlich vor jedem ``Path``- oder
    Dateisystemzugriff. Ein nicht erreichbarer Schulserver darf dadurch weder
    App-Start noch Sandboxstatus verzögern.
    """

    text = os.fspath(value).replace("/", "\\")
    lower = text.casefold()
    if lower.startswith("\\\\?\\unc\\"):
        return True
    if text.startswith("\\\\") and not lower.startswith("\\\\?\\"):
        return True
    if os.name != "nt":
        return False

    drive, _ = ntpath.splitdrive(text)
    if len(drive) != 2 or drive[1] != ":":
        return False
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_drive_type = kernel32.GetDriveTypeW
        get_drive_type.argtypes = [ctypes.c_wchar_p]
        get_drive_type.restype = ctypes.c_uint
        return get_drive_type(f"{drive}\\") == DRIVE_REMOTE
    except (AttributeError, OSError):
        return False


def windows_network_path_message(value: PathValue) -> str:
    """Erkläre die sichere Behandlung eines Windows-Netzwerkpfads."""

    return (
        "Der Windows-AppContainer unterstützt keine integrierte Ausführung "
        f"aus einem Netzwerkpfad: {os.fspath(value)}. Kopiere den vollständigen "
        "in:si-Ordner und den Kurs auf ein lokales NTFS-Laufwerk. Für einen "
        "Kurs auf einem Netzlaufwerk kann stattdessen die konfigurierte externe "
        "IDE verwendet werden."
    )


def reject_frozen_windows_network_launch(executable: PathValue | None = None) -> None:
    """Beende eine gebündelte Windows-App vom Netz mit einer klaren Meldung."""

    if sys.platform != "win32":
        return
    path = os.fspath(executable or sys.executable)
    if not is_windows_network_path(path):
        return
    message = (
        "in:si wurde direkt von einem Netzwerkpfad gestartet:\n\n"
        f"{path}\n\n"
        "Dort ist das Laden langsam und der sichere PyKIM-Runner kann nicht "
        "arbeiten. Kopiere den vollständig entpackten in:si-Ordner auf ein "
        "lokales NTFS-Laufwerk (zum Beispiel unter C:\\Users\\...\\in-si) und "
        "starte dort insi.exe."
    )
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        message_box = user32.MessageBoxW
        message_box.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint,
        ]
        message_box.restype = ctypes.c_int
        message_box(None, message, "in:si – lokaler Start erforderlich", 0x10)
    except (AttributeError, OSError, TypeError):
        pass
    raise SystemExit(message)
