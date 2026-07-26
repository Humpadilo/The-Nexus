"""Small SQLite repository with no ORM dependency."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import EntityObservation, Snapshot


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at TEXT NOT NULL,
                    total_entities INTEGER NOT NULL,
                    unavailable_entities INTEGER NOT NULL,
                    unknown_entities INTEGER NOT NULL,
                    disabled_or_unavailable_automations INTEGER NOT NULL,
                    low_battery_entities INTEGER NOT NULL,
                    registries_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS entity_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
                    entity_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attributes_json TEXT NOT NULL
                );
            """)

    def save_snapshot(self, summary: dict[str, int], observations: list[EntityObservation], registries: dict[str, Any]) -> int:
        captured_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO snapshots
                (captured_at, total_entities, unavailable_entities, unknown_entities,
                 disabled_or_unavailable_automations, low_battery_entities, registries_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (captured_at, summary["total_entities"], summary["unavailable_entities"],
                 summary["unknown_entities"], summary["disabled_or_unavailable_automations"],
                 summary["low_battery_entities"], json.dumps(registries)),
            )
            snapshot_id = int(cursor.lastrowid)
            conn.executemany(
                "INSERT INTO entity_observations (snapshot_id, entity_id, state, attributes_json) VALUES (?, ?, ?, ?)",
                [(snapshot_id, o.entity_id, o.state, json.dumps(o.attributes)) for o in observations],
            )
        return snapshot_id

    def get_snapshot(self, snapshot_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)).fetchone()
            if row is None:
                return None
            observations = conn.execute(
                "SELECT entity_id, state, attributes_json FROM entity_observations WHERE snapshot_id = ? ORDER BY entity_id",
                (snapshot_id,),
            ).fetchall()
        return {
            "id": row["id"], "captured_at": row["captured_at"],
            "summary": {key: row[key] for key in ("total_entities", "unavailable_entities", "unknown_entities", "disabled_or_unavailable_automations", "low_battery_entities")},
            "registries": json.loads(row["registries_json"]),
            "entities": [{"entity_id": item["entity_id"], "state": item["state"], "attributes": json.loads(item["attributes_json"])} for item in observations],
        }

    def latest_snapshot(self) -> Snapshot | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return None
        return Snapshot(row["id"], datetime.fromisoformat(row["captured_at"]), row["total_entities"], row["unavailable_entities"], row["unknown_entities"], row["disabled_or_unavailable_automations"], row["low_battery_entities"])
