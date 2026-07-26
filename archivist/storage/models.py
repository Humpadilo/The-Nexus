"""Typed storage records."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Snapshot:
    id: int
    captured_at: datetime
    total_entities: int
    unavailable_entities: int
    unknown_entities: int
    disabled_or_unavailable_automations: int
    low_battery_entities: int


@dataclass(frozen=True)
class EntityObservation:
    entity_id: str
    state: str
    attributes: dict
