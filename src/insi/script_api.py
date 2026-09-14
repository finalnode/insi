"""HTTP-Schnittstelle zum kontrollierten Ausführen freigegebener Skriptbeispiele."""

from .execution import script_example_manager
from .library import script_code_examples
from .sandbox import SandboxUnavailableError


def register_script_api(app) -> None:
    """Registriere die Lauf- und Statusrouten genau einmal an der NiceGUI-App."""
    from fastapi import HTTPException, Request
    from starlette.concurrency import run_in_threadpool

    allowed_examples = script_code_examples()

    @app.post("/api/script/run")
    async def run_script_example(request: Request) -> dict[str, object]:
        payload = await request.json()
        source = payload.get("source", "") if isinstance(payload, dict) else ""
        if not isinstance(source, str) or source.rstrip() not in allowed_examples:
            raise HTTPException(
                status_code=403,
                detail="Dieses Beispiel gehört nicht zum Skript.",
            )
        try:
            # Der Sandbox-Selbsttest kann beim ersten Start mehrere Sekunden
            # dauern. Währenddessen müssen UI und Statusrouten erreichbar bleiben.
            job_id = await run_in_threadpool(
                script_example_manager.start, source.rstrip()
            )
            return {"job_id": job_id}
        except SandboxUnavailableError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.get("/api/script/status/{job_id}")
    async def script_example_status(job_id: str) -> dict[str, object]:
        status = script_example_manager.status(job_id)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail="Der Programmlauf wurde nicht gefunden.",
            )
        return status
