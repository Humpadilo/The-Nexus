# Architecture Decision Records

Major architectural choices are recorded here so future contributors can understand the reason behind the current shape of the project.

## ADR-005 — Watcher uses stable finding fingerprints

**Status:** Accepted

Watcher findings are keyed by `category:entity_id` and upserted in SQLite. Unchanged active conditions update `last_seen`, evidence, and occurrence count instead of creating another row. Recovery changes the existing row to `resolved`; a returning condition reopens it.

## ADR-006 — Watcher compares snapshots, not the event stream

**Status:** Accepted

Version 0.2 runs comparisons after manual or scheduled snapshots. It does not add a long-lived Home Assistant event subscription, keeping the app local, restart-safe, and aligned with the existing read-only snapshot architecture.

## ADR-007 — Daily scheduling is the initial default

**Status:** Accepted

The app schedules one local snapshot/check every 24 hours by default. App options can disable scheduling or set an interval from 1 to 168 hours. Resolved findings are retained for 365 days by default and can be configured from 30 to 3650 days.

## ADR-008 — Expected state classification is registry-backed and conservative

**Status:** Accepted

An unavailable or unknown entity is marked expected only when the available entity registry identifies it as disabled. Missing registry data never suppresses a finding.

## ADR-001 — The Archivist runs locally

**Status:** Accepted

**Context:** The system needs to remain useful in the home and should not depend on Codex, ChatGPT, or a cloud service for collection and reporting.

**Decision:** Run The Archivist as a local Home Assistant app with app-owned persistence.

**Consequences:** The app remains available locally and can use Supervisor-managed access. Deployment must respect Home Assistant app packaging, permissions, and resource constraints.

**Alternatives considered:** Cloud-hosted collector; rejected because it would add dependency, privacy, and availability costs.

## ADR-002 — Home Assistant is the runtime source of truth

**Status:** Accepted

**Context:** Home Assistant owns live entity state and automation runtime behavior.

**Decision:** Read live state through the Home Assistant REST and WebSocket APIs. Do not duplicate or mutate Home Assistant configuration in Version 0.1.

**Consequences:** The app depends on API availability and must tolerate version and permission differences. SQLite stores observations and snapshots, not a replacement runtime model.

**Alternatives considered:** Reading Home Assistant internal files; rejected for security, coupling, and explicit project scope.

## ADR-003 — AI follows an approval workflow

**Status:** Accepted for future work

**Context:** Recommendations or repairs can affect a real home and must be understandable and reversible.

**Decision:** Future AI behavior follows Observe → Recommend → Approve → Apply, with verification after application.

**Consequences:** AI modules may require evidence, audit records, approval UX, and rollback planning. Automatic production repair is prohibited.

**Alternatives considered:** Fully autonomous repair; rejected because it violates human control and reversibility requirements.

## ADR-004 — Use modular subsystem boundaries

**Status:** Accepted

**Context:** The project will grow from collection into monitoring, organization, reasoning, and controlled implementation.

**Decision:** Keep Archivist, Watcher, Curator, Oracle, Steward, and Laboratory as separate conceptual boundaries with explicit contracts.

**Consequences:** Small modules can be tested and replaced independently. Cross-module contracts must be documented before integration.

**Alternatives considered:** One large assistant service; rejected because it would blur ownership and make safety boundaries harder to review.

## ADR-005 — Reliability over novelty

**Status:** Accepted

**Context:** Home automation is infrastructure used by people in their homes, not only a demonstration environment.

**Decision:** Prefer simple, observable, reversible, well-tested behavior over novel features that increase operational uncertainty.

**Consequences:** Feature work may be slower, and ideas may be deferred. The project gains clearer failure modes and lower maintenance cost.

**Alternatives considered:** Optimize for maximum feature count; rejected by project rules.
