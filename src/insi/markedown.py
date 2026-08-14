"""Parser und Validator für PyKIMs annotationsbasiertes M@rkdown."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


ANNOTATION = re.compile(r"^@(?P<name>[a-z]+):(?P<value>.*)$")
TAG = re.compile(r"^[a-z0-9äöüß]+(?:[-_][a-z0-9äöüß]+)*$")
BLOCK = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:[ \t]+step=[1-9][0-9]*)?$")
DIFFICULTIES = {"einfach", "mittel", "fortgeschritten"}


@dataclass(frozen=True)
class MarkedAnnotation:
    name: str
    value: str
    line: int


@dataclass(frozen=True)
class MarkedCodeBlock:
    language: str
    source: str
    line: int


@dataclass(frozen=True)
class MarkedIssue:
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class MarkedDocument:
    kind: str
    title: str
    annotations: tuple[MarkedAnnotation, ...]
    code_blocks: tuple[MarkedCodeBlock, ...]
    issues: tuple[MarkedIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def _next_nonempty(
    lines: list[str], index: int, *, skip_prefix: str = ""
) -> str:
    for line in lines[index + 1 :]:
        stripped = line.strip()
        if not stripped or (skip_prefix and stripped.startswith(skip_prefix)):
            continue
        return stripped
    return ""


def parse_markedown(content: str, *, kind: str) -> MarkedDocument:
    """Parse M@rkdown und liefere alle strukturellen Probleme mit Zeilenangabe."""
    if kind not in {"script", "task"}:
        raise ValueError("M@rkdown kennt nur script und task.")
    lines = content.splitlines()
    annotations: list[MarkedAnnotation] = []
    blocks: list[MarkedCodeBlock] = []
    issues: list[MarkedIssue] = []
    title = ""
    fence_line = 0
    fence_language = ""
    fence_source: list[str] = []

    for index, line in enumerate(lines):
        number = index + 1
        stripped = line.strip()
        if fence_line:
            if stripped == "```":
                blocks.append(
                    MarkedCodeBlock(
                        fence_language,
                        "\n".join(fence_source),
                        fence_line,
                    )
                )
                fence_line = 0
                fence_language = ""
                fence_source = []
            else:
                fence_source.append(line)
            continue
        if stripped.startswith("```"):
            fence_line = number
            fence_language = stripped.removeprefix("```").strip().casefold()
            if not fence_language:
                issues.append(
                    MarkedIssue(number, "code-language", "Der Codeblock benötigt eine Sprache.")
                )
            continue
        if not title and line.startswith("# "):
            title = line.removeprefix("# ").strip()
            if not title:
                issues.append(MarkedIssue(number, "empty-title", "Die Überschrift ist leer."))
            continue
        if not stripped.startswith("@"):
            continue
        match = ANNOTATION.fullmatch(stripped)
        if match is None:
            issues.append(
                MarkedIssue(number, "annotation-syntax", "Ungültige M@rkdown-Annotation.")
            )
            continue
        name, value = match.group("name"), match.group("value").strip()
        annotations.append(MarkedAnnotation(name, value, number))

    if fence_line:
        issues.append(
            MarkedIssue(fence_line, "unclosed-code", "Der Codeblock wird nicht mit ``` geschlossen.")
        )
    if not title:
        issues.append(MarkedIssue(1, "missing-title", "Es fehlt eine Überschrift mit '# '."))

    allowed = (
        {"button", "tags"}
        if kind == "script"
        else {"difficulty", "tags", "hint", "source", "block"}
    )
    seen_blocks: set[str] = set()
    for item in annotations:
        if item.name not in allowed:
            issues.append(
                MarkedIssue(
                    item.line,
                    "unknown-annotation",
                    f"@{item.name}: ist in diesem Dokumenttyp nicht erlaubt.",
                )
            )
            continue
        if not item.value:
            issues.append(
                MarkedIssue(item.line, "empty-annotation", f"@{item.name}: benötigt einen Wert.")
            )
            continue
        if item.name == "difficulty" and item.value not in DIFFICULTIES:
            issues.append(
                MarkedIssue(
                    item.line,
                    "difficulty",
                    "@difficulty: erlaubt einfach, mittel oder fortgeschritten.",
                )
            )
        elif item.name == "tags":
            tags = [tag.strip() for tag in item.value.split(",")]
            if any(not TAG.fullmatch(tag) for tag in tags):
                issues.append(
                    MarkedIssue(
                        item.line,
                        "tags",
                        "Tags müssen kommagetrennte Kleinbuchstaben-Begriffe sein.",
                    )
                )
            elif len(tags) != len(set(tags)):
                issues.append(MarkedIssue(item.line, "duplicate-tags", "Ein Tag ist doppelt."))
        elif item.name == "source":
            label, separator, url = item.value.partition("|")
            parsed = urlparse(url.strip()) if separator else None
            if not label.strip() or (
                parsed is not None and (parsed.scheme not in {"http", "https"} or not parsed.netloc)
            ):
                issues.append(
                    MarkedIssue(
                        item.line,
                        "source",
                        "Eine Quelle ist 'Name' oder 'Name | https://…'.",
                    )
                )
        elif item.name == "button":
            if item.value not in {"run", "copy"}:
                issues.append(
                    MarkedIssue(item.line, "button", "@button: erlaubt run oder copy.")
                )
            if _next_nonempty(
                lines, item.line - 1, skip_prefix="@button:"
            ) != "```python":
                issues.append(
                    MarkedIssue(
                        item.line,
                        "button-position",
                        "@button: muss direkt vor einem Python-Codeblock stehen.",
                    )
                )
        elif item.name == "block":
            if not BLOCK.fullmatch(item.value):
                issues.append(
                    MarkedIssue(
                        item.line,
                        "block",
                        "@block: benötigt eine kebab-case-Kennung und optional step=N.",
                    )
                )
            identifier = item.value.split()[0]
            if identifier in seen_blocks:
                issues.append(
                    MarkedIssue(item.line, "duplicate-block", "Die Blockkennung ist doppelt.")
                )
            seen_blocks.add(identifier)
            if _next_nonempty(lines, item.line - 1) != "```python":
                issues.append(
                    MarkedIssue(
                        item.line,
                        "block-position",
                        "@block: muss direkt vor einem Python-Codeblock stehen.",
                    )
                )

    if kind == "task":
        difficulties = [item for item in annotations if item.name == "difficulty"]
        if not difficulties:
            issues.append(
                MarkedIssue(1, "missing-difficulty", "Aufgaben benötigen @difficulty:.")
            )
        elif len(difficulties) > 1:
            issues.append(
                MarkedIssue(difficulties[1].line, "duplicate-difficulty", "@difficulty: ist doppelt.")
            )

    return MarkedDocument(
        kind,
        title,
        tuple(annotations),
        tuple(blocks),
        tuple(issues),
    )


def validate_markedown(content: str, *, kind: str) -> tuple[MarkedIssue, ...]:
    return parse_markedown(content, kind=kind).issues


__all__ = [
    "MarkedAnnotation",
    "MarkedCodeBlock",
    "MarkedDocument",
    "MarkedIssue",
    "parse_markedown",
    "validate_markedown",
]
