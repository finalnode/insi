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

    # Bestehende Dokumente müssen nach dem Einlesen erreichbar sein; früher
    # lag die Aufgabennavigation hinter einem return und blieb immer leer.
    from insi.course_builder_view import save_course_markdown
    from insi.training.backends import get_authoring_backend

    save_course_markdown(source, "Skripte", "kapitel", "# Kapitel Navigation")
    save_course_markdown(source, "Aufgaben", "frei", "# Freie Navigation\n@difficulty:mittel\n\nBeschreibe deine Lösung.")
    save_course_markdown(source, "Aufgaben", "geprueft", "# Geprüfte Navigation\n@difficulty:mittel\n\nSchreibe ein Programm.", paradigm="oop")
    (source / "Trainer" / "geprueft.yml").write_text(
        get_authoring_backend("pykim").generate_source("geprueft", "Geprüfte Navigation", ("position",)),
        encoding="utf-8",
    )
    user.find("Pfad verwenden").click()
    await user.should_see("1 Skripte · 2 Aufgaben · 1 Trainer")
    user.find("Kapitel Navigation").click()
    await user.should_see("Skriptkapitel")
    user.find("Freie Navigation").click()
    await user.should_see("Freie Aufgabe")
    user.find("Geprüfte Navigation").click()
    await user.should_see("Trainer.yml – Expertenansicht")


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_project_states_main.py")
async def test_student_can_save_and_restore_a_named_project_state(user):
    from nicegui import ui
    from insi.course import get_course_directory
    from insi.markdown_editor import MarkdownEditor
    from insi.projects import student_projects

    await user.open("/")
    await user.should_see("UI-Projektkurs")
    user.find("Öffnen").click()
    await user.should_see("Mein Lernstand", retries=50)

    user.find("Meine Projekte").click()
    await user.should_see("Versionsprojekt", retries=50)
    await user.should_see("Spriteeditor")
    await user.should_see("Musikeditor")
    project = student_projects(get_course_directory())[0]
    for source in ("print('erster Stand')\n", "print('zweiter Stand')\n"):
        user.find(ui.codemirror).clear().type(source).trigger("change")
        await user.should_see("Ungespeicherte Änderungen")
        user.find(marker="save-project-code").click()
        assert project.entrypoint.read_text(encoding="utf-8") == source
        assert user.notify.contains("Projektcode gespeichert.")

    user.find("Dokumentation").click()
    for documentation in ("# Erster Entwurf\n", "# Überarbeitet\n"):
        with user.client:
            editor, = user.find(MarkdownEditor).elements
            editor.set_value(documentation)
        await user.should_see("Ungespeicherte Änderungen")
        user.find(marker="save-project-documentation").click()
        assert project.documentation.read_text(encoding="utf-8") == documentation
        assert user.notify.contains("Dokumentation gespeichert.")

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
    assert project.entrypoint.read_text(encoding="utf-8") == source
    assert project.documentation.read_text(encoding="utf-8") == documentation

    user.find("Dokumentation").click()
    project.documentation.write_text("# Extern geändert\n", encoding="utf-8")
    with user.client:
        editor, = user.find(MarkdownEditor).elements
        editor.set_value("# Veralteter Editorstand\n")
    user.find(marker="save-project-documentation").click()
    await user.should_see("Speichern nicht möglich")
    assert user.notify.contains("außerhalb der Suite verändert")
    assert project.documentation.read_text(encoding="utf-8") == "# Extern geändert\n"


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_project_states_main.py")
async def test_project_editors_load_on_selection_and_keep_unsaved_changes(user, monkeypatch):
    from nicegui import ui
    from insi import projects_view
    from insi.markdown_editor import MarkdownEditor

    reads, histories = [], []
    read_text = projects_view.project_text
    render_history = projects_view.render_project_history

    def tracked_text(project, path):
        reads.append((project.name, path.name))
        return read_text(project, path)

    def tracked_history(ui, run, project, *args):
        histories.append(project.name)
        return render_history(ui, run, project, *args)

    monkeypatch.setattr(projects_view, "project_text", tracked_text)
    monkeypatch.setattr(projects_view, "render_project_history", tracked_history)
    await user.open("/")
    user.find("Öffnen").click()
    await user.should_see("Mein Lernstand", retries=50)
    user.find("Meine Projekte").click()
    await user.should_see("Versionsprojekt", retries=50)
    assert reads == [("Versionsprojekt", "main.py"), ("Versionsprojekt", "README.md")]
    assert histories == ["Versionsprojekt"]

    code, = user.find(ui.codemirror).elements
    user.find(ui.codemirror).clear().type("print('ungespeichert')\n")
    user.find("Dokumentation").click()
    with user.client:
        docs, = user.find(MarkdownEditor).elements
        docs.set_value("# Ungespeicherte Dokumentation")
    user.find("Zweites Projekt").click()
    await user.should_see("Leeres Python-Projekt")
    assert reads[-2:] == [("Zweites Projekt", "main.py"), ("Zweites Projekt", "README.md")]
    assert histories == ["Versionsprojekt", "Zweites Projekt"]

    user.find("Versionsprojekt").click()
    user.find("Dokumentation").click()
    assert docs in user.find(MarkdownEditor).elements
    assert docs.value == "# Ungespeicherte Dokumentation"
    user.find("Code").click()
    assert code in user.find(ui.codemirror).elements
    assert code.value == "print('ungespeichert')\n"
    assert len(reads) == 4
    assert len(histories) == 2


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_main.py")
async def test_tasks_load_on_open_and_preserve_editor_and_results(user, monkeypatch):
    from types import SimpleNamespace
    from nicegui import ui
    from insi import tasks_view
    from insi.execution import ExecutionResult
    from insi.training.registry import exercise_names, get_activity, get_exercise

    reads, results = [], []
    original_read = tasks_view.read_student_source
    original_results = tasks_view.render_exercise_test_results

    def tracked_read(path, course):
        reads.append(path)
        return original_read(path, course)

    def tracked_results(ui, name, **kwargs):
        results.append(name)
        return original_results(ui, name, **kwargs)

    monkeypatch.setattr(tasks_view, "read_student_source", tracked_read)
    monkeypatch.setattr(tasks_view, "render_exercise_test_results", tracked_results)
    monkeypatch.setattr(tasks_view, "sandbox_status", lambda: SimpleNamespace(available=True, gui_available=True))
    monkeypatch.setattr(tasks_view.execution_manager, "execute", lambda *args, **kwargs:
                        ExecutionResult(0, "Ausgabe der ersten Aufgabe", ""))
    await user.open("/")
    user.find("Öffnen").click()
    await user.should_see("Mein Lernstand", retries=50)
    user.find("Aufgaben").click()
    await user.should_see("Imperative Aufgaben", retries=50)
    assert reads == results == []
    from insi.course import get_course_directory, provision_course_exercises
    provision_course_exercises(get_course_directory())
    names = [name for name in exercise_names() if get_activity(name) is None][:2]
    first, = user.find(kind=ui.expansion, content=get_exercise(names[0]).title).elements
    second, = user.find(kind=ui.expansion, content=get_exercise(names[1]).title).elements
    with user.client:
        first.set_value(True)
    assert len(reads) == 1
    assert results == names[:1]
    editor, = user.find(ui.codemirror).elements
    user.find(ui.codemirror).clear().type("print('mein Stand')\n").trigger("change")
    with user.client:
        first.set_value(False)
        second.set_value(True)
    assert len(reads) == 2
    assert results == names
    with user.client:
        second.set_value(False)
        first.set_value(True)
    assert editor.value == "print('mein Stand')\n"
    assert len(reads) == 2
    user.find(marker=f"run-task-{names[0]}").click()
    await user.should_see("Ausgabe der ersten Aufgabe", retries=50)
    assert results == [*names, names[0]]
    with user.client:
        first.set_value(False)
        first.set_value(True)
    assert len(reads) == 2
    assert results == [*names, names[0]]
    await user.should_see("Ausgabe der ersten Aufgabe")
