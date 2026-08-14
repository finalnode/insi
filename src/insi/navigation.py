"""Zentrale Tab-Navigation des Lernstudios."""


def create_navigation(ui):
    """Erzeuge Tabs in stabiler Reihenfolge und liefere Container und Seiten zurück."""
    with ui.tabs().classes("pykim-main-navigation w-full") as tabs:
        setup = ui.tab("Setup", icon="settings")
        tools = ui.tab("Werkzeuge", icon="construction")
        overview = ui.tab("Übersicht", icon="dashboard")
        tasks = ui.tab("Aufgaben", icon="checklist")
        examples = ui.tab("Beispiele", icon="lightbulb")
        projects = ui.tab("Meine Projekte", icon="folder_special")
        extensions = ui.tab("Erweiterungen", icon="extension")
        submission = ui.tab("Abgabe", icon="upload_file")
        # Technische Vorarbeit bleibt erhalten, bis der Lernworkflow stabil ist.
        submission.set_visibility(False)
        sheet = ui.tab("Cheatsheet", icon="bolt")
        script = ui.tab("Skript", icon="menu_book")
        pyxel = ui.tab("Pyxel", icon="sports_esports")
        browser = ui.tab("Python-Spielwiese", icon="code")
    return tabs, (
        setup, tools, overview, tasks, examples, projects, extensions, submission,
        sheet, script, pyxel, browser,
    )


__all__ = ["create_navigation"]
