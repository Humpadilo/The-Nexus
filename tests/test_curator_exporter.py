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


def test_export_filenames_do_not_overwrite_same_minute(tmp_path: Path) -> None:
    exporter = CuratorExporter(FakeCuratorClient(), tmp_path)
    exporter.data = {"system.json": {"ok": True}}

    first = exporter._write_zip()
    second = exporter._write_zip()

    assert first.name.startswith("Curator_Report_")
    assert first != second
    assert first.exists()
    assert second.exists()
