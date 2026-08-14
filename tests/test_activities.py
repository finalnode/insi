import pytest

from pykim.trainer.activities import activity_from_data, annotated_code_blocks
from insi.activity_view import parsons_html
from insi.theme import configure_theme


def test_matching_activity_checks_complete_pairs():
    activity = activity_from_data({
        "id": "zuordnung",
        "title": "Begriffe zuordnen",
        "mode": "matching",
        "pairs": [
            {"id": "a", "left": "for", "right": "Zählschleife"},
            {"id": "b", "left": "if", "right": "Bedingung"},
        ],
    })

    assert activity is not None
    assert activity.matching_is_correct({"a": "Zählschleife", "b": "Bedingung"})
    assert not activity.matching_is_correct({"a": "Bedingung", "b": "Zählschleife"})


def test_parsons_activity_assembles_multiline_blocks():
    activity = activity_from_data({
        "id": "sortieren",
        "title": "Code sortieren",
        "mode": "parsons",
        "blocks": [
            {"id": "print", "code": "print(ergebnis)"},
            {"id": "value", "code": "ergebnis = 2 + 3"},
        ],
        "solution": ["value", "print"],
        "tests": [{"type": "calls", "names": ["print"]}],
    })

    assert activity is not None
    assert activity.assemble(["value", "print"]) == "ergebnis = 2 + 3\nprint(ergebnis)\n"
    assert activity.order_is_correct(["value", "print"])
    rendered = parsons_html(activity, ["print", "value"])
    assert "draggable" not in rendered
    assert 'class="pykim-parsons-block"' in rendered
    assert "onpointer" not in rendered
    assert "<script" not in rendered
    with pytest.raises(ValueError, match="unvollständig"):
        activity.assemble(["value"])


def test_parsons_solution_must_contain_every_block_once():
    with pytest.raises(ValueError, match="jeden Codeblock"):
        activity_from_data({
            "id": "kaputt",
            "title": "Kaputt",
            "mode": "parsons",
            "blocks": [
                {"id": "a", "code": "a = 1"},
                {"id": "b", "code": "b = 2"},
            ],
            "solution": ["a", "a"],
        })


def test_parsons_blocks_are_excluded_from_generic_code_actions():
    class ThemeRecorder:
        head = ""

        def colors(self, **_kwargs):
            pass

        def add_body_html(self, _html):
            pass

        def add_head_html(self, html):
            self.head = html

    recorder = ThemeRecorder()
    configure_theme(recorder)

    assert "pre.closest('.pykim-parsons-block, .pykim-no-code-actions')" in recorder.head
    assert "pykim-parsons-placeholder" in recorder.head


def test_parsons_blocks_can_be_annotated_in_assignment_markdown():
    markdown = """# Puzzle

Ordne den Code.

@block:first
```python
zahl = 2
```

@block:second
```python
print(zahl)
```
"""
    blocks = annotated_code_blocks(markdown)
    activity = activity_from_data(
        {"id": "puzzle", "title": "Puzzle", "mode": "parsons", "tests": []},
        assignment_markdown=markdown,
    )

    assert [block.id for block in blocks] == ["first", "second"]
    assert activity is not None
    assert activity.solution == ("first", "second")
    assert activity.assemble(activity.solution) == "zahl = 2\nprint(zahl)\n"


def test_parsons_steps_allow_equivalent_block_orders():
    markdown = """@block:import step=1
```python
from pykim import *
```
@block:position step=2
```python
set_position(20, 20)
```
@block:paint step=2
```python
paint("purple")
```
@block:run step=3
```python
run()
```
"""
    activity = activity_from_data(
        {"id": "puzzle", "title": "Puzzle", "mode": "parsons", "tests": []},
        assignment_markdown=markdown,
    )

    assert activity is not None
    assert activity.order_is_correct(["import", "position", "paint", "run"])
    assert activity.order_is_correct(["import", "paint", "position", "run"])
    assert not activity.order_is_correct(["paint", "import", "position", "run"])
