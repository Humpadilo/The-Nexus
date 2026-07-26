"""Typed contracts for the rebuildable semantic knowledge projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

SEMANTIC_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SemanticFact:
    """One canonical fact with explicit source evidence."""

    fact_type: str
    subject_id: str
    payload: dict[str, Any]
    provenance: dict[str, Any]
    confidence: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "fact_type": self.fact_type,
            "subject_id": self.subject_id,
            "payload": self.payload,
            "provenance": self.provenance,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class SemanticProjection:
    """A versioned semantic view derived entirely from one raw snapshot."""

    snapshot_id: int
    generated_at: datetime
    summary: dict[str, Any]
    facts: tuple[SemanticFact, ...]
    schema_version: int = SEMANTIC_SCHEMA_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
            "facts": [fact.as_dict() for fact in self.facts],
        }
