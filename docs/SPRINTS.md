# Sprints

This file tracks current development. Completed sprints remain here as an historical record. Detailed future ideas belong in the roadmap or parking lot.

## Current sprint — Sprint 1: Foundation hardening

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

### In progress

- [ ] Validate installation on a real Home Assistant OS host after configuring private-repository credentials.
- [ ] Confirm registry behavior against supported Home Assistant versions.

### Blocked

- The target Home Assistant host cannot clone the private GitHub repository until a GitHub registry credential is configured.

### Next sprint

- Define Watcher requirements in `SPEC.md`.
- Decide whether snapshot history belongs in Version 0.2 or Version 0.3 implementation planning.
- Add a real installation test procedure to the release checklist.

## Completed sprint history

### Sprint 0 — Project foundation

- [x] Establish the local-first project direction.
- [x] Create the initial Archivist implementation.
- [x] Establish basic tests and packaging.
