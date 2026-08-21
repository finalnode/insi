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
    snapshot_project,
    workspace_file_roots,
)


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
