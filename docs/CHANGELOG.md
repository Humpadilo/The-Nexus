# Changelog

This documentation changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The root [CHANGELOG.md](../CHANGELOG.md) remains the release-facing project history.

## Unreleased — architecture documentation alignment

- Synchronized repository documentation with the approved local-first Home Operating System architecture.
- Distinguished implemented modules from planned Raven, Planner, Engineer, Oracle, and Tracy boundaries.
- Clarified Tracy and the Interface Layer, including Concierge as a presentation role rather than a core intelligence component.
- Updated module responsibilities, semantic-layer status, approval boundaries, and current project identity across the documentation set.

## [0.6.0] - 2026-07-27

### Added

- Raven read-only diagnostic investigations using snapshot evidence and available Home Assistant automation, script, and scene configuration APIs.
- Explicit dependency tracing, broken-reference detection, unavailable-dependency findings, orphaned-helper detection, diagnoses persistence, and JSON export.
- Raven Ingress investigation controls and tests.

### Scope

- Raven produces evidence-backed diagnoses and repair recommendations only. It does not perform repairs or call Home Assistant services.

### Verification

- Version 0.6.0 installed and ran on Home Assistant OS with Ingress loaded.
- A live snapshot collected 437 entities, including 20 unavailable and 119 unknown, and persisted 142 active Watcher findings.
- Raven investigated the real `input_select.house_mode` control across 13 configuration sources and identified a high-confidence broken reference using snapshot and read-only configuration evidence.
- Raven diagnoses persisted in SQLite and the JSON diagnosis export was downloaded from Ingress.
- Local suite: 18 tests passed; release verification tag: `v0.6.0-verified`.

## [0.5.0] - 2026-07-26

### Added

- Curator organization projection for areas, devices, entities, helpers, automations, scripts, scenes, human concepts, relationships, and health context.
- Explicit `Unassigned` organization and evidence-backed organization cues for missing area assignments.
- Curator JSON export endpoints and a progressive-disclosure Ingress view.
- Deterministic actionable Watcher context with likely cause, impact, recommended read-only repair guidance, confidence, dependencies, evidence, and provenance.

### Scope

- Curator is a read-only organization layer and does not modify Home Assistant.
- Relationship discovery uses explicit references available in collected snapshot attributes; it does not read Home Assistant configuration files or invent dependencies.

### Live verification

- Version 0.5.0 installed and started successfully on Home Assistant OS.
- Ingress loaded and the Curator view rendered after a live snapshot of 437 entities.
- Curator export parsed successfully with 9 areas, 9 concepts, 48 explicit relationships, 94 organization cues, and provenance.
- Local suite: 15 tests passed; release verification tag: `v0.5.0-verified`.

## [0.4.5] - 2026-07-26

### Added

- The Nexus Experience presentation refinement between the Dashboard and Curator sprints.
- Module-oriented navigation affordances for current and future Nexus capabilities.
- Contextual overview health language, progressive disclosure, a story-oriented timeline, responsive layout, accessibility improvements, and restrained micro-interactions.

### Scope

- No Archivist, Watcher, Semantic Foundation, or Home Assistant behavior was redesigned.
- Curator, Planner, Engineer, and Oracle remain unavailable future modules.

### Live verification

- Version 0.4.5 installed and started successfully on Home Assistant OS.
- Ingress loaded the module-oriented Nexus Experience.
- Manual live snapshot collected 437 entities, 60 devices, and 8 areas.
- Audit bundle downloaded and parsed successfully with 1,379 semantic facts and provenance.
- Local suite: 14 tests passed; release verification tag: `v0.4.5-verified`.

## [0.2.0] - 2026-07-27

### Added

- Watcher snapshot comparison and evidence-backed findings.
- Stable finding fingerprints with active, ongoing, and resolved states.
- Configurable daily scheduling and resolved-finding retention.
- Ingress findings view, JSON export, and audit bundle findings.
- Watcher specifications, decisions, architecture updates, and tests.

### Live verification

- Verified Version 0.2.0 on Home Assistant OS after rebinding the app to a fresh public repository clone.
- Completed two live snapshots; the second contained 438 entities, 20 unavailable, 122 unknown, and 143 persisted findings.
- Downloaded and validated the audit bundle and findings export.

## [0.4.0] - 2026-07-26

### Added

- The Nexus Dashboard with overview, health, semantic explorer, timeline, and reports sections.
- Dashboard projections and tests over existing semantic and Watcher data.

### Live verification

- Installed and started Version 0.4.0 on Home Assistant OS; Ingress loaded successfully.
- Manual live snapshot collected 436 entities, 59 devices, and 8 areas.
- Dashboard rendered semantic areas, devices, capabilities, entities, timeline, and report links.
- Downloaded audit bundle parsed successfully with 1,375 semantic facts and provenance.
- Local suite: 14 tests passed; release verification tag: `v0.4.0-verified`.

## [0.3.0] - 2026-07-26

### Added

- Rebuildable semantic knowledge projections derived from raw snapshots.
- Canonical entity, device, area, capability, and health facts with provenance and confidence.
- Dashboard-oriented summaries, grouping fields, relationships, and semantic JSON exports.
- SQLite schema migration and tests for deterministic replacement-safe projections.

### Live verification

- Version 0.3.0 installed and ran on Home Assistant OS.
- Ingress loaded and manual snapshot 4 completed: 437 entities, 20 unavailable, 120 unknown.
- The JSON audit bundle parsed successfully with semantic schema 1, 1,379 facts, 60 devices, and 8 areas.

## [0.1.0] - 2026-07-26

### Added

- The initial local Home Assistant application, The Archivist.
- FastAPI Ingress page and health endpoint.
- Read-only REST and WebSocket collection.
- SQLite snapshots and entity observations.
- Snapshot summaries and JSON audit bundles.
- Unit tests for collection, storage, and reports.
- Initial Nexus documentation framework.
- Repository metadata and Home Assistant packaging corrections.

### Repository improvements

- Added the Home Assistant app repository manifest.
- Added current architecture and label metadata.
- Documented the local installation and safety boundaries.
- Hardened startup paths and mounted the web UI static assets.
- Added end-to-end API smoke coverage for the Version 0.1 workflow.
- Completed the live Home Assistant OS smoke test: app running, Ingress loaded, 436 entities collected, 66 unavailable, 102 unknown, SQLite persistence confirmed, and JSON audit bundle downloaded and validated.
- Tagged the verified baseline `v0.1.0-verified` (the original `v0.1.0` tag remains unchanged).
