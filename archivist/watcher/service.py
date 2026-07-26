"""Explainable, low-noise comparison of stored snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import FindingCandidate

HEALTHY_STATES = {"on", "off"}
PROBLEM_STATES = {"unavailable", "unknown"}


class Watcher:
    """Compare two snapshot bundles without making Home Assistant changes."""

    def compare(
        self,
        previous: dict[str, Any] | None,
        current: dict[str, Any],
    ) -> list[FindingCandidate]:
        if previous is None:
            return []

        current_id = int(current["id"])
        previous_id = int(previous["id"])
        observed_at = datetime.fromisoformat(current["captured_at"])
        old_entities = {item["entity_id"]: item for item in previous.get("entities", [])}
        new_entities = {item["entity_id"]: item for item in current.get("entities", [])}
        expected = self._expected_entities(current)
        findings: list[FindingCandidate] = []

        for entity_id in sorted(set(old_entities) | set(new_entities)):
            old = old_entities.get(entity_id)
            new = new_entities.get(entity_id)
            if old is None and new is not None:
                findings.append(self._candidate(
                    "entity_added", entity_id, "Entity added", f"{entity_id} appeared in the latest snapshot.",
                    "info", "high", False, "active", current_id, observed_at, new, None, previous_id,
                ))
                continue
            if new is None and old is not None:
                findings.append(self._candidate(
                    "entity_removed", entity_id, "Entity removed", f"{entity_id} is absent from the latest snapshot.",
                    "warning", "high", entity_id in expected, "active", current_id, observed_at, None, old, previous_id,
                ))
                continue
            assert old is not None and new is not None
            old_state, new_state = str(old.get("state", "unknown")), str(new.get("state", "unknown"))
            is_expected = entity_id in expected

            if new_state in PROBLEM_STATES:
                category = "entity_unavailable" if new_state == "unavailable" else "entity_unknown"
                title = "Entity remains unavailable" if new_state == "unavailable" else "Entity remains unknown"
                findings.append(self._candidate(
                    category, entity_id, title,
                    f"{entity_id} is {new_state} in the latest snapshot.",
                    "info" if is_expected else "warning", "high", is_expected, "active",
                    current_id, observed_at, new, old, previous_id,
                ))
            elif old_state in PROBLEM_STATES:
                category = "entity_unavailable" if old_state == "unavailable" else "entity_unknown"
                title = "Entity recovered"
                findings.append(self._candidate(
                    category, entity_id, title,
                    f"{entity_id} recovered from {old_state} to {new_state}.",
                    "info", "high", is_expected, "resolved", current_id, observed_at, new, old, previous_id,
                ))

            old_battery, new_battery = self._battery(old), self._battery(new)
            if new_battery is not None and new_battery < 20:
                findings.append(self._candidate(
                    "low_battery", entity_id, "Low battery",
                    f"{entity_id} reports {new_battery:g}% battery.",
                    "warning", "medium", False, "active", current_id, observed_at, new, old, previous_id,
                ))
            elif old_battery is not None and old_battery < 20 and (new_battery is None or new_battery >= 20):
                findings.append(self._candidate(
                    "low_battery", entity_id, "Battery recovered",
                    f"{entity_id} no longer reports a low battery level.",
                    "info", "medium", False, "resolved", current_id, observed_at, new, old, previous_id,
                ))

            if entity_id.startswith("automation."):
                old_bad, new_bad = old_state in {"off", *PROBLEM_STATES}, new_state in {"off", *PROBLEM_STATES}
                if new_bad:
                    findings.append(self._candidate(
                        "automation_availability", entity_id, "Automation availability issue",
                        f"{entity_id} is {new_state}; automation availability may require attention.",
                        "info" if is_expected else "warning", "high", is_expected, "active",
                        current_id, observed_at, new, old, previous_id,
                    ))
                elif old_bad:
                    findings.append(self._candidate(
                        "automation_availability", entity_id, "Automation recovered",
                        f"{entity_id} returned to {new_state}.", "info", "high", is_expected, "resolved",
                        current_id, observed_at, new, old, previous_id,
                    ))

        return findings

    @staticmethod
    def _expected_entities(snapshot: dict[str, Any]) -> set[str]:
        expected: set[str] = set()
        for item in snapshot.get("registries", {}).get("entities", []):
            entity_id = item.get("entity_id")
            if entity_id and (item.get("disabled_by") or item.get("disabled")):
                expected.add(entity_id)
        return expected

    @staticmethod
    def _battery(item: dict[str, Any]) -> float | None:
        attributes = item.get("attributes", {})
        value = attributes.get("battery", attributes.get("battery_level"))
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _candidate(
        category: str,
        entity_id: str,
        title: str,
        description: str,
        severity: str,
        confidence: str,
        expected: bool,
        status: str,
        snapshot_id: int,
        observed_at: datetime,
        current: dict[str, Any] | None,
        previous: dict[str, Any] | None,
        previous_id: int,
    ) -> FindingCandidate:
        return FindingCandidate(
            fingerprint=f"{category}:{entity_id}", category=category, entity_id=entity_id,
            title=title, description=description, severity=severity, confidence=confidence,
            expected=expected, status=status, snapshot_id=snapshot_id, observed_at=observed_at,
            evidence={
                "current_snapshot_id": snapshot_id,
                "previous_snapshot_id": previous_id,
                "entity_id": entity_id,
                "current": current,
                "previous": previous,
            },
        )

