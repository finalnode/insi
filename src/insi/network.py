"""HTTPS-Zugriffe mit einem auch in Desktop-Builds verfügbaren CA-Bündel."""

from __future__ import annotations

import ssl
from urllib.request import urlopen as _stdlib_urlopen

import certifi


def urlopen(request, timeout: float):
    """Öffne eine HTTPS-Anfrage mit dem von certifi gelieferten CA-Bündel."""
    context = ssl.create_default_context()
    # Systemzertifikate bleiben erhalten; certifi ergänzt das verlässliche
    # Mozilla-Bündel für eingefrorene Python-Laufzeiten ohne eigenen CA-Pfad.
    context.load_verify_locations(cafile=certifi.where())
    return _stdlib_urlopen(request, timeout=timeout, context=context)


__all__ = ["urlopen"]
