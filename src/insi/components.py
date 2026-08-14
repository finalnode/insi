"""Kleine gemeinsame UI-Bausteine für ein konsistentes Lernstudio."""


def section_heading(ui, title: str, description: str = "", *, level: int = 2) -> None:
    """Zeige eine semantische, überall gleich gestaltete Abschnittsüberschrift."""
    sizes = {1: "text-3xl", 2: "text-2xl", 3: "text-xl"}
    ui.label(title).classes(f"{sizes.get(level, 'text-xl')} font-bold").props(
        f'role="heading" aria-level="{level}"'
    )
    if description:
        ui.label(description).classes("text-grey-7")


def empty_state(ui, title: str, description: str, *, icon: str = "info") -> None:
    """Zeige fehlende Daten nicht als losen Text, sondern als klaren Zustand."""
    with ui.card().classes("w-full bg-grey-1 shadow-none border"):
        with ui.row().classes("items-center"):
            ui.icon(icon, color="grey")
            ui.label(title).classes("font-bold")
        ui.label(description).classes("text-grey-7")


__all__ = ["empty_state", "section_heading"]
