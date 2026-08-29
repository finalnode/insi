"""Browserloser NiceGUI-Smoke für den wichtigsten Schülerweg."""

import pytest

pytest.importorskip("nicegui")
pytest_plugins = ("nicegui.testing.user_plugin",)

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

    user.find("Setup").click()
    await user.should_see("Kursordner einrichten", retries=50)

    user.find("Aufgaben").click()
    await user.should_see("Aufgaben und Testfälle", retries=50)
    await user.should_see("Imperative Aufgaben")

    user.find("Skript").click()
    await user.should_see("PyKIM-Skript", retries=50)
    await user.should_see("Inhaltsverzeichnis")
    await user.should_see("Erste Schritte mit PyKIM")

    user.find("Meine Projekte").click()
    await user.should_see("Du hast noch kein eigenes Projekt angelegt.", retries=50)

    user.find("Werkzeuge").click()
    await user.should_see("IDE, Dateien und Updates", retries=50)
    await user.should_see("Meine lokalen Daten")
    await user.should_see("Datenexport erstellen")
    user.find("Lokale Daten entfernen").click()
    await user.should_see("Alle lokalen Daten in den Papierkorb?")
    user.find("Abbrechen").click()
    user.find("Trainer-Autorenwerkzeuge").click()
    await user.should_see("Aufgabenprüfung")
    await user.should_see("Kurswerkstatt öffnen")

    user.find("Hilfe").click()
    await user.should_see("Dokumentation · Documentation")
    await user.should_see("Erste Schritte mit in:si")
    user.find("Schließen").click()

    user.find("Quellen").click()
    await user.should_see("AGPL-3.0-or-later von in:si")
    await user.should_see("Copyright © 2026 in:si contributors")
    user.find("Lizenztexte offline lesen").click()
    await user.should_see("Lizenz und rechtliche Hinweise")


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_preflight_main.py")
async def test_course_start_blocks_and_repairs_incompatible_runtime(user):
    await user.open("/")
    await user.should_see("UI-Runtimekurs")
    user.find("Öffnen").click()
    await user.should_see("Kurslaufzeit ist noch nicht bereit", retries=50)
    await user.should_see("PyKIM hat Version 0.5.0")
    await user.should_see("PyKIM==0.6.0 · installiert: 0.5.0")
    user.find("Laufzeit reparieren").click()
    await user.should_see("Mein Lernstand", retries=50)


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_main.py")
async def test_course_studio_exposes_both_task_hint_workflows(user, tmp_path):
    source = tmp_path / "author-course"
    source.mkdir()
    await user.open("/course-builder")
    await user.should_see("Kursprojekt")
    user.find(marker="course-source").type(str(source))
    user.find("Pfad verwenden").click()
    await user.should_see("0 Skripte · 0 Aufgaben · 0 Trainer")
    user.find("Kursangaben").click()
    await user.should_see("Python-Version des Kurses")
    await user.should_see("Kurspakete mit exakter Version – eines pro Zeile")
    await user.should_see("in:si prüft und installiert sie, legt die Versionen aber nicht fest.")

    user.find(marker="new-task-menu").click()
    await user.should_see("Freie Aufgabe mit Hinweisen")
    await user.should_see("Geprüfte PyKIM-Aufgabe mit Hinweisen")
    user.find(marker="new-checked-task").click()
    await user.should_see("Gestufte Hinweise (Hints) – einer pro Zeile")
    await user.should_see("Trainer.yml – Expertenansicht")

    user.find(marker="new-task-menu").click()
    user.find(marker="new-free-task").click()
    await user.should_see("Freie Aufgabe")
    await user.should_see("Die Hinweise werden Lernenden schrittweise angeboten.")


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_project_states_main.py")
async def test_student_can_save_and_restore_a_named_project_state(user):
    await user.open("/")
    await user.should_see("UI-Projektkurs")
    user.find("Öffnen").click()
    await user.should_see("Mein Lernstand", retries=50)

    user.find("Meine Projekte").click()
    await user.should_see("Versionsprojekt", retries=50)
    await user.should_see("Spriteeditor")
    await user.should_see("Musikeditor")
    user.find("Projektstände").click()
    user.find("Neuen Projektstand speichern").click()
    user.find(marker="project-state-title").type("Erster guter Stand")
    user.find(marker="save-project-state").click()
    await user.should_see("Erster guter Stand")
    await user.should_see("Benannt")

    user.find("Diesen Stand wiederherstellen").click()
    await user.should_see("Projektstand wiederherstellen?")
    user.find("Wiederherstellen").click()
    await user.should_see("Vor Wiederherstellung", retries=50)
    await user.should_see("Erster guter Stand")
    assert user.notify.contains("wurde wiederhergestellt")
