from archivist.reports.summary import build_summary


def test_build_summary_counts_health_automation_and_battery() -> None:
    states = [
        {"entity_id": "light.one", "state": "on", "attributes": {}},
        {"entity_id": "sensor.bad", "state": "unavailable", "attributes": {}},
        {"entity_id": "sensor.unknown", "state": "unknown", "attributes": {}},
        {"entity_id": "automation.door", "state": "off", "attributes": {}},
        {"entity_id": "sensor.battery", "state": "on", "attributes": {"battery": 12}},
    ]
    assert build_summary(states) == {"total_entities": 5, "unavailable_entities": 1, "unknown_entities": 1, "disabled_or_unavailable_automations": 1, "low_battery_entities": 1}
