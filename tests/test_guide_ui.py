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
    await user.should_see("Mein Lernstand", retries=150)

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
    await user.should_see("Mein Lernstand", retries=150)


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
    await user.should_see("Mein Lernstand", retries=150)

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
    await user.should_see("Mein Lernstand", retries=150)
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
    await user.should_see("Mein Lernstand", retries=150)
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


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_main.py")
async def test_parallel_task_actions_and_results_stay_with_their_task(user, monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from nicegui import ui, run
    from insi import tasks_view
    from insi.course import exercise_file, get_course_directory, provision_course_exercises
    from insi.execution import ExecutionResult
    from insi.file_storage import atomic_write_json
    from insi.progress import progress_file
    from insi.training.registry import exercise_names, get_activity, get_exercise

    original_io = run.io_bound
    pending, started, stopped = {}, asyncio.Queue(), []

    async def controlled_io(function, *args, **kwargs):
        if function == tasks_view.execution_manager.execute:
            future = asyncio.get_running_loop().create_future()
            pending[args[0]] = future
            started.put_nowait(args[0])
            return await future
        return await original_io(function, *args, **kwargs)

    def stop(path):
        stopped.append(path)
        return True

    def element(marker):
        result, = user.find(marker=marker).elements
        return result

    monkeypatch.setattr(run, "io_bound", controlled_io)
    monkeypatch.setattr(tasks_view.execution_manager, "stop", stop)
    monkeypatch.setattr(tasks_view, "sandbox_status", lambda: SimpleNamespace(available=True, gui_available=True))
    await user.open("/")
    user.find("Öffnen").click()
    await user.should_see("Mein Lernstand", retries=150)
    course = get_course_directory()
    provision_course_exercises(course)
    names = [name for name in exercise_names() if get_activity(name) is None][:2]
    paths = [exercise_file(name, course) for name in names]
    user.find("Aufgaben").click()
    await user.should_see("Imperative Aufgaben", retries=50)
    panels = []
    for name in names:
        panel, = user.find(kind=ui.expansion, content=get_exercise(name).title).elements
        panels.append(panel)
        with user.client:
            panel.set_value(True)
    buttons = [element(f"run-task-{name}") for name in names]
    stops = [element(f"stop-task-{name}") for name in names]
    statuses = [element(f"task-status-{name}") for name in names]
    outputs = [element(f"task-output-{name}") for name in names]
    try:
        for index, name in enumerate(names):
            user.find(marker=f"run-task-{name}").click()
            assert await asyncio.wait_for(started.get(), timeout=5) == paths[index]
            assert not buttons[index].enabled and stops[index].enabled
        with user.client:
            panels[0].set_value(False)
            panels[0].set_value(True)
        assert [status.text for status in statuses] == ["LÄUFT", "LÄUFT"]

        # The second run finishes first; its progress must not refresh task one.
        attempts = [{"exercise": names[1], "passed": True, "total": 1,
                     "tests": [{"passed": True, "message": "Ergebnis zweite Aufgabe"}]}]
        atomic_write_json(progress_file(course), {"attempts": attempts})
        pending[paths[1]].set_result(ExecutionResult(0, "Ausgabe zwei", ""))
        await user.should_see("Ergebnis zweite Aufgabe", retries=50)
        assert outputs[1].content == "Ausgabe zwei"
        assert outputs[0].content == "Programm läuft …"
        assert buttons[1].enabled and not stops[1].enabled
        assert not buttons[0].enabled and stops[0].enabled

        user.find(marker=f"stop-task-{names[0]}").click()
        assert stopped == paths[:1]
        assert statuses[0].text == "WIRD BEENDET"
        assert statuses[1].text == "BEREIT"
        attempts.append({"exercise": names[0], "passed": False, "total": 1,
                         "tests": [{"passed": False, "message": "Ergebnis erste Aufgabe"}]})
        atomic_write_json(progress_file(course), {"attempts": attempts})
        pending[paths[0]].set_result(ExecutionResult(-15, "Ausgabe eins", "", stopped=True))
        await user.should_see("Ergebnis erste Aufgabe", retries=50)
        assert [output.content for output in outputs] == ["Ausgabe eins", "Ausgabe zwei"]
        assert all(button.enabled for button in buttons)
        assert not any(button.enabled for button in stops)
        assert [status.text for status in statuses] == ["BEREIT", "BEREIT"]
        await user.should_see("Ergebnis zweite Aufgabe")
        for index, panel in enumerate(panels):
            labels = {child.text for child in panel.descendants() if isinstance(child, ui.label)}
            messages = ("Ergebnis erste Aufgabe", "Ergebnis zweite Aufgabe")
            assert messages[index] in labels
            assert messages[1 - index] not in labels
    finally:
        for future in pending.values():
            if not future.done():
                future.cancel()
        await asyncio.sleep(0)


@pytest.mark.anyio
@pytest.mark.e2e
@pytest.mark.nicegui_main_file("tests/ui_main.py")
async def test_delayed_task_result_and_journal_stay_in_original_course(user, monkeypatch, tmp_path):
    import asyncio
    from types import SimpleNamespace
    from nicegui import ui, run
    from insi import tasks_view
    from insi.course import get_course_directory, provision_course_exercises, set_course_directory
    from insi.execution import ExecutionResult
    from insi.file_storage import atomic_write_json
    from insi.progress import load_progress, progress_file
    from insi.training.registry import exercise_names, get_activity, get_exercise

    ready, finish = asyncio.Event(), asyncio.Event()
    original_io = run.io_bound
    courses = []

    async def controlled_io(function, *args, **kwargs):
        if function == tasks_view.execution_manager.execute:
            courses.append(args[1])
            ready.set()
            await finish.wait()
            return ExecutionResult(0, "Späte Ausgabe aus Kurs A", "")
        return await original_io(function, *args, **kwargs)

    monkeypatch.setattr(run, "io_bound", controlled_io)
    monkeypatch.setattr(tasks_view, "sandbox_status", lambda: SimpleNamespace(available=True, gui_available=True))
    await user.open("/")
    user.find("Öffnen").click()
    await user.should_see("Mein Lernstand", retries=150)
    first = get_course_directory()
    second = tmp_path / "other-course"
    second.mkdir()
    provision_course_exercises(first)
    name = next(name for name in exercise_names() if get_activity(name) is None)
    for course, message in ((first, "Prüfergebnis Kurs A"), (second, "Prüfergebnis Kurs B")):
        atomic_write_json(progress_file(course), {"attempts": [{
            "exercise": name, "passed": True, "total": 1,
            "tests": [{"passed": True, "message": message}],
        }]})
    original_second = progress_file(second).read_bytes()
    user.find("Aufgaben").click()
    await user.should_see("Imperative Aufgaben", retries=50)
    panel, = user.find(kind=ui.expansion, content=get_exercise(name).title).elements
    with user.client:
        panel.set_value(True)
    user.find(marker=f"run-task-{name}").click()
    try:
        await asyncio.wait_for(ready.wait(), timeout=5)
        set_course_directory(second)
        assert get_course_directory() == second
        user.find(kind=ui.textarea, content="Mein Dokubuch-Eintrag").type("Notiz aus Ansicht A")
        user.find("Eintrag speichern").click()
        finish.set()
        await user.should_see("Späte Ausgabe aus Kurs A", retries=50)
        assert courses == [first]
        labels = {child.text for child in panel.descendants() if isinstance(child, ui.label)}
        assert "Prüfergebnis Kurs A" in labels
        assert "Prüfergebnis Kurs B" not in labels
        assert load_progress(first)["journal"][name]["text"] == "Notiz aus Ansicht A"
        assert progress_file(second).read_bytes() == original_second
        user.find(marker=f"run-task-{name}").click()
        await asyncio.sleep(0)
        assert user.notify.contains("Kurs wurde gewechselt")
        assert courses == [first]
    finally:
        finish.set()
        set_course_directory(first)
        await asyncio.sleep(0)
