"""Small SQLite repository with no ORM dependency."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import EntityObservation, Snapshot
from archivist.semantic.models import SemanticProjection
from archivist.watcher.models import FindingCandidate


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
                CREATE TABLE IF NOT EXISTS watcher_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    entity_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    expected INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    resolved_at TEXT,
                    occurrence_count INTEGER NOT NULL DEFAULT 1,
                    first_snapshot_id INTEGER NOT NULL,
                    last_snapshot_id INTEGER NOT NULL,
                    evidence_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_watcher_status ON watcher_findings(status);
                CREATE INDEX IF NOT EXISTS idx_watcher_last_seen ON watcher_findings(last_seen);
                CREATE TABLE IF NOT EXISTS semantic_projections (
                    snapshot_id INTEGER PRIMARY KEY REFERENCES snapshots(id),
                    schema_version INTEGER NOT NULL,
                    generated_at TEXT NOT NULL,
                    summary_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS semantic_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
                    fact_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    UNIQUE(snapshot_id, fact_type, subject_id)
                );
                CREATE INDEX IF NOT EXISTS idx_semantic_fact_type ON semantic_facts(snapshot_id, fact_type);
                CREATE INDEX IF NOT EXISTS idx_semantic_subject ON semantic_facts(subject_id);
                CREATE TABLE IF NOT EXISTS raven_diagnoses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
                    target TEXT,
                    status TEXT NOT NULL,
                    diagnosis_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_raven_created_at ON raven_diagnoses(created_at);
            """)
            conn.execute("PRAGMA user_version = 4")

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
            findings = conn.execute(
                "SELECT * FROM watcher_findings WHERE first_snapshot_id <= ? ORDER BY status, severity DESC, last_seen DESC",
                (snapshot_id,),
            ).fetchall()
            semantic = self._semantic_projection(conn, snapshot_id)
        return {
            "id": row["id"], "captured_at": row["captured_at"],
            "summary": {key: row[key] for key in ("total_entities", "unavailable_entities", "unknown_entities", "disabled_or_unavailable_automations", "low_battery_entities")},
            "registries": json.loads(row["registries_json"]),
            "entities": [{"entity_id": item["entity_id"], "state": item["state"], "attributes": json.loads(item["attributes_json"])} for item in observations],
            "watcher_findings": [self._finding_dict(item) for item in findings],
            "semantic": semantic,
        }

    def save_semantic_projection(self, projection: SemanticProjection) -> None:
        """Replace one snapshot's derived projection atomically."""
        with self._connect() as conn:
            conn.execute("DELETE FROM semantic_facts WHERE snapshot_id = ?", (projection.snapshot_id,))
            conn.execute("DELETE FROM semantic_projections WHERE snapshot_id = ?", (projection.snapshot_id,))
            conn.execute(
                "INSERT INTO semantic_projections (snapshot_id, schema_version, generated_at, summary_json) VALUES (?, ?, ?, ?)",
                (projection.snapshot_id, projection.schema_version, projection.generated_at.isoformat(), json.dumps(projection.summary)),
            )
            conn.executemany(
                """INSERT INTO semantic_facts
                (snapshot_id, fact_type, subject_id, payload_json, provenance_json, confidence)
                VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        projection.snapshot_id,
                        fact.fact_type,
                        fact.subject_id,
                        json.dumps(fact.payload),
                        json.dumps(fact.provenance),
                        fact.confidence,
                    )
                    for fact in projection.facts
                ],
            )

    def get_semantic_projection(self, snapshot_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            return self._semantic_projection(conn, snapshot_id)

    def save_raven_diagnosis(self, diagnosis: dict[str, Any]) -> int:
        """Persist one immutable Raven diagnosis and its evidence."""
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO raven_diagnoses (created_at, snapshot_id, target, status, diagnosis_json) VALUES (?, ?, ?, ?, ?)",
                (datetime.now(UTC).isoformat(), diagnosis["snapshot_id"], diagnosis.get("target"), diagnosis["status"], json.dumps(diagnosis)),
            )
        return int(cursor.lastrowid)

    def list_raven_diagnoses(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id, created_at, snapshot_id, target, status, diagnosis_json FROM raven_diagnoses ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": row["id"], "created_at": row["created_at"], "snapshot_id": row["snapshot_id"], "target": row["target"], "status": row["status"], "diagnosis": json.loads(row["diagnosis_json"])} for row in rows]

    def latest_snapshot(self) -> Snapshot | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return None
        return Snapshot(row["id"], datetime.fromisoformat(row["captured_at"]), row["total_entities"], row["unavailable_entities"], row["unknown_entities"], row["disabled_or_unavailable_automations"], row["low_battery_entities"])

    def list_snapshots(self, limit: int = 12) -> list[Snapshot]:
        """Return recent snapshot metadata for the dashboard timeline."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            Snapshot(
                row["id"], datetime.fromisoformat(row["captured_at"]),
                row["total_entities"], row["unavailable_entities"],
                row["unknown_entities"], row["disabled_or_unavailable_automations"],
                row["low_battery_entities"],
            )
            for row in rows
        ]

    def list_findings(self, status: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM watcher_findings"
        parameters: list[Any] = []
        if status:
            query += " WHERE status = ?"
            parameters.append(status)
        query += " ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END, last_seen DESC"
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [self._finding_dict(row) for row in rows]

    def save_findings(self, findings: list[FindingCandidate]) -> None:
        with self._connect() as conn:
            for finding in findings:
                existing = conn.execute(
                    "SELECT * FROM watcher_findings WHERE fingerprint = ?", (finding.fingerprint,)
                ).fetchone()
                observed_at = finding.observed_at.isoformat()
                if existing is None:
                    conn.execute(
                        """INSERT INTO watcher_findings
                        (fingerprint, category, entity_id, title, description, severity, confidence,
                         expected, status, first_seen, last_seen, resolved_at, occurrence_count,
                         first_snapshot_id, last_snapshot_id, evidence_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (finding.fingerprint, finding.category, finding.entity_id, finding.title,
                         finding.description, finding.severity, finding.confidence, int(finding.expected),
                         finding.status, observed_at, observed_at,
                         observed_at if finding.status == "resolved" else None, 1,
                         finding.snapshot_id, finding.snapshot_id, json.dumps(finding.evidence)),
                    )
                    continue
                reopened = existing["status"] == "resolved" and finding.status == "active"
                conn.execute(
                    """UPDATE watcher_findings SET category = ?, entity_id = ?, title = ?, description = ?,
                    severity = ?, confidence = ?, expected = ?, status = ?, first_seen = ?, last_seen = ?,
                    resolved_at = ?, occurrence_count = ?, first_snapshot_id = ?, last_snapshot_id = ?, evidence_json = ?
                    WHERE fingerprint = ?""",
                    (finding.category, finding.entity_id, finding.title, finding.description,
                     finding.severity, finding.confidence, int(finding.expected), finding.status,
                     observed_at if reopened else existing["first_seen"], observed_at,
                     observed_at if finding.status == "resolved" else None,
                     int(existing["occurrence_count"]) + 1, finding.snapshot_id if reopened else existing["first_snapshot_id"],
                     finding.snapshot_id, json.dumps(finding.evidence), finding.fingerprint),
                )

    def prune_resolved_findings(self, older_than_days: int) -> int:
        cutoff = datetime.now(UTC).timestamp() - older_than_days * 86400
        cutoff_iso = datetime.fromtimestamp(cutoff, UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM watcher_findings WHERE status = 'resolved' AND resolved_at < ?", (cutoff_iso,)
            )
        return cursor.rowcount

    @staticmethod
    def _finding_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"], "fingerprint": row["fingerprint"], "category": row["category"],
            "entity_id": row["entity_id"], "title": row["title"], "description": row["description"],
            "severity": row["severity"], "confidence": row["confidence"], "expected": bool(row["expected"]),
            "status": row["status"], "first_seen": row["first_seen"], "last_seen": row["last_seen"],
            "resolved_at": row["resolved_at"], "occurrence_count": row["occurrence_count"],
            "first_snapshot_id": row["first_snapshot_id"], "last_snapshot_id": row["last_snapshot_id"],
            "evidence": json.loads(row["evidence_json"]),
        }

    @staticmethod
    def _semantic_projection(conn: sqlite3.Connection, snapshot_id: int) -> dict[str, Any] | None:
        projection = conn.execute(
            "SELECT * FROM semantic_projections WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        if projection is None:
            return None
        facts = conn.execute(
            """SELECT fact_type, subject_id, payload_json, provenance_json, confidence
            FROM semantic_facts WHERE snapshot_id = ? ORDER BY fact_type, subject_id""",
            (snapshot_id,),
        ).fetchall()
        return {
            "schema_version": projection["schema_version"],
            "snapshot_id": projection["snapshot_id"],
            "generated_at": projection["generated_at"],
            "summary": json.loads(projection["summary_json"]),
            "facts": [
                {
                    "fact_type": fact["fact_type"],
                    "subject_id": fact["subject_id"],
                    "payload": json.loads(fact["payload_json"]),
                    "provenance": json.loads(fact["provenance_json"]),
                    "confidence": fact["confidence"],
                }
                for fact in facts
            ],
        }
