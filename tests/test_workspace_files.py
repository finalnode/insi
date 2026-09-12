import shutil
from pathlib import Path

import pytest

from insi.workspace_files import (
    FileScope,
    course_files_directory,
    global_files_directory,
    import_workspace_bytes,
    import_workspace_file,
    project_files_directory,
    sandbox_readable_roots,
    workspace_file_roots,
)
from insi.project_history import (
    project_states,
    restore_project_state,
    save_project_state,
    snapshot_project,
    snapshot_project_if_changed,
)
from insi.projects import create_project


def test_imports_are_copied_into_global_course_and_project_scopes(tmp_path):
    course = tmp_path / "course"
    project = course / "Projekte" / "game"
    project.mkdir(parents=True)

    global_file = import_workspace_bytes(b"global", "palette.json", FileScope.GLOBAL)
    course_file = import_workspace_bytes(
        b"course", "words.txt", FileScope.COURSE, course=course
    )
    project_file = import_workspace_bytes(
        b"project",
        "level.txt",
        FileScope.PROJECT,
        course=course,
        project=project,
    )

    assert global_file.path.parent == global_files_directory()
    assert course_file.path.parent == course_files_directory(course)
    assert project_file.path.parent == project_files_directory(project)
    assert global_file.path.read_bytes() == b"global"
    assert course_file.path.read_bytes() == b"course"
    assert project_file.path.read_bytes() == b"project"
    assert set(workspace_file_roots(course)) == {
        global_files_directory(),
        course_files_directory(course),
    }


def test_duplicate_imports_never_overwrite_existing_files(tmp_path):
    course = tmp_path / "course"

    first = import_workspace_bytes(b"first", "data.csv", FileScope.COURSE, course=course)
    second = import_workspace_bytes(b"second", "data.csv", FileScope.COURSE, course=course)

    assert first.path.name == "data.csv"
    assert second.path.name == "data-2.csv"
    assert first.path.read_bytes() == b"first"
    assert second.path.read_bytes() == b"second"


@pytest.mark.parametrize("filename", ["../secret.txt", "folder/file.txt", "", ".."])
def test_import_rejects_paths_instead_of_plain_filenames(tmp_path, filename):
    with pytest.raises(ValueError):
        import_workspace_bytes(b"x", filename, FileScope.COURSE, course=tmp_path)


