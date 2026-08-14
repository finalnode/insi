import subprocess
import sys

import pytest

from insi.extensions import (
    add_extension,
    ensure_extension_module,
    list_extensions,
    update_extension,
)


def test_extension_is_importable_from_course_root(tmp_path):
    created = add_extension(
        tmp_path, "def square(length):\n    return length * 4\n"
    )

    assert created[0].name == "square"
    assert created[0].import_line == "from erweiterungen import square"
    completed = subprocess.run(
        [sys.executable, "-c", "from erweiterungen import *; print(square(5))"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == "20"


def test_existing_function_name_is_rejected(tmp_path):
    add_extension(tmp_path, "def square():\n    return 1\n")

    with pytest.raises(ValueError, match="bereits"):
        add_extension(tmp_path, "def square():\n    return 2\n")


def test_single_function_can_be_updated_without_touching_others(tmp_path):
    add_extension(
        tmp_path,
        "def square():\n    return 1\n\n\ndef stairs():\n    return 3\n",
    )
    update_extension(tmp_path, "square", "def square():\n    return 2\n")

    snippets = {item.name: item.source for item in list_extensions(tmp_path)}
    assert "return 2" in snippets["square"]
    assert "return 3" in snippets["stairs"]


def test_extension_rejects_program_code_at_module_level(tmp_path):
    with pytest.raises(ValueError, match="Beispielaufrufe"):
        add_extension(tmp_path, "def square():\n    pass\nsquare()\n")


def test_empty_module_contains_pykim_import(tmp_path):
    module = ensure_extension_module(tmp_path)

    assert module.name == "erweiterungen.py"
    assert "from pykim import *" in module.read_text(encoding="utf-8")
