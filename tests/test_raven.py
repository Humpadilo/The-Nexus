from archivist.raven.service import RavenInvestigator


def test_raven_traces_house_mode_and_identifies_broken_reference() -> None:
    snapshot = {
        "id": 12,
        "captured_at": "2026-07-27T00:00:00+00:00",
        "entities": [
            {"entity_id": "input_select.house_mode", "state": "Morning", "attributes": {"friendly_name": "House mode"}},
            {"entity_id": "automation.house_mode", "state": "on", "attributes": {"friendly_name": "House mode controller"}},
            {"entity_id": "light.kitchen", "state": "on", "attributes": {"friendly_name": "Kitchen"}},
        ],
        "registries": {"entities": [{"entity_id": "input_select.house_mode", "area_id": "kitchen"}], "devices": [], "areas": []},
    }
    configurations = {
        "automation.house_mode": {
            "alias": "House mode controller",
            "trigger": [{"platform": "state", "entity_id": "input_select.house_mode"}],
            "action": [{"service": "light.turn_on", "target": {"entity_id": "light.missing"}}],
        }
    }

    diagnosis = RavenInvestigator().investigate(snapshot, configurations, "input_select.house_mode")

    assert diagnosis["status"] == "diagnosed"
    assert diagnosis["root_cause"]["category"] == "broken_reference"
    assert diagnosis["root_cause"]["target"] == "light.missing"
    assert all(edge["target"] != "light.turn_on" for edge in diagnosis["execution_paths"])
    assert diagnosis["execution_paths"][0]["source"] == "automation.house_mode"
    assert diagnosis["evidence"]["read_only"] is True


def test_raven_reports_orphaned_house_mode_helper() -> None:
    snapshot = {
        "id": 13,
        "entities": [{"entity_id": "input_select.house_mode", "state": "Morning", "attributes": {}}],
        "registries": {"entities": [], "devices": [], "areas": []},
    }

    diagnosis = RavenInvestigator().investigate(snapshot, {}, "input_select.house_mode")

    assert diagnosis["status"] == "diagnosed"
    assert diagnosis["findings"][0]["category"] == "orphaned_helper"
