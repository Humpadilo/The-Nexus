"""Derive an explainable summary from Home Assistant state payloads."""

from typing import Any


def build_summary(states: list[dict[str, Any]]) -> dict[str, int]:
    automations = [s for s in states if s.get("entity_id", "").startswith("automation.")]
    low_battery = [s for s in states if _battery_level(s) is not None and _battery_level(s) < 20]
    return {
        "total_entities": len(states),
        "unavailable_entities": sum(s.get("state") == "unavailable" for s in states),
        "unknown_entities": sum(s.get("state") == "unknown" for s in states),
        "disabled_or_unavailable_automations": sum(s.get("state") in {"off", "unavailable"} for s in automations),
        "low_battery_entities": len(low_battery),
    }


def _battery_level(state: dict[str, Any]) -> float | None:
    value = state.get("attributes", {}).get("battery")
    if value is None:
        value = state.get("attributes", {}).get("battery_level")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
