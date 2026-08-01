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
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from archivist.api.home_assistant import HomeAssistantClient
from archivist.collector.service import Collector
from archivist.config import Settings
from archivist.curator.exporter import create_export
from archivist.curator.service import CuratorBuilder
from archivist.dashboard.service import DashboardBuilder
from archivist.engineer.service import EngineerProposalBuilder
from archivist.logging import configure_logging
from archivist.raven.service import RavenInvestigator
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
    curator_export_lock = asyncio.Lock()

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
        curator = CuratorBuilder().build(latest_bundle, current_database.list_findings())
        raven_diagnoses = current_database.list_raven_diagnoses(limit=5)
        latest_diagnosis_id = raven_diagnoses[0]["id"] if raven_diagnoses else None
        engineer_proposals = [
            proposal for proposal in current_database.list_engineer_proposals(limit=20)
            if proposal.get("diagnosis_id") == latest_diagnosis_id
        ]
        return templates.TemplateResponse(
            request=request, name="index.html",
            context={"latest": latest, "findings": findings, "dashboard": dashboard, "curator": curator, "raven_diagnoses": raven_diagnoses, "engineer_proposals": engineer_proposals},
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

    def curator_bundle(snapshot_id: int) -> JSONResponse | Response:
        bundle = current_database.get_snapshot(snapshot_id)
        if bundle is None:
            return JSONResponse({"error": "Snapshot not found"}, status_code=404)
        projection = CuratorBuilder().build(bundle, current_database.list_findings())
        return Response(
            json.dumps(projection, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=curator-{snapshot_id}.json"},
        )

    @application.get("/curator/latest.json")
    async def curator_latest() -> Response:
        latest_snapshot = current_database.latest_snapshot()
        if latest_snapshot is None:
            return JSONResponse({"error": "Snapshot not found"}, status_code=404)
        return curator_bundle(latest_snapshot.id)

    @application.get("/curator/{snapshot_id}.json")
    async def curator_download(snapshot_id: int) -> Response:
        return curator_bundle(snapshot_id)

    @application.post("/curator/export")
    async def run_curator_export() -> JSONResponse:
        """Generate the full Curator ZIP from an app, dashboard, or service trigger."""
        if curator_export_lock.locked():
            return JSONResponse({"error": "A Curator export is already running."}, status_code=409)
        try:
            async with curator_export_lock:
                archive = await create_export(settings=current_settings)
            return JSONResponse({"status": "success", "filename": archive.name,
                                 "download_url": "curator/export/latest.zip"})
        except Exception:
            logger.exception("curator_export_failed")
            return JSONResponse({"error": "Curator export failed. Check the app logs."}, status_code=502)

    @application.get("/curator/export/latest.zip")
    async def download_curator_export() -> Response:
        exports = sorted(current_settings.curator_export_dir.glob("Curator_Report_*.zip"), reverse=True)
        if not exports:
            return JSONResponse({"error": "No Curator export has been generated yet."}, status_code=404)
        return FileResponse(exports[0], filename=exports[0].name, media_type="application/zip")

    @application.get("/watcher/findings")
    async def watcher_findings() -> JSONResponse:
        return JSONResponse({"findings": current_database.list_findings()})

    @application.get("/watcher/findings.json")
    async def watcher_findings_download() -> Response:
        payload = json.dumps({"findings": current_database.list_findings()}, indent=2)
        return Response(payload, media_type="application/json", headers={"Content-Disposition": "attachment; filename=watcher-findings.json"})

    @application.post("/raven/investigate")
    async def raven_investigate(request: Request) -> JSONResponse:
        latest_snapshot = current_database.latest_snapshot()
        if latest_snapshot is None:
            return JSONResponse({"error": "Run a snapshot before investigating."}, status_code=409)
        bundle = current_database.get_snapshot(latest_snapshot.id)
        if bundle is None:
            return JSONResponse({"error": "Snapshot not found"}, status_code=404)
        try:
            body = await request.json()
            target = body.get("target") if isinstance(body, dict) else None
            client = HomeAssistantClient(current_settings.ha_rest_url, current_settings.ha_ws_url, current_settings.supervisor_token)
            configurations = await client.get_configurations(bundle.get("entities", []))
            diagnosis = RavenInvestigator().investigate(bundle, configurations, target)
            diagnosis_id = current_database.save_raven_diagnosis(diagnosis)
            diagnosis["diagnosis_id"] = diagnosis_id
            proposal = EngineerProposalBuilder().build_house_mode_proposal(diagnosis, configurations)
            proposal_id = current_database.save_engineer_proposal(proposal, diagnosis_id) if proposal else None
            if proposal_id:
                proposal["id"] = proposal_id
                diagnosis["lifecycle"] = "Restoration Proposed"
                diagnosis["restoration_proposal_id"] = proposal_id
                current_database.update_raven_diagnosis(diagnosis_id, diagnosis)
            return JSONResponse({"diagnosis_id": diagnosis_id, "diagnosis": diagnosis, "repair_proposal": proposal})
        except Exception:
            logger.exception("raven_investigation_failed")
            return JSONResponse({"error": "Raven investigation failed. Check the app logs."}, status_code=502)

    @application.get("/raven/diagnoses.json")
    async def raven_diagnoses_download() -> Response:
        payload = json.dumps({"diagnoses": current_database.list_raven_diagnoses()}, indent=2)
        return Response(payload, media_type="application/json", headers={"Content-Disposition": "attachment; filename=raven-diagnoses.json"})

    @application.get("/engineer/proposals/{proposal_id}")
    async def engineer_proposal(proposal_id: int) -> JSONResponse:
        proposal = current_database.get_engineer_proposal(proposal_id)
        if proposal is None:
            return JSONResponse({"error": "Repair proposal not found"}, status_code=404)
        diagnosis_id = proposal.get("diagnosis_id")
        diagnosis = current_database.get_raven_diagnosis(int(diagnosis_id)) if diagnosis_id else None
        if diagnosis is None or diagnosis["diagnosis"].get("investigation_id") != proposal.get("investigation_id"):
            return JSONResponse({"error": "Restoration proposal is not linked to this investigation."}, status_code=409)
        return JSONResponse({"proposal": proposal, "audit": current_database.list_repair_audit(proposal_id)})

    @application.post("/engineer/proposals/{proposal_id}/cancel")
    async def cancel_engineer_proposal(proposal_id: int) -> JSONResponse:
        proposal = current_database.get_engineer_proposal(proposal_id)
        if proposal is None:
            return JSONResponse({"error": "Repair proposal not found"}, status_code=404)
        if proposal["status"] not in {"proposed", "approved"}:
            return JSONResponse({"error": f"Proposal cannot be cancelled from status {proposal['status']}"}, status_code=409)
        current_database.update_engineer_proposal(proposal_id, "cancelled", "proposal_cancelled", {"read_only": True})
        return JSONResponse({"proposal_id": proposal_id, "status": "cancelled"})

    @application.post("/engineer/proposals/{proposal_id}/approve")
    async def approve_engineer_proposal(proposal_id: int) -> JSONResponse:
        proposal = current_database.get_engineer_proposal(proposal_id)
        if proposal is None:
            return JSONResponse({"error": "Repair proposal not found"}, status_code=404)
        return JSONResponse({"error": "The Nexus is read-only. This proposal remains Restoration Proposed and cannot be applied.", "status": "Restoration Proposed", "read_only": True}, status_code=409)

    return application


app = create_app()


if __name__ == "__main__":
    runtime_settings = Settings()
    uvicorn.run(app, host=runtime_settings.host, port=runtime_settings.port, proxy_headers=True)
