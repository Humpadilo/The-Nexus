# Institutional Memory

This file records why the project works the way it does. It should evolve when facts, assumptions, or lessons change. Do not use it as a task list; use [SPRINTS.md](SPRINTS.md) for active work and [DECISIONS.md](DECISIONS.md) for formal architecture decisions.

## Current project identity

The Nexus is the long-term system direction. The Archivist is the implemented Version 0.1 subsystem. The name separation prevents future modules from being confused with the current collector.

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
- A real Home Assistant OS installation test remains an operational verification step.

## Rejected or deferred ideas

Automatic repair, hidden background intelligence, direct reading of protected Home Assistant files, and cloud-only operation are outside the current foundation and conflict with the project rules.

## Lessons so far

Packaging requirements are part of the product, not an afterthought. A project can pass Python unit tests while still failing Home Assistant app validation, image labeling, permissions, or repository discovery.
