"""Build a portable, read-only Home Assistant intelligence export."""

from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from archivist.api.home_assistant import HomeAssistantApiError, HomeAssistantClient
from archivist.config import Settings

EXPORT_FILES = (
    "system.json", "areas.json", "devices.json", "entities.json", "helpers.json",
    "automations.json", "scripts.json", "scenes.json", "dashboards.json",
    "statistics.json", "history_summary.json", "integrations.json", "weather.json",
    "energy.json", "presence.json", "vacuum.json", "lighting.json", "media.json",
    "repairs.json", "logs_summary.json", "diagnostics.json", "capabilities.json",
    "config.json", "supervisor.json", "network.json", "services.json", "exposures.json",
    "blueprints.json", "traces.json", "recorder.json", "themes.json", "custom_components.json",
    "device_diagnostics.json", "ENTITY_RELATIONSHIPS.json", "SERVICE_CATALOG.json", "FEATURE_MATRIX.json",
    "CAPABILITIES.md", "KNOWLEDGE_GAPS.md", "AI_CONTEXT.md",
)


def _domain(entity_id: str) -> str:
    return entity_id.split(".", 1)[0] if "." in entity_id else ""


def _items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [dict(item, id=key) for key, item in value.items() if isinstance(item, dict)]
    return []


def _json(value: Any) -> Any:
    """Make API values safe for JSON, including occasional datetime values."""
    return json.loads(json.dumps(value, default=str))


