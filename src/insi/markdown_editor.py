"""Offline gebündelter Markdown-/WYSIWYG-Editor für Kurse und Projekte."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from nicegui.elements.mixins.disableable_element import DisableableElement
from nicegui.elements.mixins.value_element import ValueElement
from nicegui.events import GenericEventArguments, Handler, ValueChangeEventArguments

from .markedown import MarkedIssue, validate_markedown


CourseMarkdownKind = Literal["script", "task-body"]

_ANNOTATIONS = {
    "run": ("Ausführen", "@button:run\n", ("script",)),
    "copy": ("Kopieren", "@button:copy\n", ("script",)),
    "tags": ("Tags", "@tags: thema, kompetenz\n", ("script",)),
    "hint": (
        "Hinweis",
        "@hint: Formuliere hier einen gestuften Hinweis.\n",
        (),
    ),
    "source": (
        "Quelle",
        "@source: Quellenname | https://example.org\n",
        (),
    ),
    "block": (
        "Parsons-Block",
        "@block:block-id step=1\n```python\n# Codeblock\n```\n",
        ("task-body",),
    ),
}


def validate_editor_markdown(
    markdown: str,
    *,
    course_kind: CourseMarkdownKind,
) -> tuple[MarkedIssue, ...]:
    """Validiere genau den im Editor sichtbaren Kursinhalt mit lokalen Zeilen."""
    if course_kind == "script":
        return validate_markedown(markdown, kind="script")
    if course_kind != "task-body":
        raise ValueError("Unbekannter Kursdokumenttyp für den Markdowneditor.")
    prefix = "# Aufgabe\n@difficulty:mittel\n\n"
    offset = prefix.count("\n")
    return tuple(
        MarkedIssue(issue.line - offset, issue.code, issue.message)
        for issue in validate_markedown(prefix + markdown, kind="task")
        if issue.line > offset
    )


class MarkdownEditor(
    ValueElement[str],
    DisableableElement,
    component="markdown_editor.js",
    dependencies=[
        "vendor/toastui_editor/toastui-editor-all.min.js",
        "vendor/toastui_editor/de-de.min.js",
    ],
    default_classes="insi-markdown-editor w-full",
):
    """TOAST UI mit Markdown als einzigem kanonischen Speicherformat."""

    VALUE_PROP = "value"
    LOOPBACK = False

    def __init__(
        self,
        value: str = "",
        *,
        on_change: Handler[ValueChangeEventArguments[str]] | None = None,
        height: str = "34rem",
        initial_mode: str = "wysiwyg",
        course_kind: CourseMarkdownKind | None = None,
    ) -> None:
        if initial_mode not in {"markdown", "wysiwyg"}:
            raise ValueError("Der Editormodus muss markdown oder wysiwyg sein.")
        super().__init__(value=value, on_value_change=on_change)
        self.add_resource(Path(__file__).parent / "vendor" / "toastui_editor")
        self._props["height"] = height
        self._props["initial-mode"] = initial_mode
        self._props["course-kind"] = course_kind
        self._props["annotation-items"] = [
            {"name": name, "label": label, "text": text}
            for name, (label, text, kinds) in _ANNOTATIONS.items()
            if course_kind in kinds
        ]
        self._update_method = "updateValue"
        self._course_kind = course_kind
        if course_kind is not None:
            self.on("validation", self._handle_validation)

    def _handle_value_change(self, value: Any) -> None:
        super()._handle_value_change(value)
        if self._send_update_on_value_change:
            self.run_method("updateValue")

    def insert_text(self, text: str, *, markdown_mode: bool = False) -> None:
        """Füge Text an der Auswahl ein; Annotationen erzwingen Markdownmodus."""
        self.run_method("insertText", text, markdown_mode)

    def set_mode(self, mode: str) -> None:
        if mode not in {"markdown", "wysiwyg"}:
            raise ValueError("Der Editormodus muss markdown oder wysiwyg sein.")
        self.run_method("setMode", mode)

    def _handle_validation(self, event: GenericEventArguments) -> None:
        payload = event.args
        if isinstance(payload, list) and len(payload) == 1:
            payload = payload[0]
        if not isinstance(payload, dict) or self._course_kind is None:
            return
        markdown = payload.get("markdown", "")
        request_id = payload.get("request_id", 0)
        if not isinstance(markdown, str) or not isinstance(request_id, int):
            return
        issues = validate_editor_markdown(markdown, course_kind=self._course_kind)
        self.run_method(
            "setValidation",
            {
                "request_id": request_id,
                "issues": [
                    {"line": issue.line, "code": issue.code, "message": issue.message}
                    for issue in issues
                ],
            },
        )


def insert_course_annotation(editor: MarkdownEditor, annotation: str) -> None:
    """Füge eine bekannte in:si-Annotation ohne frei ausführbaren Code ein."""
    try:
        text = _ANNOTATIONS[annotation][1]
    except KeyError:
        raise ValueError(f"Unbekannte Kursannotation: {annotation}") from None
    editor.insert_text(text, markdown_mode=True)


__all__ = [
    "CourseMarkdownKind",
    "MarkdownEditor",
    "insert_course_annotation",
    "validate_editor_markdown",
]
