from datetime import UTC, datetime

from archivist.dashboard.service import DashboardBuilder
from archivist.storage.models import Snapshot


def test_dashboard_groups_semantic_facts_and_finding_health() -> None:
    latest = {
        "id": 7,
        "semantic": {"facts": [
            {"fact_type": "entity", "payload": {"display_name": "Lamp", "domain": "light", "entity_id": "light.lamp", "area_id": "room", "state": "on", "availability": "available"}},
            {"fact_type": "health", "payload": {"health_state": "available"}},
            {"fact_type": "area", "payload": {"display_name": "Room", "entity_ids": ["light.lamp"]}},
            {"fact_type": "device", "payload": {"display_name": "Bridge", "entity_ids": ["light.lamp"]}},
            {"fact_type": "capability", "payload": {"domain": "light", "capabilities": ["state"]}},
        ]},
    }
    finding = {"status": "active", "severity": "warning", "title": "Unavailable", "last_seen": "now"}
    result = DashboardBuilder().build(latest, [Snapshot(7, datetime.now(UTC), 1, 0, 0, 0, 0)], [finding])
    assert result["overview"]["health"] == "attention"
    assert result["overview"]["areas"] == 1
    assert result["health"]["counts"] == {"warning": 1}
    assert result["explorer"]["entities"][0]["display_name"] == "Lamp"
    assert result["timeline"][0]["id"] == 7
