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
- The verified release is tagged `v0.1.0`.

## Sprint 2 — The Watcher

Watcher compares stored snapshots, persists evidence-backed findings, exposes a low-noise Ingress view, and schedules local read-only checks.

### Blocked

- No current engineering blocker is recorded.

### Next sprint

- Define Curator requirements and normalization boundaries.

## Completed sprint history

### Sprint 0 — Project foundation

- [x] Establish the local-first project direction.
- [x] Create the initial Archivist implementation.
- [x] Establish basic tests and packaging.
