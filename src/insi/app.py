"""Dünner Application Composer und Startpunkt für in:si."""

from __future__ import annotations

import platform

from . import __version__
from .branding import APP_DISPLAY_NAME
from .context import AppContext
from .desktop import (
    apply_macos_app_icon,
    app_icon_path,
    browser_favicon,
    configure_native_app_icon,
    parse_arguments,
    prepare_windows_browser_fallback,
)


def main(
    *,
    show: bool = True,
    native: bool | None = None,
    arguments: list[str] | None = None,
    run_server: bool = True,
) -> None:
    """Komponiere Framework, Workspace und Desktop-Lebenszyklus."""
    desktop = not parse_arguments(arguments).browser if native is None else native
    try:
        from nicegui import app as nicegui_app, run as nicegui_run, ui
    except ImportError:
        raise RuntimeError(
            f"{APP_DISPLAY_NAME} benötigt NiceGUI. Installiere es mit "
            "pip install insi."
        ) from None

    # Die umfangreichen Views und Prozessmanager werden erst geladen, nachdem
    # NiceGUI tatsächlich verfügbar ist. CLI-Helfer und Packaging-Checks können
    # den Composer dadurch ohne die gesamte Lernumgebung importieren.
    from insi.execution import execution_manager, script_example_manager
    from .workspace_view import register_workspace

    context = AppContext(ui, nicegui_app, nicegui_run, desktop)
    register_workspace(context)
    if not run_server:
        return

    nicegui_app.on_shutdown(execution_manager.stop_all)
    nicegui_app.on_shutdown(script_example_manager.stop_all)
    port = None
    icon = app_icon_path()
    if desktop and platform.system() == "Darwin":
        configure_native_app_icon(nicegui_app.native, icon)
    if desktop and platform.system() == "Windows":
        from nicegui.native.event_manager import event_manager
        from nicegui.native.native_mode import find_open_port

        port = find_open_port()
        prepare_windows_browser_fallback(
            event_manager,
            f"http://127.0.0.1:{port}/",
        )
    ui.run(
        title=f"{APP_DISPLAY_NAME} {__version__}",
        favicon=browser_favicon(),
        host="127.0.0.1",
        port=port,
        reload=False,
        show=show and not desktop,
        native=desktop,
        window_size=(1280, 850) if desktop else None,
    )


if __name__ == "__main__":
    main()


__all__ = [
    "apply_macos_app_icon",
    "app_icon_path",
    "browser_favicon",
    "configure_native_app_icon",
    "main",
    "parse_arguments",
    "prepare_windows_browser_fallback",
]
