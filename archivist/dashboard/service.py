"""Build compact, presentation-safe data for The Nexus Dashboard."""

from __future__ import annotations

from collections import Counter
from typing import Any

from archivist.storage.models import Snapshot


class DashboardBuilder:
    """Translate stored semantic facts and findings into dashboard sections."""

    def build(
        self,
        latest: dict[str, Any] | None,
        snapshots: list[Snapshot],
        findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        semantic = (latest or {}).get("semantic") or {}
        facts = semantic.get("facts") or []
        by_type: dict[str, list[dict[str, Any]]] = {}
        for fact in facts:
            by_type.setdefault(fact["fact_type"], []).append(fact)
        entities = by_type.get("entity", [])
        devices = by_type.get("device", [])
        areas = by_type.get("area", [])
        capabilities = by_type.get("capability", [])
        health = by_type.get("health", [])
        active = [f for f in findings if f["status"] == "active"]
        resolved = [f for f in findings if f["status"] == "resolved"]
        severity_counts = Counter(f["severity"] for f in active)
        health_counts = Counter(f["payload"].get("health_state", "available") for f in health)
        unavailable = health_counts.get("unavailable", 0)
        unknown = health_counts.get("unknown", 0)
        overall_health = "critical" if severity_counts["critical"] else "attention" if active else "healthy"
        if overall_health == "healthy":
            health_label = "The House Dreams Peacefully"
            health_message = f"{len(entities)} entities monitored · Everything responding normally"
        elif overall_health == "critical":
            health_label = "The Watchers Have Seen Something Unusual"
            health_message = f"{len(active)} active findings need review"
        else:
            health_label = "The House Dreams Restlessly"
            health_message = f"{len(active)} active finding{'s' if len(active) != 1 else ''} to review"
        timeline = [
            {
                "id": item.id,
                "captured_at": item.captured_at.isoformat(),
                "entities": item.total_entities,
                "unavailable": item.unavailable_entities,
                "unknown": item.unknown_entities,
                "headline": "House state captured",
                "summary": (
                    f"{item.total_entities} entities observed with "
                    f"{item.unavailable_entities} unavailable and {item.unknown_entities} unknown."
                ),
            }
            for item in snapshots
        ]
        return {
            "overview": {
                "health": overall_health,
                "health_label": health_label,
                "health_message": health_message,
                "snapshot": latest,
                "entities": len(entities),
                "devices": len(devices),
                "areas": len(areas),
                "active_findings": len(active),
                "resolved_findings": len(resolved),
                "unavailable": unavailable,
                "unknown": unknown,
                "latest_activity": (active + resolved)[:5],
            },
            "health": {
                "counts": dict(severity_counts),
                "states": dict(health_counts),
                "critical": [f for f in active if f["severity"] == "critical"][:20],
                "warning": [f for f in active if f["severity"] == "warning"][:30],
                "informational": [f for f in active if f["severity"] == "informational"][:20],
                "resolved": resolved[:20],
            },
            "explorer": {
                "areas": [f["payload"] for f in areas],
                "devices": [f["payload"] for f in devices],
                "capabilities": [f["payload"] for f in capabilities],
                "entities": [f["payload"] for f in entities],
            },
            "timeline": timeline,
            "reports": {
                "snapshot_id": latest.get("id") if latest else None,
                "finding_count": len(findings),
            },
        }
