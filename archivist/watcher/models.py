"""Typed Watcher records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

FindingStatus = Literal["active", "resolved"]


@dataclass(frozen=True)
class FindingCandidate:
    """A finding observation produced by comparing two snapshots."""

    fingerprint: str
    category: str
    entity_id: str | None
    title: str
    description: str
    severity: str
    confidence: str
    expected: bool
    status: FindingStatus
    snapshot_id: int
    observed_at: datetime
    evidence: dict[str, Any]

