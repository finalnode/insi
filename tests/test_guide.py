import json
import ast
import hashlib
import io
import stat
import threading
import time
import zipfile
import sys
from urllib.error import HTTPError
from pathlib import Path
from types import SimpleNamespace

import pykim
import pytest
from insi.app import (
    apply_macos_app_icon,
    app_icon_path,
    browser_favicon,
    configure_native_app_icon,
    parse_arguments,
    prepare_windows_browser_fallback,
)
from insi.content import PYODIDE_PLAYGROUND
from insi.course import (
    clear_course_selection,
    course_name_confirmation_matches,
    create_course,
    provision_course_exercises,
    exercise_file,
    get_course_directory,
    get_course_directories,
    get_student_name,
    reset_exercise_file,
    set_course_directory,
    trash_course,
)
from insi.runtime import RuntimeCandidate
from insi.progress import (
    load_progress,
    clear_exercise_progress,
    remove_packaged_example_attempts,
    revealed_hint_count,
)
from insi.execution import ExecutionManager, ScriptExampleManager
from insi.script_quality import (
    annotated_script_blocks,
    classify_script_block,
    run_headless,
)
from insi.author_workspace import (
    AuthorDraft,
    assignment_markdown,
    load_published_draft,
    save_author_draft,
    validate_author_draft,
)
from insi.examples import (
    copy_example_to_course,
    example_programs,
    launch_example,
    start_example,
)
from insi.library import (
    PACKAGED_CONTENT_ROOT,
    script_chapters,
    script_code_examples,
    render_script_markdown,
    render_task_markdown,
    task_assignment,
    task_document,
    task_documents,
    task_hints,
    task_tags,
    task_names,
    task_sources,
)
from insi.updates import (
    _course_active_marker,
    active_content_root,
    check_app_update,
    check_content_update,
    install_content_update,
    check_updates,
    format_content_version,
    sync_certificate_content,
    verify_certificate_trainers,
    verify_certificate_authorization,
)
from insi.course_setup import (
    course_setup_info,
    install_new_course_archive,
    install_new_course_setup,
    sync_installed_course_content,
)
from insi.course_archive import (
    build_course_archive,
    course_content_source,
    parse_course_archive,
)
from insi.course_builder_view import (
    analyze_course_directory,
    course_documents,
    course_source_counts,
    create_portable_course,
    ensure_course_source,
    import_course_candidates,
    load_course_document,
    save_course_assignment,
    save_course_markdown,
)
from insi.markedown import parse_markedown, validate_markedown
from insi.course_catalog import load_course_catalog, parse_course_catalog
from insi.system import (
    execute_student_program,
    execute_script_example,
    github_version,
    install_or_repair_pyxel,
    read_student_source,
    run_student_program,
    save_student_source,
    source_hash,
    SourceConflictError,
)
from insi.sources import source_references
from insi.legal import legal_document_path, legal_document_text
from insi.documentation import documentation_text
from insi.assignments import ASSIGNMENTS, get_assignment
from pykim.trainer.authoring import generate_exercise_source


def test_guide_starts_as_desktop_by_default_and_supports_browser_fallback():
    assert not parse_arguments([]).browser
    assert parse_arguments(["--browser"]).browser
    assert app_icon_path() != "🤖"
    assert browser_favicon().startswith("data:image/png;base64,")
    assert not apply_macos_app_icon("🤖")
    native = SimpleNamespace(start_args={})
    assert configure_native_app_icon(native, Path(app_icon_path()))
    assert native.start_args["icon"].endswith("insi/assets/app-icon.png")


def test_windows_browser_fallback_opens_only_without_native_window():
    class Events:
        def on(self, event_type, handler):
            assert event_type == "shown"
            self.handler = handler

    opened = threading.Event()
    events = Events()
    prepare_windows_browser_fallback(
        events,
        "http://127.0.0.1:8765/",
        delay=0,
        opener=lambda url: opened.set(),
    )
    assert opened.wait(1)

    opened.clear()
    events = Events()
    prepare_windows_browser_fallback(
        events,
        "http://127.0.0.1:8765/",
        delay=0.05,
        opener=lambda url: opened.set(),
    )
    events.handler(None)
    assert not opened.wait(0.1)


def test_course_deletion_confirmation_uses_current_exact_input():
    expected = "PyKIM Standardkurs"

    assert course_name_confirmation_matches(expected, expected)
    assert not course_name_confirmation_matches(f"'{expected}", expected)
    assert not course_name_confirmation_matches(expected[:-1], expected)


def test_runtime_version_matches_project_metadata():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    import insi

    with (Path(__file__).parents[1] / "pyproject.toml").open("rb") as source:
        assert insi.__version__ == tomllib.load(source)["project"]["version"]


def test_published_example_course_setup_is_valid():
    setup = Path(__file__).parents[1] / "examples" / "course-setups" / (
        "pykim-standardkurs.insi-setup"
    )
    from insi.course_setup import setup_info

    parsed = setup_info(setup)
    assert parsed.course == "PyKIM Standardkurs"
    assert parsed.repository == "https://github.com/finalnode/PyKIM_Kurs.git"


def test_legacy_course_setup_is_migrated_with_backup(tmp_path):
    from insi.course_setup import (
        LEGACY_SETUP_FILENAME,
        SETUP_FILENAME,
        course_setup_info,
    )

    course = tmp_path / "legacy-course"
    legacy = course / ".pykim" / LEGACY_SETUP_FILENAME
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({
        "format": "pykim-course-setup-v1",
        "name": "python-legacy.pykim-setup",
        "teacher": "Frau Beispiel",
        "school": "OSZ KIM",
        "course": "Python Legacy",
        "repository": "https://github.com/example/course.git",
        "branch": "main",
        "scripts_path": "Skripte",
        "assignments_path": "Aufgaben",
        "trainers_path": "Trainer",
    }), encoding="utf-8")

    info = course_setup_info(course)

    assert info is not None
    assert info.name == "python-legacy.insi-setup"
    migrated = course / ".pykim" / SETUP_FILENAME
    assert json.loads(migrated.read_text(encoding="utf-8"))["format"] == (
        "insi-course-setup-v1"
    )
    assert not legacy.exists()
    assert (course / ".pykim" / "backups" / LEGACY_SETUP_FILENAME).is_file()


def test_footer_sources_collect_software_course_and_assignment_sources(
    tmp_path, monkeypatch
):
    content = tmp_path / "content"
    assignments = content / "Aufgaben" / "imperativ"
    assignments.mkdir(parents=True)
    (assignments / "mit-quelle.md").write_text(
        "# Aufgabe\n@source: CS Circles | https://example.test/task\n",
        encoding="utf-8",
    )
    (assignments / "_entwurf.md").write_text(
        "# Entwurf\n@source: Versteckt | https://example.test/hidden\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYKIM_CONTENT_DIR", str(content))
    setup_path = Path(__file__).parents[1] / "examples" / "course-setups" / (
        "pykim-standardkurs.insi-setup"
    )
    from insi.course_setup import setup_info

    references = source_references(setup_info(setup_path))

    assert any(item.kind == "software" for item in references)
    assert any(item.kind == "license" for item in references)
    assert any(
        item.kind == "privacy" and item.url.endswith("/DATENSCHUTZ.md")
        for item in references
    )
    assert any(
        item.kind == "course"
        and item.url == "https://github.com/finalnode/PyKIM_Kurs"
        for item in references
    )
    assert any(
        item.label == "CS Circles" and item.url == "https://example.test/task"
        for item in references
    )
    assert all(item.label != "Versteckt" for item in references)


