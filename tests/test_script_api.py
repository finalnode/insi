import asyncio
import threading

import httpx
from fastapi import FastAPI

from insi import script_api
from insi.sandbox import SandboxUnavailableError


def make_app(monkeypatch):
    monkeypatch.setattr(script_api, "script_code_examples", lambda: {"print(1)"})
    app = FastAPI()
    script_api.register_script_api(app)
    return app


def test_slow_script_launch_keeps_status_requests_responsive(monkeypatch):
    entered = threading.Event()
    release = threading.Event()

    def slow_start(source):
        entered.set()
        release.wait(3)
        return "new-job"

    monkeypatch.setattr(script_api.script_example_manager, "start", slow_start)
    monkeypatch.setattr(
        script_api.script_example_manager, "status", lambda _: {"finished": False}
    )
    app = make_app(monkeypatch)

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            launch = asyncio.create_task(
                client.post("/api/script/run", json={"source": "print(1)"})
            )
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                assert not launch.done(), "Der Programmstart hat den Eventloop blockiert"
                status = await asyncio.wait_for(
                    client.get("/api/script/status/existing-job"), timeout=1
                )
                assert status.status_code == 200
                assert not launch.done()
            finally:
                release.set()
                response = await launch
            assert response.json() == {"job_id": "new-job"}

    asyncio.run(scenario())


def test_script_launch_preserves_validation_and_sandbox_error(monkeypatch):
    calls = []

    def unavailable(source):
        calls.append(source)
        raise SandboxUnavailableError("Sandbox nicht verfügbar")

    monkeypatch.setattr(script_api.script_example_manager, "start", unavailable)
    app = make_app(monkeypatch)

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            invalid = await client.post("/api/script/run", json={"source": "other"})
            assert invalid.status_code == 403
            assert calls == []
            failed = await client.post("/api/script/run", json={"source": "print(1)"})
            assert failed.status_code == 503
            assert failed.json() == {"detail": "Sandbox nicht verfügbar"}
            assert calls == ["print(1)"]

    asyncio.run(scenario())
