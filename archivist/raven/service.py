"""Build evidence-backed diagnoses from snapshot and configuration evidence."""

from __future__ import annotations

import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any


ENTITY_REFERENCE = re.compile(r"\b[a-z0-9_]+\.[a-z0-9_]+\b")
HELPER_DOMAINS = {"input_boolean", "input_button", "input_datetime", "input_number", "input_select", "input_text", "counter", "timer", "schedule", "group"}


class RavenInvestigator:
    """Perform deterministic, read-only investigations with explicit evidence."""

    def investigate(
        self,
        snapshot: dict[str, Any],
        configurations: dict[str, dict[str, Any]] | None = None,
        target: str | None = None,
    ) -> dict[str, Any]:
        configurations = configurations or {}
        entities = {str(item["entity_id"]): item for item in snapshot.get("entities", []) if item.get("entity_id")}
        registries = snapshot.get("registries") or {}
        entity_registry = {str(item.get("entity_id")): item for item in registries.get("entities", []) if item.get("entity_id")}
        devices = {str(item.get("id")): item for item in registries.get("devices", []) if item.get("id")}
        selected = self._select_target(target, entities)
        references: list[dict[str, Any]] = []
        for source, config in configurations.items():
            for reference in sorted(self._references(config)):
                references.append(self._edge(source, reference, entities, entity_registry, devices, snapshot["id"]))

        incoming = defaultdict(list)
        for edge in references:
            incoming[edge["target"]].append(edge)
        relevant = self._relevant_sources(selected, incoming, configurations)
        scoped_edges = [edge for edge in references if edge["source"] in relevant or edge["target"] == selected]
        findings = self._findings(selected, entities, entity_registry, devices, scoped_edges, incoming, configurations, snapshot["id"])
        root_cause = self._root_cause(findings)
        diagnosis = self._diagnosis(selected, entities, configurations, findings, root_cause)
        return {
            "schema_version": 1,
            "investigation_id": f"raven-{snapshot['id']}-{selected or 'unknown'}",
            "snapshot_id": snapshot["id"],
            "target": selected,
            "target_requested": target,
            "status": "diagnosed" if findings else "no_fault_found",
            "root_cause": root_cause,
            "diagnosis": diagnosis,
            "repair_recommendation": self._repair_recommendation(root_cause, findings),
            "findings": findings,
            "execution_paths": scoped_edges,
            "configuration_sources": sorted(configurations),
            "evidence": {
                "snapshot_id": snapshot["id"],
                "captured_at": snapshot.get("captured_at"),
                "configuration_entities": sorted(configurations),
                "read_only": True,
            },
        }

    @staticmethod
    def _select_target(target: str | None, entities: dict[str, dict[str, Any]]) -> str | None:
        if target and target in entities:
            return target
        if target and target.startswith("concept:"):
            term = target.removeprefix("concept:").replace("_", " ").lower()
            matches = [entity_id for entity_id, item in entities.items() if term in f"{entity_id} {(item.get('attributes') or {}).get('friendly_name', '')}".lower()]
            helper_domains = ("input_boolean.", "input_button.", "input_number.", "input_select.", "input_text.")
            matches.sort(key=lambda entity_id: (0 if any(entity_id.startswith(domain) for domain in helper_domains) else 1, entity_id))
            return matches[0] if matches else None
        if target:
            normalized = target.lower()
            matches = [entity_id for entity_id, item in entities.items() if normalized in f"{entity_id} {(item.get('attributes') or {}).get('friendly_name', '')}".lower()]
            return sorted(matches)[0] if matches else target
        candidates = [entity_id for entity_id, item in entities.items() if entity_id.startswith("input_select.") and "mode" in f"{entity_id} {(item.get('attributes') or {}).get('friendly_name', '')}".lower()]
        return sorted(candidates)[0] if candidates else None

    @staticmethod
    def _references(value: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(value, str):
            found.update(ENTITY_REFERENCE.findall(value))
        elif isinstance(value, dict):
            for nested in value.values():
                found.update(RavenInvestigator._references(nested))
        elif isinstance(value, (list, tuple, set)):
            for nested in value:
                found.update(RavenInvestigator._references(nested))
        return found

    @staticmethod
    def _edge(source: str, target: str, entities: dict[str, dict[str, Any]], registry: dict[str, dict[str, Any]], devices: dict[str, dict[str, Any]], snapshot_id: int) -> dict[str, Any]:
        if target in entities:
            state = entities[target].get("state", "unknown")
            relation = "references"
            health = "unavailable" if state == "unavailable" else "unknown" if state == "unknown" else "available"
        else:
            health = "missing"
            relation = "broken_reference"
        return {
            "source": source,
            "target": target,
            "relation": relation,
            "target_health": health,
            "confidence": "high" if target in entities else "high",
            "provenance": {"source_type": "raven_configuration", "source_id": source, "snapshot_id": snapshot_id},
        }

    @staticmethod
    def _relevant_sources(selected: str | None, incoming: dict[str, list[dict[str, Any]]], configurations: dict[str, dict[str, Any]]) -> set[str]:
        if not selected:
            return set(configurations)
        relevant = {edge["source"] for edge in incoming.get(selected, [])}
        return relevant or set(configurations)

    def _findings(self, selected: str | None, entities: dict[str, dict[str, Any]], registry: dict[str, dict[str, Any]], devices: dict[str, dict[str, Any]], edges: list[dict[str, Any]], incoming: dict[str, list[dict[str, Any]]], configurations: dict[str, dict[str, Any]], snapshot_id: int) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for edge in edges:
            if edge["relation"] == "broken_reference":
                suggestion = self._rename_suggestion(edge["target"], entities)
                findings.append(self._finding("broken_reference", "Broken reference", edge["target"], "A configuration references an entity that is not present in the collected state.", "critical", "high", edge, snapshot_id, suggestion))
            elif edge["target_health"] in {"unavailable", "unknown"}:
                findings.append(self._finding("unavailable_dependency", "Unavailable dependency", edge["target"], f"The dependency currently reports {edge['target_health']}.", "warning", "high", edge, snapshot_id))
        if selected and selected in entities:
            item = entities[selected]
            state = str(item.get("state", "unknown"))
            if state in {"unavailable", "unknown"}:
                findings.append({"category": "target_unhealthy", "title": "Selected target is not healthy", "target": selected, "description": f"The selected target reports {state} in snapshot {snapshot_id}.", "severity": "warning", "confidence": "high", "evidence": {"snapshot_id": snapshot_id, "entity_id": selected, "state": state}})
            if selected.startswith(tuple(HELPER_DOMAINS)) and not incoming.get(selected):
                findings.append({"category": "orphaned_helper", "title": "Helper has no known dependents", "target": selected, "description": "No collected automation, script, scene, or entity configuration references this helper.", "severity": "informational", "confidence": "medium", "evidence": {"snapshot_id": snapshot_id, "entity_id": selected}})
            if not (registry.get(selected) or {}).get("area_id"):
                findings.append({"category": "missing_area_assignment", "title": "Selected target has no area assignment", "target": selected, "description": "The selected object is not assigned to an area in the entity registry.", "severity": "informational", "confidence": "high", "evidence": {"snapshot_id": snapshot_id, "entity_id": selected}})
        return findings

    @staticmethod
    def _finding(category: str, title: str, target: str, description: str, severity: str, confidence: str, edge: dict[str, Any], snapshot_id: int, suggestion: str | None = None) -> dict[str, Any]:
        result = {"category": category, "title": title, "target": target, "description": description, "severity": severity, "confidence": confidence, "evidence": {"snapshot_id": snapshot_id, "source": edge["source"], "target": target, "provenance": edge["provenance"]}}
        if suggestion:
            result["possible_rename"] = suggestion
        return result

    @staticmethod
    def _rename_suggestion(target: str, entities: dict[str, dict[str, Any]]) -> str | None:
        domain, _, object_id = target.partition(".")
        candidates = [entity_id for entity_id in entities if entity_id.startswith(f"{domain}.")]
        if not candidates:
            return None
        best = max(candidates, key=lambda candidate: SequenceMatcher(None, object_id, candidate.partition(".")[2]).ratio())
        return best if SequenceMatcher(None, object_id, best.partition(".")[2]).ratio() >= 0.62 else None

    @staticmethod
    def _root_cause(findings: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not findings:
            return None
        priority = {"broken_reference": 0, "target_unhealthy": 1, "unavailable_dependency": 2, "orphaned_helper": 3, "missing_area_assignment": 4}
        return min(findings, key=lambda item: priority.get(item["category"], 9))

    @staticmethod
    def _diagnosis(selected: str | None, entities: dict[str, dict[str, Any]], configurations: dict[str, dict[str, Any]], findings: list[dict[str, Any]], root_cause: dict[str, Any] | None) -> str:
        if root_cause is None:
            return f"Raven found no evidence-backed fault for {selected or 'the requested target'} in the collected snapshot."
        affected = len(configurations)
        return f"Raven investigated {selected or 'the selected concept'} across {affected} configuration source(s) and found {root_cause['title'].lower()}. {root_cause['description']}"

    @staticmethod
    def _repair_recommendation(root_cause: dict[str, Any] | None, findings: list[dict[str, Any]]) -> str:
        if root_cause is None:
            return "No repair is recommended from the available evidence. Collect another snapshot or select a more specific target."
        if root_cause["category"] == "broken_reference":
            return "Review the referencing configuration and replace the missing reference only after confirming the intended current entity."
        if root_cause["category"] == "unavailable_dependency":
            return "Restore or replace the unavailable dependency, then confirm the dependent configuration recovers."
        if root_cause["category"] == "orphaned_helper":
            return "Confirm whether the helper is intentionally unused before removing or reconnecting it."
        return "Review the evidence and related configuration before making any change."
