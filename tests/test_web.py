import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from archivist.config import Settings
from archivist.main import create_app
from archivist.storage.database import Database


class FakeClient:
    async def get_states(self):
        return [
            {"entity_id": "sensor.one", "state": "on", "attributes": {"battery_level": 10}},
            {"entity_id": "light.unavailable", "state": "unavailable", "attributes": {}},
        ]

    async def get_registries(self):
        return {"entities": [], "devices": [], "areas": []}

    async def get_configurations(self, states):
        return {
            "automation.house_mode": {
                "trigger": [{"platform": "state", "entity_id": "sensor.one"}],
                "action": [{"service": "light.turn_on", "target": {"entity_id": "light.missing"}}],
            }
        }


def test_health_and_ingress_page(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path)
    client = TestClient(create_app(settings, Database(settings.database_path)))

    health = client.get("/health")
    page = client.get("/")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "the-archivist"}
    assert page.status_code == 200
    assert "The Archivist" in page.text
    assert "The Nexus" in page.text
    assert "Semantic Foundation" in page.text
    assert "Understand your home." in page.text
    assert "Curator" in page.text
    assert "The House Dreams Peacefully" in page.text
    assert client.get("/static/styles.css").status_code == 200


def test_snapshot_and_audit_download(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(data_dir=tmp_path)
    database = Database(settings.database_path)
    application = create_app(settings, database)
    client = TestClient(application)

    monkeypatch.setattr("archivist.main.HomeAssistantClient", lambda *args, **kwargs: FakeClient())
    response = client.post("/snapshot")

    assert response.status_code == 200
    snapshot_id = response.json()["snapshot_id"]
    bundle_path = tmp_path / "bundles" / f"snapshot-{snapshot_id}.json"
    assert bundle_path.exists()
    assert json.loads(bundle_path.read_text(encoding="utf-8"))["summary"]["total_entities"] == 2

    download = client.get(f"/audit/{snapshot_id}.json")
    assert download.status_code == 200
    assert download.headers["content-disposition"] == f"attachment; filename=snapshot-{snapshot_id}.json"
    assert download.json()["entities"][0]["entity_id"] == "light.unavailable"
    assert client.get("/watcher/findings").status_code == 200
    assert client.get("/watcher/findings.json").headers["content-disposition"] == "attachment; filename=watcher-findings.json"
    curator_download = client.get(f"/curator/{snapshot_id}.json")
    assert curator_download.status_code == 200
    assert curator_download.headers["content-disposition"] == f"attachment; filename=curator-{snapshot_id}.json"
    assert curator_download.json()["summary"]["entity_count"] == 2
    assert client.get("/curator/latest.json").status_code == 200
    raven = client.post("/raven/investigate", json={"target": "sensor.one"})
    assert raven.status_code == 200
    assert raven.json()["diagnosis"]["status"] == "diagnosed"
    assert client.get("/raven/diagnoses.json").headers["content-disposition"] == "attachment; filename=raven-diagnoses.json"
    semantic_download = client.get(f"/semantic/{snapshot_id}.json")
    assert semantic_download.status_code == 200
    assert semantic_download.headers["content-disposition"] == f"attachment; filename=semantic-{snapshot_id}.json"


def test_curator_export_requires_token_and_downloads_latest_zip(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(data_dir=tmp_path, curator_trigger_token="test-token", schedule_enabled=False)
    database = Database(settings.database_path)
    application = create_app(settings, database)
    client = TestClient(application)

    async def fake_create_export(*, settings):
        settings.curator_export_dir.mkdir(parents=True, exist_ok=True)
        archive = settings.curator_export_dir / "Curator_Report_2026-08-01_1200.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("system.json", "{}")
        return archive

    monkeypatch.setattr("archivist.main.create_export", fake_create_export)

    assert client.post("/curator/export").status_code == 401
    headers = {"Authorization": "Bearer test-token"}
    response = client.post("/curator/export", headers=headers)
    assert response.status_code == 200
    assert response.json()["filename"] == "Curator_Report_2026-08-01_1200.zip"

    download = client.get("/curator/export/latest.zip", headers=headers)
    assert download.status_code == 200
    assert download.content.startswith(b"PK")
    assert client.get("/curator/export/latest.zip").status_code == 401
