from pathlib import Path

from archivist.storage.database import Database
from archivist.storage.models import EntityObservation


def test_snapshot_round_trip(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    summary = {"total_entities": 1, "unavailable_entities": 0, "unknown_entities": 0, "disabled_or_unavailable_automations": 0, "low_battery_entities": 0}
    snapshot_id = db.save_snapshot(summary, [EntityObservation("light.one", "on", {"friendly_name": "One"})], {"areas": []})
    bundle = db.get_snapshot(snapshot_id)
    assert bundle is not None
    assert bundle["summary"] == summary
    assert bundle["entities"][0]["entity_id"] == "light.one"
