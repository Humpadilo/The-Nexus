# The Nexus Documentation

The Nexus is the long-term project name for a local-first Home Assistant operating system. The repository currently contains the first working subsystem, **The Archivist**. The Nexus is the direction and shared vocabulary; The Archivist is the implementation that exists today.

## Current status

Version `0.1.0` is the foundation release. It is a Home Assistant app with Ingress, a FastAPI web interface, a health endpoint, read-only Home Assistant REST and WebSocket collection, SQLite persistence, snapshot summaries, JSON audit bundles, structured logging, and unit tests.

The following are not implemented in this repository: AI analysis, automatic repair, YAML generation, approval workflows, monitoring, SmartThings integration, house modes, occupancy intelligence, voice control, and the future modules beyond the Archivist foundation.

## Vision

The Nexus should help a household understand and maintain its automation system while keeping control local, explicit, reversible, and understandable. The intended progression is:

```text
Observe → Explain → Recommend → Approve → Apply → Verify
```

Version 0.1 stops at observation and reporting.

## Goals

- Build a trustworthy local foundation for Home Assistant maintenance.
- Make system state inspectable without reading protected Home Assistant files.
- Keep future intelligence modular and replaceable.
- Make every later recommendation explainable and reviewable.
- Reduce maintenance burden instead of adding hidden automation behavior.

## Quick start

For Home Assistant installation, see the root [README](../README.md). For local development:

```text
python -m venv .venv
.venv/Scripts/activate
pip install -r ../requirements.txt
pytest
python -m archivist.main
```

The application stores runtime data in `/data` inside the app container. `ARCHIVIST_DATA_DIR` can override that location during local development.

## Repository structure

```text
archivist/       Python application package
tests/           Unit tests for collection, storage, and reports
rootfs/          Container startup script
config.yaml      Home Assistant app definition
Dockerfile       App image definition
repository.yaml  Home Assistant app repository metadata
docs/            Project operating documentation
```

## Documentation map

- [ARCHITECTURE.md](ARCHITECTURE.md) — technical design and boundaries
- [ROADMAP.md](ROADMAP.md) — major-version direction
- [SPEC.md](SPEC.md) — feature specification format and current foundation specification
- [SPRINTS.md](SPRINTS.md) — current and completed sprint record
- [PROJECT_RULES.md](PROJECT_RULES.md) — project constitution
- [TEAM.md](TEAM.md) — human, AI, and module responsibilities
- [MEMORY.md](MEMORY.md) — institutional memory and known assumptions
- [DECISIONS.md](DECISIONS.md) — architecture decision records
- [PARKING_LOT.md](PARKING_LOT.md) — ideas intentionally outside active work
- [CHANGELOG.md](CHANGELOG.md) — documentation history for the project
- [Root README](../README.md) — installation and developer instructions
- [Root CHANGELOG](../CHANGELOG.md) — release changelog
