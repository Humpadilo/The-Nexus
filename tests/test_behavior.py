from datetime import datetime, timezone

import pytest

from archivist.api.home_assistant import HomeAssistantClient
from archivist.api.home_assistant import HomeAssistantApiError
from archivist.behavior.service import BehaviorHistoryService
from archivist.config import Settings


class FakeBehaviorClient:
    def __init__(self, *, fail_history=False, real_history_shape=False):
        self.fail_history = fail_history
        self.real_history_shape = real_history_shape
        self.calls = []

    async def get_states(self):
        return [
            {"entity_id": "binary_sensor.kitchen_motion", "attributes": {"device_class": "motion"}},
            {"entity_id": "binary_sensor.den_occupancy", "attributes": {"device_class": "occupancy"}},
            {"entity_id": "person.alice", "attributes": {}},
            {"entity_id": "light.kitchen", "attributes": {}},
            {"entity_id": "media_player.den", "attributes": {}},
            {"entity_id": "sensor.temperature", "attributes": {"device_class": "temperature"}},
        ]

    async def get_registries(self):
        return {"entities": [
            {"entity_id": "binary_sensor.kitchen_motion", "area_id": "kitchen"},
            {"entity_id": "binary_sensor.den_occupancy", "area_id": "den"},
            {"entity_id": "light.kitchen", "area_id": "kitchen"},
        ], "areas": [{"area_id": "kitchen", "name": "Kitchen"}, {"area_id": "den", "name": "Den"}]}

    async def get_history(self, start, *, end=None, entity_ids=None):
        self.calls.append((start, end, entity_ids))
        if self.fail_history:
            raise RuntimeError("history unavailable")
        if self.real_history_shape:
            return [
                [
                    {"entity_id": "binary_sensor.kitchen_motion", "state": "on", "last_changed": "2026-01-01T08:00:00+00:00"},
                    {"entity_id": "binary_sensor.kitchen_motion", "state": "off", "last_changed": "2026-01-01T08:02:00+00:00"},
                ],
                [
                    {"entity_id": "person.alice", "state": "home", "last_changed": "2026-01-01T08:03:00+00:00"},
                ],
            ]
        return [
            {"entity_id": "binary_sensor.kitchen_motion", "states": [{"state": "on", "last_changed": "2026-01-01T08:00:00+00:00"}]},
            {"entity_id": "binary_sensor.den_occupancy", "states": [{"state": "on", "last_changed": "2026-01-01T08:10:00+00:00"}]},
            {"entity_id": "light.kitchen", "states": [{"state": "on", "last_changed": "2026-01-01T08:05:00+00:00"}]},
        ]

    async def get_logbook(self, start, *, end=None, entity_ids=None):
        return [{"name": "Kitchen light", "context_user_id": "user-1", "message": "Bearer should not be exported", "token": "secret"}]


def test_discovery_uses_states_and_registry_without_hardcoded_ids():
    selected = BehaviorHistoryService.discover_entities([
        {"entity_id": "binary_sensor.office_motion", "attributes": {"device_class": "motion"}},
        {"entity_id": "person.someone", "attributes": {}},
        {"entity_id": "light.office", "attributes": {}},
    ], {"entities": [{"entity_id": "binary_sensor.office_motion", "area_id": "office"}]})
    assert {item["kind"] for item in selected.values()} == {"motion", "presence", "light"}


