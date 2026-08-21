"""Dateibasierte Kapitel und Aufgabenstellungen des Lernstudios."""

from dataclasses import dataclass
from pathlib import Path
import re


PACKAGED_CONTENT_ROOT = Path(__file__).resolve().parent
PARADIGMS = ("imperativ", "oop")
BUTTON_DIRECTIVES = ("run", "copy")
REPOSITORY_DOCUMENT_STEMS = frozenset({
    "aufgaben",
    "authors",
    "changelog",
    "code_of_conduct",
    "contributing",
    "license",
    "qualitaetssicherung",
    "readme",
    "security",
    "trainer_autoren",
})
_ANNOTATED_CODE = re.compile(
    r"(?P<directives>(?:^@button:(?:run|copy)[ \t]*\n)+)"
    r"(?P<fence>```python[ \t]*\n(?P<source>.*?)```)",
    flags=re.MULTILINE | re.DOTALL,
)
_ANNOTATED_TASK_BLOCK = re.compile(
    r"^@block:[a-z0-9]+(?:-[a-z0-9]+)*"
    r"(?:[ \t]+step=[1-9][0-9]*)?[ \t]*\n"
    r"```python[ \t]*\n.*?```[ \t]*(?:\n|$)",
    flags=re.MULTILINE | re.DOTALL,
)
_TASK_HINT = re.compile(
    r"^@hint:[ \t]*(?P<body>.+?)[ \t]*$",
    flags=re.MULTILINE,
)
_TASK_TAGS = re.compile(
    r"^@tags:[ \t]*(?P<body>.+?)[ \t]*$",
    flags=re.MULTILINE,
)


@dataclass(frozen=True)
class MarkdownDocument:
    name: str
    title: str
    paradigm: str
    content: str
    path: Path


@dataclass(frozen=True)
class TaskAssignment:
    summary: str
    requirements: tuple[str, ...]
    difficulty: str


@dataclass(frozen=True)
class TaskSource:
    label: str
    url: str = ""


def is_repository_document(path: str | Path) -> bool:
    """Erkenne übliche Projektmetadaten, die keine Lernkapitel sind."""
    return Path(path).stem.casefold() in REPOSITORY_DOCUMENT_STEMS


def _title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("_", " ").replace("-", " ").title()


def _documents(
    folder: str,
    paradigm: str,
    *,
    content_root: Path | None = None,
) -> tuple[MarkdownDocument, ...]:
    if paradigm not in PARADIGMS:
        raise ValueError(f"Unbekanntes Programmierparadigma: {paradigm}")
    from .updates import active_content_root

    root = content_root or active_content_root(PACKAGED_CONTENT_ROOT)
    directory = root / folder / paradigm
    documents = []
    for path in sorted(directory.rglob("*.md")):
        relative = path.relative_to(directory)
        if (
            any(part.startswith("_") for part in relative.parts)
            or is_repository_document(relative)
        ):
            continue
        content = path.read_text(encoding="utf-8")
        documents.append(
            MarkdownDocument(path.stem, _title(content, path.stem), paradigm, content, path)
        )
    return tuple(documents)


def script_chapters(paradigm: str) -> tuple[MarkdownDocument, ...]:
    """Liefere die Skriptkapitel eines Lernwegs in Dateireihenfolge."""
    return _documents("Skripte", paradigm)


def script_code_examples() -> frozenset[str]:
    """Liefere exakt die mit @button:run freigegebenen Python-Blöcke."""
    examples: set[str] = set()
    for paradigm in PARADIGMS:
        for chapter in script_chapters(paradigm):
            for match in _ANNOTATED_CODE.finditer(chapter.content):
                buttons = _directive_buttons(match.group("directives"))
                if "run" in buttons:
                    examples.add(match.group("source").rstrip())
    return frozenset(examples)


def _directive_buttons(directives: str) -> tuple[str, ...]:
    requested = {
        line.removeprefix("@button:").strip()
        for line in directives.splitlines()
    }
    return tuple(button for button in BUTTON_DIRECTIVES if button in requested)


def render_script_markdown(content: str) -> str:
    """Verberge Autorenanweisungen und markiere den unmittelbar folgenden Block."""
    def replace(match: re.Match[str]) -> str:
        buttons = ",".join(_directive_buttons(match.group("directives")))
        marker = (
            f'<div class="pykim-code-options" data-buttons="{buttons}" '
            'aria-hidden="true"></div>'
        )
        return f"{marker}\n\n{match.group('fence')}"

    return _ANNOTATED_CODE.sub(replace, content)


