"""Read-only behavior history export for Home Assistant evidence."""

from __future__ import annotations

import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from archivist.api.home_assistant import HomeAssistantClient
from archivist.config import Settings

SECRET_KEY_RE = re.compile(r"(token|secret|password|api[_-]?key|authorization|bearer)", re.IGNORECASE)
BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
SECRET_VALUE_RE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]+|eyJ[A-Za-z0-9._-]+)\b")


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not isinstance(value, str):
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if SECRET_KEY_RE.search(str(key)):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        cleaned = BEARER_RE.sub("[REDACTED]", value)
        return SECRET_VALUE_RE.sub("[REDACTED]", cleaned)
    return value


def _domain(entity_id: str) -> str:
    return entity_id.split(".", 1)[0] if "." in entity_id else ""


def _friendly_area(area_id: str | None, areas: dict[str, str]) -> str | None:
    if not area_id:
        return None
    return areas.get(area_id, area_id.replace("_", " ").title())


@dataclass(frozen=True)
class BehaviorHistoryExporter:
    """Write a behavior report as a small ChatGPT-friendly ZIP."""

    output_dir: Path

    def write(self, report: dict[str, Any], generated_at: datetime | None = None) -> Path:
        generated_at = generated_at or datetime.now(UTC)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        archive = self.output_dir / f"Behavior_History_{generated_at.strftime('%Y-%m-%d_%H%M%S')}.zip"
        counter = 1
        while archive.exists():
            archive = self.output_dir / (
                f"Behavior_History_{generated_at.strftime('%Y-%m-%d_%H%M%S')}_{counter}.zip"
            )
            counter += 1
        payload = json.dumps(_redact(report), indent=2, sort_keys=True)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("behavior_report.json", payload)
            bundle.writestr(
                "README.txt",
                "Read-only Home Assistant behavior history evidence. "
                "This report is bounded, redacted, and does not modify Home Assistant.\n",
            )
        return archive


