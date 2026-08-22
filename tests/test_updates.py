"""Gezielte Verträge für den manuellen App- und Inhaltsabgleich."""

import threading

from insi.updates import AppUpdate, ContentUpdate, check_updates


def test_combined_update_check_runs_independent_requests_in_parallel(
    tmp_path, monkeypatch
):
    barrier = threading.Barrier(2, timeout=2)

    def app_update(_timeout):
        barrier.wait()
        return AppUpdate("0.7.0", "0.7.0", False, "", "")

    def content_update(_packaged_root, _timeout):
        barrier.wait()
        return ContentUpdate("1", "1", False, True, {})

    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr("insi.updates.check_app_update", app_update)
    monkeypatch.setattr("insi.updates.check_content_update", content_update)

    status = check_updates(tmp_path)

    assert status.app is not None
    assert status.content is not None
    assert status.error == ""


def test_course_update_check_skips_unrelated_packaged_content_request(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setattr(
        "insi.updates.check_app_update",
        lambda _timeout: AppUpdate("0.7.0", "0.7.0", False, "", ""),
    )
    monkeypatch.setattr(
        "insi.updates.check_content_update",
        lambda *_args: calls.append("content"),
    )

    status = check_updates(tmp_path, include_content=False)

    assert status.app is not None
    assert status.content is None
    assert calls == []
