"""Sicherer Arbeitsbereich für gemeinsam versionierte Trainer- und Markdownentwürfe."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from insi.training.registry import get_exercise
from pykim.trainer.definitions import exercise_from_data
from insi.training.pykim_backend import normalize_pykim_document

from .library import task_document
from .markedown import validate_markedown


@dataclass(frozen=True)
class AuthorDraft:
    name: str
    trainer_source: str
    assignment_markdown: str

    @property
    def content_hash(self) -> str:
        payload = self.trainer_source.rstrip() + "\n---\n" + self.assignment_markdown.rstrip()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TaskMarkdownParts:
    """Visuell bearbeitbarer Aufgabentext plus strukturierte Annotationen."""

    title: str
    body: str
    difficulty: str = "mittel"
    hints: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()


def split_task_markdown(content: str) -> TaskMarkdownParts:
    """Trenne in:si-Metadaten vom eigentlichen Markdownkörper."""
    title = "Aufgabe"
    difficulty = "mittel"
    hints: list[str] = []
    tags: list[str] = []
    sources: list[str] = []
    body: list[str] = []
    heading_seen = False
    for line in content.splitlines():
        if not heading_seen and line.startswith("# "):
            title = line[2:].strip() or title
            heading_seen = True
        elif line.startswith("@difficulty:"):
            difficulty = line.removeprefix("@difficulty:").strip() or "mittel"
        elif line.startswith("@hint:"):
            value = line.removeprefix("@hint:").strip()
            if value:
                hints.append(value)
        elif line.startswith("@tags:"):
            tags.extend(
                value.strip() for value in line.removeprefix("@tags:").split(",")
                if value.strip()
            )
        elif line.startswith("@source:"):
            value = line.removeprefix("@source:").strip()
            if value:
                sources.append(value)
        else:
            body.append(line)
    return TaskMarkdownParts(
        title,
        "\n".join(body).strip(),
        difficulty,
        tuple(dict.fromkeys(hints)),
        tuple(dict.fromkeys(tags)),
        tuple(dict.fromkeys(sources)),
    )


def compose_task_markdown(parts: TaskMarkdownParts) -> str:
    """Erzeuge kanonisches Aufgaben-Markdown aus visuellen Formularfeldern."""
    metadata = [f"@difficulty:{parts.difficulty.strip() or 'mittel'}"]
    clean_tags = tuple(dict.fromkeys(tag.strip() for tag in parts.tags if tag.strip()))
    if clean_tags:
        metadata.append("@tags: " + ", ".join(clean_tags))
    metadata.extend(f"@hint: {hint.strip()}" for hint in parts.hints if hint.strip())
    metadata.extend(f"@source: {source.strip()}" for source in parts.sources if source.strip())
    return "\n".join(
        [f"# {parts.title.strip() or 'Aufgabe'}", *metadata, "", parts.body.strip(), ""]
    )


def assignment_markdown(
    title: str,
    summary: str,
    requirements: str,
    difficulty: str,
    *,
    hints: tuple[str, ...] | list[str] = (),
    tags: tuple[str, ...] | list[str] = (),
) -> str:
    bullets = [line.strip().removeprefix("- ") for line in requirements.splitlines() if line.strip()]
    if not bullets:
        bullets = ["Beschreibe hier das überprüfbare Ziel."]
    metadata = [f"@difficulty:{difficulty}"]
    clean_tags = tuple(
        dict.fromkeys(
            tag.strip().casefold().replace(" ", "-") for tag in tags if tag.strip()
        )
    )
    if clean_tags:
        metadata.append("@tags: " + ", ".join(clean_tags))
    metadata.extend(f"@hint: {hint.strip()}" for hint in hints if hint.strip())
    return "\n".join(
        [
            f"# {title.strip()}",
            *metadata,
            "",
            summary.strip(),
            "",
            "## Anforderungen",
            "",
            *(f"- {item}" for item in bullets),
            "",
        ]
    )


def validate_author_draft(draft: AuthorDraft) -> tuple[str, ...]:
    issues: list[str] = []
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", draft.name):
        issues.append("Die Kennung muss ein kebab-case-Name sein.")
    try:
        payload = yaml.safe_load(draft.trainer_source)
        payload = normalize_pykim_document(payload, source_name="Trainer-YAML")
        definitions = payload.get("exercises")
        if not isinstance(definitions, list) or len(definitions) != 1:
            raise ValueError("Ein Entwurf benötigt genau eine PyKIM-Aufgabe.")
        exercise = exercise_from_data(definitions[0])
        if exercise.name != draft.name:
            issues.append("Die YAML-Kennung stimmt nicht mit dem Entwurfsnamen überein.")
    except (AttributeError, TypeError, ValueError, yaml.YAMLError) as error:
        issues.append(f"Trainer-YAML ist ungültig: {error}")
    lines = draft.assignment_markdown.splitlines()
    if not any(line.startswith("# ") for line in lines):
        issues.append("Im Markdown fehlt die Überschrift der Aufgabe.")
    if not any(line.startswith("@difficulty:") for line in lines):
        issues.append("Im Markdown fehlt @difficulty:.")
    if not any(line.startswith("- ") for line in lines):
        issues.append("Im Markdown fehlt mindestens eine überprüfbare Anforderung.")
    issues.extend(
        f"M@rkdown Zeile {issue.line}: {issue.message}"
        for issue in validate_markedown(draft.assignment_markdown, kind="task")
    )
    return tuple(issues)


def load_published_draft(name: str) -> AuthorDraft:
    get_exercise(name)  # verständliche Fehlermeldung für unbekannte Kennungen
    from .library import PACKAGED_CONTENT_ROOT
    from .updates import active_content_root

    source_path = active_content_root(PACKAGED_CONTENT_ROOT) / "Trainer" / "definitions.yml"
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    definition = next(
        (item for item in payload["exercises"] if item.get("id") == name), None
    )
    if definition is None:
        raise ValueError(f"Die Trainingsdefinition für {name!r} wurde nicht gefunden.")
    document = task_document(name)
    if document is None:
        raise ValueError(f"Für {name!r} fehlt das Aufgaben-Markdown.")
    return AuthorDraft(
        name,
        yaml.safe_dump(
            {"format": 1, "exercises": [definition]},
            allow_unicode=True,
            sort_keys=False,
        ),
        document.content,
    )


def save_author_draft(
    course: str | Path,
    draft: AuthorDraft,
    *,
    paradigm: str,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    issues = validate_author_draft(draft)
    if issues:
        raise ValueError(" ".join(issues))
    if paradigm not in {"imperativ", "oop"}:
        raise ValueError("Der Lernweg muss imperativ oder oop sein.")
    root = Path(course).expanduser().resolve() / ".pykim" / "author_drafts"
    trainer_path = root / "trainer" / f"{draft.name}.yml"
    markdown_path = root / "Aufgaben" / paradigm / f"{draft.name}.md"
    if not overwrite and (trainer_path.exists() or markdown_path.exists()):
        raise FileExistsError(
            "Der Entwurf existiert bereits. Aktiviere Überschreiben nur bewusst."
        )
    trainer_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    trainer_path.write_text(draft.trainer_source.rstrip() + "\n", encoding="utf-8")
    markdown_path.write_text(draft.assignment_markdown.rstrip() + "\n", encoding="utf-8")
    return trainer_path, markdown_path


__all__ = [
    "AuthorDraft", "TaskMarkdownParts", "assignment_markdown",
    "compose_task_markdown", "load_published_draft", "save_author_draft",
    "split_task_markdown", "validate_author_draft",
]
