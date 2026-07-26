from archivist.semantic.models import SEMANTIC_SCHEMA_VERSION
from archivist.semantic.service import SemanticBuilder


def semantic_snapshot() -> dict:
    return {
        "id": 7,
        "registries": {
            "entities": [
                {"entity_id": "sensor.kitchen", "device_id": "device-1", "area_id": "area-kitchen"},
            ],
            "devices": [{"id": "device-1", "name": "Kitchen Sensor", "manufacturer": "Example"}],
            "areas": [{"area_id": "area-kitchen", "name": "Kitchen"}],
        },
        "entities": [
            {
                "entity_id": "sensor.kitchen",
                "state": "on",
                "attributes": {"friendly_name": "Kitchen Temperature", "temperature": 21.5, "battery": 72},
            },
        ],
    }


def test_semantic_projection_is_dashboard_oriented_and_provenance_backed() -> None:
    projection = SemanticBuilder().build(semantic_snapshot())
    facts = {fact.fact_type: fact for fact in projection.facts if fact.subject_id == "sensor.kitchen"}

    assert projection.schema_version == SEMANTIC_SCHEMA_VERSION
    assert projection.summary["entity_count"] == 1
    assert projection.summary["device_count"] == 1
    assert projection.summary["area_count"] == 1
    assert facts["entity"].payload["display_name"] == "Kitchen Temperature"
    assert facts["entity"].payload["device_id"] == "device-1"
    assert facts["health"].payload["health_state"] == "available"
    assert "temperature" in facts["capability"].payload["capabilities"]
    assert facts["health"].provenance["snapshot_id"] == 7
    assert facts["health"].provenance["source_id"] == "sensor.kitchen"


def test_semantic_projection_is_rebuildable_from_same_snapshot() -> None:
    builder = SemanticBuilder()
    first = builder.build(semantic_snapshot())
    second = builder.build(semantic_snapshot())

    assert first.summary == second.summary
    assert [fact.as_dict() for fact in first.facts] == [fact.as_dict() for fact in second.facts]


def test_semantic_projection_handles_missing_registries() -> None:
    snapshot = semantic_snapshot()
    snapshot["registries"] = {"entities": [], "devices": [], "areas": []}
    projection = SemanticBuilder().build(snapshot)
    entity = next(fact for fact in projection.facts if fact.fact_type == "entity")

    assert entity.confidence == "medium"
    assert entity.payload["device_id"] is None
    assert entity.payload["area_id"] is None
    assert entity.provenance["source_type"] == "entity_observation"
