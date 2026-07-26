# Institutional Memory

This file records why the project works the way it does. It should evolve when facts, assumptions, or lessons change. Do not use it as a task list; use [SPRINTS.md](SPRINTS.md) for active work and [DECISIONS.md](DECISIONS.md) for formal architecture decisions.

## Verified Version 0.1 production baseline

On 2026-07-26, Version 0.1.0 was installed from `https://github.com/Humpadilo/The-Nexus` into Home Assistant OS. The app started successfully, its Ingress page loaded, and a live snapshot collected 436 entities, including 66 unavailable and 102 unknown entities. The snapshot remained available after an Ingress reload, confirming SQLite persistence. The 706,362-byte JSON audit bundle was downloaded and parsed successfully. The local test suite reported 5 passing tests. This baseline is tagged `v0.1.0`.

The formal Sprint 1 verification close is tagged `v0.1.0-verified`. During the Version 0.2.0 live smoke test on 2026-07-26, Supervisor's stale repository clone was bypassed by adding a fresh public `.git` repository source and reinstalling the app. The upgraded app started successfully, Ingress loaded, two live snapshots completed, and the second snapshot produced 438 entities, 20 unavailable, 122 unknown, and 143 persisted Watcher findings. The 942,137-byte audit bundle and 218,015-byte findings export were downloaded and parsed successfully. The current release is tagged `v0.2.0`.

Watcher begins from this persisted snapshot model. It remains read-only and local; it does not require Codex, ChatGPT, or a cloud service.

## Current project identity

The Nexus is the long-term system direction. The Archivist is the implemented Version 0.1 subsystem. The name separation prevents future modules from being confused with the current collector.

Version 0.3 adds the implemented Semantic Knowledge Foundation. It is a rebuildable projection of stored Home Assistant state and registry data, not an independent source of truth. Its dashboard-oriented facts provide stable labels, relationships, grouping, health, provenance, and confidence for the future Curator UI.

Version 0.4 adds The Nexus Dashboard as a read-only consumer of semantic facts and Watcher findings. Live Version 0.3 verification produced snapshot 4 with 437 entities, 20 unavailable, 120 unknown, 1,379 semantic facts, 60 devices, and 8 areas. Version 0.4.0 was then verified on Home Assistant OS: Ingress loaded, the dashboard rendered live semantic data, a manual snapshot collected 436 entities, 59 devices, and 8 areas, and its audit bundle parsed with 1,375 facts and provenance. Version 0.4.5 added the presentation-only Nexus Experience; live verification confirmed Version 0.4.5 running in Home Assistant, module-oriented Ingress navigation, a snapshot of 437 entities, 60 devices, and 8 areas, and an audit bundle with 1,379 facts and provenance. The verified release is tagged `v0.4.5-verified`.

## Local-first assumption

The Archivist runs as a Home Assistant app and continues operating without Codex or ChatGPT. This preserves local control and makes collection and reporting available even when development tools or cloud services are unavailable.

## Home Assistant facts and quirks

- Home Assistant apps receive persistent storage at `/data`.
- The app uses the Supervisor proxy and `SUPERVISOR_TOKEN` for Home Assistant Core API access.
- REST state collection and WebSocket registry collection are separate operations.
- Registry data may not be accessible on every installation or version, so Version 0.1 treats registry collection as best effort.
- Home Assistant app packaging has its own metadata, architecture, Ingress, and repository requirements; Docker success alone is not installation proof.

## Storage philosophy

SQLite is runtime state. JSON is an exported audit representation, not the source of truth for live persistence. App-owned data stays under the app data directory.

## Security memory

The project intentionally avoids `secrets.yaml`, authentication files, integration credentials, backups, `core.config_entries`, and arbitrary access-token stores. Version 0.1 does not modify Home Assistant configuration.

## Naming conventions

- The Nexus: the long-term project and documentation umbrella.
- The Archivist: the current collector and snapshot subsystem.
- Watcher, Curator, Oracle, Steward, Laboratory: future subsystem names and boundaries.
- Version numbers describe project maturity, not the presence of every named subsystem.

## SmartThings assumptions

No SmartThings integration or implementation is present in this repository. Any SmartThings architecture, migration, or device model is an unconfirmed future assumption and must be specified before implementation.

## House Modes and dashboards

No house-mode model or dashboard system is implemented here. Future work must define the data source, ownership, user interaction, privacy implications, and failure behavior before treating either as an architecture commitment.

## Known limitations

- Version 0.1 does not monitor continuously.
- Version 0.1 does not use AI.
- Version 0.1 does not repair or write Home Assistant configuration.
- Low-battery and automation classifications are best-effort state-derived summaries.
- Registry availability depends on Home Assistant API support and permissions.
- The original Version 0.1 data was not visible after the Supervisor repository rebind; Version 0.2.0 persistence was re-verified with fresh live snapshots. Future upgrades should preserve and explicitly verify `/data` continuity.

## Rejected or deferred ideas

Automatic repair, hidden background intelligence, direct reading of protected Home Assistant files, and cloud-only operation are outside the current foundation and conflict with the project rules.

## Lessons so far

Packaging requirements are part of the product, not an afterthought. A project can pass Python unit tests while still failing Home Assistant app validation, image labeling, permissions, or repository discovery.
