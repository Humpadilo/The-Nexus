"""Collect states and optional registries, then persist a snapshot."""

from dataclasses import dataclass
from typing import Any

from archivist.api.home_assistant import HomeAssistantClient
from archivist.reports.summary import build_summary
from archivist.storage.database import Database
from archivist.storage.models import EntityObservation
from archivist.watcher.service import Watcher


@dataclass(frozen=True)
class CollectionResult:
    snapshot_id: int
    bundle: dict[str, Any]


class Collector:
    def __init__(self, client: HomeAssistantClient, database: Database) -> None:
        self.client, self.database, self.watcher = client, database, Watcher()

    async def run(self) -> CollectionResult:
        previous_meta = self.database.latest_snapshot()
        previous = self.database.get_snapshot(previous_meta.id) if previous_meta else None
        states = await self.client.get_states()
        registries = await self.client.get_registries()
        observations = [EntityObservation(s["entity_id"], str(s.get("state", "unknown")), s.get("attributes", {})) for s in states if s.get("entity_id")]
        snapshot_id = self.database.save_snapshot(build_summary(states), observations, registries)
        current = self.database.get_snapshot(snapshot_id) or {}
        findings = self.watcher.compare(previous, current)
        self.database.save_findings(findings)
        current = self.database.get_snapshot(snapshot_id) or current
        return CollectionResult(snapshot_id, current)
