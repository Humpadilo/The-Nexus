import pytest

from archivist.collector.service import Collector
from archivist.storage.database import Database


class FakeClient:
    async def get_states(self):
        return [{"entity_id": "sensor.one", "state": "on", "attributes": {"battery_level": 10}}]

    async def get_registries(self):
        return {"entities": [{"id": "sensor.one"}], "devices": [], "areas": []}


@pytest.mark.asyncio
async def test_collector_persists_read_only_payload(tmp_path):
    result = await Collector(FakeClient(), Database(tmp_path / "test.db")).run()
    assert result.snapshot_id == 1
    assert result.bundle["summary"]["low_battery_entities"] == 1
    assert result.bundle["registries"]["entities"][0]["id"] == "sensor.one"