@pytest.mark.asyncio
async def test_history_is_chunked_limited_and_report_is_secret_safe():
    client = FakeBehaviorClient()
    service = BehaviorHistoryService(client, days=2, max_events=100, chunk_hours=99)
    report = await service.run(end=datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert len(client.calls) == 2  # 24-hour chunks, not one unbounded request
    assert report["metadata"]["limits"]["chunk_hours"] == 24
    assert report["metadata"]["requested_days"] == 2
    assert report["transitions"][0]["from"] == "Kitchen"
    assert report["transitions"][0]["to"] == "Den"
    assert report["likely_room_paths"][0]["transition_count"] == 1
    assert report["likely_room_paths"][0]["confidence"] == "low"
    assert report["light_changes_relative_to_motion"][0]["within_15_minutes_of_motion"] is True
    assert report["aggregates"]["events_by_kind_and_hour"]["motion"]["8"] == 4
    assert report["manual_corrections"]["entries_with_user_context"][0]["token"] == "[REDACTED]"
    assert "Bearer should not be exported" not in str(report)


@pytest.mark.asyncio
async def test_real_home_assistant_history_shape_is_analyzed():
    report = await BehaviorHistoryService(FakeBehaviorClient(real_history_shape=True), days=1).run(
        end=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )
    assert report["metadata"]["history_event_count"] == 3
    assert report["aggregates"]["events_by_entity"]["binary_sensor.kitchen_motion"] == 2
    assert report["aggregates"]["arrival_patterns"][0]["entity_id"] == "person.alice"


def test_compact_grouped_history_inherits_group_entity_id():
    selected = {
        "binary_sensor.kitchen_motion": {
            "entity_id": "binary_sensor.kitchen_motion",
            "kind": "motion",
            "area_id": "kitchen",
        }
    }
    report = BehaviorHistoryService.analyze(
        [
            [
                {"entity_id": "binary_sensor.kitchen_motion", "state": "off", "last_changed": "2026-01-01T08:00:00+00:00"},
                {"state": "on", "last_changed": "2026-01-01T08:01:00+00:00"},
            ]
        ],
        [],
        selected,
        {"areas": [{"area_id": "kitchen", "name": "Kitchen"}]},
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert report["metadata"]["history_event_count"] == 2
    assert report["aggregates"]["events_by_entity"]["binary_sensor.kitchen_motion"] == 2


@pytest.mark.asyncio
async def test_history_failure_is_reported_without_failing_whole_export():
    report = await BehaviorHistoryService(FakeBehaviorClient(fail_history=True), days=1).run(
        end=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )
    assert report["event_timeline"] == []
    assert any(error["source"] == "history" for error in report["errors"])


@pytest.mark.asyncio
async def test_no_discovered_entities_skips_unfiltered_history_reads():
    class EmptyDiscoveryClient(FakeBehaviorClient):
        async def get_states(self):
            return [{"entity_id": "sensor.temperature", "attributes": {"device_class": "temperature"}}]

        async def get_history(self, start, *, end=None, entity_ids=None):
            raise AssertionError("history should not be called without discovered behavior entities")

        async def get_logbook(self, start, *, end=None, entity_ids=None):
            raise AssertionError("logbook should not be called without discovered behavior entities")

    report = await BehaviorHistoryService(EmptyDiscoveryClient(), days=1).run(
        end=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )

    assert report["event_timeline"] == []
    assert report["metadata"]["api_chunks"] == 0
    assert any(error["source"] == "discovery" for error in report["errors"])


def test_behavior_settings_are_bounded(tmp_path):
    settings = Settings(
        data_dir=tmp_path,
        behavior_history_days=365,
        behavior_history_max_events=999999,
        behavior_history_max_entities=999,
        behavior_history_chunk_hours=99,
    )

    assert settings.behavior_history_days == 90
    assert settings.behavior_history_max_events == 100000
    assert settings.behavior_history_max_entities == 500
    assert settings.behavior_history_chunk_hours == 24


@pytest.mark.asyncio
async def test_history_client_uses_official_bounded_rest_paths():
    client = HomeAssistantClient("http://ha/api", "ws://ha/ws", "token")
    calls = []

    async def fake_get_json(path):
        calls.append(path)
        return []

    client.get_json = fake_get_json
    await client.get_history("2026-01-01T00:00:00+00:00", end="2026-01-02T00:00:00+00:00", entity_ids=["light.kitchen"])
    await client.get_logbook("2026-01-01T00:00:00+00:00", end="2026-01-02T00:00:00+00:00", entity_ids=["light.kitchen"])
    assert calls[0].startswith("/history/period/")
    assert "filter_entity_id=light.kitchen" in calls[0]
    assert calls[1].startswith("/logbook/")
    assert "entity=light.kitchen" in calls[1]


@pytest.mark.asyncio
async def test_history_client_refuses_unfiltered_reads():
    client = HomeAssistantClient("http://ha/api", "ws://ha/ws", "token")

    with pytest.raises(HomeAssistantApiError, match="unfiltered history"):
        await client.get_history("2026-01-01T00:00:00+00:00", entity_ids=[])

    with pytest.raises(HomeAssistantApiError, match="unfiltered logbook"):
        await client.get_logbook("2026-01-01T00:00:00+00:00", entity_ids=None)
