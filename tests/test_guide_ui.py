"""Browserloser NiceGUI-Smoke für den wichtigsten Schülerweg."""

import pytest

pytest.importorskip("nicegui")
pytest_plugins = ("nicegui.testing.user_plugin", "anyio.pytest_plugin")

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_main.py")
async def test_student_can_open_overview_tasks_and_script(user):
    await user.open("/")
    await user.should_see("UI-Standardkurs")
    user.find("Öffnen").click()
    await user.should_see("Mein Lernstand", retries=50)

    user.find("Aufgaben").click()
    await user.should_see("Aufgaben und Testfälle")
    await user.should_see("Imperative Aufgaben")

    user.find("Skript").click()
    await user.should_see("PyKIM-Skript")
    await user.should_see("Inhaltsverzeichnis")
    await user.should_see("Erste Schritte mit PyKIM")

    user.find("Meine Projekte").click()
    await user.should_see("Du hast noch kein eigenes Projekt angelegt.")

    user.find("Werkzeuge").click()
    await user.should_see("IDE, Dateien und Updates")
    user.find("Trainer-Autorenwerkzeuge").click()
    await user.should_see("Aufgabenprüfung")
    await user.should_see("Neue Trainingsdefinition entwerfen")
