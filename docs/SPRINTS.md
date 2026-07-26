# Sprints

This file tracks current development. Completed sprints remain here as an historical record. Detailed future ideas belong in the roadmap or parking lot.

## Current sprint — Sprint 2: The Watcher

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

- Define Curator requirements and normalization boundaries.

## Completed sprint history

### Sprint 0 — Project foundation

- [x] Establish the local-first project direction.
- [x] Create the initial Archivist implementation.
- [x] Establish basic tests and packaging.
