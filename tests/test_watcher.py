from __future__ import annotations

from archivist.watcher.service import Watcher
from archivist.watcher.scheduler import WatcherScheduler


def snapshot(snapshot_id: int, captured_at: str, entities: list[dict], registries: dict | None = None) -> dict:
    return {
        "id": snapshot_id,
        "captured_at": captured_at,
        "entities": entities,
        "registries": registries or {"entities": [], "devices": [], "areas": []},
    }


def test_watcher_detects_transitions_and_expected_states() -> None:
    previous = snapshot(1, "2026-07-27T00:00:00+00:00", [
        {"entity_id": "sensor.old", "state": "on", "attributes": {}},
        {"entity_id": "sensor.battery", "state": "on", "attributes": {"battery": 50}},
        {"entity_id": "sensor.disabled", "state": "on", "attributes": {}},
    ])
    current = snapshot(2, "2026-07-27T01:00:00+00:00", [
        {"entity_id": "sensor.old", "state": "unavailable", "attributes": {}},
        {"entity_id": "sensor.battery", "state": "on", "attributes": {"battery": 10}},
        {"entity_id": "sensor.disabled", "state": "unknown", "attributes": {}},
        {"entity_id": "sensor.new", "state": "on", "attributes": {}},
    ], {"entities": [{"entity_id": "sensor.disabled", "disabled_by": "user"}], "devices": [], "areas": []})

    findings = Watcher().compare(previous, current)
    by_category = {(finding.category, finding.entity_id): finding for finding in findings}
    assert by_category["entity_unavailable", "sensor.old"].severity == "warning"
    assert by_category["low_battery", "sensor.battery"].status == "active"
    assert by_category["entity_unknown", "sensor.disabled"].expected is True
    assert by_category["entity_unknown", "sensor.disabled"].severity == "info"
    assert by_category["entity_added", "sensor.new"].status == "active"


def test_watcher_marks_recovery_and_ignores_initial_baseline() -> None:
    baseline = snapshot(1, "2026-07-27T00:00:00+00:00", [{"entity_id": "sensor.one", "state": "unavailable", "attributes": {}}])
    assert Watcher().compare(None, baseline) == []
    recovered = snapshot(2, "2026-07-27T01:00:00+00:00", [{"entity_id": "sensor.one", "state": "on", "attributes": {}}])
    findings = Watcher().compare(baseline, recovered)
    assert len(findings) == 1
    assert findings[0].status == "resolved"
    assert findings[0].category == "entity_unavailable"


def test_scheduler_uses_daily_default_interval() -> None:
    scheduler = WatcherScheduler(lambda: None, 24)  # type: ignore[arg-type]
    assert scheduler.interval_seconds == 24 * 60 * 60
