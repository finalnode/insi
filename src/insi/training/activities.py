"""Deklarative Aktivitäten wie Zuordnungen und Parsons-Puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import yaml

@dataclass(frozen=True)
class MatchingPair:
    id: str
    left: str
    right: str


@dataclass(frozen=True)
class CodeBlock:
    id: str
    code: str
    step: int | None = None


@dataclass(frozen=True)
class Activity:
    name: str
    title: str
    mode: str
    pairs: tuple[MatchingPair, ...] = ()
    blocks: tuple[CodeBlock, ...] = ()
    solution: tuple[str, ...] = ()

    def assemble(self, order: list[str] | tuple[str, ...]) -> str:
        blocks = {block.id: block.code for block in self.blocks}
        if set(order) != set(blocks) or len(order) != len(blocks):
            raise ValueError("Die Blockreihenfolge ist unvollständig oder enthält Duplikate.")
        return "\n".join(blocks[item].rstrip("\n") for item in order) + "\n"

    def order_is_correct(self, order: list[str] | tuple[str, ...]) -> bool:
        identifiers = {block.id for block in self.blocks}
        if len(order) != len(identifiers) or set(order) != identifiers:
            return False
        steps = {block.id: block.step for block in self.blocks}
        if steps and all(step is not None for step in steps.values()):
            selected_steps = [steps[identifier] for identifier in order]
            return selected_steps == sorted(selected_steps)
        return tuple(order) == self.solution

    def matching_is_correct(self, answers: dict[str, str]) -> bool:
        return answers == {pair.id: pair.right for pair in self.pairs}


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} muss nichtleerer Text sein.")
    return value


def _step(value: object, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} muss eine positive ganze Zahl sein.")
    return value


def _validate_block_steps(blocks: tuple[CodeBlock, ...]) -> None:
    if blocks and any(block.step is not None for block in blocks) and any(
        block.step is None for block in blocks
    ):
        raise ValueError("Bei Reihenfolgestufen benötigt jeder Block eine step-Angabe.")


_ANNOTATED_BLOCK = re.compile(
    r"^@block:(?P<id>[a-z0-9]+(?:-[a-z0-9]+)*)"
    r"(?:[ \t]+step=(?P<step>[1-9][0-9]*))?[ \t]*\n"
    r"```python[ \t]*\n(?P<code>.*?)```",
    flags=re.MULTILINE | re.DOTALL,
)


def annotated_code_blocks(markdown: str) -> tuple[CodeBlock, ...]:
    """Lese Parsons-Blöcke in Lösungsreihenfolge aus Markdown-Annotationen."""
    blocks = tuple(
        CodeBlock(
            match.group("id"),
            match.group("code").rstrip(),
            int(match.group("step")) if match.group("step") else None,
        )
        for match in _ANNOTATED_BLOCK.finditer(markdown)
    )
    if blocks and len({block.id for block in blocks}) != len(blocks):
        raise ValueError("@block-Kennungen müssen eindeutig sein.")
    _validate_block_steps(blocks)
    return blocks


def activity_from_data(
    data: dict,
    *,
    assignment_markdown: str | None = None,
) -> Activity | None:
    mode = data.get("mode")
    if mode not in {"matching", "parsons"}:
        return None
    name = _text(data.get("id"), "id")
    title = _text(data.get("title"), "title")
    if mode == "matching":
        unknown = set(data) - {"id", "title", "mode", "pairs"}
        raw_pairs = data.get("pairs")
        if unknown or not isinstance(raw_pairs, list) or len(raw_pairs) < 2:
            raise ValueError("Eine Zuordnungsaufgabe benötigt mindestens zwei gültige Paare.")
        pairs = tuple(
            MatchingPair(
                _text(pair.get("id"), "pair.id"),
                _text(pair.get("left"), "pair.left"),
                _text(pair.get("right"), "pair.right"),
            )
            for pair in raw_pairs if isinstance(pair, dict)
        )
        if len(pairs) != len(raw_pairs) or len({pair.id for pair in pairs}) != len(pairs):
            raise ValueError("Zuordnungspaare benötigen eindeutige Kennungen.")
        return Activity(name, title, mode, pairs=pairs)

    unknown = set(data) - {
        "id", "title", "mode", "blocks", "solution", "tests", "optimization"
    }
    raw_blocks, solution = data.get("blocks"), data.get("solution")
    if raw_blocks is None and assignment_markdown is not None:
        blocks = annotated_code_blocks(assignment_markdown)
        if unknown or len(blocks) < 2:
            raise ValueError("Ein Parsons-Puzzle benötigt mindestens zwei @block-Annotationen.")
        return Activity(
            name,
            title,
            mode,
            blocks=blocks,
            solution=tuple(block.id for block in blocks),
        )
    if unknown or not isinstance(raw_blocks, list) or len(raw_blocks) < 2:
        raise ValueError("Ein Parsons-Puzzle benötigt mindestens zwei Codeblöcke.")
    blocks = tuple(
        CodeBlock(
            _text(block.get("id"), "block.id"),
            _text(block.get("code"), "block.code"),
            _step(block.get("step"), "block.step"),
        )
        for block in raw_blocks if isinstance(block, dict)
    )
    ids = {block.id for block in blocks}
    if len(blocks) != len(raw_blocks) or len(ids) != len(blocks):
        raise ValueError("Codeblöcke benötigen eindeutige Kennungen.")
    _validate_block_steps(blocks)
    if not isinstance(solution, list) or set(solution) != ids or len(solution) != len(ids):
        raise ValueError("solution muss jeden Codeblock genau einmal enthalten.")
    return Activity(name, title, mode, blocks=blocks, solution=tuple(solution))


def load_activities(
    path: str | Path,
    assignments_path: str | Path | None = None,
) -> dict[str, Activity]:
    result = {}
    assignments = Path(assignments_path) if assignments_path is not None else None
    for source in sorted(Path(path).glob("*.yml")):
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("format") != 1:
            continue
        definition = {key: value for key, value in data.items() if key != "format"}
        markdown = None
        if definition.get("mode") == "parsons" and assignments is not None:
            matches = [item for item in assignments.rglob(f"{definition.get('id')}.md")]
            if len(matches) != 1:
                raise ValueError(
                    f"Für das Parsons-Puzzle {definition.get('id')!r} fehlt eindeutiges Markdown."
                )
            markdown = matches[0].read_text(encoding="utf-8")
        activity = activity_from_data(definition, assignment_markdown=markdown)
        if activity is not None:
            if activity.name in result:
                raise ValueError(f"Die Aktivitätskennung {activity.name!r} ist doppelt.")
            result[activity.name] = activity
    return result


__all__ = [
    "Activity",
    "CodeBlock",
    "MatchingPair",
    "activity_from_data",
    "annotated_code_blocks",
    "load_activities",
]
