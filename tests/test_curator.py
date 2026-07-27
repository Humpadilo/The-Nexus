from archivist.curator.service import CuratorBuilder


def test_curator_organizes_areas_concepts_relationships_and_cues() -> None:
    latest = {
        "id": 7,
        "entities": [
            {"entity_id": "light.kitchen", "attributes": {"friendly_name": "Kitchen light"}},
            {"entity_id": "input_boolean.arrival", "attributes": {"friendly_name": "Arrival"}},
            {"entity_id": "automation.kitchen", "attributes": {"entity_id": ["light.kitchen", "input_boolean.arrival"]}},
        ],
        "semantic": {"facts": [
            {"fact_type": "area", "subject_id": "kitchen", "payload": {"display_name": "Kitchen"}, "provenance": {"source_type": "area_registry", "source_id": "kitchen"}},
            {"fact_type": "device", "subject_id": "device-1", "payload": {"display_name": "Kitchen device", "area_id": "kitchen", "entity_ids": ["light.kitchen"]}, "provenance": {"source_type": "device_registry", "source_id": "device-1"}},
            {"fact_type": "entity", "subject_id": "light.kitchen", "payload": {"display_name": "Kitchen light", "domain": "light", "area_id": "kitchen", "device_id": "device-1", "state": "on"}, "provenance": {"source_type": "entity_registry", "source_id": "light.kitchen"}},
            {"fact_type": "entity", "subject_id": "input_boolean.arrival", "payload": {"display_name": "Arrival", "domain": "input_boolean", "state": "off"}, "provenance": {"source_type": "entity_registry", "source_id": "input_boolean.arrival"}},
            {"fact_type": "entity", "subject_id": "automation.kitchen", "payload": {"display_name": "Kitchen automation", "domain": "automation", "state": "on"}, "provenance": {"source_type": "entity_registry", "source_id": "automation.kitchen"}},
        ]},
    }
    findings = [{"id": 3, "category": "entity_unavailable", "title": "Unavailable light", "status": "ongoing", "severity": "warning", "confidence": "high", "entity_id": "light.kitchen", "evidence": {"snapshot_id": 7}, "last_snapshot_id": 7}]

    result = CuratorBuilder().build(latest, findings)

    assert result["summary"]["area_count"] == 2
    assert any(area["display_name"] == "Unassigned" for area in result["areas"])
    assert any(concept["concept_id"] == "lighting" for concept in result["concepts"])
    assert {("automation.kitchen", "light.kitchen"), ("automation.kitchen", "input_boolean.arrival")} <= {(item["source"], item["target"]) for item in result["relationships"]}
    assert result["findings"][0]["likely_cause"]
    assert result["findings"][0]["evidence"]["snapshot_id"] == 7
    assert result["organization_cues"][0]["category"] == "missing_area_assignment"
