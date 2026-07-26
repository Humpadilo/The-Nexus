# Changelog

The project operating documentation is in [`docs/`](docs/README.md), including the [documentation changelog](docs/CHANGELOG.md).

## 0.1.0 - 2026-07-26

- Added the first Home Assistant app definition with Ingress support.
- Added FastAPI health and snapshot UI.
- Added read-only REST/WebSocket collection and SQLite persistence.
- Added JSON audit bundle downloads and unit tests.
- Hardened FastAPI startup and made templates/assets independent of the working directory.
- Added API smoke tests for health, Ingress rendering, snapshot execution, persistence, and audit downloads.
