"""Build deterministic, dashboard-oriented facts from raw snapshot data."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from .models import SemanticFact, SemanticProjection


class SemanticBuilder:
    """Translate one stored snapshot into a rebuildable semantic projection."""

    def build(self, snapshot: dict[str, Any]) -> SemanticProjection:
        snapshot_id = int(snapshot["id"])
        registries = snapshot.get("registries") or {}
        entity_registry = {
            entity_id: entry
            for entry in registries.get("entities", [])
            if (entity_id := self._entity_id(entry))
        }
        device_registry = {
            str(entry["id"]): entry
            for entry in registries.get("devices", [])
            if entry.get("id")
        }
        area_registry = {
            str(entry.get("area_id") or entry.get("id")): entry
            for entry in registries.get("areas", [])
            if entry.get("area_id") or entry.get("id")
        }

        observations = {
            str(entity["entity_id"]): entity
            for entity in snapshot.get("entities", [])
            if entity.get("entity_id")
        }
        entity_ids_by_device: dict[str, list[str]] = defaultdict(list)
        entity_ids_by_area: dict[str, list[str]] = defaultdict(list)
        facts: list[SemanticFact] = []

        for entity_id in sorted(observations):
            observation = observations[entity_id]
            registry = entity_registry.get(entity_id, {})
            device_id = self._optional_string(registry.get("device_id"))
            area_id = self._optional_string(registry.get("area_id"))
            if device_id:
                entity_ids_by_device[device_id].append(entity_id)
            if area_id:
                entity_ids_by_area[area_id].append(entity_id)

            attributes = observation.get("attributes") or {}
            state = str(observation.get("state", "unknown"))
            domain, object_id = self._split_entity_id(entity_id)
            disabled_by = registry.get("disabled_by") or registry.get("disabled")
            display_name = (
                attributes.get("friendly_name")
                or registry.get("name")
                or object_id.replace("_", " ").title()
            )
            common = {
                "entity_id": entity_id,
                "domain": domain,
                "object_id": object_id,
                "display_name": str(display_name),
                "state": state,
                "availability": self._availability(state),
                "device_id": device_id,
                "area_id": area_id,
                "disabled": bool(disabled_by),
                "device_class": attributes.get("device_class"),
                "unit_of_measurement": attributes.get("unit_of_measurement"),
                "icon": attributes.get("icon"),
            }
            facts.append(
                SemanticFact(
                    "entity",
                    entity_id,
                    common,
                    self._provenance(snapshot_id, "entity_observation", entity_id, registry),
                    "high" if registry else "medium",
                )
            )
            facts.append(
                SemanticFact(
                    "health",
                    entity_id,
                    self._health_payload(state, attributes, bool(disabled_by)),
                    self._provenance(snapshot_id, "entity_observation", entity_id, registry),
                    "high" if registry else "medium",
                )
            )
            facts.append(
                SemanticFact(
                    "capability",
                    entity_id,
                    self._capability_payload(domain, attributes),
                    self._provenance(snapshot_id, "entity_observation", entity_id, registry),
                    "high" if attributes else "medium",
                )
            )

        for device_id in sorted(device_registry):
            device = device_registry[device_id]
            facts.append(
                SemanticFact(
                    "device",
                    device_id,
                    {
                        "device_id": device_id,
                        "display_name": str(device.get("name") or device.get("model") or device_id),
                        "manufacturer": device.get("manufacturer"),
                        "model": device.get("model"),
                        "area_id": self._optional_string(device.get("area_id")),
                        "entity_ids": sorted(entity_ids_by_device.get(device_id, [])),
                    },
                    self._provenance(snapshot_id, "device_registry", device_id),
                    "high",
                )
            )

        for area_id in sorted(area_registry):
            area = area_registry[area_id]
            facts.append(
                SemanticFact(
                    "area",
                    area_id,
                    {
                        "area_id": area_id,
                        "display_name": str(area.get("name") or area_id),
                        "aliases": area.get("aliases") or [],
                        "floor_id": area.get("floor_id"),
                        "entity_ids": sorted(entity_ids_by_area.get(area_id, [])),
                    },
                    self._provenance(snapshot_id, "area_registry", area_id),
                    "high",
                )
            )

        summary = self._summary(facts)
        return SemanticProjection(snapshot_id, datetime.now(UTC), summary, tuple(facts))

    @staticmethod
    def _entity_id(entry: dict[str, Any]) -> str | None:
        value = entry.get("entity_id") or entry.get("id")
        return str(value) if value else None

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        return str(value) if value else None

    @staticmethod
    def _split_entity_id(entity_id: str) -> tuple[str, str]:
        domain, separator, object_id = entity_id.partition(".")
        return (domain, object_id) if separator else ("unknown", entity_id)

    @staticmethod
    def _availability(state: str) -> str:
        if state == "unavailable":
            return "unavailable"
        if state == "unknown":
            return "unknown"
        return "available"

    @staticmethod
    def _health_payload(state: str, attributes: dict[str, Any], disabled: bool) -> dict[str, Any]:
        battery = attributes.get("battery", attributes.get("battery_level"))
        try:
            battery = float(battery) if battery is not None else None
        except (TypeError, ValueError):
            battery = None
        health_state = "disabled" if disabled else SemanticBuilder._availability(state)
        if battery is not None and battery < 20:
            health_state = "low_battery"
        return {
            "state": state,
            "availability": SemanticBuilder._availability(state),
            "health_state": health_state,
            "expected": disabled,
            "battery_level": battery,
        }

    @staticmethod
    def _capability_payload(domain: str, attributes: dict[str, Any]) -> dict[str, Any]:
        capabilities = ["state"]
        if attributes.get("supported_features") is not None:
            capabilities.append("supported_features")
        for key in ("battery", "battery_level", "temperature", "humidity", "energy", "power", "device_class"):
            if attributes.get(key) is not None and key not in capabilities:
                capabilities.append(key)
        return {"domain": domain, "capabilities": sorted(capabilities)}

    @staticmethod
    def _provenance(snapshot_id: int, source_type: str, source_id: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
        provenance: dict[str, Any] = {
            "snapshot_id": snapshot_id,
            "source_type": source_type,
            "source_id": source_id,
        }
        if registry:
            provenance["registry_present"] = True
        return provenance

    @staticmethod
    def _summary(facts: list[SemanticFact]) -> dict[str, Any]:
        entities = [fact for fact in facts if fact.fact_type == "entity"]
        health = [fact for fact in facts if fact.fact_type == "health"]
        domains = Counter(fact.payload["domain"] for fact in entities)
        availability = Counter(fact.payload["availability"] for fact in entities)
        health_states = Counter(fact.payload["health_state"] for fact in health)
        return {
            "entity_count": len(entities),
            "device_count": sum(fact.fact_type == "device" for fact in facts),
            "area_count": sum(fact.fact_type == "area" for fact in facts),
            "fact_count": len(facts),
            "domains": dict(sorted(domains.items())),
            "availability": dict(sorted(availability.items())),
            "health_states": dict(sorted(health_states.items())),
        }