def test_legal_documents_are_available_offline():
    assert legal_document_text("agpl").lstrip().startswith(
        "GNU AFFERO GENERAL PUBLIC LICENSE"
    )
    assert "AGPL-3.0-or-later" in legal_document_text("scope")
    assert "TOAST UI Editor" in legal_document_text("third-party")
    assert legal_document_path("agpl").name == "LICENSE"

    with pytest.raises(ValueError, match="Unbekannter Rechtstext"):
        legal_document_text("../README.md")


def test_documentation_is_available_offline_in_both_languages():
    assert "# Erste Schritte mit in:si" in documentation_text("de")
    assert "# Getting started with in:si" in documentation_text("en")

    with pytest.raises(ValueError, match="Unbekannte Dokumentsprache"):
        documentation_text("fr")


def test_packaged_course_catalog_contains_the_public_standard_course():
    courses = load_course_catalog(online=False)

    assert [course.id for course in courses] == ["pykim-standardkurs"]
    assert courses[0].setup.course == "PyKIM Standardkurs"
    assert courses[0].setup.repository == "https://github.com/finalnode/PyKIM_Kurs.git"
    assert "Python" in courses[0].tags


def test_course_catalog_rejects_an_invalid_setup():
    with pytest.raises(ValueError, match="GitHub"):
        parse_course_catalog(json.dumps({
            "format": 1,
            "courses": [{
                "id": "unsafe",
                "description": "Ungültig",
                "level": "Test",
                "tags": ["Test"],
                "setup": {
                    "format": "insi-course-setup-v1",
                    "name": "unsafe.insi-setup",
                    "teacher": "Test",
                    "school": "Test",
                    "course": "Test",
                    "repository": "https://example.test/course.git",
                    "branch": "main",
                    "scripts_path": "Skripte",
                    "assignments_path": "Aufgaben",
                    "trainers_path": "Trainer",
                },
            }],
        }).encode())


def test_multiple_course_directories_are_remembered_and_selectable(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    first = tmp_path / "kurs-a"
    second = tmp_path / "kurs-b"

    create_course(first, "Ada")
    create_course(second, "Grace")

    assert get_course_directory() == second.resolve()
    assert get_course_directories() == (second.resolve(), first.resolve())

    set_course_directory(first)
    assert get_course_directory() == first.resolve()
    assert get_course_directories() == (first.resolve(), second.resolve())

    clear_course_selection()
    assert get_course_directory() is None
    assert get_course_directories() == (first.resolve(), second.resolve())


def test_each_selected_course_uses_its_own_cached_content(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    packaged = tmp_path / "packaged"
    packaged.mkdir()
    courses = (tmp_path / "kurs-a", tmp_path / "kurs-b")
    setups = (
        SimpleNamespace(
            repository="https://github.com/example/course.git",
            branch="main",
            scripts_path="Skripte",
            assignments_path="Aufgaben",
            trainers_path="Trainer",
        ),
        SimpleNamespace(
            repository="https://github.com/example/course.git",
            branch="beta",
            scripts_path="Skripte",
            assignments_path="Aufgaben",
            trainers_path="Trainer",
        ),
    )
    roots = []
    for index, setup in enumerate(setups):
        revision = str(index + 1) * 40
        root = tmp_path / "config" / "content" / "versions" / revision
        root.mkdir(parents=True)
        content = f"Kurs {index}".encode()
        (root / "test.md").write_bytes(content)
        (root / "content-manifest.json").write_text(
            json.dumps({
                "content_version": revision,
                "files": {"test.md": hashlib.sha256(content).hexdigest()},
            }),
            encoding="utf-8",
        )
        marker = _course_active_marker(setup)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"content_version": revision}), encoding="utf-8")
        roots.append(root)

    monkeypatch.setattr(
        "insi.course_setup.course_setup_info",
        lambda course: setups[courses.index(Path(course))],
    )
    for course, expected in zip(courses, roots):
        set_course_directory(course)
        assert active_content_root(packaged) == expected


def test_uploaded_setup_creates_and_selects_a_managed_course(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    data = json.dumps({
        "format": "insi-course-setup-v1",
        "name": "python-11a.insi-setup",
        "teacher": "Frau Beispiel",
        "school": "OSZ KIM",
        "course": "Python 11A",
        "repository": "https://github.com/example/course.git",
        "branch": "main",
        "scripts_path": "Skripte",
        "assignments_path": "Aufgaben",
        "trainers_path": "Trainer",
    }).encode()
    calls = []
    target = tmp_path / "content"
    monkeypatch.setattr(
        "insi.updates.sync_certificate_content",
        lambda info: calls.append(info.repository) or target,
    )
    monkeypatch.setattr(
        "insi.registries.activate_content_registries",
        lambda root, **paths: calls.append(("registries", root, paths)),
    )
    monkeypatch.setattr(
        "insi.course.provision_course_exercises",
        lambda course: calls.append(Path(course)),
    )

    info, course = install_new_course_setup(
        data,
        base_directory=tmp_path / "courses",
    )

    assert info.course == "Python 11A"
    assert course == (tmp_path / "courses" / "python-11a").resolve()
    assert course_setup_info(course) == info
    assert get_course_directory() == course
    assert calls == [
        "https://github.com/example/course.git",
        (
            "registries",
            target,
            {"trainers_path": "Trainer", "assignments_path": "Aufgaben"},
        ),
        course,
    ]


def portable_course_archive(*, prefix: str = "") -> bytes:
    setup = {
        "format": "insi-course-setup-v1",
        "name": "python-11a.insi-setup",
        "teacher": "Frau Beispiel",
        "school": "OSZ KIM",
        "course": "Python 11A",
        "repository": "https://github.com/example/course.git",
        "branch": "main",
        "scripts_path": "Skripte",
        "assignments_path": "Aufgaben",
        "trainers_path": "Trainer",
    }
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{prefix}python-11a.insi-setup",
            json.dumps(setup, ensure_ascii=False),
        )
        archive.writestr(
            f"{prefix}Skripte/imperativ/01_start.md", "# Start\n"
        )
        archive.writestr(
            f"{prefix}Aufgaben/imperativ/quadrat.md",
            "# Quadrat\n\nZeichne ein Quadrat.\n",
        )
        archive.writestr(
            f"{prefix}Trainer/quadrat.yml",
            "format: 1\nid: quadrat\ntitle: Quadrat\ntests:\n"
            "  - type: square\n    start: [50, 50]\n    side: 5\n",
        )
        archive.writestr(f"{prefix}Skripte/_entwurf.md", "# Unsichtbar\n")
        archive.writestr(f"{prefix}README.md", "Nicht Teil des Kursinhalts.\n")
    return target.getvalue()


def test_portable_course_archive_accepts_repository_style_wrapper():
    bundle = parse_course_archive(portable_course_archive(prefix="course-main/"))

    assert bundle.setup.course == "Python 11A"
    assert bundle.revision.startswith("archive-")
    assert set(bundle.files) == {
        "Skripte/imperativ/01_start.md",
        "Aufgaben/imperativ/quadrat.md",
        "Trainer/quadrat.yml",
    }


