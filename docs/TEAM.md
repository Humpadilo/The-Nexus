# Team and Responsibilities

The Nexus is built by a human owner, development collaborators, and future runtime modules. Runtime module names are roles and boundaries, not claims that all modules are implemented.

## Matt — Product Owner

- Owns vision and product priorities.
- Makes final approval decisions.
- Performs or coordinates real-home testing.
- Decides which tradeoffs are acceptable.
- Confirms when a feature is safe to apply to production.

## ChatGPT — Lead Architect

- Helps turn goals into requirements.
- Proposes system design and boundaries.
- Plans features and milestones.
- Reviews consistency, risks, and integration effects.
- Provides Home Assistant and platform guidance.

ChatGPT is not a runtime dependency of the app.

## Codex — Lead Engineer

- Implements approved changes.
- Refactors and tests the codebase.
- Maintains documentation and packaging.
- Verifies changes in proportion to their risk.
- Records assumptions and architectural decisions.

Codex is a development tool, not a production service.

## Future runtime modules

### Archivist — Collector

Implemented foundation module. Collects read-only state and registry observations, stores snapshots, and produces audit summaries.

### Watcher — Monitor

Implemented in Version 0.2. Compares persisted snapshots, stores evidence-backed findings, and reports new, ongoing, and resolved conditions without changing Home Assistant.

### Semantic layer — Knowledge foundation

Implemented in Version 0.3. Translates raw Archivist observations into deterministic canonical facts with stable identity, relationships, provenance, confidence, and dashboard-oriented grouping fields. It is rebuildable from stored snapshot data and is not a replacement for SQLite snapshots, an AI reasoning system, or a write path to Home Assistant.

### Nexus Dashboard — Presentation

Implemented in Version 0.4 as the read-only presentation consumer of Semantic Knowledge Foundation and Watcher data.

### Curator — Organizer

Implemented in Version 0.5. Organizes semantic facts, explicit snapshot references, and Watcher findings around areas, human concepts, relationships, and read-only health context. It does not create a competing source of truth.

### Oracle — Reasoning

Future module. Explains observations and produces evidence-backed recommendations. It must not apply changes.

### Steward — Implementation

Future module. Applies explicitly approved, reversible changes and records the result.

### Laboratory — Validation

Future module. Simulates or validates proposed changes away from production.
