"""Build evidence-backed diagnoses from snapshot and configuration evidence."""

from __future__ import annotations

import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any


# Home Assistant entity IDs have an alphabetic/underscore domain. Requiring
# that prefix prevents scene attribute keys such as ``14.1`` from becoming
# false entity references while still accepting normal IDs.
ENTITY_REFERENCE = re.compile(r"\b[a-z_][a-z0-9_]*\.[a-z0-9_]+\b")
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
            for reference, path in sorted(self._reference_locations(config)):
                references.append(self._edge(source, reference, entities, entity_registry, devices, snapshot["id"], path))

        incoming = defaultdict(list)
        for edge in references:
            incoming[edge["target"]].append(edge)
        relevant = self._relevant_sources(selected, incoming, configurations)
        scoped_edges = [edge for edge in references if edge["source"] in relevant or edge["target"] == selected]
        findings = self._findings(selected, entities, entity_registry, devices, scoped_edges, incoming, configurations, snapshot["id"])
        root_cause = self._root_cause(findings)
        findings = self._prioritize(findings)
        human = self._human_sections(selected, entities, configurations, findings, root_cause)
        diagnosis = human["diagnosis"]
        return {
            "schema_version": 1,
            "investigation_id": f"raven-{snapshot['id']}-{selected or 'unknown'}",
            "snapshot_id": snapshot["id"],
            "target": selected,
            "target_requested": target,
            "status": "diagnosed" if findings else "no_fault_found",
            "lifecycle": "Root Cause Identified" if root_cause else "Observed",
            "root_cause": root_cause,
            "diagnosis": diagnosis,
            "what_happened": human["what_happened"],
            "why_it_happened": human["why_it_happened"],
            "restoration_plan": human["restoration_plan"],
            "validation_steps": human["validation_steps"],
            "repair_recommendation": human["restoration_plan"][0] if human["restoration_plan"] else "Collect another snapshot before proposing restoration.",
            "findings": findings,
            "execution_paths": scoped_edges,
            "configuration_sources": sorted(configurations),
            "evidence": {
                "snapshot_id": snapshot["id"],
                "captured_at": snapshot.get("captured_at"),
                "configuration_entities": sorted(configurations),
                "entity_ids": sorted(entities),
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
    def _reference_locations(value: Any, path: tuple[str, ...] = ()) -> set[tuple[str, tuple[str, ...]]]:
        found: set[tuple[str, tuple[str, ...]]] = set()
        if isinstance(value, str):
            found.update((reference, path) for reference in ENTITY_REFERENCE.findall(value))
        elif isinstance(value, dict):
            for nested_key, nested in value.items():
                normalized_key = str(nested_key).lower()
                if normalized_key in {"service", "action"} and isinstance(nested, str):
                    continue
                if normalized_key in {"entity_id", "entity_ids"}:
                    found.update(RavenInvestigator._reference_locations(nested, path + (normalized_key,)))
                elif normalized_key not in {"service", "action"} or not isinstance(nested, str):
                    found.update(RavenInvestigator._reference_locations(nested, path + (normalized_key,)))
        elif isinstance(value, (list, tuple, set)):
            for index, nested in enumerate(value):
                found.update(RavenInvestigator._reference_locations(nested, path + (str(index),)))
        return found

    @staticmethod
    def _references(value: Any) -> set[str]:
        """Return entity references for compatibility with callers and tests."""
        return {reference for reference, _ in RavenInvestigator._reference_locations(value)}

    @staticmethod
    def _edge(source: str, target: str, entities: dict[str, dict[str, Any]], registry: dict[str, dict[str, Any]], devices: dict[str, dict[str, Any]], snapshot_id: int, path: tuple[str, ...]) -> dict[str, Any]:
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
            "path": list(path),
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
                findings.append({"category": "missing_area_assignment", "title": "Selected target has no area assignment", "target": selected, "description": "The selected object is not assigned to an area in the entity registry.", "severity": "informational", "confidence": "high", "evidence": {"snapshot_id": snapshot_id, "source": "entity_registry", "entity_id": selected}})
        return findings

    @staticmethod
    def _finding(category: str, title: str, target: str, description: str, severity: str, confidence: str, edge: dict[str, Any], snapshot_id: int, suggestion: str | None = None) -> dict[str, Any]:
        result = {"category": category, "title": title, "target": target, "description": description, "human_description": RavenInvestigator._human_finding(category, target, edge["source"]), "impact": RavenInvestigator._impact(category), "severity": severity, "confidence": confidence, "evidence": {"snapshot_id": snapshot_id, "source": edge["source"], "target": target, "path": edge.get("path", []), "provenance": edge["provenance"]}}
        if suggestion:
            result["possible_rename"] = suggestion
        return result

    @staticmethod
    def _human_finding(category: str, target: str, source: str) -> str:
        if category == "broken_reference":
            return f"{source} tries to use {target}, but that object is no longer available under that name."
        if category == "unavailable_dependency":
            return f"{source} depends on {target}, which is currently unavailable or unknown."
        return f"{source} has a dependency that needs review: {target}."

    @staticmethod
    def _impact(category: str) -> str:
        return {
            "broken_reference": "The affected automation path may stop before completing its action.",
            "unavailable_dependency": "The dependent behavior may be skipped or produce an incomplete result.",
            "target_unhealthy": "The selected control may not accept or expose the expected state.",
            "orphaned_helper": "The helper has no known dependent behavior in the collected evidence.",
            "missing_area_assignment": "The object is harder to locate in human-centered navigation.",
        }.get(category, "The effect should be confirmed against the related configuration.")

    @staticmethod
    def _prioritize(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        severity = {"critical": 0, "warning": 1, "informational": 2}
        confidence = {"high": 0, "medium": 1, "low": 2}
        category = {"broken_reference": 0, "target_unhealthy": 1, "unavailable_dependency": 2, "orphaned_helper": 3, "missing_area_assignment": 4}
        return sorted(findings, key=lambda item: (severity.get(item.get("severity"), 9), category.get(item.get("category"), 9), confidence.get(item.get("confidence"), 9), item.get("target", "")))

    @staticmethod
    def _human_sections(selected: str | None, entities: dict[str, dict[str, Any]], configurations: dict[str, dict[str, Any]], findings: list[dict[str, Any]], root_cause: dict[str, Any] | None) -> dict[str, Any]:
        target_name = selected or "the selected control"
        if not findings:
            happened = f"Raven observed {target_name}, but the available evidence does not show a current fault."
            return {"diagnosis": happened, "what_happened": happened, "why_it_happened": "No likely cause was established from the collected evidence.", "restoration_plan": [], "validation_steps": ["Collect another snapshot if the behavior still appears incorrect."]}
        happened = f"{target_name} has {len(findings)} evidence-backed issue(s) across {len(configurations)} related configuration source(s)."
        causes = "; ".join(finding.get("human_description", finding["description"]) for finding in findings[:5])
        plan = []
        if root_cause:
            if root_cause["category"] == "broken_reference":
                replacement = next((item.get("possible_rename") for item in findings if item.get("possible_rename")), None)
                plan.append(f"Replace the missing reference {root_cause['target']}" + (f" with {replacement} after confirming the match." if replacement else " after confirming the intended current object."))
            elif root_cause["category"] == "unavailable_dependency":
                plan.append(f"Restore or replace the unavailable dependency {root_cause['target']}, then retest the dependent behavior.")
            elif root_cause["category"] == "orphaned_helper":
                plan.append(f"Confirm whether {root_cause['target']} is intentionally unused before reconnecting or removing it.")
            else:
                plan.append("Review the selected object and its related configuration before making a change.")
        if len(findings) > 1:
            plan.append(f"Review the remaining {len(findings) - 1} related finding(s) in priority order before closing the investigation.")
        validation = ["Run the affected control and its dependent automations.", "Collect a fresh snapshot and rerun Raven.", "Confirm that the original finding is resolved and no higher-severity dependent finding remains."]
        return {"diagnosis": f"What happened: {happened} Why did it happen: {causes}", "what_happened": happened, "why_it_happened": causes, "restoration_plan": plan, "validation_steps": validation}

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
