"""Schnelle Erkennung nichtlokaler Windows-Pfade ohne Dateizugriff."""

from __future__ import annotations

import ctypes
import ntpath
import os
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
    """Erkläre einen Netzwerkpfad, der das lokale Staging umgangen hat."""

    return (
        "Der Netzwerkpfad wurde nicht in den lokalen AppContainer-Bereich "
        f"gespiegelt: {os.fspath(value)}. Der sichere Lauf wurde abgebrochen."
    )
