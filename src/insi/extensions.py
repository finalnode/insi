"""Eine persönliche, wiederverwendbare Python-Werkzeugkiste je Kurs."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


MODULE_NAME = "erweiterungen"
HEADER = '''"""Meine mit PyKIM erstellte Werkzeugkiste."""

from pykim import *
'''


@dataclass(frozen=True)
class ExtensionSnippet:
    name: str
    path: Path
    source: str
    kind: str

    @property
    def import_line(self) -> str:
        return f"from {MODULE_NAME} import {self.name}"


def extension_file(course: str | Path) -> Path:
    return Path(course).expanduser().resolve() / f"{MODULE_NAME}.py"


def ensure_extension_module(course: str | Path) -> Path:
    root = Path(course).expanduser().resolve()
    target = extension_file(root)
    if not target.exists():
        legacy = root / MODULE_NAME
        migrated: list[str] = []
        if legacy.is_dir():
            for path in sorted(legacy.glob("*.py")):
                if path.name != "__init__.py":
                    migrated.append(path.read_text(encoding="utf-8").strip())
            backup = root / f"{MODULE_NAME}_altes_paket"
            if backup.exists():
                raise FileExistsError(
                    "Die alte Erweiterungsstruktur konnte nicht gesichert werden: "
                    f"{backup.name} existiert bereits."
                )
            legacy.rename(backup)
        source = HEADER.rstrip()
        if migrated:
            source += "\n\n\n" + "\n\n\n".join(migrated)
        target.write_text(source + "\n", encoding="utf-8")
    return target


def _tree(source: str) -> ast.Module:
    try:
        return ast.parse(source)
    except SyntaxError as error:
        where = f" in Zeile {error.lineno}" if error.lineno else ""
        raise ValueError(f"Der Code enthält einen Syntaxfehler{where}: {error.msg}") from error


def _definitions(source: str) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, ...]:
    tree = _tree(source)
    definitions = tuple(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not node.name.startswith("_")
    )
    return definitions


def _new_definitions(source: str) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef, ...]:
    tree = _tree(source)
    definitions = []
    for index, node in enumerate(tree.body):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                raise ValueError("Funktions- und Klassennamen dürfen nicht mit _ beginnen.")
            definitions.append(node)
        elif (
            index == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        else:
            raise ValueError(
                "Füge hier nur Funktions- oder Klassendefinitionen ein. "
                "Importe und Beispielaufrufe gehören nicht in das Snippet."
            )
    if not definitions:
        raise ValueError("Definiere mindestens eine Funktion oder Klasse.")
    names = [node.name for node in definitions]
    if len(names) != len(set(names)):
        raise ValueError("Das Snippet enthält einen Namen mehrfach.")
    return tuple(definitions)


def list_extensions(course: str | Path) -> tuple[ExtensionSnippet, ...]:
    path = ensure_extension_module(course)
    source = path.read_text(encoding="utf-8")
    snippets = []
    for node in _definitions(source):
        segment = ast.get_source_segment(source, node) or ""
        kind = "Klasse" if isinstance(node, ast.ClassDef) else "Funktion"
        snippets.append(ExtensionSnippet(node.name, path, segment.rstrip() + "\n", kind))
    return tuple(snippets)


def add_extension(course: str | Path, source: str) -> tuple[ExtensionSnippet, ...]:
    """Füge neue Definitionen hinzu, sofern deren Namen noch frei sind."""
    nodes = _new_definitions(source)
    existing = {snippet.name for snippet in list_extensions(course)}
    duplicates = sorted(existing & {node.name for node in nodes})
    if duplicates:
        raise ValueError(
            "Diese Funktion oder Klasse gibt es bereits: " + ", ".join(duplicates)
        )
    target = ensure_extension_module(course)
    current = target.read_text(encoding="utf-8").rstrip()
    target.write_text(current + "\n\n\n" + source.strip() + "\n", encoding="utf-8")
    created = {node.name for node in nodes}
    return tuple(item for item in list_extensions(course) if item.name in created)


def update_extension(course: str | Path, name: str, source: str) -> ExtensionSnippet:
    """Ersetze genau eine vorhandene Definition ohne andere Werkzeuge anzutasten."""
    nodes = _new_definitions(source)
    if len(nodes) != 1 or nodes[0].name != name:
        raise ValueError(f"Beim Bearbeiten muss genau {name!r} definiert werden.")
    target = ensure_extension_module(course)
    current = target.read_text(encoding="utf-8")
    old = next((node for node in _definitions(current) if node.name == name), None)
    if old is None or old.end_lineno is None:
        raise ValueError(f"Die Erweiterung {name!r} wurde nicht gefunden.")
    lines = current.splitlines(keepends=True)
    replacement = source.strip() + "\n"
    updated = "".join(lines[: old.lineno - 1]) + replacement + "".join(lines[old.end_lineno :])
    target.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return next(item for item in list_extensions(course) if item.name == name)


__all__ = [
    "ExtensionSnippet", "MODULE_NAME", "add_extension", "ensure_extension_module",
    "extension_file", "list_extensions", "update_extension",
]
