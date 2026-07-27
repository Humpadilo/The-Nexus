"""Prepare the first bounded repair proposal without changing Home Assistant."""

from __future__ import annotations

from typing import Any


class EngineerProposalBuilder:
    """Build a reviewable proposal from one Raven diagnosis.

    Version one is deliberately limited to a single confirmed entity-reference
    replacement in UI-managed automation configuration.
    """

    def build_house_mode_proposal(self, diagnosis: dict[str, Any], configurations: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
        if diagnosis.get("target") != "input_select.house_mode":
            return None
        rename_findings = [
            finding for finding in diagnosis.get("findings", [])
            if finding.get("category") == "broken_reference" and finding.get("possible_rename")
        ]
        if not rename_findings:
            return None
        missing = str(rename_findings[0]["target"])
        replacement = str(rename_findings[0]["possible_rename"])
        if replacement not in diagnosis.get("evidence", {}).get("entity_ids", []) and replacement not in {
            edge.get("target") for edge in diagnosis.get("execution_paths", [])
        }:
            return None
        changes = []
        sources = []
        for edge in diagnosis.get("execution_paths", []):
            if edge.get("target") != missing or edge.get("relation") != "broken_reference":
                continue
            source = str(edge["source"])
            sources.append(source)
            changes.append({
                "object": source,
                "domain": source.partition(".")[0],
                "path": edge.get("path", []),
                "before": missing,
                "after": replacement,
                "configuration": configurations.get(source, {}),
            })
        if not changes:
            return None
        dependents = sorted({
            edge["source"] for edge in diagnosis.get("execution_paths", [])
            if edge.get("target") == diagnosis.get("target")
        })
        return {
            "schema_version": 1,
            "kind": "house_mode_entity_reference_repair",
            "status": "proposed",
            "lifecycle": "Restoration Proposed",
            "approval_state": "not_requested",
            "read_only": True,
            "target": diagnosis["target"],
            "investigation_id": diagnosis.get("investigation_id"),
            "finding_ids": [str(finding.get("finding_id")) for finding in rename_findings if finding.get("finding_id")],
            "addresses_finding_ids": [str(finding.get("finding_id")) for finding in rename_findings if finding.get("finding_id")],
            "specific_control": "House Mode control input_select.house_mode",
            "missing_reference": missing,
            "intended_entity": replacement,
            "why": "The replacement exists in the collected entity state, matches the missing entity's domain, and is the strongest evidence-backed rename candidate.",
            "configuration_sources": sorted(set(sources)),
            "dependent_objects": dependents,
            "proposed_changes": changes,
            "expected_effect": "House Mode automations that currently reference the missing media player will resolve the action target again.",
            "risks": ["The replacement may not be the intended speaker for every House Mode path.", "Changing an automation can alter its next execution after reload."],
            "rollback_plan": "Restore each before value at the recorded configuration path and reload the automation domain.",
            "confidence": "high",
            "evidence": {
                "snapshot_id": diagnosis["snapshot_id"],
                "diagnosis_id": diagnosis.get("diagnosis_id"),
                "root_cause": diagnosis.get("root_cause"),
                "finding_count": len(rename_findings),
                "read_only": True,
            },
            "application_record": None,
            "verification_result": None,
            "validation_steps": [
                "Confirm all proposed objects still exist before applying.",
                "Apply only the recorded entity-reference replacements.",
                "Reload the automation domain only.",
                "Run every House Mode automation and verify the selected action target responds.",
                "Collect a new snapshot and rerun Raven to confirm the broken reference is resolved.",
            ],
        }

    @staticmethod
    def apply_entity_replacements(configuration: dict[str, Any], changes: list[dict[str, Any]], *, rollback: bool = False) -> dict[str, Any]:
        """Return a changed copy after validating every recorded path."""
        import copy

        updated = copy.deepcopy(configuration)
        for change in changes:
            path = list(change["path"])
            expected = change["after"] if rollback else change["before"]
            replacement = change["before"] if rollback else change["after"]
            cursor: Any = updated
            for component in path[:-1]:
                cursor = cursor[int(component)] if isinstance(cursor, list) else cursor[component]
            last = path[-1]
            current = cursor[int(last)] if isinstance(cursor, list) else cursor[last]
            if current != expected:
                raise ValueError(f"repair path changed before application: {change['object']} {path}")
            if isinstance(cursor, list):
                cursor[int(last)] = replacement
            else:
                cursor[last] = replacement
        return updated
