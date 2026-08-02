from pathlib import Path

import pytest

from archivist.curator.exporter import CuratorExporter


class FakeCuratorClient:
    async def websocket_command(self, command: str, **payload):
        assert command == "config_entries/get"
        return [{"entry_id": "entry-hue", "domain": "hue"}]


@pytest.mark.asyncio
async def test_integration_device_counts_resolve_config_entry_ids(tmp_path: Path) -> None:
    exporter = CuratorExporter(FakeCuratorClient(), tmp_path)
    exporter.states = [{"entity_id": "light.kitchen"}, {"entity_id": "sensor.temperature"}]
    exporter.config = {"components": ["hue", "sensor"]}
    exporter.registries = {
        "devices": [{"id": "device-1", "config_entries": ["entry-hue"]}],
    }

    result = await exporter.integrations()

    assert result["items"] == [
        {"integration": "hue", "version": None, "device_count": 1, "entity_count": 0},
        {"integration": "sensor", "version": None, "device_count": 0, "entity_count": 1},
    ]


@pytest.mark.asyncio
async def test_room_capabilities_group_entities_and_room_automations(tmp_path: Path) -> None:
    exporter = CuratorExporter(FakeCuratorClient(), tmp_path)
    exporter.states = [
        {"entity_id": "light.bedroom", "state": "off", "attributes": {"friendly_name": "Bedroom light"}},
        {"entity_id": "binary_sensor.hall_motion", "state": "on", "attributes": {"device_class": "motion"}},
        {"entity_id": "input_boolean.night_mode", "state": "off", "attributes": {}},
        {"entity_id": "automation.hall_light", "state": "on", "attributes": {"friendly_name": "Hall light"}},
    ]
    exporter.registries = {
        "areas": [
            {"id": "bedroom", "name": "Matt's Bedroom"},
            {"id": "hall", "name": "Upstairs Hall"},
        ],
        "devices": [],
        "entities": [
            {"entity_id": "light.bedroom", "area_id": "bedroom"},
            {"entity_id": "binary_sensor.hall_motion", "area_id": "hall"},
            {"entity_id": "input_boolean.night_mode", "area_id": "bedroom"},
            {"entity_id": "automation.hall_light", "area_id": None},
        ],
    }
    exporter.data = {
        "automations.json": {"items": [{
            "entity_id": "automation.hall_light",
            "trigger": [{"entity_id": "binary_sensor.hall_motion"}],
            "action": [{"target": {"entity_id": "light.bedroom"}}],
        }]},
        "scripts.json": {"items": []},
    }

    result = await exporter.room_capabilities()
    rooms = {room["display_name"]: room for room in result["rooms"]}

    assert "light.bedroom" in [item["entity_id"] for item in rooms["Matt's Bedroom"]["capabilities"]["lights"]]
    assert "binary_sensor.hall_motion" in [item["entity_id"] for item in rooms["Upstairs Hall"]["capabilities"]["motion_sensors"]]
    assert "input_boolean.night_mode" in [item["entity_id"] for item in rooms["Matt's Bedroom"]["capabilities"]["helpers"]]
    assert "automation.hall_light" in [item["entity_id"] for item in rooms["Matt's Bedroom"]["capabilities"]["automations"]]
    assert "automation.hall_light" in [item["entity_id"] for item in rooms["Upstairs Hall"]["capabilities"]["automations"]]


def test_export_filenames_do_not_overwrite_same_minute(tmp_path: Path) -> None:
    exporter = CuratorExporter(FakeCuratorClient(), tmp_path)
    exporter.data = {"system.json": {"ok": True}}

    first = exporter._write_zip()
    second = exporter._write_zip()

    assert first.name.startswith("Curator_Report_")
    assert first != second
    assert first.exists()
    assert second.exists()
