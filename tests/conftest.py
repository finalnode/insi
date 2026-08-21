import os
from pathlib import Path

import pytest


# Der lokale Entwicklungsrechner kann einen neueren Inhaltsstand aktiviert
# haben. Tests starten reproduzierbar immer mit dem im Checkout enthaltenen
# Beispielkurs und überschreiben diesen Pfad nur gezielt pro Test.
os.environ.setdefault(
    "PYKIM_CONTENT_DIR",
    str(Path(__file__).resolve().parents[1] / "src" / "insi"),
)
os.environ.setdefault(
    "PYKIM_TRAINER_PROVIDER",
    "insi.training.provider:provider",
)

from pykim.testing import reset_world


@pytest.fixture(autouse=True)
def clean_world(monkeypatch, tmp_path):
    # Tests dürfen niemals den lokal konfigurierten Schülerkurs verändern.
    # Die beim Einsammeln benötigte Inhaltsvorgabe wird pro Test entfernt;
    # dadurch lassen sich Aktivierung und Kurs-Caches realistisch prüfen.
    monkeypatch.delenv("PYKIM_CONTENT_DIR", raising=False)
    monkeypatch.setenv("PYKIM_PROGRESS_MODE", "disabled")
    monkeypatch.setenv("PYKIM_CONFIG_DIR", str(tmp_path / "config"))
    reset_world()
    packaged = Path(__file__).resolve().parents[1] / "src" / "insi"
    from insi.registries import activate_content_registries
    from insi import sandbox

    activate_content_registries(packaged)
    # Unit- und Integrationstests führen Testprogramme lokal aus. Die
    # Produktionslogik besitzt dafür keinen Umgebungsvariablen-Bypass und
    # verlangt auf echten Systemen weiterhin einen verifizierten OS-Adapter.
    monkeypatch.setattr(sandbox, "_adapter_override", sandbox._TestAdapter())
