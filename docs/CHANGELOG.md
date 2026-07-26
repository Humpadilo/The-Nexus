# Changelog

This documentation changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The root [CHANGELOG.md](../CHANGELOG.md) remains the release-facing project history.

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
- Tagged the verified baseline `v0.1.0`.
