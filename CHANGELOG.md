# Changelog

## 0.4.0 - 2026-07-26

- Added The Nexus Dashboard with Overview, Health, semantic Explorer, Timeline, and Reports sections.
- Added read-only dashboard projections over semantic facts and Watcher findings.
- Added dashboard navigation, responsive styling, semantic drill-down tables, and report links.
- Added dashboard service and web regression tests.
- Verified on Home Assistant OS: Version 0.4.0 installed and running, Ingress loaded, and a live manual snapshot collected 436 entities, 59 devices, and 8 areas.
- Verified the dashboard displayed semantic data and report links; the downloaded audit bundle parsed successfully with 1,375 semantic facts and provenance.
- Release verification tag: `v0.4.0-verified`.

## 0.3.0 - 2026-07-26

- Added the rebuildable semantic knowledge projection for entities, devices, areas, capabilities, and health.
- Added versioned semantic facts with stable identifiers, dashboard-oriented grouping fields, provenance, and confidence.
- Added SQLite persistence, replacement-safe rebuilds, semantic audit data, and a read-only semantic JSON export.
- Added semantic fixtures and tests for deterministic rebuilds, missing registries, provenance, persistence, collector integration, and exports.
- Verified on Home Assistant OS: Version 0.3.0 installed and ran successfully, Ingress loaded, snapshot 4 collected 437 entities (20 unavailable, 120 unknown), and the downloaded audit bundle contained semantic schema version 1, 1,379 semantic facts, 60 devices, and 8 areas.

## 0.2.0 - 2026-07-27

- Added The Watcher for evidence-backed snapshot comparison.
- Added persisted active/resolved findings with severity, confidence, timestamps, occurrence counts, and current/previous snapshot evidence.
- Added detection for entity availability, entity additions/removals, low batteries, and automation availability changes.
- Added daily-by-default scheduled read-only checks and configurable resolved-finding retention.
- Added Watcher Ingress view, findings JSON export, and audit bundle integration.
- Added Watcher fixtures and persistence, endpoint, scheduler, deduplication, recovery, and classification tests.
- Verified on Home Assistant OS: Version 0.2.0 installed and started, Ingress loaded, two live snapshots completed, and 143 findings were persisted and shown.
- Downloaded and validated the live `snapshot-2.json` audit bundle and `watcher-findings.json` export.

## 0.1.0 - 2026-07-26

- Published Version 0.1 to the private `Humpadilo/The-Nexus` repository.
- Updated Home Assistant repository metadata and installation instructions.
- Documented the GitHub registry credential requirement for private repository installation.
- The repository is now public; removed the private-credential installation requirement.
- Verified production installation on Home Assistant OS: Version 0.1.0 ran through Ingress, collected 436 entities (66 unavailable, 102 unknown), persisted SQLite data across reload, and produced a validated downloadable JSON audit bundle.
- Recorded the five passing Version 0.1 smoke tests and tagged the verified baseline as `v0.1.0-verified` (the original `v0.1.0` tag remains unchanged).

The project operating documentation is in [`docs/`](docs/README.md), including the [documentation changelog](docs/CHANGELOG.md).

## 0.1.0 - 2026-07-26

- Added the first Home Assistant app definition with Ingress support.
- Added FastAPI health and snapshot UI.
- Added read-only REST/WebSocket collection and SQLite persistence.
- Added JSON audit bundle downloads and unit tests.
- Hardened FastAPI startup and made templates/assets independent of the working directory.
- Added API smoke tests for health, Ingress rendering, snapshot execution, persistence, and audit downloads.