def task_documents(
    paradigm: str,
    *,
    content_root: Path | None = None,
    assignments_path: str = "Aufgaben",
) -> tuple[MarkdownDocument, ...]:
    """Liefere Aufgabenstellungen; der Dateiname ist die Trainerkennung."""
    return _documents(assignments_path, paradigm, content_root=content_root)


def task_document(
    name: str,
    *,
    content_root: Path | None = None,
    assignments_path: str = "Aufgaben",
) -> MarkdownDocument | None:
    for paradigm in PARADIGMS:
        for document in task_documents(
            paradigm,
            content_root=content_root,
            assignments_path=assignments_path,
        ):
            if document.name == name:
                return document
    return None


def task_assignment(
    name: str,
    *,
    content_root: Path | None = None,
    assignments_path: str = "Aufgaben",
) -> TaskAssignment:
    """Erzeuge strukturierte Aufgabendaten ausschließlich aus dem Markdown."""
    document = task_document(
        name,
        content_root=content_root,
        assignments_path=assignments_path,
    )
    if document is None:
        raise ValueError(f"Für {name!r} fehlt die Aufgabenstellung.")
    metadata_content = _TASK_TAGS.sub(
        "", _TASK_HINT.sub("", _ANNOTATED_TASK_BLOCK.sub("", document.content))
    )
    lines = metadata_content.splitlines()
    difficulty = next(
        (
            line.removeprefix("@difficulty:").strip()
            for line in lines
            if line.startswith("@difficulty:")
        ),
        "mittel",
    )
    body_lines = [
        line for line in lines
        if not line.startswith("@difficulty:")
        and not line.startswith("@source:")
        and not line.startswith("@tags:")
    ]
    summary = next(
        (
            line.strip()
            for line in body_lines
            if line.strip() and not line.startswith("#") and not line.startswith("-")
        ),
        document.title,
    )
    requirements = tuple(
        line.removeprefix("- ").strip()
        for line in body_lines
        if line.startswith("- ")
    )
    return TaskAssignment(summary, requirements, difficulty)


def render_task_markdown(content: str) -> str:
    """Blende Autorenmetadaten und die bereits angezeigte Überschrift aus."""
    content = _ANNOTATED_TASK_BLOCK.sub("", content)
    content = _TASK_HINT.sub("", content)
    lines = content.splitlines()
    heading_hidden = False
    visible = []
    for line in lines:
        if line.startswith("@difficulty:"):
            continue
        if line.startswith("@source:"):
            continue
        if line.startswith("@tags:"):
            continue
        if not heading_hidden and line.startswith("# "):
            heading_hidden = True
            continue
        visible.append(line)
    return "\n".join(visible).strip()


def task_hints(content: str) -> tuple[str, ...]:
    """Lese gestufte, in der Aufgabenansicht zunächst verborgene Hinweise."""
    return tuple(
        match.group("body").strip()
        for match in _TASK_HINT.finditer(content)
        if match.group("body").strip()
    )


def task_tags(content: str) -> tuple[str, ...]:
    """Lese eindeutige Aufgabentags aus ``@tags: a, b, c``."""
    tags: list[str] = []
    for match in _TASK_TAGS.finditer(content):
        for value in match.group("body").split(","):
            tag = value.strip()
            if tag and tag not in tags:
                tags.append(tag)
    return tuple(tags)


def task_sources(content: str) -> tuple[TaskSource, ...]:
    """Lese optionale Quellenangaben im Format ``Name | URL``."""
    sources = []
    for line in content.splitlines():
        if not line.startswith("@source:"):
            continue
        value = line.removeprefix("@source:").strip()
        label, separator, url = value.partition("|")
        label, url = label.strip(), url.strip()
        if label:
            sources.append(TaskSource(label, url if separator else ""))
    return tuple(sources)


def task_names() -> tuple[str, ...]:
    """Liefere automatisch und interaktiv prüfbare Aufgabenkennungen."""
    from insi.training.registry import trainable_names

    trainable = set(trainable_names())
    return tuple(
        document.name
        for paradigm in PARADIGMS
        for document in task_documents(paradigm)
        if document.name in trainable
    )
