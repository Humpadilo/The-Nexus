"""FastAPI application entry point."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from archivist.api.home_assistant import HomeAssistantClient
from archivist.collector.service import Collector
from archivist.config import Settings
from archivist.logging import configure_logging
from archivist.storage.database import Database

configure_logging()
logger = logging.getLogger(__name__)
settings = Settings()
database = Database(settings.database_path)
templates = Jinja2Templates(directory="archivist/templates")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.bundles_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="The Archivist", lifespan=lifespan)


def collector() -> Collector:
    return Collector(HomeAssistantClient(settings.ha_rest_url, settings.ha_ws_url, settings.supervisor_token), database)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "the-archivist"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    latest = database.latest_snapshot()
    return templates.TemplateResponse(request=request, name="index.html", context={"latest": latest})


@app.post("/snapshot")
async def run_snapshot() -> Response:
    try:
        result = await collector().run()
        settings.bundles_dir.mkdir(parents=True, exist_ok=True)
        (settings.bundles_dir / f"snapshot-{result.snapshot_id}.json").write_text(json.dumps(result.bundle, indent=2), encoding="utf-8")
        return JSONResponse({"snapshot_id": result.snapshot_id, "summary": result.bundle["summary"]})
    except Exception:
        logger.exception("snapshot_failed")
        return JSONResponse({"error": "Snapshot failed. Check the app logs."}, status_code=502)


@app.get("/audit/{snapshot_id}.json")
async def audit(snapshot_id: int) -> Response:
    bundle = database.get_snapshot(snapshot_id)
    if bundle is None:
        return JSONResponse({"error": "Snapshot not found"}, status_code=404)
    return Response(json.dumps(bundle, indent=2), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=snapshot-{snapshot_id}.json"})


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port, proxy_headers=True)