def test_portable_course_archive_ignores_macos_metadata():
    original = portable_course_archive(prefix="course-main/")
    target = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as source, zipfile.ZipFile(
        target, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for member in source.infolist():
            archive.writestr(member.filename, source.read(member))
        archive.writestr(
            "__MACOSX/course-main/._python-11a.insi-setup",
            b"AppleDouble metadata",
        )

    bundle = parse_course_archive(target.getvalue())

    assert bundle.setup.course == "Python 11A"


def test_course_archive_builder_uses_only_visible_learning_content(tmp_path):
    source = tmp_path / "source"
    setup = tmp_path / "python-11a.insi-setup"
    original = portable_course_archive()
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        for member in archive.infolist():
            if member.filename.endswith(".insi-setup"):
                setup.write_bytes(archive.read(member))
                continue
            target = source / member.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))

    built = parse_course_archive(build_course_archive(source, setup))

    assert built.setup.course == "Python 11A"
    assert built.runtime is None
    assert "Skripte/_entwurf.md" not in built.files
    assert "README.md" not in built.files


def test_course_builder_creates_setup_and_importable_zip(tmp_path):
    source = ensure_course_source(tmp_path / "Mein Kurs")
    (source / "Skripte" / "start.md").write_text("# Start\n", encoding="utf-8")
    (source / "Aufgaben" / "quadrat.md").write_text("# Quadrat\n", encoding="utf-8")
    (source / "Trainer" / "quadrat.yml").write_text(
        "format: 1\nid: quadrat\ntitle: Quadrat\ntests:\n"
        "  - type: square\n    start: [50, 50]\n    side: 5\n",
        encoding="utf-8",
    )

    setup, archive = create_portable_course(
        source,
        teacher="Frau Beispiel",
        school="OSZ KIM",
        course="Mein Kurs",
        runtime_python="3.11",
        runtime_requirements=("PyKIM==0.6.0", "Pyxel==2.9.9"),
        repository="https://github.com/example/mein-kurs.git",
    )

    assert setup.parent == source
    assert archive.is_file()
    assert parse_course_archive(archive.read_bytes()).setup.course == "Mein Kurs"
    assert course_source_counts(source) == {
        "scripts": 1,
        "assignments": 1,
        "trainers": 1,
    }


def test_course_builder_can_author_a_fully_local_course(tmp_path):
    source = ensure_course_source(tmp_path / "Lokaler Kurs")
    script = save_course_markdown(
        source,
        "Skripte",
        "01-start",
        "# Start\n\n```python\nfrom pykim import *\n```",
    )
    draft = AuthorDraft(
        "quadrat",
        "format: 1\nexercises:\n  - id: quadrat\n    title: Quadrat\n"
        "    tests:\n      - type: square\n        start: [50, 50]\n"
        "        side: 5\n",
        "# Quadrat\n@difficulty:einfach\n\nZeichne ein Quadrat.\n\n"
        "## Anforderungen\n\n- Verwende vier gleich lange Seiten.\n",
    )
    markdown, trainer = save_course_assignment(source, draft)

    setup, archive = create_portable_course(
        source,
        teacher="Frau Lokal",
        school="Offline-Schule",
        course="Lokaler Kurs",
        runtime_python="3.11",
        runtime_requirements=("PyKIM==0.6.0", "Pyxel==2.9.9"),
    )
    bundle = parse_course_archive(archive.read_bytes())

    assert script.is_file() and markdown.is_file() and trainer.is_file()
    assert course_documents(source, "Skripte") == ("01-start",)
    assert load_course_document(source, "Skripte", "01-start").startswith("# Start")
    assert bundle.setup.repository == ""
    assert setup.parent == source
    assert set(bundle.files) == {
        "Skripte/imperativ/01-start.md",
        "Aufgaben/imperativ/quadrat.md",
        "Trainer/quadrat.yml",
    }


def test_portable_course_can_contain_only_scripts(tmp_path):
    source = tmp_path / "Nur Skript"
    (source / "Skripte" / "imperativ").mkdir(parents=True)
    (source / "Skripte" / "imperativ" / "start.md").write_text(
        "# Start\n\nEin reiner Lesekurs.\n", encoding="utf-8"
    )

    setup, archive = create_portable_course(
        source,
        teacher="Frau Flexibel",
        school="Offline-Schule",
        course="Nur Skript",
        runtime_python="3.11",
        runtime_requirements=(),
    )
    bundle = parse_course_archive(archive.read_bytes())

    assert setup.is_file()
    assert set(bundle.files) == {"Skripte/imperativ/start.md"}


def test_existing_course_files_are_suggested_and_copied_by_user_mapping(tmp_path):
    source = tmp_path / "Materialsammlung"
    source.mkdir()
    (source / "Kapitel.md").write_text("# Schleifen\n\nEin Kapitel.\n", encoding="utf-8")
    (source / "Reflexion.txt").write_text(
        "# Reflexion\n@difficulty:einfach\n\nWas hast du gelernt?\n",
        encoding="utf-8",
    )
    (source / "Pruefung.yaml").write_text(
        "format: 1\nid: test\ntitle: Test\nmode: answer\n",
        encoding="utf-8",
    )

    candidates = analyze_course_directory(source)
    suggestions = {item.relative_path: item.suggested_kind for item in candidates}
    imported = import_course_candidates(source, suggestions)

    assert suggestions == {
        "Kapitel.md": "script",
        "Pruefung.yaml": "trainer",
        "Reflexion.txt": "task",
    }
    assert {path.relative_to(source).as_posix() for path in imported} == {
        "Skripte/imperativ/Kapitel.md",
        "Aufgaben/imperativ/Reflexion.md",
        "Trainer/Pruefung.yml",
    }
    assert (source / "Kapitel.md").is_file()


def test_repository_documentation_is_not_suggested_as_course_content(tmp_path):
    source = tmp_path / "Repository"
    source.mkdir()
    for name in (
        "README.md",
        "CHANGELOG.md",
        "SECURITY.md",
        "QUALITAETSSICHERUNG.md",
        "TRAINER_AUTOREN.md",
    ):
        (source / name).write_text(f"# {name}\n", encoding="utf-8")
    (source / "01_start.md").write_text("# Start\n", encoding="utf-8")

    suggestions = {
        item.relative_path: item.suggested_kind
        for item in analyze_course_directory(source)
    }

    assert suggestions["01_start.md"] == "script"
    assert all(
        suggestions[name] == "ignore"
        for name in suggestions
        if name != "01_start.md"
    )


def test_portable_course_archive_rejects_unsafe_paths():
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("../ausbruch.txt", "nicht erlaubt")
        archive.writestr("course.insi-setup", "{}")

    with pytest.raises(ValueError, match="unsicheren Dateipfad"):
        parse_course_archive(target.getvalue())


def test_portable_course_archive_rejects_symbolic_links():
    target = io.BytesIO()
    link = zipfile.ZipInfo("course-main/verknuepfung")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr(link, "../../private")
        archive.writestr("course-main/course.insi-setup", "{}")

    with pytest.raises(ValueError, match="symbolischen Links"):
        parse_course_archive(target.getvalue())


