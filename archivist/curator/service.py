"""Build a human-oriented organization projection from semantic evidence."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable


HELPER_DOMAINS = {
    "counter",
    "group",
    "input_boolean",
    "input_button",
    "input_datetime",
    "input_number",
    "input_select",
    "input_text",
    "schedule",
    "timer",
}
SYSTEM_DOMAINS = {"automation", "script", "scene"}
CONCEPT_RULES: dict[str, tuple[str, ...]] = {
    "arrival": ("arrival", "arrive", "presence", "person", "home"),
    "departure": ("departure", "depart", "away", "leav", "presence"),
    "sleep": ("sleep", "bed", "bedroom", "night", "wake"),
    "guests": ("guest", "visitor"),
    "security": ("alarm", "lock", "door", "window", "camera", "motion", "security"),
    "lighting": ("light", "lamp", "brightness", "switch"),
    "climate": ("climate", "thermostat", "temperature", "humidity", "heating", "cooling", "fan"),
    "entertainment": ("media", "tv", "speaker", "music", "movie", "cast"),
    "energy": ("energy", "power", "battery", "solar", "grid"),
    "pets": ("pet", "dog", "cat"),
}
ENTITY_REFERENCE = re.compile(r"\b[a-z0-9_]+\.[a-z0-9_]+\b")


class CuratorBuilder:
    """Build a deterministic, evidence-backed human organization projection."""

    def build(self, latest: dict[str, Any] | None, findings: list[dict[str, Any]]) -> dict[str, Any]:
        semantic = (latest or {}).get("semantic") or {}
        facts = semantic.get("facts") or []
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for fact in facts:
            by_type[str(fact.get("fact_type"))].append(fact)

        health_by_entity = {
            fact["subject_id"]: fact.get("payload", {})
            for fact in by_type["health"]
        }
        raw_attributes = {
            str(item["entity_id"]): item.get("attributes") or {}
            for item in (latest or {}).get("entities", [])
            if item.get("entity_id")
        }
        devices = {
            fact["subject_id"]: self._device(fact)
            for fact in by_type["device"]
        }
        entities = [
            self._entity(
                fact,
                health_by_entity.get(fact["subject_id"], {}),
                devices,
                raw_attributes.get(fact["subject_id"], {}),
            )
            for fact in by_type["entity"]
        ]
        relationships = self._relationships(entities)
        reverse_relationships: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for relationship in relationships:
            reverse_relationships[relationship["target"]].append(relationship)

        areas = self._areas(by_type["area"], entities, devices)
        concepts = self._concepts(entities)
        curator_findings = self._actionable_findings(
            findings, entities, reverse_relationships
        )
        organization_cues = self._organization_cues(entities, latest)
        return {
            "schema_version": 1,
            "snapshot_id": latest.get("id") if latest else None,
            "source": "semantic_projection",
            "summary": {
                "area_count": len(areas),
                "entity_count": len(entities),
                "device_count": len(devices),
                "relationship_count": len(relationships),
                "concept_count": len(concepts),
                "finding_count": len(curator_findings),
                "organization_cue_count": len(organization_cues),
            },
            "areas": areas,
            "concepts": concepts,
            "relationships": relationships,
            "findings": curator_findings,
            "organization_cues": organization_cues,
        }

    @staticmethod
    def _device(fact: dict[str, Any]) -> dict[str, Any]:
        payload = fact.get("payload", {})
        return {
            "device_id": fact["subject_id"],
            "display_name": payload.get("display_name", fact["subject_id"]),
            "area_id": payload.get("area_id"),
            "entity_ids": list(payload.get("entity_ids") or []),
            "manufacturer": payload.get("manufacturer"),
            "model": payload.get("model"),
            "provenance": fact.get("provenance", {}),
            "confidence": fact.get("confidence", "medium"),
        }

    @staticmethod
    def _entity(
        fact: dict[str, Any],
        health: dict[str, Any],
        devices: dict[str, dict[str, Any]],
        attributes: dict[str, Any],
    ) -> dict[str, Any]:
        payload = fact.get("payload", {})
        device_id = payload.get("device_id")
        area_id = payload.get("area_id")
        if not area_id and device_id in devices:
            area_id = devices[device_id].get("area_id")
        domain = str(payload.get("domain", "unknown"))
        return {
            "entity_id": fact["subject_id"],
            "display_name": payload.get("display_name", fact["subject_id"]),
            "domain": domain,
            "area_id": area_id,
            "device_id": device_id,
            "state": payload.get("state", "unknown"),
            "availability": payload.get("availability", "unknown"),
            "health_state": health.get("health_state", payload.get("availability", "unknown")),
            "category": CuratorBuilder._category(domain),
            "provenance": fact.get("provenance", {}),
            "confidence": fact.get("confidence", "medium"),
            "attributes": attributes,
            "references": sorted(CuratorBuilder._references(attributes)),
        }

    @staticmethod
    def _category(domain: str) -> str:
        if domain in HELPER_DOMAINS:
            return "helpers"
        if domain in SYSTEM_DOMAINS:
            return f"{domain}s" if domain != "scene" else "scenes"
        return "entities"

    @staticmethod
    def _references(attributes: dict[str, Any]) -> set[str]:
        references: set[str] = set()

        def visit(value: Any) -> None:
            if isinstance(value, str):
                references.update(ENTITY_REFERENCE.findall(value))
            elif isinstance(value, dict):
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, (list, tuple, set)):
                for nested in value:
                    visit(nested)

        visit(attributes)
        return references

    @staticmethod
    def _areas(
        area_facts: Iterable[dict[str, Any]],
        entities: list[dict[str, Any]],
        devices: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        areas: dict[str, dict[str, Any]] = {}
        for fact in area_facts:
            payload = fact.get("payload", {})
            area_id = str(fact["subject_id"])
            areas[area_id] = {
                "area_id": area_id,
                "display_name": payload.get("display_name", area_id),
                "entity_ids": [],
                "device_ids": [],
                "categories": {},
                "provenance": fact.get("provenance", {}),
            }
        unassigned = {
            "area_id": None,
            "display_name": "Unassigned",
            "entity_ids": [],
            "device_ids": [],
            "categories": {},
            "provenance": {"source_type": "curator_organization", "source_id": "unassigned"},
        }
        for entity in entities:
            area = areas.get(entity.get("area_id")) if entity.get("area_id") else None
            target = area or unassigned
            target["entity_ids"].append(entity["entity_id"])
            category = entity["category"]
            target["categories"][category] = target["categories"].get(category, 0) + 1
        for device in devices.values():
            area = areas.get(device.get("area_id")) if device.get("area_id") else None
            (area or unassigned)["device_ids"].append(device["device_id"])
        if unassigned["entity_ids"] or unassigned["device_ids"]:
            areas["__unassigned__"] = unassigned
        for area in areas.values():
            area["entity_ids"].sort()
            area["device_ids"].sort()
        return sorted(areas.values(), key=lambda area: (area["area_id"] is None, area["display_name"].lower()))

    @staticmethod
    def _concepts(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        concepts: list[dict[str, Any]] = []
        for name, terms in CONCEPT_RULES.items():
            members = [
                entity for entity in entities
                if any(term in f"{entity['entity_id']} {entity['display_name']} {entity['domain']}".lower() for term in terms)
            ]
            if members:
                concepts.append({
                    "concept_id": name,
                    "display_name": name.replace("_", " ").title(),
                    "entity_ids": [entity["entity_id"] for entity in members],
                    "area_ids": sorted({entity["area_id"] for entity in members if entity.get("area_id")}),
                    "confidence": "medium",
                    "basis": "deterministic label and domain matching",
                })
        return concepts

    @staticmethod
    def _relationships(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        known = {entity["entity_id"] for entity in entities}
        relationships: list[dict[str, Any]] = []
        for entity in entities:
            for target in entity["references"]:
                if target in known and target != entity["entity_id"]:
                    relationships.append({
                        "source": entity["entity_id"],
                        "target": target,
                        "relation": "references",
                        "confidence": "medium",
                        "provenance": entity["provenance"],
                    })
        return sorted(relationships, key=lambda item: (item["source"], item["target"]))

    @staticmethod
    def _actionable_findings(
        findings: list[dict[str, Any]],
        entities: list[dict[str, Any]],
        reverse_relationships: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        known = {entity["entity_id"] for entity in entities}
        actionable: list[dict[str, Any]] = []
        for finding in findings:
            entity_id = finding.get("entity_id")
            dependencies = [item["source"] for item in reverse_relationships.get(entity_id, [])]
            category = finding.get("category", "observation")
            cause, impact, repair = {
                "entity_unavailable": (
                    "The entity did not report a usable state in the latest snapshot.",
                    "Dependents may not receive current state.",
                    "Check the related device or integration before changing configuration.",
                ),
                "entity_unknown": (
                    "Home Assistant reported an unknown state.",
                    "Automations relying on this value may behave unexpectedly.",
                    "Inspect the source entity and its dependents; do not repair automatically.",
                ),
                "low_battery": (
                    "The latest observation reports a low battery level.",
                    "The device may stop reporting soon.",
                    "Check the device battery and confirm the entity recovers after replacement.",
                ),
                "automation_availability": (
                    "The automation is off, unavailable, or unknown in the latest observation.",
                    "Its dependent entities may not be updated by that automation.",
                    "Review the automation and referenced objects before making a change.",
                ),
            }.get(category, (
                "The Watcher recorded a change in the latest comparison.",
                "The affected object may have changed behavior or availability.",
                "Review the evidence and related objects before making a change.",
            ))
            actionable.append({
                "finding_id": finding.get("id"),
                "category": category,
                "title": finding.get("title"),
                "status": finding.get("status"),
                "severity": finding.get("severity"),
                "confidence": finding.get("confidence"),
                "entity_id": entity_id,
                "likely_cause": cause,
                "impact": impact,
                "recommended_repair": repair,
                "dependencies": sorted(set(dependencies)),
                "evidence": finding.get("evidence", {}),
                "provenance": {
                    "source_type": "watcher_finding",
                    "source_id": str(finding.get("id") or finding.get("fingerprint")),
                    "snapshot_id": finding.get("last_snapshot_id"),
                },
                "entity_known": entity_id in known if entity_id else False,
            })
        return actionable

    @staticmethod
    def _organization_cues(entities: list[dict[str, Any]], latest: dict[str, Any] | None) -> list[dict[str, Any]]:
        cues: list[dict[str, Any]] = []
        for entity in entities:
            if not entity.get("area_id"):
                cues.append({
                    "category": "missing_area_assignment",
                    "title": "Entity is not assigned to an area",
                    "entity_id": entity["entity_id"],
                    "severity": "informational",
                    "confidence": entity["confidence"],
                    "recommended_repair": "Assign an area in Home Assistant if this object belongs to a known room.",
                    "evidence": {"snapshot_id": (latest or {}).get("id"), "entity_id": entity["entity_id"]},
                    "provenance": entity["provenance"],
                })
        return cues