class CuratorExporter:
    """Collect independent sections; a failed read never stops the package."""

    def __init__(self, client: HomeAssistantClient, output_dir: Path, runtime: dict[str, Any] | None = None) -> None:
        self.client = client
        self.output_dir = output_dir
        self.runtime = runtime or self._runtime_from_environment()
        self.states: list[dict[str, Any]] = []
        self.registries: dict[str, list[dict[str, Any]]] = {}
        self.config: dict[str, Any] = {}
        self.supervisor: dict[str, Any] = {}
        self.source_status: dict[str, dict[str, Any]] = {}
        self.data: dict[str, Any] = {}
        self.errors: list[dict[str, str]] = []

    async def run(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        await self._base_reads()
        sections: dict[str, Callable[[], Awaitable[Any]]] = {
            "system.json": self.system,
            "areas.json": self.areas,
            "devices.json": self.devices,
            "entities.json": self.entities,
            "helpers.json": self.helpers,
            "automations.json": lambda: self.configured("automation"),
            "scripts.json": lambda: self.configured("script"),
            "scenes.json": lambda: self.configured("scene"),
            "dashboards.json": self.dashboards,
            "statistics.json": self.statistics,
            "history_summary.json": self.history_summary,
            "integrations.json": self.integrations,
            "weather.json": self.weather,
            "energy.json": self.energy,
            "presence.json": self.presence,
            "vacuum.json": self.vacuum,
            "lighting.json": self.lighting,
            "media.json": self.media,
            "repairs.json": self.repairs,
            "logs_summary.json": self.logs_summary,
            "diagnostics.json": self.diagnostics,
            "capabilities.json": self.capabilities,
            "config.json": self.configuration,
            "supervisor.json": self.supervisor_info,
            "network.json": self.network,
            "services.json": self.services,
            "exposures.json": self.exposures,
            "blueprints.json": self.blueprints,
            "traces.json": self.traces,
            "recorder.json": self.recorder,
            "themes.json": self.themes,
            "custom_components.json": self.custom_components,
            "device_diagnostics.json": self.device_diagnostics,
            "ENTITY_RELATIONSHIPS.json": self.entity_relationships,
            "SERVICE_CATALOG.json": self.service_catalog,
            "FEATURE_MATRIX.json": self.feature_matrix,
        }
        for filename, collector in sections.items():
            try:
                self.data[filename] = _json(await collector())
            except Exception as exc:  # section isolation is a core export guarantee
                self.data[filename] = {"schema_version": 1, "available": False, "items": [], "error": str(exc)}
                self.errors.append({"section": filename, "error": str(exc)})
        self.data["errors.json"] = {"schema_version": 1, "runtime": self.runtime, "errors": self.errors}
        if isinstance(self.data.get("system.json"), dict):
            self.data["system.json"]["source_status"] = self.source_status
        self.data["summary.md"] = self.summary()
        self.data["CAPABILITIES.md"] = self.capabilities_report()
        self.data["KNOWLEDGE_GAPS.md"] = self.knowledge_gaps_report()
        self.data["AI_CONTEXT.md"] = self.ai_context_report()
        return self._write_zip()

    async def _base_reads(self) -> None:
        try:
            self.states = await self.client.get_states()
        except Exception as exc:
            self.errors.append({"section": "base.states", "error": str(exc)})
        try:
            self.registries = await self.client.get_registries()
        except Exception as exc:
            self.errors.append({"section": "base.registries", "error": str(exc)})
            self.registries = {}
        try:
            payload = await self.client.websocket_command("get_config")
            self.config = payload if isinstance(payload, dict) else {}
        except Exception as exc:
            self.errors.append({"section": "base.config", "error": str(exc)})
        try:
            payload = await self.client.get_json("config")
            if isinstance(payload, dict):
                self.config = {**self.config, **payload}
        except Exception as exc:
            self.errors.append({"section": "base.rest_config", "error": str(exc)})
        try:
            self.supervisor = await self.client.get_supervisor_json("supervisor/info")
        except Exception as exc:
            self._source_error("supervisor", exc)

    def _source_error(self, source: str, exc: Exception) -> dict[str, Any]:
        message = str(exc)
        self.source_status[source] = {"available": False, "error": message}
        self.errors.append({"section": source, "error": message})
        return {"available": False, "error": message}

    async def _optional_ws(self, source: str, command: str, **payload: Any) -> Any:
        try:
            result = await self.client.websocket_command(command, **payload)
            self.source_status[source] = {"available": True, "command": command}
            return result
        except Exception as exc:
            return self._source_error(source, exc)

    async def _optional_rest(self, source: str, path: str) -> Any:
        try:
            result = await self.client.get_json(path)
            self.source_status[source] = {"available": True, "path": path}
            return result
        except Exception as exc:
            return self._source_error(source, exc)

    def _state_map(self) -> dict[str, dict[str, Any]]:
        return {str(item.get("entity_id")): item for item in self.states if item.get("entity_id")}

    def _entity_registry(self) -> dict[str, dict[str, Any]]:
        return {str(item.get("entity_id")): item for item in self.registries.get("entities", []) if item.get("entity_id")}

    async def system(self) -> dict[str, Any]:
        return {"schema_version": 1, "available": True, "ha_version": self.config.get("version"),
                "supervisor_version": None, "os_version": None,
                "integration_count": len(self.config.get("components") or []),
                "device_count": len(self.registries.get("devices", [])),
                "entity_count": len(self.states), "area_count": len(self.registries.get("areas", [])),
                "automation_count": sum(_domain(str(s.get("entity_id"))) == "automation" for s in self.states),
                "script_count": sum(_domain(str(s.get("entity_id"))) == "script" for s in self.states),
                "scene_count": sum(_domain(str(s.get("entity_id"))) == "scene" for s in self.states),
                "dashboard_count": None, "read_only": True, "runtime": self.runtime,
                "supervisor": {"version": self.supervisor.get("version") if isinstance(self.supervisor, dict) else None},
                "source_status": self.source_status}

    @staticmethod
    def _runtime_from_environment() -> dict[str, Any]:
        import os

        addon = bool(os.getenv("SUPERVISOR_TOKEN") or os.getenv("SUPERVISOR_CORE_API") or Path("/data/options.json").exists())
        token_available = bool(os.getenv("SUPERVISOR_TOKEN"))
        return {"environment": "home_assistant_addon" if addon else "standalone",
                "home_assistant_api_source": "supervisor_core_proxy" if addon else "configured_or_default",
                "supervisor_token_available": token_available,
                "degraded": not (addon and token_available),
                "read_only": True}

    async def areas(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": self.registries.get("areas", []),
                "floors": self.registries.get("floors", []), "labels": self.registries.get("labels", [])}

    async def devices(self) -> dict[str, Any]:
        areas = {x.get("id"): x.get("name") for x in self.registries.get("areas", [])}
        items = []
        for item in self.registries.get("devices", []):
            copy = dict(item)
            copy["area"] = areas.get(item.get("area_id"))
            copy["integration"] = item.get("via_device_id") or item.get("config_entries") or item.get("connections")
            items.append(copy)
        return {"schema_version": 1, "items": items}

    async def entities(self) -> dict[str, Any]:
        devices = {x.get("id"): x for x in self.registries.get("devices", [])}
        areas = {x.get("id"): x.get("name") for x in self.registries.get("areas", [])}
        items = []
        state_map = self._state_map()
        for entity_id in sorted(set(state_map) | set(self._entity_registry())):
            state = state_map.get(entity_id, {})
            registry = self._entity_registry().get(entity_id, {})
            device = devices.get(registry.get("device_id"), {})
            items.append({"entity_id": entity_id, "friendly_name": (state.get("attributes") or {}).get("friendly_name"),
                          "current_state": state.get("state"), "attributes": state.get("attributes") or {},
                          "device": registry.get("device_id"), "area": areas.get(registry.get("area_id") or device.get("area_id")),
                          "domain": _domain(entity_id), "last_changed": state.get("last_changed"), "last_updated": state.get("last_updated"),
                          "registry": registry, "disabled_by": registry.get("disabled_by"), "hidden_by": registry.get("hidden_by"),
                          "entity_category": registry.get("entity_category")})
        return {"schema_version": 1, "items": items}

    async def helpers(self) -> dict[str, Any]:
        domains = {"input_boolean", "input_select", "input_number", "input_text", "input_datetime", "input_button", "timer", "counter", "schedule"}
        return {"schema_version": 1, "items": [s for s in self.states if _domain(str(s.get("entity_id"))) in domains]}

    async def configured(self, domain: str) -> dict[str, Any]:
        items = []
        for state in self.states:
            entity_id = str(state.get("entity_id"))
            if _domain(entity_id) != domain:
                continue
            config = dict(state.get("attributes") or {})
            object_id = str(config.get("id") or entity_id.split(".", 1)[-1])
            try:
                config = await self.client.get_configuration(domain, object_id)
            except HomeAssistantApiError:
                pass
            items.append({"entity_id": entity_id, "enabled": state.get("state") != "off", **config})
        return {"schema_version": 1, "items": items}

    async def dashboards(self) -> dict[str, Any]:
        dashboards = await self._optional_ws("dashboards", "lovelace/dashboards")
        configs = {"default": await self._optional_ws("dashboard.default", "lovelace/config")}
        for dashboard in _items(dashboards):
            url_path = dashboard.get("url_path") or dashboard.get("id")
            if url_path:
                configs[str(url_path)] = await self._optional_ws(f"dashboard:{url_path}", "lovelace/config", url_path=url_path)
        return {"schema_version": 1, "panels": await self._optional_ws("panels", "get_panels"),
                "dashboards": dashboards, "configs": configs,
                "resources": await self._optional_ws("dashboard.resources", "lovelace/resources")}

    async def statistics(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": await self.client.websocket_command("recorder/get_statistics_metadata")}

    async def history_summary(self) -> dict[str, Any]:
        return {"schema_version": 1, "available": False, "first_recorded_date": None, "latest_recorded_date": None,
                "available_statistics": len(self.data.get("statistics.json", {}).get("items", [])),
                "recorder_status": "not queried; no recorder history exported"}

    async def integrations(self) -> dict[str, Any]:
        domains = Counter(_domain(str(s.get("entity_id"))) for s in self.states)
        components = sorted(self.config.get("components") or domains)
        return {"schema_version": 1, "items": [{"integration": name, "version": None,
            "device_count": sum(name in (d.get("config_entries") or []) for d in self.registries.get("devices", [])),
            "entity_count": domains.get(name, 0)} for name in components]}

    async def weather(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": [s for s in self.states if _domain(str(s.get("entity_id"))) == "weather"]}

    async def energy(self) -> dict[str, Any]:
        try:
            prefs = await self.client.websocket_command("energy/get_prefs")
        except Exception as exc:
            prefs = {"available": False, "error": str(exc)}
        return {"schema_version": 1, "dashboard": prefs,
                "entities": [s for s in self.states if any(term in str(s.get("entity_id")).lower() for term in ("energy", "power", "solar"))]}

    async def presence(self) -> dict[str, Any]:
        return {"schema_version": 1, "persons": [s for s in self.states if _domain(str(s.get("entity_id"))) == "person"],
                "device_trackers": [s for s in self.states if _domain(str(s.get("entity_id"))) == "device_tracker"],
                "zones": [s for s in self.states if _domain(str(s.get("entity_id"))) == "zone"],
                "presence_sensors": [s for s in self.states if _domain(str(s.get("entity_id"))) in {"binary_sensor", "sensor"} and any(x in str(s.get("entity_id")).lower() for x in ("presence", "occupancy", "motion"))]}

    async def vacuum(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": [s for s in self.states if _domain(str(s.get("entity_id"))) == "vacuum"]}

    async def lighting(self) -> dict[str, Any]:
        return {"schema_version": 1, "groups": [s for s in self.states if _domain(str(s.get("entity_id"))) == "group"],
                "lights": [s for s in self.states if _domain(str(s.get("entity_id"))) == "light"],
                "adaptive_lighting": [s for s in self.states if "adaptive_lighting" in str(s.get("entity_id"))]}

    async def media(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": [s for s in self.states if _domain(str(s.get("entity_id"))) == "media_player"],
                "brands": {brand: [s.get("entity_id") for s in self.states if brand in json.dumps(s).lower()] for brand in ("apple_tv", "roku", "homepod")}}

    async def repairs(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": await self.client.websocket_command("repairs/list")}

    async def logs_summary(self) -> dict[str, Any]:
        try:
            text = await self.client.get_text("error_log")
            lines = [line for line in text.splitlines() if line.strip()]
            levels = Counter("error" if "error" in line.lower() or "exception" in line.lower() else "warning" if "warn" in line.lower() else "other" for line in lines)
            return {"schema_version": 1, "available": True, "line_count": len(lines), "levels": levels,
                    "recent_line_count": min(50, len(lines)), "note": "Only counts are exported; raw logs are omitted."}
        except Exception as exc:
            return {"schema_version": 1, "available": False, "note": "Large Home Assistant logs are intentionally not exported.", "error": str(exc)}

    async def diagnostics(self) -> dict[str, Any]:
        registry = self._entity_registry()
        unavailable = [s for s in self.states if s.get("state") in {"unavailable", "unknown"}]
        disabled = [e for e in registry.values() if e.get("disabled_by")]
        return {"schema_version": 1, "configuration_problems": [], "missing_entities": [],
                "unavailable_entities": [s.get("entity_id") for s in unavailable],
                "disabled_entities": [e.get("entity_id") for e in disabled],
                "system_health": await self._optional_ws("system_health", "system_health/info")}

    async def capabilities(self) -> dict[str, Any]:
        """Preserve every state-level capability signal exposed by integrations."""
        capability_keys = {
            "supported_features", "supported_color_modes", "effect_list", "fan_modes", "hvac_modes",
            "preset_modes", "swing_modes", "source_list", "sound_mode_list", "media_content_type",
            "available_commands", "options", "modes", "water_modes", "mop_modes", "cleaning_mode",
        }
        items = []
        for state in self.states:
            attributes = state.get("attributes") or {}
            selected = {key: attributes[key] for key in capability_keys if key in attributes}
            if selected:
                items.append({"entity_id": state.get("entity_id"), "domain": _domain(str(state.get("entity_id"))), **selected})
        return {"schema_version": 1, "items": items}

    async def configuration(self) -> dict[str, Any]:
        entries = await self._optional_ws("config_entries", "config_entries/get")
        return {"schema_version": 1, "home_assistant_config": self.config, "config_entries": entries,
                "components": self.config.get("components", []), "location": {
                    key: self.config.get(key) for key in ("location_name", "latitude", "longitude", "elevation", "time_zone", "unit_system") if key in self.config}}

    async def supervisor_info(self) -> dict[str, Any]:
        result: dict[str, Any] = {"schema_version": 1, "supervisor": self.supervisor}
        for name, path in (("addons", "addons"), ("core", "core/info"), ("host", "host/info"), ("os", "os/info"), ("network", "network/info")):
            result[name] = await self._optional_supervisor(name, path)
        return result

    async def _optional_supervisor(self, source: str, path: str) -> Any:
        try:
            value = await self.client.get_supervisor_json(path)
            self.source_status[source] = {"available": True, "path": path}
            return value
        except Exception as exc:
            return self._source_error(source, exc)

    async def network(self) -> dict[str, Any]:
        integrations = {name: [s.get("entity_id") for s in self.states if name in str(s.get("entity_id", ""))]
                        for name in ("matter", "thread", "bluetooth", "zha", "zwave", "wifi", "smartthings", "homekit", "mqtt")}
        return {"schema_version": 1, "supervisor_network": await self._optional_supervisor("network", "network/info"),
                "integration_entities": integrations}

    async def services(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": await self._optional_ws("services", "get_services")}

    async def exposures(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": await self._optional_ws("exposures", "homeassistant/expose_entity/list")}

    async def blueprints(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": await self._optional_ws("blueprints", "blueprint/list")}

    async def traces(self) -> dict[str, Any]:
        items = []
        for state in self.states:
            entity_id = str(state.get("entity_id", ""))
            if _domain(entity_id) != "automation":
                continue
            object_id = entity_id.split(".", 1)[-1]
            trace = await self._optional_ws(f"trace:{entity_id}", "trace/list", domain="automation", item_id=object_id)
            items.append({"entity_id": entity_id, "traces": trace})
        return {"schema_version": 1, "items": items, "note": "Trace retention is controlled by Home Assistant."}

    async def recorder(self) -> dict[str, Any]:
        return {"schema_version": 1,
                "statistics_metadata": await self._optional_ws("recorder.metadata", "recorder/get_statistics_metadata"),
                "statistic_ids": await self._optional_ws("recorder.ids", "recorder/list_statistic_ids"),
                "recorder_info": await self._optional_ws("recorder.info", "recorder/info"),
                "history_policy": "No unbounded recorder history is exported."}

    async def themes(self) -> dict[str, Any]:
        return {"schema_version": 1, "items": await self._optional_ws("themes", "frontend/get_themes")}

    async def custom_components(self) -> dict[str, Any]:
        components = self.config.get("components") or []
        custom = sorted(name for name in components if "." in str(name) or str(name).startswith(("hacs", "custom")))
        hacs_states = [s for s in self.states if "hacs" in str(s.get("entity_id", "")).lower()]
        return {"schema_version": 1, "identified_from_loaded_components": custom,
                "hacs_entities": hacs_states,
                "note": "Home Assistant Core does not expose a universal custom-component or HACS repository registry over the standard API."}

    async def device_diagnostics(self) -> dict[str, Any]:
        device_ids = {d.get("id") for d in self.registries.get("devices", [])}
        entity_registry = self._entity_registry()
        unavailable_devices = []
        for device_id in device_ids:
            entity_ids = [e_id for e_id, entry in entity_registry.items() if entry.get("device_id") == device_id]
            states = [s for s in self.states if s.get("entity_id") in entity_ids]
            if states and all(s.get("state") in {"unavailable", "unknown"} for s in states):
                unavailable_devices.append(device_id)
        return {"schema_version": 1, "unavailable_devices": unavailable_devices,
                "diagnostic_entities": [e_id for e_id, entry in entity_registry.items() if entry.get("entity_category") == "diagnostic"],
                "note": "Integration-specific diagnostic payloads are not universally available through the Core API."}

    async def entity_relationships(self) -> dict[str, Any]:
        known = {str(s.get("entity_id")) for s in self.states if s.get("entity_id")}
        relationships = []
        for state in self.states:
            source = str(state.get("entity_id"))
            references = self._references(state.get("attributes") or {})
            for target in sorted(references & known):
                if source != target:
                    relationships.append({"source": source, "target": target, "relation": "attribute_reference"})
        for device_id, device in ((d.get("id"), d) for d in self.registries.get("devices", [])):
            entity_ids = [e_id for e_id, entry in self._entity_registry().items() if entry.get("device_id") == device_id]
            for entity_id in entity_ids:
                relationships.append({"source": device_id, "target": entity_id, "relation": "device_contains"})
        return {"schema_version": 1, "items": relationships}

    @staticmethod
    def _references(value: Any) -> set[str]:
        import re

        found: set[str] = set()
        if isinstance(value, str):
            found.update(re.findall(r"\b[a-z0-9_]+\.[a-z0-9_]+\b", value))
        elif isinstance(value, dict):
            for nested in value.values():
                found.update(CuratorExporter._references(nested))
        elif isinstance(value, (list, tuple, set)):
            for nested in value:
                found.update(CuratorExporter._references(nested))
        return found

    async def service_catalog(self) -> dict[str, Any]:
        return await self.services()

    async def feature_matrix(self) -> dict[str, Any]:
        matrix: dict[str, dict[str, Any]] = {}
        for state in self.states:
            domain = _domain(str(state.get("entity_id")))
            attributes = state.get("attributes") or {}
            entry = matrix.setdefault(domain, {"entity_count": 0, "supported_features": set(), "attribute_keys": set()})
            entry["entity_count"] += 1
            if attributes.get("supported_features") is not None:
                entry["supported_features"].add(attributes["supported_features"])
            entry["attribute_keys"].update(attributes.keys())
        return {"schema_version": 1, "items": [{"domain": domain, "entity_count": value["entity_count"],
            "supported_features": sorted(value["supported_features"], key=str), "attribute_keys": sorted(value["attribute_keys"])}
            for domain, value in sorted(matrix.items())]}

    def capabilities_report(self) -> str:
        matrix = self.data.get("FEATURE_MATRIX.json", {}).get("items", [])
        return "\n".join(["# Capabilities", "", "The current snapshot exposes these domain-level capabilities and attribute surfaces:", "",
            *[f"- **{item['domain']}**: {item['entity_count']} entities; attributes: {', '.join(item['attribute_keys']) or 'none'}" for item in matrix], "",
            "Capability details are preserved in `capabilities.json`, `services.json`, and `feature_matrix.json`."])

    def knowledge_gaps_report(self) -> str:
        gaps = ["Recorder event history is intentionally bounded and not exported wholesale.",
                "Integration-specific diagnostics require integration-specific endpoints and may not be exposed.",
                "HACS repositories and custom-component files have no universal standard Core API endpoint.",
                "Unavailable entities, devices, and failed sources are listed in diagnostics and errors."]
        return "\n".join(["# Knowledge Gaps", "", *[f"- {gap}" for gap in gaps]])

    def ai_context_report(self) -> str:
        system = self.data.get("system.json", {})
        return "\n".join(["# AI Context", "", "This is a read-only point-in-time intelligence package for ChatGPT.", "",
            f"Home Assistant version: {system.get('ha_version') or 'unknown'}.",
            f"The snapshot contains {system.get('entity_count', 0)} entities, {system.get('device_count', 0)} devices, and {system.get('area_count', 0)} areas.",
            "Use entities and registries as primary evidence; use relationships, automations, services, capabilities, and diagnostics to infer behavior.",
            "Missing or unavailable sections are evidence gaps, not proof that a feature does not exist."])

    def summary(self) -> str:
        system = self.data.get("system.json", {})
        counts = {name.removesuffix(".json"): len(payload.get("items", [])) if isinstance(payload, dict) and isinstance(payload.get("items"), list) else None for name, payload in self.data.items() if name.endswith(".json")}
        largest = sorted(((k, v) for k, v in counts.items() if v is not None), key=lambda x: x[1], reverse=True)[:5]
        findings = [f"- {name}: {value}" for name, value in largest]
        future = [
            "Supervisor add-on update/install history and backup inventory",
            "Integration-specific diagnostics payloads and repair flow details",
            "HACS repository metadata and custom component file manifests",
            "Automation trace execution details and failure trend aggregation",
            "Bounded recorder history, event, and logbook summaries",
            "Network topology for Matter, Thread, Bluetooth, Zigbee, Z-Wave, Wi-Fi, HomeKit, and MQTT",
            "Dashboard screenshots, card rendering results, and custom-card resource metadata",
            "Per-device firmware update history, diagnostics, and integration-specific capability schemas",
            "Occupancy, energy, climate, maintenance, and behavior trends over time",
        ]
        return "\n".join(["# Curator Intelligence Export", "", "## System Overview", "",
            f"- Home Assistant: {system.get('ha_version', 'unknown')}", f"- Entities: {system.get('entity_count', 0)}",
            f"- Devices: {system.get('device_count', 0)}", f"- Areas: {system.get('area_count', 0)}", "- Read-only: yes", "",
            "## Interesting findings", "", "- Review unavailable entities and vacuum attributes first.", "",
            "## Potential issues", "", f"- Sections with collection errors: {len(self.errors)}", "",
            "## Counts", "", *findings, "", "## Recommendations", "", "- Use the JSON files as the source of truth for ChatGPT analysis.",
            "- Treat unavailable fields as unknown rather than as evidence that the feature is absent.", "", "## Potential Future Exports", "",
            *[f"- {item}" for item in future], "", "## Version", "", "Curator export schema version 2."])

    def _write_zip(self) -> Path:
        timestamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H%M")
        archive = self.output_dir / f"Curator_Report_{timestamp}.zip"
        with tempfile.TemporaryDirectory(prefix="curator-") as staging:
            root = Path(staging)
            for filename, payload in self.data.items():
                path = root / filename
                path.write_text(payload if isinstance(payload, str) else json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for path in sorted(root.iterdir()):
                    bundle.write(path, path.name)
        return archive


async def create_export(settings: Settings | None = None, output_dir: Path | None = None) -> Path:
    settings = settings or Settings()
    target = output_dir or settings.curator_export_dir
    runtime = {"environment": settings.runtime_environment,
               "home_assistant_api_source": "supervisor_core_proxy" if settings.runtime_environment == "home_assistant_addon" else "configured_or_default",
               "supervisor_token_available": bool(settings.supervisor_token),
               "degraded": not bool(settings.supervisor_token), "read_only": True}
    return await CuratorExporter(HomeAssistantClient(settings.ha_rest_url, settings.ha_ws_url, settings.supervisor_token), target, runtime).run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a read-only Curator intelligence ZIP export")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    print(asyncio.run(create_export(output_dir=args.output_dir)))


if __name__ == "__main__":
    main()
