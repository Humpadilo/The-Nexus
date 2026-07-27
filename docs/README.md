# The Nexus Documentation

The Nexus is the long-term project name for a local-first Home Operating System. Home Assistant is the execution platform, while The Nexus is the product identity and shared architectural vocabulary.

## Current status

Version `0.6.0` is the current verified Home Assistant release. Sprint 7 implementation is version `0.7.0` in the repository but remains pending live Supervisor deployment verification. Implemented modules include Archivist, Watcher, the Semantic Layer, Dashboard / Nexus Experience, Curator, Raven, and the bounded Engineer proposal path. The current runtime keeps restoration proposals read-only: it does not apply production changes.

The following are not implemented in this repository: Planner, Oracle, Tracy, broad AI analysis, YAML generation, SmartThings integration, house modes, occupancy intelligence, voice control, and unrelated production changes. The only Engineer path is the bounded House Mode proposal workflow; application is intentionally unavailable in the read-only Sprint 7 runtime.

## Vision

The Nexus should help a household understand and maintain its automation system while keeping control local, explicit, reversible, and understandable. The intended progression is:

```text
Observe → Recommend → Approve → Apply
```

Version 0.6 stops at read-only diagnosis, organization, observation, reporting, and evidence-backed context.

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
- [IDEA_INBOX.md](IDEA_INBOX.md) — uncommitted future concepts and their initial constraints
- [CHANGELOG.md](CHANGELOG.md) — documentation history for the project
- [Root README](../README.md) — installation and developer instructions
- [Root CHANGELOG](../CHANGELOG.md) — release changelog
