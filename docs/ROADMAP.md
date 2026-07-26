# Roadmap

This roadmap describes major versions, not a task backlog. Active work belongs in [SPRINTS.md](SPRINTS.md). Ideas that are not committed to a version belong in [PARKING_LOT.md](PARKING_LOT.md).

## v0.1 — Foundation

### Goals

Establish a local Home Assistant app and a durable observation foundation.

### Expected features

- Home Assistant app definition with Ingress.
- FastAPI web page and health endpoint.
- Read-only state and registry collection.
- SQLite snapshots and entity observations.
- Snapshot summaries and JSON audit bundles.
- Structured logging and unit tests.

### Success criteria

The app can be installed, started locally, run without Codex or ChatGPT, collect available read-only data, persist a snapshot, and download an audit bundle.

## v0.2 — Watcher

### Goals

Detect meaningful changes and recurring health conditions without changing Home Assistant.

### Expected features

- Change detection between snapshots.
- Explicit watcher rules.
- Local event or scheduled observation strategy.
- Tests for duplicate, missing, and changed observations.

### Success criteria

Users can see what changed and why it was reported, with no automatic repair.

## v0.3 — Semantic Knowledge Foundation

### Goals

Introduce a small, deterministic semantic boundary between raw snapshots and higher-level modules so the project has one reusable interpretation of Home Assistant entities, devices, areas, capabilities, health states, and provenance.

### Expected features

- Canonical local models for entities, devices, areas, capabilities, and health-relevant states.
- Stable identity and relationship rules with explicit handling for missing or changing registry data.
- Provenance from every canonical fact back to snapshot and observation evidence.
- Confidence and expectedness metadata without AI inference.
- Versioned contracts, migration behavior, fixtures, and read-only exports.
- Compatibility with existing raw snapshot and Watcher records.

### Non-goals

- General-purpose knowledge graph infrastructure.
- AI reasoning, recommendations, notifications, or repair.
- Replacing raw snapshots as the source of truth.
- Writing Home Assistant state or configuration.

### Success criteria

Watcher and future Curator code can consume the same tested canonical facts, every fact remains traceable to stored observations, and missing registry data degrades predictably without blocking snapshots.

## v0.4 — Curator

### Goals

Organize canonical semantic facts into useful local views without duplicating Home Assistant interpretation rules.

### Expected features

- Entity, device, and area organization.
- Human-readable relationships, capabilities, and health context.
- Filters and views built from semantic contracts.
- Clear provenance from displayed information to canonical facts and raw snapshots.

### Success criteria

Users can navigate a coherent representation of their Home Assistant system and trace important information back to collected evidence.

## v0.5 — Health Reports

### Goals

Turn observations into clear maintenance reports.

### Expected features

- Grouped health findings.
- Severity and confidence fields.
- Human-readable report views.
- Report tests with stable fixtures.

### Success criteria

Reports explain findings without requiring the user to inspect raw JSON.

## v0.6 — AI Recommendations

### Goals

Introduce optional explanation and recommendation assistance.

### Expected features

- Explicit recommendation objects.
- Evidence attached to each recommendation.
- Local operation when AI is unavailable.
- No automatic production writes.

### Success criteria

Recommendations are optional, explainable, and never silently applied.

## v0.7 — YAML Generation

### Goals

Generate proposed Home Assistant configuration changes as reviewable artifacts.

### Expected features

- Generated YAML kept outside active configuration by default.
- Validation before presentation.
- Diff-oriented review.

### Success criteria

Users can inspect and reject generated changes without affecting production.

## v0.8 — Simulation

### Goals

Test proposed changes before applying them.

### Expected features

- Laboratory/test environment.
- Fixture-driven simulation.
- Validation and rollback planning.

### Success criteria

The system can show expected effects and known risks before approval.

## v0.9 — Approval Workflow

### Goals

Formalize human approval for changes.

### Expected features

- Observe → Recommend → Approve → Apply state machine.
- Audit trail.
- Expiration and cancellation.
- Explicit identity of the approver.

### Success criteria

No production change can occur without a visible, recorded approval.

## v0.10 — Activity Intelligence

### Goals

Understand patterns such as occupancy, activity, and house modes without hiding assumptions.

### Expected features

- Explicit data sources and retention rules.
- Explainable activity summaries.
- Privacy-preserving local processing.

### Success criteria

Activity insights are useful, local-first, and clear about uncertainty.

## v1.0 — AI Home Engineer

### Goals

Deliver a trustworthy assistant for understanding and maintaining a Home Assistant system.

### Expected features

- Integrated observation, explanation, recommendation, approval, application, and verification.
- Strong auditability.
- Safe failure and rollback behavior.

### Success criteria

The system reduces maintenance effort while preserving human control and local operability.