def test_external_symlinks_are_not_followed(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("secret", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlinks stehen auf diesem Testsystem nicht zur Verfügung.")

    with pytest.raises(ValueError, match="reguläre Dateien"):
        import_workspace_file(link, FileScope.GLOBAL)


def test_project_import_cannot_target_a_directory_outside_the_course(tmp_path):
    course = tmp_path / "course"
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(ValueError, match="nicht im ausgewählten Kurs"):
        import_workspace_bytes(
            b"x",
            "file.txt",
            FileScope.PROJECT,
            course=course,
            project=outside,
        )


def test_import_size_limit_is_enforced_before_writing(tmp_path, monkeypatch):
    monkeypatch.setattr("insi.workspace_files.MAX_IMPORTED_FILE_BYTES", 3)

    with pytest.raises(ValueError, match="größer"):
        import_workspace_bytes(b"four", "file.bin", FileScope.COURSE, course=tmp_path)

    assert not course_files_directory(tmp_path).joinpath("file.bin").exists()


def test_project_snapshots_are_complete_and_pruned(tmp_path):
    course = tmp_path / "course"
    project = course / "Projekte" / "game"
    project.mkdir(parents=True)
    source = project / "main.py"

    for index in range(4):
        source.write_text(f"print({index})\n", encoding="utf-8")
        snapshot_project(project, course, keep=2)

    snapshot_root = course / ".pykim" / "backups" / "project-snapshots" / "game"
    snapshots = sorted(item for item in snapshot_root.iterdir() if item.is_dir())

    assert len(snapshots) == 2
    assert (snapshots[-1] / "main.py").read_text(encoding="utf-8") == "print(3)\n"


def test_automatic_execution_snapshot_is_created_only_for_changed_content(tmp_path):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")

    first = snapshot_project_if_changed(project.directory, course)
    duplicate = snapshot_project_if_changed(project.directory, course)
    project.entrypoint.write_text("print('changed')\n", encoding="utf-8")
    second = snapshot_project_if_changed(project.directory, course)

    assert first is not None
    assert duplicate is None
    assert second is not None
    states = project_states(project.directory, course)
    assert len(states) == 2
    assert all(state.title == "Automatisch vor Ausführung" for state in states)
    assert all(state.comment == "Stand vor dem Start des Projekts." for state in states)


def test_named_current_state_prevents_redundant_execution_snapshot(tmp_path):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")
    named = save_project_state(project.directory, course, "Funktioniert")

    automatic = snapshot_project_if_changed(project.directory, course)

    assert automatic is None
    assert project_states(project.directory, course) == (named,)


def test_named_project_states_keep_comment_hashes_and_survive_auto_pruning(tmp_path):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")
    project.entrypoint.write_text("print('named')\n", encoding="utf-8")

    named = save_project_state(
        project.directory,
        course,
        "Erster spielbarer Stand",
        "Die Bewegung funktioniert.",
    )
    for index in range(3):
        project.entrypoint.write_text(f"print({index})\n", encoding="utf-8")
        snapshot_project(project.directory, course, keep=1)

    states = project_states(project.directory, course)

    assert len(states) == 2
    assert named.id in {state.id for state in states}
    restored_named = next(state for state in states if state.id == named.id)
    assert restored_named.named
    assert restored_named.comment == "Die Bewegung funktioniert."
    assert any(file.path == "main.py" and len(file.sha256) == 64 for file in named.files)


def test_project_state_restore_preserves_current_work_as_automatic_state(tmp_path):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")
    project.entrypoint.write_text("print('stable')\n", encoding="utf-8")
    stable = save_project_state(project.directory, course, "Stabil")
    project.entrypoint.write_text("print('experiment')\n", encoding="utf-8")

    restored = restore_project_state(project.directory, course, stable.id)

    assert restored.id == stable.id
    assert project.entrypoint.read_text(encoding="utf-8") == "print('stable')\n"
    safety = next(
        state
        for state in project_states(project.directory, course)
        if state.kind == "automatic" and state.title == "Vor Wiederherstellung"
    )
    assert next(file for file in safety.files if file.path == "main.py").sha256 != next(
        file for file in stable.files if file.path == "main.py"
    ).sha256


def test_oldest_automatic_state_can_be_restored_while_pruning(tmp_path):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")
    for index in range(10):
        project.entrypoint.write_text(f"print({index})\n", encoding="utf-8")
        snapshot_project(project.directory, course)
    oldest = project_states(project.directory, course)[-1]
    project.entrypoint.write_text("print('current')\n", encoding="utf-8")

    restore_project_state(project.directory, course, oldest.id)

    assert project.entrypoint.read_text(encoding="utf-8") == "print(0)\n"


def test_legacy_snapshot_without_manifest_remains_restorable(tmp_path):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")
    project.entrypoint.write_text("print('legacy')\n", encoding="utf-8")
    legacy = (
        course
        / ".pykim"
        / "backups"
        / "project-snapshots"
        / project.slug
        / "20260101T120000.000000Z"
    )
    legacy.parent.mkdir(parents=True)
    shutil.copytree(project.directory, legacy)
    project.entrypoint.write_text("print('current')\n", encoding="utf-8")

    state = next(state for state in project_states(project.directory, course) if state.path == legacy)
    restore_project_state(project.directory, course, state.id)

    assert not state.named
    assert "Älterer Projektstand" in state.comment
    assert project.entrypoint.read_text(encoding="utf-8") == "print('legacy')\n"


def test_tampered_project_state_is_rejected_without_changing_project(tmp_path):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")
    state = save_project_state(project.directory, course, "Sauber")
    project.entrypoint.write_text("print('current')\n", encoding="utf-8")
    (state.path / "main.py").write_text("print('tampered')\n", encoding="utf-8")

    with pytest.raises(ValueError, match="nachträglich verändert"):
        restore_project_state(project.directory, course, state.id)

    assert project.entrypoint.read_text(encoding="utf-8") == "print('current')\n"


def test_failed_project_state_swap_rolls_back_current_project(tmp_path, monkeypatch):
    course = tmp_path / "course"
    project = create_project(course, "Game", "empty")
    state = save_project_state(project.directory, course, "Alt")
    project.entrypoint.write_text("print('current')\n", encoding="utf-8")
    real_replace = __import__("insi.project_history", fromlist=["os"]).os.replace

    def fail_activation(source, target):
        if ".restore-" in Path(source).name and Path(target) == project.directory:
            raise OSError("simulierter Abbruch")
        return real_replace(source, target)

    monkeypatch.setattr("insi.project_history.os.replace", fail_activation)

    with pytest.raises(OSError, match="simulierter Abbruch"):
        restore_project_state(project.directory, course, state.id)

    assert project.entrypoint.read_text(encoding="utf-8") == "print('current')\n"


def test_sandbox_roots_expose_selected_files_but_not_the_whole_course(tmp_path):
    course = tmp_path / "course"
    task = course / "Aufgaben" / "task.py"
    task.parent.mkdir(parents=True)
    task.write_text("print('ok')", encoding="utf-8")
    internal = course / ".pykim" / "private.json"
    internal.parent.mkdir()
    internal.write_text("secret", encoding="utf-8")

    roots = sandbox_readable_roots(course, task)

    assert task.resolve() in roots
    assert course.resolve() not in roots
    assert internal.resolve() not in roots


def test_snapshot_rejects_arbitrary_directories(tmp_path):
    course = tmp_path / "course"
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(ValueError, match="Projekt des Kurses"):
        snapshot_project(outside, course)


def test_snapshot_rejects_project_symlinks_that_could_copy_external_data(tmp_path):
    course = tmp_path / "course"
    project = course / "Projekte" / "game"
    project.mkdir(parents=True)
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")
    try:
        (project / "linked.txt").symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks stehen auf diesem Testsystem nicht zur Verfügung.")

    with pytest.raises(ValueError, match="symbolischen Links"):
        snapshot_project(project, course)
