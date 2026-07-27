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

### Raven — Investigator

Implemented in Version 0.6. Investigates selected controls using snapshot evidence and read-only Home Assistant configuration reads. It traces explicit dependencies, identifies broken and unavailable references, explains likely causes, and produces repair recommendations without modifying production.

### Oracle — Reasoning

Future module. Predicts future states and identifies emerging issues. It must expose uncertainty and evidence.

### Planner — Planning

Future module. Creates recommended plans and workflows. Plans remain proposals until explicitly approved.

### Engineer — Bounded implementation

The first bounded workflow is implemented. Engineer turns Raven evidence into a House Mode repair proposal with exact before-and-after values, risks, rollback, and validation steps. Production application requires explicit approval, is limited to the recorded UI-managed automation objects, reloads only the affected domain, and records an audit event.

### Tracy — Intelligence and orchestration

Future module. Coordinates Nexus modules, understands intent, personalizes context, and translates technical information into natural language. Tracy does not directly execute production changes.

### Interface Layer

Future presentation role for dashboard, touchscreen, voice, mobile, and other interfaces. Concierge belongs here as a presentation role rather than a core intelligence module.
