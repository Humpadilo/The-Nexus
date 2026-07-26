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
        return {
            "overview": {
                "health": "critical" if severity_counts["critical"] else "attention" if active else "healthy",
                "snapshot": latest,
                "entities": len(entities),
                "devices": len(devices),
                "areas": len(areas),
                "active_findings": len(active),
                "resolved_findings": len(resolved),
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
            "timeline": [
                {"id": item.id, "captured_at": item.captured_at.isoformat(),
                 "entities": item.total_entities, "unavailable": item.unavailable_entities,
                 "unknown": item.unknown_entities}
                for item in snapshots
            ],
            "reports": {
                "snapshot_id": latest.get("id") if latest else None,
                "finding_count": len(findings),
            },
        }
