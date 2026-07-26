# Changelog

## 0.1.0 - 2026-07-26

- Published Version 0.1 to the private `Humpadilo/The-Nexus` repository.
- Updated Home Assistant repository metadata and installation instructions.
- Documented the GitHub registry credential requirement for private repository installation.
- The repository is now public; removed the private-credential installation requirement.
- Verified production installation on Home Assistant OS: Version 0.1.0 ran through Ingress, collected 436 entities (66 unavailable, 102 unknown), persisted SQLite data across reload, and produced a validated downloadable JSON audit bundle.
- Recorded the five passing Version 0.1 smoke tests and tagged the verified baseline as `v0.1.0`.

The project operating documentation is in [`docs/`](docs/README.md), including the [documentation changelog](docs/CHANGELOG.md).

## 0.1.0 - 2026-07-26

- Added the first Home Assistant app definition with Ingress support.
- Added FastAPI health and snapshot UI.
- Added read-only REST/WebSocket collection and SQLite persistence.
- Added JSON audit bundle downloads and unit tests.
- Hardened FastAPI startup and made templates/assets independent of the working directory.
- Added API smoke tests for health, Ingress rendering, snapshot execution, persistence, and audit downloads.
