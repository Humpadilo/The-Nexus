from pathlib import Path

from fastapi.testclient import TestClient

from archivist.config import Settings
from archivist.main import create_app
from archivist.raven.service import RavenInvestigator
from archivist.storage.database import Database
from archivist.storage.models import EntityObservation
from archivist.engineer.service import EngineerProposalBuilder


def _snapshot(snapshot_id: int = 1) -> dict:
    return {
        "id": snapshot_id,
        "captured_at": "2026-07-27T00:00:00+00:00",
        "entities": [
            {"entity_id": "input_select.house_mode", "state": "home", "attributes": {}},
            {"entity_id": "media_player.bedroom_matts_room", "state": "idle", "attributes": {}},
        ],
        "registries": {"entities": [], "devices": [], "areas": []},
    }


def _configurations() -> dict:
    return {
        "automation.house_mode": {
            "action": [{"target": {"entity_id": "media_player.matts_room"}}]
        }
    }


def test_simultaneous_investigations_have_distinct_findings_and_no_leakage() -> None:
    investigator = RavenInvestigator()
    first = investigator.investigate(_snapshot(1), _configurations(), "input_select.house_mode")
    second = investigator.investigate(_snapshot(2), {}, "input_select.house_mode")

    assert first["investigation_id"] != second["investigation_id"]
    assert first["findings"][0]["finding_id"]
    assert {finding["finding_id"] for finding in first["findings"]}.isdisjoint(
        {finding["finding_id"] for finding in second["findings"]}
    )


def test_proposal_explicitly_addresses_findings_and_stays_proposed() -> None:
    diagnosis = RavenInvestigator().investigate(_snapshot(), _configurations(), "input_select.house_mode")
    proposal = EngineerProposalBuilder().build_house_mode_proposal(diagnosis, _configurations())

    assert proposal is not None
    assert proposal["investigation_id"] == diagnosis["investigation_id"]
    assert proposal["addresses_finding_ids"] == proposal["finding_ids"]
    assert proposal["lifecycle"] == "Restoration Proposed"
    assert proposal["application_record"] is None
    assert proposal["read_only"] is True


def test_historical_applied_without_application_record_is_not_reported_as_applied(tmp_path: Path) -> None:
    db = Database(tmp_path / "archivist.db")
    summary = {"total_entities": 0, "unavailable_entities": 0, "unknown_entities": 0, "disabled_or_unavailable_automations": 0, "low_battery_entities": 0}
    snapshot_id = db.save_snapshot(summary, [], {})
    diagnosis = {"snapshot_id": snapshot_id, "target": "input_select.house_mode", "status": "diagnosed", "investigation_id": "raven-test", "evidence": {"read_only": True}}
    diagnosis_id = db.save_raven_diagnosis(diagnosis)
    proposal_id = db.save_engineer_proposal({"target": "input_select.house_mode", "status": "applied", "investigation_id": "raven-test", "application_record": None}, diagnosis_id)

    stored = db.get_engineer_proposal(proposal_id)
    assert stored is not None
    assert stored["status"] == "proposed"
    assert stored["lifecycle"] == "Restoration Proposed"


def test_apply_endpoint_is_hard_read_only(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path)
    db = Database(settings.database_path)
    summary = {"total_entities": 0, "unavailable_entities": 0, "unknown_entities": 0, "disabled_or_unavailable_automations": 0, "low_battery_entities": 0}
    snapshot_id = db.save_snapshot(summary, [], {})
    diagnosis_id = db.save_raven_diagnosis({"snapshot_id": snapshot_id, "target": "input_select.house_mode", "status": "diagnosed", "investigation_id": "raven-test", "evidence": {"read_only": True}})
    proposal_id = db.save_engineer_proposal({"target": "input_select.house_mode", "status": "proposed", "investigation_id": "raven-test", "application_record": None}, diagnosis_id)
    client = TestClient(create_app(settings, db))

    response = client.post(f"/engineer/proposals/{proposal_id}/approve", json={"confirmation": "APPROVE HOUSE MODE REPAIR"})
    assert response.status_code == 409
    assert response.json()["read_only"] is True
    assert db.get_engineer_proposal(proposal_id)["status"] == "proposed"
