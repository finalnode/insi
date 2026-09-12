"""Wiederverwendung des Lernstands bei Erstaufbau und frische Ergebnisse danach."""

from unittest.mock import MagicMock
from types import SimpleNamespace

from insi import learning_view


def test_test_results_use_index_without_reading_or_rescanning(monkeypatch):
    def unexpected(*args):
        raise AssertionError("Der vorhandene Index muss verwendet werden.")

    monkeypatch.setattr(learning_view, "load_progress", unexpected)
    monkeypatch.setattr(learning_view, "latest_attempts", unexpected)
    ui = MagicMock()
    latest = {"task": {"tests": [], "passed": 1, "total": 2}}
    learning_view.render_test_results(ui, "task", latest=latest)
    ui.badge.assert_called_with("1 / 2 bestanden", color="negative")
    learning_view.render_test_results(ui, "task", latest={})


def test_refresh_without_index_loads_new_result_each_time(monkeypatch):
    progress = {"attempts": [{"exercise": "task", "tests": [], "passed": 0, "total": 1}]}
    monkeypatch.setattr(learning_view, "load_progress", lambda course=None: progress)
    ui = MagicMock()
    learning_view.render_test_results(ui, "task")
    ui.badge.assert_called_with("0 / 1 bestanden", color="negative")
    progress["attempts"].append({"exercise": "task", "tests": [], "passed": 1, "total": 1})
    learning_view.render_test_results(ui, "task")
    ui.badge.assert_called_with("1 / 1 bestanden", color="positive")


def test_overview_only_collects_task_names_once(monkeypatch):
    names = MagicMock(return_value=())
    monkeypatch.setattr(learning_view, "task_names", names)
    monkeypatch.setattr(learning_view, "load_progress", lambda: {})
    learning_view.render_overview(MagicMock())
    names.assert_called_once_with()


def test_overview_adds_cards_in_batches_from_the_original_snapshot(monkeypatch):
    names = tuple(f"task-{index}" for index in range(49))
    monkeypatch.setattr(learning_view, "task_names", lambda: names)
    monkeypatch.setattr(learning_view, "load_progress", lambda: {})
    monkeypatch.setattr(learning_view, "get_activity", lambda _: None)
    monkeypatch.setattr(learning_view, "get_exercise", lambda name: SimpleNamespace(title=name))
    ui = MagicMock()
    learning_view.render_overview(ui)
    assert ui.card.call_count == 24
    ui.label.assert_any_call("0 von 49 Aufgaben vollständig gelöst")
    more = ui.button.call_args.kwargs["on_click"]

    def changed_course(*args):
        raise AssertionError("Nachladen darf nicht auf den neuen Kurs zugreifen")

    for attribute in ("load_progress", "get_activity", "get_exercise", "task_names"):
        monkeypatch.setattr(learning_view, attribute, changed_course)
    more()
    assert ui.card.call_count == 48
    more()
    assert ui.card.call_count == 49
    ui.button.return_value.props.return_value.set_visibility.assert_called_with(False)
    more()
    assert ui.card.call_count == 49
