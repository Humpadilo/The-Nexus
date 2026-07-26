# Sprints

This file tracks current development. Completed sprints remain here as an historical record. Detailed future ideas belong in the roadmap or parking lot.

## Current sprint — Sprint 5: Curator

### Completed

- [x] Initialize the Git repository.
- [x] Create the Version 0.1 Home Assistant app definition.
- [x] Add Python 3.12 Docker packaging.
- [x] Add FastAPI Ingress page.
- [x] Add health endpoint.
- [x] Add read-only Home Assistant REST and WebSocket client.
- [x] Add SQLite snapshot and observation storage.
- [x] Add manual snapshot action.
- [x] Add summary and JSON audit bundle.
- [x] Add collector, storage, and report unit tests.
- [x] Add repository metadata and current Home Assistant packaging fixes.
- [x] Complete the live Home Assistant OS smoke test for Version 0.1.0.

### Sprint 1 production evidence

Version 0.1.0 was installed from the public repository on 2026-07-26 and verified on Home Assistant OS:

- The app installed and ran successfully.
- The Ingress page loaded.
- A live snapshot collected 436 entities, including 66 unavailable and 102 unknown.
- SQLite persistence was confirmed after reloading the Ingress page.
- The 706,362-byte JSON audit bundle was downloaded and validated.
- The local test suite passed with 5 tests.
- The original release remains tagged `v0.1.0`; the formally verified close is tagged `v0.1.0-verified`.

## Sprint 2 — The Watcher — complete

Watcher compares stored snapshots, persists evidence-backed findings, exposes a low-noise Ingress view, and schedules local read-only checks.

### Completed

- [x] Compare adjacent snapshots for meaningful changes.
- [x] Detect availability, additions/removals, low batteries, and automation changes.
- [x] Classify disabled entities as expected when registry data permits.
- [x] Persist severity, confidence, timestamps, status, occurrence count, and evidence.
- [x] Deduplicate unchanged conditions and mark recoveries resolved.
- [x] Add daily-by-default scheduling and configurable retention.
- [x] Add Ingress findings view and machine-readable exports.
- [x] Add migrations, fixtures, structured logs, and tests.
- [x] Complete live Home Assistant OS smoke verification.

### Sprint 2 verification

- Local suite: 9 tests passed.
- Release: `v0.2.0`.
- Live Home Assistant OS: the app was rebound to a fresh public repository clone after Supervisor reported a stale repository-cache authentication failure, then installed and started successfully at Version 0.2.0.
- Ingress loaded and displayed the Watcher view.
- Two live manual snapshots completed. The second snapshot collected 438 entities, including 20 unavailable and 122 unknown, and generated 143 persisted findings.
- SQLite persistence was confirmed by the second snapshot and the loaded findings view.
- `snapshot-2.json` (942,137 bytes) and `watcher-findings.json` (218,015 bytes) downloaded and parsed successfully.

### Blocked

- No current engineering blocker is recorded.

### Next sprint

- Define and implement the Semantic Knowledge Foundation.

## Sprint 3 — Semantic Knowledge Foundation — complete

Create the deterministic translation boundary between Archivist snapshots and higher-level modules.

### Planned outcomes

- Canonical, versioned models for entity, device, area, capability, availability, and health facts.
- Stable identity and relationship rules that tolerate incomplete or changing registry data.
- Evidence and confidence on every canonical fact, linked to snapshot observations.
- Read-only persistence or derived views that do not replace raw snapshots.
- Watcher compatibility tests proving existing findings remain reproducible.
- Fixtures and migration tests for representative Home Assistant API variations.
- Dashboard-oriented summaries, grouping, labels, relationships, and drill-down fields.

### Explicit non-goals

- Curator presentation features.
- AI reasoning or recommendations.
- YAML generation, repair, notifications, or Home Assistant writes.
- A general-purpose graph database or hidden ontology.

### Sprint 4 ordering

Sprint 3 is complete and verified. Sprint 4 implements The Nexus Dashboard as the presentation layer over the verified semantic contracts.

### Sprint 3 verification

- Version 0.3.0 semantic projection implemented.
- Local suite: 13 tests passed.
- Compilation and `git diff --check` passed.
- Live Home Assistant OS: Version 0.3.0 installed and ran successfully after removing a stale duplicate repository source.
- Ingress loaded and manual snapshot 4 completed: 437 entities, 20 unavailable, 120 unknown.
- SQLite persistence was confirmed by the stored snapshot and reloadable Ingress view.
- `snapshot-4.json` downloaded and validated: semantic schema 1, 1,379 facts, 60 devices, 8 areas, and fact provenance present.
- Release verification tag: `v0.3.0-verified`.

## Sprint 4 — The Nexus Dashboard — complete

- [x] Add a polished read-only Overview, Health, Explorer, Timeline, and Reports experience.
- [x] Render semantic entities, devices, areas, capabilities, relationships, and health context.
- [x] Render Watcher active, ongoing, informational, and resolved findings without duplicate backend logic.
- [x] Preserve manual snapshots, audit bundles, semantic exports, and findings exports.
- [x] Add dashboard projection tests and responsive styling.
- [x] Verify the dashboard locally and through Home Assistant Ingress.

### Sprint 4 verification

- Local suite: 14 tests passed.
- Dashboard remains read-only and operates entirely from local SQLite semantic and Watcher data.
- Version 0.4.0 installed and started successfully on Home Assistant OS.
- Ingress loaded and rendered the dashboard from live SQLite data.
- Manual snapshot collected 436 entities, 59 devices, and 8 areas.
- Audit bundle downloaded and parsed successfully with 1,375 semantic facts and provenance.
- Release verification tag: `v0.4.0-verified`.

## Completed sprint history

### Sprint 0 — Project foundation

- [x] Establish the local-first project direction.
- [x] Create the initial Archivist implementation.
- [x] Establish basic tests and packaging.
