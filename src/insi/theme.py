"""OSZ-KIM-Theme und Browserverhalten des lokalen Lernstudios."""

from functools import lru_cache
from pathlib import Path


_ASSET_DIR = Path(__file__).with_name("assets")
_HEAD_SCRIPTS = (
    "theme_playground.js",
    "theme_code_actions.js",
    "theme_unsaved_changes.js",
)


@lru_cache(maxsize=None)
def _asset_text(name: str) -> str:
    return (_ASSET_DIR / name).read_text(encoding="utf-8")


def _script(name: str) -> str:
    return f"<script>\n{_asset_text(name)}</script>"


def configure_theme(ui) -> None:
    ui.colors(primary="#f36b2b", secondary="#9b9da0", accent="#5f6164")
    ui.add_body_html(_script("theme_parsons.js"))
    ui.add_head_html(
        f"<style>\n{_asset_text('theme.css')}</style>\n"
        + "\n".join(_script(name) for name in _HEAD_SCRIPTS)
    )


__all__ = ["configure_theme"]
