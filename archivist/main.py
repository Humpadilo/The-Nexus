"""FastAPI application entry point."""

from __future__ import annotations

import json
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Iterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from archivist.api.home_assistant import HomeAssistantClient
from archivist.collector.service import Collector
from archivist.config import Settings
from archivist.dashboard.service import DashboardBuilder
from archivist.logging import configure_logging
from archivist.storage.database import Database
from archivist.watcher.scheduler import WatcherScheduler

configure_logging()
logger = logging.getLogger(__name__)
TEMPLATES_DIRECTORY = Path(__file__).resolve().parent / "templates"


def create_app(app_settings: Settings | None = None, app_database: Database | None = None) -> FastAPI:
    """Create the web application with injectable settings and storage for testing."""
    current_settings = app_settings or Settings()
    current_database = app_database or Database(current_settings.database_path)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIRECTORY))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> Iterator[None]:
        current_settings.data_dir.mkdir(parents=True, exist_ok=True)
        current_settings.bundles_dir.mkdir(parents=True, exist_ok=True)
        scheduled_task: asyncio.Task[None] | None = None
        if current_settings.schedule_enabled:
            scheduled_task = asyncio.create_task(
                WatcherScheduler(collector, current_settings.schedule_interval_hours).run()
            )
            logger.info("watcher_scheduler_started", extra={"interval_hours": current_settings.schedule_interval_hours})
        try:
            yield
        finally:
            if scheduled_task is not None:
                scheduled_task.cancel()
                await asyncio.gather(scheduled_task, return_exceptions=True)
                logger.info("watcher_scheduler_stopped")

    application = FastAPI(title="The Archivist", lifespan=lifespan)
    application.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
        name="static",
    )

    def collector() -> Collector:
        return Collector(
            HomeAssistantClient(
                current_settings.ha_rest_url,
                current_settings.ha_ws_url,
                current_settings.supervisor_token,
            ),
            current_database,
        )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "the-archivist"}

    @application.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        latest = current_database.latest_snapshot()
        findings = current_database.list_findings(limit=25)
        latest_bundle = current_database.get_snapshot(latest.id) if latest else None
        dashboard = DashboardBuilder().build(
            latest_bundle, current_database.list_snapshots(), current_database.list_findings()
        )
        return templates.TemplateResponse(
            request=request, name="index.html",
            context={"latest": latest, "findings": findings, "dashboard": dashboard},
        )

    @application.post("/snapshot")
    async def run_snapshot() -> Response:
        try:
            result = await collector().run()
            current_database.prune_resolved_findings(current_settings.finding_retention_days)
            current_settings.bundles_dir.mkdir(parents=True, exist_ok=True)
            bundle_path = current_settings.bundles_dir / f"snapshot-{result.snapshot_id}.json"
            bundle_path.write_text(json.dumps(result.bundle, indent=2), encoding="utf-8")
            return JSONResponse({"snapshot_id": result.snapshot_id, "summary": result.bundle["summary"]})
        except Exception:
            logger.exception("snapshot_failed")
            return JSONResponse({"error": "Snapshot failed. Check the app logs."}, status_code=502)

    @application.get("/audit/{snapshot_id}.json")
    async def audit(snapshot_id: int) -> Response:
        bundle = current_database.get_snapshot(snapshot_id)
        if bundle is None:
            return JSONResponse({"error": "Snapshot not found"}, status_code=404)
        return Response(
            json.dumps(bundle, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=snapshot-{snapshot_id}.json"},
        )

    @application.get("/semantic/{snapshot_id}.json")
    async def semantic(snapshot_id: int) -> Response:
        projection = current_database.get_semantic_projection(snapshot_id)
        if projection is None:
            return JSONResponse({"error": "Semantic projection not found"}, status_code=404)
        return Response(
            json.dumps(projection, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=semantic-{snapshot_id}.json"},
        )

    @application.get("/watcher/findings")
    async def watcher_findings() -> JSONResponse:
        return JSONResponse({"findings": current_database.list_findings()})

    @application.get("/watcher/findings.json")
    async def watcher_findings_download() -> Response:
        payload = json.dumps({"findings": current_database.list_findings()}, indent=2)
        return Response(payload, media_type="application/json", headers={"Content-Disposition": "attachment; filename=watcher-findings.json"})

    return application


app = create_app()


if __name__ == "__main__":
    runtime_settings = Settings()
    uvicorn.run(app, host=runtime_settings.host, port=runtime_settings.port, proxy_headers=True)
