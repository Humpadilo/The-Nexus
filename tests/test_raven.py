from archivist.raven.service import RavenInvestigator
from archivist.engineer.service import EngineerProposalBuilder


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
    assert diagnosis["lifecycle"] == "Root Cause Identified"
    assert diagnosis["root_cause"]["category"] == "broken_reference"
    assert diagnosis["root_cause"]["target"] == "light.missing"
    assert all(edge["target"] != "light.turn_on" for edge in diagnosis["execution_paths"])
    assert diagnosis["execution_paths"][0]["source"] == "automation.house_mode"
    assert diagnosis["evidence"]["read_only"] is True
    assert diagnosis["what_happened"]
    assert diagnosis["why_it_happened"]
    assert diagnosis["validation_steps"]


def test_raven_reports_orphaned_house_mode_helper() -> None:
    snapshot = {
        "id": 13,
        "entities": [{"entity_id": "input_select.house_mode", "state": "Morning", "attributes": {}}],
        "registries": {"entities": [], "devices": [], "areas": []},
    }

    diagnosis = RavenInvestigator().investigate(snapshot, {}, "input_select.house_mode")

    assert diagnosis["status"] == "diagnosed"
    assert diagnosis["findings"][0]["category"] == "orphaned_helper"


def test_engineer_builds_bounded_house_mode_rename_proposal() -> None:
    snapshot = {
        "id": 14,
        "entities": [
            {"entity_id": "input_select.house_mode", "state": "Morning", "attributes": {}},
            {"entity_id": "media_player.bedroom_matts_room", "state": "idle", "attributes": {}},
        ],
        "registries": {"entities": [{"entity_id": "input_select.house_mode", "area_id": "kitchen"}], "devices": [], "areas": []},
    }
    configurations = {
        "automation.work_day_wakeup_2": {
            "id": "work_day_wakeup_2",
            "action": [{"target": {"entity_id": "media_player.matts_room"}}],
        }
    }
    diagnosis = RavenInvestigator().investigate(snapshot, configurations, "input_select.house_mode")
    proposal = EngineerProposalBuilder().build_house_mode_proposal(diagnosis, configurations)

    assert proposal is not None
    assert proposal["intended_entity"] == "media_player.bedroom_matts_room"
    assert proposal["proposed_changes"][0]["before"] == "media_player.matts_room"
    assert proposal["proposed_changes"][0]["after"] == "media_player.bedroom_matts_room"
    updated = EngineerProposalBuilder.apply_entity_replacements(configurations["automation.work_day_wakeup_2"], proposal["proposed_changes"])
    assert updated["action"][0]["target"]["entity_id"] == "media_player.bedroom_matts_room"
    restored = EngineerProposalBuilder.apply_entity_replacements(updated, proposal["proposed_changes"], rollback=True)
    assert restored == configurations["automation.work_day_wakeup_2"]


def test_raven_ignores_numeric_scene_attribute_keys() -> None:
    references = RavenInvestigator._references(
        {
            "scene": {"entity_id": "14.1"},
            "target": {"entity_id": "light.kitchen"},
        }
    )

    assert references == {"light.kitchen"}
