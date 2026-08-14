"""Tests für HTTPS-Zugriffe der Desktop-App."""

from insi import network


def test_urlopen_uses_certifi_certificate_bundle(monkeypatch):
    calls = []

    class Context:
        def load_verify_locations(self, *, cafile):
            calls.append(("certificates", cafile))

    context = Context()

    monkeypatch.setattr(network.certifi, "where", lambda: "/bundle/cacert.pem")
    monkeypatch.setattr(
        network.ssl,
        "create_default_context",
        lambda: calls.append(("system-context",)) or context,
    )
    monkeypatch.setattr(
        network,
        "_stdlib_urlopen",
        lambda request, *, timeout, context: calls.append(
            ("urlopen", request, timeout, context)
        ) or "response",
    )

    assert network.urlopen("https://example.test", 4.5) == "response"
    assert calls == [
        ("system-context",),
        ("certificates", "/bundle/cacert.pem"),
        ("urlopen", "https://example.test", 4.5, context),
    ]
