"""Plattformspezifische Desktop-Helfer ohne Abhängigkeit von den Views."""

from __future__ import annotations

import argparse
import base64
import threading
import webbrowser
from pathlib import Path

from .branding import APP_DISPLAY_NAME


def prepare_windows_browser_fallback(
    event_manager,
    url: str,
    *,
    delay: float = 12.0,
    opener=webbrowser.open,
) -> threading.Event:
    """Öffne bei einem hängenden nativen Windows-Fenster den Browser."""
    window_shown = threading.Event()
    event_manager.on("shown", lambda _: window_shown.set())

    def open_if_needed() -> None:
        if window_shown.wait(delay):
            return
        print(
            "Das native Windows-Fenster wurde nicht rechtzeitig sichtbar; "
            f"öffne {APP_DISPLAY_NAME} im Standardbrowser unter {url}"
        )
        opener(url)

    threading.Thread(
        target=open_if_needed,
        name="insi-windows-browser-fallback",
        daemon=True,
    ).start()
    return window_shown


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Lese die bewusst kleine Kommandozeile der Anwendung."""
    parser = argparse.ArgumentParser(description=f"{APP_DISPLAY_NAME} starten")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="im normalen Browser statt als Desktopfenster starten",
    )
    return parser.parse_args(arguments)


def app_icon_path() -> Path | str:
    """Nutze das gemeinsame Projekticon und sonst den Emoji-Fallback."""
    project_icon = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "macos"
        / "assets"
        / "app-icon-master.png"
    )
    bundled_icon = (
        Path(__file__).resolve().parent
        / "assets"
        / "app-icon.png"
    )
    if bundled_icon.is_file():
        return bundled_icon
    return project_icon if project_icon.is_file() else "🤖"


def browser_favicon() -> str:
    """Bette das kleine Icon direkt ein und umgehe den aggressiven Favicon-Cache."""
    favicon = (
        Path(__file__).resolve().parent
        / "assets"
        / "app-icon-64.png"
    )
    if not favicon.is_file():
        return "🤖"
    encoded = base64.b64encode(favicon.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def apply_macos_app_icon(icon: Path | str) -> bool:
    """Setze auch beim Start aus dem Quellcode das macOS-Dock-Icon."""
    if not isinstance(icon, Path) or not icon.is_file():
        return False
    try:
        from AppKit import NSApplication, NSImage

        image = NSImage.alloc().initWithContentsOfFile_(str(icon))
        if image is None:
            return False
        NSApplication.sharedApplication().setApplicationIconImage_(image)
        return True
    except Exception:
        return False


def configure_native_app_icon(native_config, icon: Path | str) -> bool:
    """Reiche das Icon an den separaten pywebview/Cocoa-Prozess weiter."""
    if not isinstance(icon, Path) or not icon.is_file():
        return False
    native_config.start_args["icon"] = str(icon)
    return True


__all__ = [
    "apply_macos_app_icon",
    "app_icon_path",
    "browser_favicon",
    "configure_native_app_icon",
    "parse_arguments",
    "prepare_windows_browser_fallback",
]
