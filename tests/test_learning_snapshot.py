"""Wiederverwendung des Lernstands bei Erstaufbau und frische Ergebnisse danach."""

from unittest.mock import MagicMock

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
