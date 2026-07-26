from pathlib import Path

from archivist.storage.database import Database
from archivist.storage.models import EntityObservation
from archivist.watcher.models import FindingCandidate
from datetime import datetime, UTC


def test_snapshot_round_trip(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    summary = {"total_entities": 1, "unavailable_entities": 0, "unknown_entities": 0, "disabled_or_unavailable_automations": 0, "low_battery_entities": 0}
    snapshot_id = db.save_snapshot(summary, [EntityObservation("light.one", "on", {"friendly_name": "One"})], {"areas": []})
    bundle = db.get_snapshot(snapshot_id)
    assert bundle is not None
    assert bundle["summary"] == summary
    assert bundle["entities"][0]["entity_id"] == "light.one"


def test_findings_are_upserted_with_evidence_and_recovery(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    observed = datetime(2026, 7, 27, tzinfo=UTC)
    active = FindingCandidate("entity_unavailable:light.one", "entity_unavailable", "light.one", "Unavailable", "Still unavailable", "warning", "high", False, "active", 1, observed, {"current_snapshot_id": 1})
    db.save_findings([active, active])
    findings = db.list_findings()
    assert len(findings) == 1
    assert findings[0]["occurrence_count"] == 2
    assert findings[0]["evidence"]["current_snapshot_id"] == 1

    resolved = FindingCandidate("entity_unavailable:light.one", "entity_unavailable", "light.one", "Recovered", "Recovered", "info", "high", False, "resolved", 2, datetime(2026, 7, 28, tzinfo=UTC), {"current_snapshot_id": 2})
    db.save_findings([resolved])
    assert db.list_findings()[0]["status"] == "resolved"
