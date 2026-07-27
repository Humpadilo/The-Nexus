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

**Decision:** Keep Archivist, Watcher, Semantic Layer, Dashboard / Nexus Experience, Curator, Raven, Planner, Engineer, Oracle, and Tracy as separate conceptual boundaries with explicit contracts. The Interface Layer, including any future Concierge presentation, remains separate from intelligence and orchestration.

**Consequences:** Small modules can be tested and replaced independently. Cross-module contracts must be documented before integration.

**Alternatives considered:** One large assistant service; rejected because it would blur ownership and make safety boundaries harder to review.

## ADR-005 — Reliability over novelty

**Status:** Accepted

**Context:** Home automation is infrastructure used by people in their homes, not only a demonstration environment.

**Decision:** Prefer simple, observable, reversible, well-tested behavior over novel features that increase operational uncertainty.

**Consequences:** Feature work may be slower, and ideas may be deferred. The project gains clearer failure modes and lower maintenance cost.

**Alternatives considered:** Optimize for maximum feature count; rejected by project rules.

## ADR-009 — Add a narrow semantic knowledge layer before Curator

**Status:** Accepted and implemented

**Context:** Archivist stores raw Home Assistant observations and Watcher interprets selected fields directly. Curator is expected to organize the same information. If each higher-level module interprets entity identity, registry relationships, capabilities, availability, or expectedness independently, the project will accumulate duplicate rules and inconsistent results.

**Decision:** Introduce a deterministic semantic knowledge layer before Curator. It will translate raw snapshots into versioned canonical facts and relationships, preserve provenance and confidence, and remain read-only. Raw snapshots and observations remain the source of truth. The layer will be local and persistence-compatible with the existing SQLite model.

The Semantic Knowledge Foundation must be rebuildable entirely from Home Assistant state and configuration and must never become an independent source of truth.

**Boundaries:** The layer is not a general-purpose knowledge graph, AI reasoning service, intent engine, notification system, or repair path. It must not invent unsupported facts, hide missing registry data, or sever evidence links. Watcher may adopt the canonical facts after compatibility tests; Curator must consume the shared contracts rather than create a competing interpretation.

**Consequences:** Entity/device/area semantics become reusable and testable. The project gains an explicit place for normalization and provenance while avoiding premature graph infrastructure. The completed ordering is Archivist → Watcher → Semantic Layer → Curator; future modules consume these contracts.

**Alternatives considered:** Put normalization directly in Curator; rejected because Watcher and future modules would continue to duplicate interpretation rules. Introduce a full knowledge graph; rejected as disproportionate to the current local, snapshot-based scope.

## ADR-010 — Tracy is the intelligence and orchestration layer

**Status:** Accepted for future implementation

**Context:** The Nexus will eventually need a coherent intelligence layer for conversation, intent understanding, personalization, planning, and presenting recommendations. The earlier Concierge concept combined those responsibilities with the interface through which users would experience them. That combination would make a presentation surface responsible for intelligence and could blur the boundary between conversation, planning, and production behavior.

**Decision:** Define Tracy as the long-term intelligence and orchestration layer of The Nexus. Tracy may understand conversation and intent, personalize the experience, coordinate context across Nexus modules, plan proposed work, and present evidence-backed recommendations. Tracy does not directly execute production changes and does not become a source of truth for Home Assistant state or configuration.

Define Concierge as a presentation/interface role rather than a core intelligence component. A Concierge is one way Tracy may interact with users through a touchscreen, voice interface, mobile application, dashboard, or future interface. Multiple interfaces may expose Tracy, and a Concierge may present information from Tracy and other Nexus modules without owning their logic.

**Boundaries:** Tracy must remain separated from production execution. Any future change must continue through the explicit Observe → Recommend → Approve → Apply boundary and an approved implementation path. Concierge must not directly control Home Assistant automations, services, devices, or configuration. Conversation, intent handling, and presentation must not silently become production logic. Archivist, Watcher, the Semantic Knowledge Foundation, and other core modules remain independently useful without Tracy or a Concierge.

**Consequences:** The architecture gains a stable distinction between intelligence/orchestration and user interface. Future interfaces can change without duplicating Tracy's conversation and planning responsibilities, while Tracy can consume documented module contracts without becoming a backend source of truth. Additional contracts will be required before implementation, including context access, recommendation evidence, personalization boundaries, privacy, and approval handoff.

**Alternatives considered:** Make Concierge the intelligence layer; rejected because it couples conversational intelligence to a specific presentation channel. Let Tracy execute approved changes directly; rejected because production execution must remain explicit, reviewable, reversible, and owned by the future implementation boundary.

## ADR-011 — Raven is a read-only diagnostic investigator

**Status:** Accepted and implemented in Version 0.6

**Context:** Curator organizes evidence, but a real household failure requires a module that can follow explicit dependencies and inspect available execution configuration without asking the user to manually trace Home Assistant automation paths.

**Decision:** Raven investigates a selected entity, helper, automation, script, scene, or concept using stored snapshots, semantic facts, registry data, Watcher findings, and read-only Home Assistant REST configuration reads for UI-managed automations, scripts, and scenes when available. Raven persists diagnoses with provenance, severity, confidence, root-cause evidence, and repair recommendations.

**Boundaries:** Raven must not call Home Assistant services, write configuration, read protected files, perform automatic repair, or invent relationships when configuration evidence is unavailable. Configuration reads are evidence attached to an investigation, not a replacement source of truth. Planner, Engineer, Oracle, and Tracy remain outside Sprint 6.

**Consequences:** Raven can diagnose broken references, unavailable dependencies, likely renamed entities, orphaned helpers, missing area assignments, and explicit execution paths. Some failures will remain undiagnosable when Home Assistant does not expose the relevant configuration or execution evidence; Raven must report that limitation explicitly.

## ADR-012 — First repair workflow is bounded and approval-gated

**Context:** Raven can identify the real House Mode failure, but diagnosis alone leaves the user to manually translate evidence into a production edit. A general repair engine would exceed the current product boundary.

**Decision:** Implement one bounded Engineer workflow for a verified House Mode entity-reference replacement in UI-managed automation configuration. The proposal must contain before-and-after values, exact configuration paths, affected objects, evidence, confidence, risk, rollback, and validation steps. Applying it requires explicit human confirmation and reloads only the affected Home Assistant domain.

**Boundaries:** Raven remains read-only and owns diagnosis. Engineer owns proposal preparation and the explicitly approved application path. No YAML editing, broad autonomous repair, silent approval, unrelated object changes, or production write occurs outside the recorded proposal.

**Consequences:** The first repair path is intentionally narrow and reversible. It establishes the approval and audit contract for later Engineer work without making Engineer a general-purpose mutation system.
