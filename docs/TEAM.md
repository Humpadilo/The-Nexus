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

Planned module. Detects changes, recurring conditions, and events according to explicit rules.

### Curator — Organizer

Planned module. Organizes, normalizes, and presents collected information.

### Oracle — Reasoning

Future module. Explains observations and produces evidence-backed recommendations. It must not apply changes.

### Steward — Implementation

Future module. Applies explicitly approved, reversible changes and records the result.

### Laboratory — Validation

Future module. Simulates or validates proposed changes away from production.