def test_archive_import_is_offline_and_name_collisions_create_a_second_course(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    data = portable_course_archive(prefix="course-main/")

    first_info, first = install_new_course_archive(
        data, base_directory=tmp_path / "courses"
    )
    first_task = first / "Aufgaben" / "imperativ" / "quadrat.py"
    first_task.write_text("# persönliche Lösung\n", encoding="utf-8")
    second_info, second = install_new_course_archive(
        data, base_directory=tmp_path / "courses"
    )

    assert first_info == second_info
    assert first.name == "python-11a"
    assert second.name == "python-11a-2"
    assert first_task.read_text(encoding="utf-8") == "# persönliche Lösung\n"
    assert course_content_source(first)["type"] == "archive"
    assert course_content_source(second)["type"] == "archive"
    set_course_directory(first)
    assert active_content_root(PACKAGED_CONTENT_ROOT).name.startswith("archive-")
    result = sync_installed_course_content(first)
    assert not result.checked_online
    assert "kein Online-Abgleich" in result.message

    # Der Archivimport lädt die globalen Trainerregister neu. Für die folgenden
    # Tests stellen wir deshalb den mitgelieferten Inhalt ausdrücklich wieder her.
    clear_course_selection()
    monkeypatch.setenv("PYKIM_CONTENT_DIR", str(PACKAGED_CONTENT_ROOT))
    from insi.registries import activate_content_registries

    activate_content_registries(PACKAGED_CONTENT_ROOT)


def test_course_deletion_uses_system_trash_and_forgets_course(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    create_course(course)
    setup = course / ".pykim" / "course.insi-setup"
    setup.parent.mkdir(exist_ok=True)
    setup.write_text("{}", encoding="utf-8")
    trashed = []
    monkeypatch.setitem(
        sys.modules,
        "send2trash",
        SimpleNamespace(send2trash=lambda path: trashed.append(path)),
    )

    trash_course(course)

    assert trashed == [str(course.resolve())]
    assert get_course_directory() is None
    assert get_course_directories() == ()


def test_course_deletion_rejects_unmarked_directories(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    directory = tmp_path / "ordinary-folder"
    directory.mkdir()
    set_course_directory(directory)

    with pytest.raises(ValueError, match="Kurskennung"):
        trash_course(directory)


def test_startup_sync_uses_repository_from_installed_course_setup(tmp_path, monkeypatch):
    course = tmp_path / "course"
    target = tmp_path / "config" / "content" / "versions" / ("a" * 40)
    course.mkdir()
    target.mkdir(parents=True)
    setup = SimpleNamespace(
        trainers_path="Trainer",
        assignments_path="Aufgaben",
    )
    calls = []

    monkeypatch.setattr(
        "insi.course_setup.course_setup_info", lambda selected: setup
    )
    monkeypatch.setattr(
        "insi.updates.active_content_root", lambda _packaged: tmp_path / "old"
    )
    monkeypatch.setattr(
        "insi.updates.sync_certificate_content",
        lambda configuration, timeout=20.0: calls.append(
            (configuration, timeout)
        ) or target,
    )
    monkeypatch.setattr(
        "insi.registries.activate_content_registries",
        lambda root, **paths: calls.append(("registries", root, paths)),
    )
    monkeypatch.setattr(
        "insi.course.provision_course_exercises",
        lambda selected: calls.append(("provision", selected)),
    )

    result = sync_installed_course_content(course, timeout=7.0)

    assert result.checked_online and result.updated
    assert calls == [
        (setup, 7.0),
        (
            "registries",
            tmp_path / "old",
            {"trainers_path": "Trainer", "assignments_path": "Aufgaben"},
        ),
        ("provision", course.resolve()),
    ]


def test_browser_playground_starts_with_plain_python_and_has_reset_action():
    assert "for zahl in range(1, 6)" in PYODIDE_PLAYGROUND
    assert "from pykim" not in PYODIDE_PLAYGROUND
    assert "resetPyKIMBrowserExample" in PYODIDE_PLAYGROUND
    assert "stopPyKIMBrowserPython" in PYODIDE_PLAYGROUND
    assert "erst beim Ausführen geladen" in PYODIDE_PLAYGROUND
    assert "pyodide-highlight" in PYODIDE_PLAYGROUND
    assert "handlePyKIMBrowserEditorKey" in PYODIDE_PLAYGROUND


def test_every_exercise_has_a_complete_assignment():
    from insi.training.registry import exercise_names

    assert set(ASSIGNMENTS) == set(exercise_names())
    assert get_assignment("quadrat-5").summary
    assert task_assignment("quadrat-5").difficulty == "einfach"
    assert task_assignment("musik-pixel-klasse").difficulty == "fortgeschritten"
    assert "@difficulty:" not in render_task_markdown(
        task_document("quadrat-5").content
    )
    assert "# Praxischeck" not in render_task_markdown(
        task_document("quadrat-5").content
    )


def test_assignment_metadata_is_optional_for_repository_markdown(
    tmp_path, monkeypatch
):
    overlay = tmp_path / "overlay"
    assignment = overlay / "Aufgaben" / "imperativ" / "frei.md"
    assignment.parent.mkdir(parents=True)
    assignment.write_text(
        "# Freie Aufgabe\n\nBearbeite diese Aufgabe ohne Metadaten.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYKIM_CONTENT_DIR", str(overlay))

    parsed = task_assignment("frei")

    assert parsed.summary == "Bearbeite diese Aufgabe ohne Metadaten."
    assert parsed.requirements == ()
    assert parsed.difficulty == "mittel"


def test_task_block_annotations_are_hidden_from_assignment_text():
    rendered = render_task_markdown(
        "# Puzzle\n\nOrdne den Code.\n\n@block:start\n```python\nx = 1\n```\n"
    )

    assert rendered == "Ordne den Code."


def test_task_hints_and_sources_are_parsed_but_hidden_from_assignment():
    content = """# Aufgabe
@difficulty:mittel
@tags: schleifen, pixel, schleifen
@source: CS Circles | https://example.test/task

Ordne den Code.

@hint: Beginne mit dem Import.
@hint: Der Funktionsaufruf steht am Ende.
"""

    assert render_task_markdown(content) == "Ordne den Code."
    assert task_hints(content) == (
        "Beginne mit dem Import.",
        "Der Funktionsaufruf steht am Ende.",
    )
    assert task_tags(content) == ("schleifen", "pixel")
    assert task_sources(content)[0].label == "CS Circles"
    assert task_sources(content)[0].url == "https://example.test/task"


def test_markedown_parser_reports_annotations_and_line_specific_errors():
    valid = """# Aufgabe
@difficulty:mittel
@tags: schleifen, pixel
@hint: Prüfe deine Startposition, bevor du beginnst.
@source: Eigene Aufgabe | https://example.test/aufgabe

Löse die Aufgabe.

@block:start step=1
```python
from pykim import *
```
"""
    document = parse_markedown(valid, kind="task")

    assert document.valid
    assert [item.name for item in document.annotations] == [
        "difficulty",
        "tags",
        "hint",
        "source",
        "block",
    ]
    assert document.code_blocks[0].language == "python"

    invalid = "# Fehler\n@tags: Python, python\n@unknown: wert\n```python\n"
    issues = validate_markedown(invalid, kind="task")

    assert {issue.code for issue in issues} >= {
        "tags",
        "unknown-annotation",
        "unclosed-code",
        "missing-difficulty",
    }
    assert all(issue.line >= 1 for issue in issues)


def test_packaged_learning_content_is_valid_markedown():
    issues = []
    for paradigm in ("imperativ", "oop"):
        for chapter in script_chapters(paradigm):
            issues.extend(
                (chapter.path.name, issue)
                for issue in validate_markedown(chapter.content, kind="script")
            )
        for task in task_documents(paradigm):
            issues.extend(
                (task.path.name, issue)
                for issue in validate_markedown(task.content, kind="task")
            )

    assert issues == []


def test_markdown_library_covers_all_trainers_and_both_learning_paths():
    from insi.training.registry import exercise_names

    assert set(task_names()) == set(exercise_names())
    assert script_chapters("imperativ")
    assert script_chapters("oop")


def test_content_overlay_can_replace_scripts_without_touching_packaged_files(
    tmp_path, monkeypatch
):
    overlay = tmp_path / "overlay"
    chapter = overlay / "Skripte" / "imperativ" / "00_neu.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("# Aktualisiertes Kapitel\n", encoding="utf-8")
    nested = overlay / "Skripte" / "imperativ" / "unterricht" / "01_mehr.md"
    nested.parent.mkdir()
    nested.write_text("# Weiteres Kapitel\n", encoding="utf-8")
    hidden = overlay / "Skripte" / "imperativ" / "_entwuerfe" / "alt.md"
    hidden.parent.mkdir()
    hidden.write_text("# Unsichtbar\n", encoding="utf-8")
    (overlay / "Skripte" / "imperativ" / "README.md").write_text(
        "# Repository-Dokumentation\n", encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONTENT_DIR", str(overlay))

    assert active_content_root(PACKAGED_CONTENT_ROOT) == overlay
    assert [item.title for item in script_chapters("imperativ")] == [
        "Aktualisiertes Kapitel",
        "Weiteres Kapitel",
    ]


def test_bundled_content_manifest_matches_all_markdown_files():
    manifest = json.loads(
        (PACKAGED_CONTENT_ROOT / "content-manifest.json").read_text(encoding="utf-8")
    )
    expected = manifest["files"]
    actual = {
        path.relative_to(PACKAGED_CONTENT_ROOT).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for folder, pattern in (("Skripte", "*.md"), ("Aufgaben", "*.md"), ("Trainer", "*.yml"))
        for path in (PACKAGED_CONTENT_ROOT / folder).rglob(pattern)
    }

    assert expected == actual


def test_content_update_is_hash_checked_and_activated_atomically(tmp_path, monkeypatch):
    source = io.BytesIO()
    content = b"# Neues Kapitel\n"
    with zipfile.ZipFile(source, "w") as bundle:
        bundle.writestr("Skripte/imperativ/01_neu.md", content)
    archive = source.getvalue()
    manifest = {
        "content_version": "2099.1",
        "package_url": "https://example.invalid/content.zip",
        "package_sha256": hashlib.sha256(archive).hexdigest(),
        "files": {
            "Skripte/imperativ/01_neu.md": hashlib.sha256(content).hexdigest()
        },
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return archive

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.updates.urlopen", lambda request, timeout: Response())

    installed = install_content_update(manifest)

    assert (installed / "Skripte/imperativ/01_neu.md").read_bytes() == content
    assert active_content_root(PACKAGED_CONTENT_ROOT) == installed


def test_content_update_rejects_changed_archive(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b"manipuliert"

    monkeypatch.setattr("insi.updates.urlopen", lambda request, timeout: Response())
    with pytest.raises(ValueError, match="Prüfsumme"):
        install_content_update(
            {
                "content_version": "2099.2",
                "package_url": "https://example.invalid/content.zip",
                "package_sha256": "0" * 64,
                "files": {"Skripte/imperativ/x.md": "0" * 64},
            }
        )


def test_content_update_falls_back_to_hash_checked_raw_files(tmp_path, monkeypatch):
    content = b"# Fallback-Kapitel\n"
    name = "Skripte/imperativ/01_fallback.md"
    manifest = {
        "content_version": "2099.3",
        "package_url": "https://example.invalid/content.zip",
        "package_sha256": "0" * 64,
        "files": {name: hashlib.sha256(content).hexdigest()},
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return content

    def open_with_failed_archive(request, timeout):
        if request.full_url == manifest["package_url"]:
            raise ConnectionResetError("release server closed the connection")
        assert request.full_url.endswith(name)
        return Response()

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.updates.urlopen", open_with_failed_archive)

    installed = install_content_update(manifest)

    assert (installed / name).read_bytes() == content


def test_damaged_active_content_falls_back_to_packaged_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    version = "2099.3"
    root = tmp_path / "config" / "content" / "versions" / version
    chapter = root / "Skripte" / "imperativ" / "x.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("beschädigt", encoding="utf-8")
    (root / "content-manifest.json").write_text(
        json.dumps({"content_version": version, "files": {
            "Skripte/imperativ/x.md": "0" * 64
        }}),
        encoding="utf-8",
    )
    marker = tmp_path / "config" / "content" / "active.json"
    marker.write_text(json.dumps({"content_version": version}), encoding="utf-8")

    assert active_content_root(PACKAGED_CONTENT_ROOT) == PACKAGED_CONTENT_ROOT
    assert task_document("quadrat-5").paradigm == "imperativ"
    assert task_document("musik-pixel-klasse").paradigm == "oop"
    assert len(script_code_examples()) >= 50


def test_script_example_execution_captures_output_and_disables_progress():
    result = execute_script_example("print('Hallo aus dem Skript')")

    assert result.returncode == 0
    assert result.stdout.strip() == "Hallo aus dem Skript"
    assert result.stderr == ""


def test_script_example_uses_unbuffered_python(monkeypatch):
    calls = []

    class Completed:
        returncode = 0
        stdout = "28\n19\n"
        stderr = ""

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return Completed()

    monkeypatch.setattr("insi.system.sandbox_run", run)

    result = execute_script_example("print(28)\nprint(19)")

    assert calls[0][0][1] == "-u"
    assert calls[0][1]["env"]["PYTHONUNBUFFERED"] == "1"
    assert result.stdout == "28\n19\n"


def test_all_executable_script_blocks_are_valid_python():
    for source in script_code_examples():
        ast.parse(source)


def test_loop_comparison_examples_are_visibly_animated_and_painted():
    examples = [
        source
        for source in script_code_examples()
        if "right(4)" in source and "down(4)" in source
    ]

    assert len(examples) == 2
    for source in examples:
        assert "set_position(60, 40)" in source
        assert "speed(15)" in source
        assert 'paint("purple")' in source
        assert source.rstrip().endswith("run()")


def test_every_run_annotated_block_is_a_complete_program():
    audits = annotated_script_blocks()

    assert audits
    assert all(audit.runnable for audit in audits)
    assert {audit.kind for audit in audits} == {"console", "pykim", "pyxel"}


def test_every_console_and_pykim_script_example_runs_headless():
    failures = []
    for audit in annotated_script_blocks():
        if audit.kind == "pyxel":
            continue
        result = run_headless(audit)
        if result.returncode != 0:
            failures.append((audit.path.name, audit.line, result.stderr))

    assert failures == []


def test_revealed_hint_count_can_reuse_loaded_progress(monkeypatch):
    monkeypatch.setattr(
        "insi.progress.load_progress",
        lambda *_args, **_kwargs: pytest.fail("Lernstand wurde erneut geladen"),
    )

    assert revealed_hint_count(
        "imperativ/test", progress={"hints": {"imperativ/test": 2}}
    ) == 2


def test_author_workspace_loads_a_published_pair():
    draft = load_published_draft("quadrat-5")

    assert draft.name == "quadrat-5"
    assert "id: quadrat-5" in draft.trainer_source
    assert draft.assignment_markdown.startswith("# Quadrat")
    assert validate_author_draft(draft) == ()


def test_author_workspace_saves_both_files_with_overwrite_protection(tmp_path):
    trainer = generate_exercise_source(
        "entwurf-test", "Entwurf Test", ("pixels", "loop"), optimal_lines=8
    )
    markdown = assignment_markdown(
        "Entwurf Test",
        "Zeichne ein Muster.",
        "Male einen Punkt.\nNutze eine Schleife.",
        "mittel",
        hints=("Beginne klein.", "Nutze eine Schleife."),
        tags=("pixel", "schleifen"),
    )
    draft = AuthorDraft("entwurf-test", trainer, markdown)

    trainer_path, markdown_path = save_author_draft(
        tmp_path, draft, paradigm="imperativ"
    )

    assert trainer_path.read_text(encoding="utf-8") == trainer
    assert markdown_path.read_text(encoding="utf-8") == markdown
    assert "@tags: pixel, schleifen" in markdown
    assert markdown.count("@hint:") == 2
    assert len(draft.content_hash) == 64
    with pytest.raises(FileExistsError):
        save_author_draft(tmp_path, draft, paradigm="imperativ")
    save_author_draft(tmp_path, draft, paradigm="imperativ", overwrite=True)


def test_author_workspace_rejects_mismatched_builder_name():
    draft = AuthorDraft(
        "richtiger-name",
        generate_exercise_source("anderer-name", "Titel", ("loop",)),
        assignment_markdown("Titel", "Zusammenfassung", "Anforderung", "einfach"),
    )

    assert any("Kennung" in issue for issue in validate_author_draft(draft))


def test_script_button_annotations_apply_only_to_the_next_code_block():
    content = (
        "@button:run\n@button:copy\n```python\nprint('eins')\n```\n\n"
        "```python\nprint('zwei')\n```"
    )

    rendered = render_script_markdown(content)

    assert 'data-buttons="run,copy"' in rendered
    assert "@button:" not in rendered
    assert rendered.count("pykim-code-options") == 1


def test_course_setup_copies_legacy_solution_into_new_structure(tmp_path, monkeypatch):
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    course = tmp_path / "course"
    legacy = course / "01_grundlagen" / "quadrat_5.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("# meine alte Lösung\nright(5)\n", encoding="utf-8")

    create_course(course)
    provision_course_exercises(course)

    migrated = course / "Aufgaben" / "imperativ" / "quadrat_5.py"
    assert migrated.read_text(encoding="utf-8") == legacy.read_text(encoding="utf-8")
    assert legacy.exists()


def test_packaged_examples_are_complete_and_copy_without_overwriting(tmp_path):
    examples = example_programs()
    assert len(examples) == 20
    assert all(example.source and example.path.exists() for example in examples)

    target, created = copy_example_to_course("paint_line", tmp_path)
    assert created
    target.write_text("# meine Änderung", encoding="utf-8")
    same_target, created = copy_example_to_course("paint_line", tmp_path)
    assert not created
    assert same_target == target
    assert target.read_text(encoding="utf-8") == "# meine Änderung"
    assert target.relative_to(tmp_path).parts[:2] == ("Projekte", "beispiele")
    assert (target.parent / "projekt.json").exists()


def test_all_packaged_examples_run_headless():
    failures = []
    for example in example_programs():
        audit = classify_script_block(example.source, example.path, 1)
        if not audit.runnable:
            failures.append((example.name, audit.reason))
            continue
        result = run_headless(audit)
        if result.returncode:
            failures.append((example.name, result.stderr))

    assert failures == []


def test_running_example_explicitly_disables_progress(monkeypatch):
    calls = []

    class Process:
        def wait(self):
            return 0

    monkeypatch.setattr(
        "insi.examples.sandbox_popen",
        lambda command, **kwargs: (calls.append((command, kwargs)) or Process()),
    )

    launch_example("interaktive_steuerung_aufgabe")

    assert calls[0][1]["env"]["PYKIM_PROGRESS_MODE"] == "disabled"


def test_gallery_example_uses_observable_execution_manager(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "insi.examples.script_example_manager.start",
        lambda source, **_options: calls.append(source) or "job-123",
    )

    assert start_example("paint_line") == "job-123"
    assert calls == [next(item.source for item in example_programs() if item.name == "paint_line")]


def test_cleanup_removes_only_packaged_example_attempts(tmp_path):
    course = tmp_path / "course"
    progress_directory = course / ".pykim"
    progress_directory.mkdir(parents=True)
    example_source = example_programs()[0].source
    progress_path = progress_directory / "progress.json"
    progress_path.write_text(
        json.dumps(
            {
                "format": 1,
                "attempts": [
                    {"exercise": "example", "source": example_source},
                    {"exercise": "mine", "source": "right(5)"},
                ],
                "journal": {},
            }
        ),
        encoding="utf-8",
    )

    assert remove_packaged_example_attempts(course) == 1
    assert load_progress(course)["attempts"] == [
        {"exercise": "mine", "source": "right(5)"}
    ]
    assert (progress_directory / "progress.before-example-cleanup.json").exists()


def test_course_setup_creates_all_starters_and_preserves_student_work(
    tmp_path, monkeypatch
):
    config = tmp_path / "config"
    course = tmp_path / "webdav" / "PyKIM-Kurs"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(config))

    first = create_course(course, "Ada")
    provisioned = provision_course_exercises(course)
    square = course / "Aufgaben" / "imperativ" / "quadrat_5.py"
    square.write_text("# meine Lösung", encoding="utf-8")
    second = provision_course_exercises(course)

    assert first["created"] == [".pykim-course.json"]
    assert len(provisioned["created"]) == 11
    assert square.read_text(encoding="utf-8") == "# meine Lösung"
    assert "Aufgaben/imperativ/quadrat_5.py" in second["existing"]
    assert get_course_directory() == course.resolve()
    metadata = json.loads((course / ".pykim-course.json").read_text())
    assert metadata["student_name"] == "Ada"
    assert get_student_name(course) == "Ada"

    create_course(course, "Ada Lovelace")
    assert get_student_name(course) == "Ada Lovelace"



def test_github_version_reads_remote_pyproject(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'[project]\nname = "PyKIM"\nversion = "9.9.9"\n'

    monkeypatch.setattr("insi.system.urlopen", lambda request, timeout: Response())

    info = github_version()

    assert info["github"] == "9.9.9"
    assert info["different"]


def test_release_update_selects_matching_macos_architecture(monkeypatch):
    monkeypatch.setattr("insi.updates.platform.machine", lambda: "x86_64")
    monkeypatch.setattr(
        "insi.updates._json_url",
        lambda url, timeout: {
            "tag_name": "v9.9.9",
            "html_url": "https://example.invalid/release",
            "assets": [
                {
                    "name": "insi-9.9.9-macos-arm64.dmg",
                    "browser_download_url": "https://example.invalid/arm.dmg",
                },
                {
                    "name": "insi-9.9.9-macos-x86_64.dmg",
                    "browser_download_url": "https://example.invalid/intel.dmg",
                },
            ],
        },
    )

    update = check_app_update()

    assert update.newer
    assert update.download_url.endswith("intel.dmg")


def test_content_update_compares_bundled_manifest(tmp_path, monkeypatch):
    packaged = tmp_path / "guide"
    packaged.mkdir()
    (packaged / "content-manifest.json").write_text(
        json.dumps({"content_version": "2026.08.1"}), encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url",
        lambda url, timeout: {
            "content_version": "2026.08.2",
            "minimum_app_version": "0.2.0",
        },
    )

    update = check_content_update(packaged)

    assert update.installed == "2026.08.1"
    assert update.newer
    assert update.compatible


def test_content_version_is_displayed_as_german_date():
    assert format_content_version("2026.08.1") == "01.08.2026"
    assert format_content_version("commit-abc") == "commit-abc"


def repository_api(revision, files):
    """Erzeuge Commit- und Git-Baum-Antworten für Synchronisationstests."""
    def response(url, _timeout):
        if "/commits/" in url:
            return {"sha": revision() if callable(revision) else revision}
        if "/git/trees/" in url:
            return {
                "truncated": False,
                "tree": [
                    {"path": name, "type": "blob"}
                    for name in files
                ],
            }
        raise AssertionError(f"Unerwartete API-URL: {url}")
    return response


def test_certificate_content_sync_downloads_individual_hashed_files(tmp_path, monkeypatch):
    from insi.submission.crypto import ContentConfiguration

    files = {
        "Skripte/imperativ/01_start.md": b"# Start\n",
        "Skripte/_backup/00_alt.md": b"# Alt\n",
        "Skripte/imperativ/_entwurf.md": b"# Entwurf\n",
        "Aufgaben/imperativ/quadrat-5.md": b"# Quadrat\n",
        "Trainer/quadrat-5.yml": (
            b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
            b"  - type: square\n    start: [50, 50]\n    side: 5\n"
        ),
    }
    index = {
        "format": 1,
        "scope": "trainer",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in files.items() if name.startswith("Trainer/")
        },
    }
    revision = "a" * 40
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url",
        repository_api(revision, files),
    )

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("insi.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )

    target = sync_certificate_content(configuration)

    assert target.name == revision
    assert (target / "Skripte/imperativ/01_start.md").read_bytes() == files[
        "Skripte/imperativ/01_start.md"
    ]
    assert not (target / "Skripte/_backup/00_alt.md").exists()
    assert not (target / "Skripte/imperativ/_entwurf.md").exists()
    assert not (target / "content.yml").exists()
    assert active_content_root(PACKAGED_CONTENT_ROOT) == target


def test_certificate_authorization_uses_same_named_repository_hash(monkeypatch):
    from insi.submission.crypto import ContentConfiguration

    certificate = b'{"format":"test-certificate"}'
    expected = hashlib.sha256(certificate).hexdigest()
    requested = []
    monkeypatch.setattr(
        "insi.updates._download",
        lambda url, _timeout: requested.append(url) or f"sha256:{expected}\n".encode("ascii"),
    )
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
        "python-11a.pykim-cert",
    )

    result = verify_certificate_authorization(certificate, configuration)

    assert result.checked_online
    assert requested == [
        "https://raw.githubusercontent.com/finalnode/PyKIM_Kurs/main/"
        "certificates/python-11a.pykim-cert"
    ]


def test_certificate_authorization_rejects_unlisted_certificate(monkeypatch):
    from insi.submission.crypto import ContentConfiguration

    monkeypatch.setattr(
        "insi.updates._download",
        lambda *_args: b"sha256:" + b"0" * 64,
    )
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
        "python-11a.pykim-cert",
    )

    with pytest.raises(ValueError, match="nicht zugelassen"):
        verify_certificate_authorization(b"anderes Zertifikat", configuration)


def test_trainer_verification_ignores_remote_assignment_only_changes(tmp_path, monkeypatch):
    from insi.submission.crypto import ContentConfiguration

    files = {
        "Skripte/imperativ/01_start.md": b"# Start\n",
        "Aufgaben/imperativ/quadrat-5.md": b"# Alte Aufgabe\n",
        "Trainer/quadrat-5.yml": (
            b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
            b"  - type: square\n    start: [50, 50]\n    side: 5\n"
        ),
    }
    index = {
        "format": 1,
        "scope": "trainer",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in files.items() if name.startswith("Trainer/")
        },
    }
    revision = "b" * 40
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url", repository_api(revision, files)
    )

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("insi.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )
    sync_certificate_content(configuration)

    files["Aufgaben/imperativ/quadrat-5.md"] = b"# Neue Aufgabenformulierung\n"
    result = verify_certificate_trainers(configuration)

    assert result.checked_online
    assert not result.updated


def test_trainer_verification_replaces_changed_trainer_data(tmp_path, monkeypatch):
    from insi.submission.crypto import ContentConfiguration

    old_trainer = (
        b"format: 1\nid: quadrat-5\ntitle: Quadrat\ntests:\n"
        b"  - type: square\n    start: [50, 50]\n    side: 5\n"
    )
    new_trainer = old_trainer.replace(b"side: 5", b"side: 6")
    files = {
        "Skripte/imperativ/01_start.md": b"# Start\n",
        "Aufgaben/imperativ/quadrat-5.md": b"# Quadrat\n",
        "Trainer/quadrat-5.yml": old_trainer,
    }

    def index():
        return {
            "format": 1,
            "scope": "trainer",
            "files": {
                name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
                for name, data in files.items() if name.startswith("Trainer/")
            },
        }

    revisions = iter(("c" * 40, "d" * 40))
    current_revision = [next(revisions)]
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url",
        repository_api(lambda: current_revision[0], files),
    )

    def download(url, _timeout):
        if url.endswith("/.pykim/trainer-hashes.json"):
            return json.dumps(index()).encode("utf-8")
        return files[next(name for name in files if url.endswith("/" + name))]

    monkeypatch.setattr("insi.updates._download", download)
    configuration = ContentConfiguration(
        "https://github.com/finalnode/PyKIM_Kurs.git",
        "main",
        "Skripte",
        "Aufgaben",
        "Trainer",
    )
    sync_certificate_content(configuration)

    files["Trainer/quadrat-5.yml"] = new_trainer
    current_revision[0] = next(revisions)
    result = verify_certificate_trainers(configuration)

    assert result.checked_online
    assert result.updated
    assert (
        active_content_root(PACKAGED_CONTENT_ROOT) / "Trainer/quadrat-5.yml"
    ).read_bytes() == new_trainer


def test_missing_first_release_is_treated_as_current(tmp_path, monkeypatch):
    packaged = tmp_path / "guide"
    packaged.mkdir()
    (packaged / "content-manifest.json").write_text(
        json.dumps({"content_version": "2026.08.1"}), encoding="utf-8"
    )
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates._json_url",
        lambda url, timeout: (_ for _ in ()).throw(
            HTTPError(url, 404, "Not Found", None, None)
        ),
    )

    status = check_updates(packaged)

    assert status.error == ""
    assert status.app is not None and not status.app.newer
    assert status.content is not None and not status.content.newer


def test_run_student_program_is_limited_to_python_files_in_course(
    tmp_path, monkeypatch
):
    course = tmp_path / "course"
    task = course / "tasks" / "square.py"
    task.parent.mkdir(parents=True)
    task.write_text("print('ok')", encoding="utf-8")
    calls = []
    class Process:
        def wait(self):
            return 0

    monkeypatch.setattr(
        "insi.system.sandbox_popen",
        lambda command, cwd=None, env=None, **_options: (
            calls.append((command, cwd, env)) or Process()
        ),
    )
    monkeypatch.setattr(
        "insi.runtime.selected_runtime",
        lambda course=None: RuntimeCandidate(
            __import__("sys").executable,
            "3.11.0",
            "Test",
            True,
            ("PyKIM", "Pyxel"),
        ),
    )

    assert run_student_program(task, course) == task
    assert calls[0][0][1] == str(task)
    assert calls[0][1] != task.parent
    assert calls[0][1].name.startswith("insi-task-")
    assert str(course.resolve()) in calls[0][2]["PYTHONPATH"].split(__import__("os").pathsep)

    outside = tmp_path / "outside.py"
    outside.write_text("print('no')", encoding="utf-8")
    with pytest.raises(ValueError, match="Kursordner"):
        run_student_program(outside, course)


def test_run_student_program_rejects_non_python_files(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    text = course / "notes.txt"
    text.write_text("nothing", encoding="utf-8")

    with pytest.raises(ValueError, match="Python-Dateien"):
        run_student_program(text, course)


def test_execute_student_program_captures_output(tmp_path, monkeypatch):
    course = tmp_path / "course"
    task = course / "task.py"
    course.mkdir()
    task.write_text("print('Hallo')", encoding="utf-8")

    class Completed:
        returncode = 0
        stdout = "Hallo\n"
        stderr = ""

    calls = []
    monkeypatch.setattr(
        "insi.system.sandbox_run",
        lambda command, **kwargs: (calls.append((command, kwargs)) or Completed()),
    )
    monkeypatch.setattr(
        "insi.runtime.selected_runtime",
        lambda course=None: RuntimeCandidate(
            __import__("sys").executable,
            "3.11.0",
            "Test",
            True,
            ("PyKIM", "Pyxel"),
        ),
    )

    result = execute_student_program(task, course)

    assert result.stdout == "Hallo\n"
    assert result.returncode == 0
    assert calls[0][1]["capture_output"] is True


def test_read_and_save_student_source_only_inside_course(tmp_path):
    course = tmp_path / "course"
    task = course / "tasks" / "square.py"
    task.parent.mkdir(parents=True)
    task.write_text("right(4)\n", encoding="utf-8")

    assert read_student_source(task, course) == "right(4)\n"
    assert save_student_source(task, "right(5)\n", course) == task
    assert task.read_text(encoding="utf-8") == "right(5)\n"

    outside = tmp_path / "outside.py"
    outside.write_text("print('no')", encoding="utf-8")
    with pytest.raises(ValueError, match="Kursordner"):
        save_student_source(outside, "print('changed')", course)
    assert outside.read_text(encoding="utf-8") == "print('no')"


def test_student_source_detects_external_ide_changes(tmp_path):
    course = tmp_path / "course"
    task = course / "task.py"
    course.mkdir()
    task.write_text("right(4)\n", encoding="utf-8")
    loaded_hash = source_hash(task.read_text(encoding="utf-8"))

    task.write_text("# Änderung aus Thonny\n", encoding="utf-8")

    with pytest.raises(SourceConflictError, match="außerhalb"):
        save_student_source(task, "right(5)\n", course, expected_hash=loaded_hash)
    assert task.read_text(encoding="utf-8") == "# Änderung aus Thonny\n"


def test_reset_exercise_creates_backups_for_source_and_progress(tmp_path, monkeypatch):
    course = tmp_path / "course"
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    create_course(course)
    provision_course_exercises(course)
    task = exercise_file("quadrat-5", course)
    assert task is not None
    task.write_text("right(5)\n", encoding="utf-8")
    progress = course / ".pykim" / "progress.json"
    progress.parent.mkdir(exist_ok=True)
    progress.write_text(
        json.dumps({"format": 1, "attempts": [
            {"exercise": "quadrat-5"}, {"exercise": "treppe-5"}
        ], "journal": {}, "hints": {
            "imperativ/quadrat-5": 2,
            "imperativ/treppe-5": 1,
        }}),
        encoding="utf-8",
    )

    reset_exercise_file("quadrat-5", course)
    assert clear_exercise_progress("quadrat-5", course) == 1

    assert 'run(check="quadrat-5")' in task.read_text(encoding="utf-8")
    assert load_progress(course)["attempts"] == [{"exercise": "treppe-5"}]
    assert load_progress(course)["hints"] == {"imperativ/treppe-5": 1}
    assert list((course / ".pykim" / "backups").glob("quadrat_5-*.py"))
    assert list((course / ".pykim" / "backups").glob("progress-quadrat-5-*.json"))


def test_execution_manager_captures_output_and_stops_programs(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    quick = course / "quick.py"
    quick.write_text("print('Hallo aus PyKIM')\n", encoding="utf-8")
    manager = ExecutionManager()

    result = manager.execute(quick, course)
    assert result.returncode == 0
    assert result.stdout.strip() == "Hallo aus PyKIM"

    slow = course / "slow.py"
    slow.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    results = []
    worker = threading.Thread(target=lambda: results.append(manager.execute(slow, course)))
    worker.start()
    for _ in range(100):
        if manager.is_running(slow):
            break
        time.sleep(0.01)
    assert manager.stop(slow)
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert results[0].stopped


def test_script_example_manager_streams_output_before_program_finishes():
    manager = ScriptExampleManager()
    job_id = manager.start(
        "import time\nprint('sofort')\ntime.sleep(1)\nprint('fertig')"
    )

    live_status = None
    for _ in range(100):
        live_status = manager.status(job_id)
        if live_status and "sofort" in live_status["stdout"]:
            break
        time.sleep(0.01)

    assert live_status is not None
    assert "sofort" in live_status["stdout"]
    assert live_status["running"]

    for _ in range(200):
        final_status = manager.status(job_id)
        if final_status and not final_status["running"]:
            break
        time.sleep(0.01)
    assert final_status["returncode"] == 0
    assert "fertig" in final_status["stdout"]


def test_script_example_manager_can_stop_one_program():
    manager = ScriptExampleManager()
    first = manager.start("import time\ntime.sleep(30)")
    second = manager.start("import time\ntime.sleep(30)")

    assert manager.stop(first)
    assert not manager.status(first)["running"] or manager.status(first)["returncode"] is not None
    assert manager.status(second)["running"]
    assert manager.stop(second)


def test_pyxel_repair_uses_supported_version_range(monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return object()

    monkeypatch.setattr("insi.system.subprocess.run", run)

    install_or_repair_pyxel()

    assert calls[0][0][-1] == "pyxel>=2.2,<3"
    assert calls[0][1]["check"] is True
    execute_student_program,