class BehaviorHistoryService:
    """Collect bounded Home Assistant history/logbook evidence and summarize it."""

    BEHAVIOR_DOMAINS = {"person", "device_tracker", "light", "media_player"}
    MOTION_CLASSES = {"motion", "occupancy", "presence"}

    def __init__(
        self,
        client: Any,
        *,
        days: int = 30,
        max_events: int = 20000,
        max_entities: int = 150,
        chunk_hours: int = 24,
    ) -> None:
        self.client = client
        self.days = max(1, min(90, int(days)))
        self.max_events = max(100, min(100000, int(max_events)))
        self.max_entities = max(1, min(500, int(max_entities)))
        self.chunk_hours = max(1, min(24, int(chunk_hours)))

    @staticmethod
    def discover_entities(states: list[dict[str, Any]], registries: dict[str, Any]) -> dict[str, dict[str, Any]]:
        areas = {
            str(area.get("area_id")): str(area.get("name") or area.get("area_id"))
            for area in registries.get("areas", [])
            if area.get("area_id")
        }
        registry_entities = {
            str(item.get("entity_id")): item
            for item in registries.get("entities", [])
            if item.get("entity_id")
        }
        selected: dict[str, dict[str, Any]] = {}
        for state in states:
            entity_id = str(state.get("entity_id") or "")
            if not entity_id or "." not in entity_id:
                continue
            attributes = state.get("attributes") or {}
            domain = _domain(entity_id)
            device_class = str(attributes.get("device_class") or "").lower()
            kind: str | None = None
            if domain == "binary_sensor" and device_class in BehaviorHistoryService.MOTION_CLASSES:
                kind = "motion"
            elif domain in {"person", "device_tracker"}:
                kind = "presence"
            elif domain == "light":
                kind = "light"
            elif domain == "media_player":
                kind = "media"
            if kind is None:
                continue
            registry = registry_entities.get(entity_id, {})
            area_id = registry.get("area_id") or attributes.get("area_id")
            selected[entity_id] = {
                "entity_id": entity_id,
                "domain": domain,
                "kind": kind,
                "device_class": device_class or None,
                "area_id": area_id,
                "area_name": _friendly_area(str(area_id) if area_id else None, areas),
                "name": attributes.get("friendly_name") or entity_id,
            }
        return selected

    @classmethod
    def analyze(
        cls,
        raw_history: Any,
        logbook_entries: list[dict[str, Any]],
        selected: dict[str, dict[str, Any]],
        registries: dict[str, Any],
        start: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        areas = {
            str(area.get("area_id")): str(area.get("name") or area.get("area_id"))
            for area in registries.get("areas", [])
            if area.get("area_id")
        }
        discovered = {entity_id: dict(info) for entity_id, info in selected.items()}
        for entity_id, info in discovered.items():
            info.setdefault("entity_id", entity_id)
            info.setdefault("area_name", _friendly_area(info.get("area_id"), areas))
        service = cls(client=None)
        rows = [
            event
            for event in service._normalize_history(raw_history)
            if event.get("entity_id") in discovered
        ]
        return service._build_report(
            start,
            end,
            discovered,
            rows,
            logbook_entries,
            [],
            api_chunks=0,
        )

    async def run(self, *, end: datetime | None = None) -> dict[str, Any]:
        finished_at = end or datetime.now(UTC)
        if finished_at.tzinfo is None:
            finished_at = finished_at.replace(tzinfo=UTC)
        started_at = finished_at - timedelta(days=self.days)
        errors: list[dict[str, Any]] = []
        states: list[dict[str, Any]] = []
        registries: dict[str, Any] = {}

        try:
            states = await self.client.get_states()
        except Exception as exc:  # noqa: BLE001 - report generation must degrade gracefully.
            errors.append({"source": "states", "error": str(exc)})
        try:
            registries = await self.client.get_registries()
        except Exception as exc:  # noqa: BLE001
            errors.append({"source": "registries", "error": str(exc)})

        discovered = self.discover_entities(states, registries)
        limited_entities = list(discovered)[: self.max_entities]
        if not limited_entities:
            errors.append({"source": "discovery", "error": "No behavior entities discovered; skipped history/logbook reads."})
            return self._build_report(
                started_at,
                finished_at,
                discovered,
                [],
                [],
                errors,
                api_chunks=0,
            )

        history_rows: list[dict[str, Any]] = []
        logbook_entries: list[dict[str, Any]] = []
        api_chunks = 0
        cursor = started_at
        while cursor < finished_at and len(history_rows) < self.max_events:
            chunk_end = min(cursor + timedelta(hours=self.chunk_hours), finished_at)
            api_chunks += 1
            try:
                raw_history = await self.client.get_history(
                    _iso(cursor),
                    end=_iso(chunk_end),
                    entity_ids=limited_entities,
                )
                for event in self._normalize_history(raw_history):
                    if event.get("entity_id") in discovered:
                        history_rows.append(event)
                    if len(history_rows) >= self.max_events:
                        break
            except Exception as exc:  # noqa: BLE001
                errors.append({"source": "history", "start": _iso(cursor), "end": _iso(chunk_end), "error": str(exc)})
            try:
                raw_logbook = await self.client.get_logbook(
                    _iso(cursor),
                    end=_iso(chunk_end),
                    entity_ids=limited_entities,
                )
                logbook_entries.extend(raw_logbook if isinstance(raw_logbook, list) else [])
            except Exception as exc:  # noqa: BLE001
                errors.append({"source": "logbook", "start": _iso(cursor), "end": _iso(chunk_end), "error": str(exc)})
            cursor = chunk_end

        return self._build_report(
            started_at,
            finished_at,
            discovered,
            history_rows[: self.max_events],
            logbook_entries,
            errors,
            api_chunks=api_chunks,
        )

    def _normalize_history(self, raw_history: Any) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        def add_event(entity_id: str | None, row: dict[str, Any]) -> None:
            if not entity_id:
                return
            timestamp = row.get("last_changed") or row.get("lc") or row.get("last_updated") or row.get("lu") or row.get("time_fired")
            normalized.append(
                {
                    "entity_id": entity_id,
                    "state": row.get("state", row.get("s")),
                    "last_changed": timestamp,
                    "attributes": row.get("attributes") or row.get("a") or {},
                }
            )

        def visit(item: Any, inherited_entity_id: str | None = None) -> None:
            if isinstance(item, list):
                group_entity_id = inherited_entity_id
                if group_entity_id is None:
                    for child in item:
                        if isinstance(child, dict) and child.get("entity_id"):
                            group_entity_id = str(child["entity_id"])
                            break
                for child in item:
                    visit(child, group_entity_id)
                return
            if not isinstance(item, dict):
                return
            entity_id = str(item.get("entity_id") or item.get("e") or inherited_entity_id or "")
            states = item.get("states")
            if isinstance(states, list):
                for child in states:
                    if isinstance(child, dict):
                        visit(child, entity_id)
                return
            if "state" in item or "s" in item:
                add_event(entity_id, item)

        visit(raw_history)
        normalized.sort(key=lambda event: event.get("last_changed") or "")
        return normalized

    def _build_report(
        self,
        start: datetime,
        end: datetime,
        discovered: dict[str, dict[str, Any]],
        history_rows: list[dict[str, Any]],
        logbook_entries: list[dict[str, Any]],
        errors: list[dict[str, Any]],
        *,
        api_chunks: int,
    ) -> dict[str, Any]:
        events = self._timeline(history_rows, discovered)
        aggregates = self._aggregates(events)
        transitions = self._transitions(events)
        likely_room_paths = self._likely_room_paths(transitions)
        light_changes = self._light_changes(events)
        manual_corrections = self._manual_corrections(logbook_entries)
        gaps = self._knowledge_gaps(discovered, events, errors)
        report = {
            "report_type": "archivist_behavior_history",
            "read_only": True,
            "metadata": {
                "generated_at": _iso(datetime.now(UTC)),
                "window_start": _iso(start),
                "window_end": _iso(end),
                "timezone": str(end.tzinfo or UTC),
                "requested_days": self.days,
                "history_event_count": len(events),
                "logbook_entry_count": len(logbook_entries),
                "discovered_entity_count": len(discovered),
                "included_entity_count": min(len(discovered), self.max_entities),
                "api_chunks": api_chunks,
                "limits": {
                    "days": self.days,
                    "max_events": self.max_events,
                    "max_entities": self.max_entities,
                    "chunk_hours": self.chunk_hours,
                },
            },
            "discovered_entities": discovered,
            "event_timeline": events,
            "aggregates": aggregates,
            "transitions": transitions,
            "likely_room_paths": likely_room_paths,
            "light_changes_relative_to_motion": light_changes,
            "manual_corrections": manual_corrections,
            "occupancy_windows": self._occupancy_windows(events),
            "knowledge_gaps": gaps,
            "errors": errors,
            "confidence": {
                "overall": "medium" if events and not errors else "low",
                "basis": "Bounded Home Assistant history/logbook samples; no conclusions are inferred without events.",
                "sample_sizes": {"history_events": len(events), "logbook_entries": len(logbook_entries)},
            },
        }
        return _redact(report)

    def _timeline(self, rows: list[dict[str, Any]], discovered: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = []
        for row in rows:
            entity_id = str(row.get("entity_id") or "")
            info = discovered.get(entity_id, {})
            timestamp = _parse_datetime(row.get("last_changed"))
            timeline.append(
                {
                    "timestamp": timestamp.isoformat() if timestamp else row.get("last_changed"),
                    "entity_id": entity_id,
                    "kind": info.get("kind", "unknown"),
                    "state": row.get("state"),
                    "area_id": info.get("area_id"),
                    "area_name": info.get("area_name"),
                    "name": info.get("name", entity_id),
                }
            )
        timeline.sort(key=lambda event: event.get("timestamp") or "")
        return timeline

    def _aggregates(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        by_entity: Counter[str] = Counter()
        by_kind_hour: dict[str, Counter[str]] = defaultdict(Counter)
        by_kind_day: dict[str, Counter[str]] = defaultdict(Counter)
        first_last: dict[str, dict[str, Any]] = {}
        arrivals: list[dict[str, Any]] = []
        for event in events:
            entity_id = event["entity_id"]
            kind = event["kind"]
            timestamp = _parse_datetime(event.get("timestamp"))
            by_entity[entity_id] += 1
            if timestamp:
                by_kind_hour[kind][str(timestamp.hour)] += 1
                by_kind_day[kind][timestamp.date().isoformat()] += 1
            first_last.setdefault(entity_id, {"entity_id": entity_id, "first": event.get("timestamp"), "last": event.get("timestamp"), "count": 0})
            first_last[entity_id]["last"] = event.get("timestamp")
            first_last[entity_id]["count"] += 1
            if kind == "presence" and event.get("state") in {"home", "on"}:
                arrivals.append({"entity_id": entity_id, "timestamp": event.get("timestamp"), "state": event.get("state")})
        return {
            "events_by_entity": dict(by_entity),
            "events_by_kind_and_hour": {kind: dict(counter) for kind, counter in by_kind_hour.items()},
            "events_by_kind_and_day": {kind: dict(counter) for kind, counter in by_kind_day.items()},
            "first_last_activity": list(first_last.values()),
            "arrival_patterns": arrivals,
        }

    def _transitions(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        motion = [
            event for event in events
            if event.get("kind") == "motion" and event.get("state") in {"on", "detected", "home"}
        ]
        transitions: list[dict[str, Any]] = []
        previous: dict[str, Any] | None = None
        for event in motion:
            if previous and previous.get("area_name") and event.get("area_name") and previous.get("area_name") != event.get("area_name"):
                start = _parse_datetime(previous.get("timestamp"))
                finish = _parse_datetime(event.get("timestamp"))
                transitions.append(
                    {
                        "from": previous.get("area_name"),
                        "to": event.get("area_name"),
                        "from_entity_id": previous.get("entity_id"),
                        "to_entity_id": event.get("entity_id"),
                        "started_at": previous.get("timestamp"),
                        "ended_at": event.get("timestamp"),
                        "seconds_between": int((finish - start).total_seconds()) if start and finish else None,
                        "confidence": "medium",
                    }
                )
            previous = event
        return transitions

    def _likely_room_paths(self, transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts: Counter[tuple[str, str]] = Counter()
        for transition in transitions:
            source = transition.get("from")
            target = transition.get("to")
            if source and target:
                counts[(str(source), str(target))] += 1
        paths = [
            {
                "from": source,
                "to": target,
                "transition_count": count,
                "confidence": "high" if count >= 10 else "medium" if count >= 5 else "low",
            }
            for (source, target), count in counts.items()
        ]
        paths.sort(key=lambda item: (-item["transition_count"], item["from"], item["to"]))
        return paths

    def _light_changes(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        motion_times = [
            _parse_datetime(event.get("timestamp"))
            for event in events
            if event.get("kind") == "motion" and event.get("state") in {"on", "detected"}
        ]
        motion_times = [item for item in motion_times if item is not None]
        changes: list[dict[str, Any]] = []
        for event in events:
            if event.get("kind") != "light":
                continue
            timestamp = _parse_datetime(event.get("timestamp"))
            nearby = False
            if timestamp:
                nearby = any(abs((timestamp - motion_time).total_seconds()) <= 900 for motion_time in motion_times)
            changes.append(
                {
                    "entity_id": event.get("entity_id"),
                    "timestamp": event.get("timestamp"),
                    "state": event.get("state"),
                    "area_name": event.get("area_name"),
                    "within_15_minutes_of_motion": nearby,
                    "confidence": "medium" if nearby else "low",
                }
            )
        return changes

    def _manual_corrections(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        supported = [
            _redact(entry)
            for entry in entries
            if isinstance(entry, dict) and (entry.get("context_user_id") or entry.get("user_id"))
        ]
        return {
            "supported": bool(supported),
            "basis": "Only logbook entries with user context are included as possible manual corrections.",
            "entries_with_user_context": supported[:100],
        }

    def _occupancy_windows(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        windows: list[dict[str, Any]] = []
        open_by_entity: dict[str, dict[str, Any]] = {}
        for event in events:
            if event.get("kind") != "motion":
                continue
            entity_id = str(event.get("entity_id"))
            if event.get("state") in {"on", "detected"}:
                open_by_entity[entity_id] = event
            elif event.get("state") in {"off", "clear"} and entity_id in open_by_entity:
                start = open_by_entity.pop(entity_id)
                started = _parse_datetime(start.get("timestamp"))
                ended = _parse_datetime(event.get("timestamp"))
                windows.append(
                    {
                        "entity_id": entity_id,
                        "area_name": event.get("area_name"),
                        "started_at": start.get("timestamp"),
                        "ended_at": event.get("timestamp"),
                        "duration_seconds": int((ended - started).total_seconds()) if started and ended else None,
                    }
                )
        return windows

    def _knowledge_gaps(
        self,
        discovered: dict[str, dict[str, Any]],
        events: list[dict[str, Any]],
        errors: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        if not discovered:
            gaps.append({"type": "discovery", "message": "No behavior entities were discovered from states/registries."})
        if discovered and not events:
            gaps.append({"type": "history", "message": "No history events were available for discovered behavior entities."})
        missing_area = [entity_id for entity_id, info in discovered.items() if not info.get("area_name")]
        if missing_area:
            gaps.append({"type": "areas", "message": "Some behavior entities have no area assignment.", "entity_ids": missing_area[:50]})
        if errors:
            gaps.append({"type": "api_errors", "message": "Some Home Assistant read-only APIs failed.", "count": len(errors)})
        return gaps


async def create_behavior_export(*, settings: Settings) -> Path:
    client = HomeAssistantClient(settings.ha_rest_url, settings.ha_ws_url, settings.supervisor_token)
    service = BehaviorHistoryService(
        client,
        days=settings.behavior_history_days,
        max_events=settings.behavior_history_max_events,
        max_entities=settings.behavior_history_max_entities,
        chunk_hours=settings.behavior_history_chunk_hours,
    )
    report = await service.run()
    return BehaviorHistoryExporter(settings.behavior_export_dir).write(report)
