"""UI-Bausteine für Zuordnungsaufgaben und ausführbare Parsons-Puzzles."""

from __future__ import annotations

import html
import json
import re

from insi.training.activities import Activity
from pykim.trainer.models import CheckReport, CheckResult

from .progress import load_progress, record_attempt, save_task_answer


def saved_activity_value(key: str) -> object:
    answers = load_progress().get("answers", {})
    item = answers.get(key, {}) if isinstance(answers, dict) else {}
    text = item.get("text", "") if isinstance(item, dict) else ""
    try:
        return json.loads(text) if isinstance(text, str) and text else None
    except ValueError:
        return None


def render_matching_activity(ui, activity: Activity, *, paradigm: str) -> None:
    key = f"{paradigm}/{activity.name}"
    saved = saved_activity_value(key)
    previous = saved if isinstance(saved, dict) else {}
    choices = [pair.right for pair in reversed(activity.pairs)]
    fields = {}
    with ui.column().classes("w-full gap-3"):
        for pair in activity.pairs:
            with ui.row().classes("w-full items-center gap-3"):
                ui.label(pair.left).classes("grow font-medium")
                fields[pair.id] = ui.select(
                    choices,
                    value=previous.get(pair.id),
                    label="Zuordnung",
                ).props("outlined dense").classes("w-96 max-w-full")

        def check() -> None:
            answers = {name: field.value for name, field in fields.items()}
            successful = activity.matching_is_correct(answers)
            save_task_answer(key, json.dumps(answers, ensure_ascii=False))
            report = CheckReport(
                activity.title,
                (CheckResult(
                    successful,
                    "Alle Zuordnungen stimmen.",
                    "Mindestens eine Zuordnung stimmt noch nicht.",
                    "Vergleiche Begriffe, Code und Wirkung noch einmal.",
                ),),
            )
            record_attempt(activity.name, report, json.dumps(answers, ensure_ascii=False))
            ui.notify(
                "Alle Zuordnungen sind richtig." if successful else "Noch nicht ganz richtig.",
                type="positive" if successful else "warning",
            )

        ui.button("Zuordnung prüfen", on_click=check, icon="rule").props("color=primary")


def parsons_root_id(name: str) -> str:
    return "pykim-parsons-" + re.sub(r"[^a-zA-Z0-9_-]", "-", name)


def parsons_html(activity: Activity, order: list[str] | tuple[str, ...]) -> str:
    blocks = {block.id: block for block in activity.blocks}
    root = parsons_root_id(activity.name)
    cards = []
    for identifier in order:
        block = blocks[identifier]
        cards.append(
            f'<div class="pykim-parsons-block" data-block-id="{html.escape(identifier)}">'
            f'<pre>{html.escape(block.code)}</pre>'
            '<div class="pykim-parsons-controls">'
            '<button type="button" onclick="window.pykimMoveParsons(this,-1)" aria-label="Nach oben">↑</button>'
            '<button type="button" onclick="window.pykimMoveParsons(this,1)" aria-label="Nach unten">↓</button>'
            '</div></div>'
        )
    return f'<div id="{root}" class="pykim-parsons-list">{"".join(cards)}</div>'


async def current_parsons_order(ui, activity: Activity) -> list[str]:
    root = parsons_root_id(activity.name)
    result = await ui.run_javascript(
        f'return [...document.querySelectorAll("#{root} > [data-block-id]")].map(x=>x.dataset.blockId)',
        timeout=5.0,
    )
    return list(result) if isinstance(result, list) else []


__all__ = ["current_parsons_order", "parsons_html", "render_matching_activity", "saved_activity_value"]
