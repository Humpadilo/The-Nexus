"""Collect states and optional registries, then persist a snapshot."""

from dataclasses import dataclass
from typing import Any

from archivist.api.home_assistant import HomeAssistantClient
from archivist.reports.summary import build_summary
from archivist.storage.database import Database
from archivist.storage.models import EntityObservation


@dataclass(frozen=True)
class CollectionResult:
    snapshot_id: int
    bundle: dict[str, Any]


class Collector:
    def __init__(self, client: HomeAssistantClient, database: Database) -> None:
        self.client, self.database = client, database

    async def run(self) -> CollectionResult:
        states = await self.client.get_states()
        registries = await self.client.get_registries()
        observations = [EntityObservation(s["entity_id"], str(s.get("state", "unknown")), s.get("attributes", {})) for s in states if s.get("entity_id")]
        snapshot_id = self.database.save_snapshot(build_summary(states), observations, registries)
        return CollectionResult(snapshot_id, self.database.get_snapshot(snapshot_id) or {})
