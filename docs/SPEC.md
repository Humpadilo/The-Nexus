# Feature Specifications

Every feature begins here before implementation. A specification is the boundary between an idea and an engineering commitment. It must identify what is being built, what is deliberately excluded, and how success will be tested.

## Required specification format

### Feature

Name the feature and identify its target version.

### Goal

State the user or system outcome in plain language.

### User story

Describe who needs the feature, what they want, and why.

### Requirements

List observable behavior, data contracts, security constraints, and operational requirements.

### Non-goals

State what will not be implemented in this feature.

### Dependencies

List code modules, Home Assistant APIs, storage, permissions, or prior versions required.

### Risks

Describe failure modes, privacy concerns, migration issues, and maintenance costs.

### Acceptance criteria

Use testable statements that determine whether the feature is complete.

### Test strategy

Describe unit, integration, fixture, and manual tests needed for confidence.

## Example: Foundation snapshot

### Feature

Manual Version 0.1 snapshot collection.

### Goal

Allow a user to collect a read-only point-in-time audit of available Home Assistant entity and registry data.

### User story

As a Home Assistant owner, I want to press one button to capture the current health-relevant state of my system so that I can inspect it later without changing anything.

### Requirements

- Run as a Home Assistant app with Ingress.
- Use the Supervisor-injected token for permitted read-only API access.
- Collect entity states.
- Attempt entity, device, and area registry collection.
- Persist a snapshot and entity observations in SQLite.
- Calculate total, unavailable, unknown, automation, and low-battery summary counts when discoverable.
- Provide a downloadable JSON audit bundle.
- Store app-owned data under `/data`.
- Continue to operate without Codex or ChatGPT.

### Non-goals

- AI analysis.
- Automatic repair.
- Writing Home Assistant configuration.
- Reading protected files or credentials.
- Background monitoring.

### Dependencies

- Home Assistant app Supervisor API proxy.
- FastAPI and aiohttp.
- SQLite.
- Python 3.12.

### Risks

- Registry commands can be unavailable or differ between Home Assistant versions.
- Some states do not expose enough metadata to classify battery or automation health.
- Large installations may produce large JSON bundles.

### Acceptance criteria

- The app metadata validates for Home Assistant.
- The app starts and serves `/health`.
- A successful manual run stores a snapshot.
- Registry failures do not prevent the state snapshot from being stored.
- The JSON bundle contains summary, entity observations, and registry sections.
- Unit tests cover collection orchestration, storage round trips, and summary generation.

### Test strategy

- Unit-test summary derivation with representative state fixtures.
- Unit-test SQLite snapshot round trips using a temporary database.
- Unit-test collection with a fake Home Assistant client.
- Perform a manual Home Assistant OS installation test before release.

## Feature: Semantic Knowledge Foundation (Version 0.3)

### Goal

Provide one deterministic, rebuildable semantic projection over raw Archivist snapshots so Watcher and Curator can share canonical facts without creating a second source of truth.

### User story

As a Home Assistant owner, I want collected entities, devices, areas, capabilities, and health states represented consistently so that the next dashboard can present my system clearly and trace every displayed fact back to its source.

### Requirements

- Derive semantic facts entirely from the stored snapshot's Home Assistant state and registry payloads.
- Keep raw snapshots and observations authoritative; semantic data must be replaceable and rebuildable.
- Provide versioned canonical facts for entities, devices, areas, capabilities, and health.
- Provide stable subject identifiers, display labels, domain/grouping fields, relationships, availability, expectedness, and health state.
- Attach snapshot and source evidence plus confidence to every fact.
- Provide summary counts and domain/availability/health groupings suitable for dashboard cards, filters, and drill-down views.
- Persist the projection locally in SQLite and expose a read-only machine-readable export.
- Preserve compatibility with existing Watcher findings and audit bundles.
- Degrade predictably when registry data is unavailable.

### Non-goals

- Curator UI or the rich visual dashboard itself.
- A general-purpose graph database or hidden ontology.
- AI inference, recommendations, notifications, repair, or Home Assistant writes.
- Replacing raw snapshots with semantic data.

### Dependencies

- Archivist snapshots and entity observations.
- Best-effort Home Assistant entity, device, and area registry payloads.
- SQLite schema migration from Version 0.2.

### Risks

- Home Assistant registry fields vary by version and integration.
- Overly broad capability inference could create misleading dashboard data.
- Derived data can drift if it is not rebuilt transactionally from raw snapshots.

### Acceptance criteria

- A stored snapshot can produce a versioned semantic projection without contacting Home Assistant again.
- Rebuilding the same snapshot produces identical facts, summaries, identifiers, relationships, provenance, and confidence.
- Every fact links to its snapshot and source observation or registry entry.
- Missing registry data does not prevent entity and health facts from being generated.
- The projection provides stable fields for dashboard grouping, filtering, summary cards, and entity/device/area drill-downs.
- Replacing a projection never changes the raw snapshot or Watcher findings.
- A semantic JSON export is available for a stored snapshot.
- Tests cover canonical models, dashboard-oriented fields, missing registries, persistence, rebuilds, collector integration, and export behavior.

### Test strategy

- Use fixture snapshots representing complete and incomplete registry responses.
- Compare repeated builds for deterministic semantic output.
- Round-trip projections through SQLite and replace them to verify rebuild safety.
- Verify the collector stores semantic data without changing raw summaries or findings.
- Verify the read-only semantic export and provenance fields.

## Feature: Watcher snapshot comparison (Version 0.2)

### Goal

Turn persisted Archivist snapshots into low-noise, evidence-backed health and change findings without modifying Home Assistant.

### User story

As a Home Assistant owner, I want the Archivist to show what changed since the last snapshot and whether an issue is new, ongoing, or resolved, so that I can investigate only meaningful conditions.

### Requirements

- Compare adjacent snapshots and detect unavailable/unknown transitions, added and removed entities, low batteries, and automation availability changes.
- Classify disabled registry entities as expected where registry data makes that distinction available.
- Persist one finding per stable category/entity fingerprint with severity, confidence, first-seen, last-seen, occurrence count, resolution status, and snapshot evidence.
- Update ongoing findings instead of creating duplicate rows.
- Run checks manually and on a configurable local schedule, daily by default.
- Show active and resolved findings in Ingress and export machine-readable findings JSON.
- Include findings in snapshot audit bundles and retain resolved findings for a configurable period.

### Non-goals

- AI analysis, recommendations, YAML generation, configuration changes, automatic repair, notifications, or cloud dependencies.

### Acceptance criteria

- Two snapshots produce persisted findings with evidence and stable fingerprints.
- Repeated unchanged conditions update one finding and its occurrence count.
- Recovery marks the same finding resolved.
- Manual and scheduled checks use the same read-only collection path.
- Tests cover detection, expected classification, deduplication, recovery, persistence, exports, and scheduling configuration.

## Feature: The Nexus Dashboard (Version 0.4)

The dashboard is a read-only presentation consumer of semantic projections and Watcher findings. It must not create a competing interpretation of Home Assistant data or add a write path.

### Acceptance criteria

- Ingress provides intuitive Overview, Health, Explorer, Timeline, and Reports sections.
- Overview shows latest snapshot, entity/device/area counts, finding counts, overall health, and recent activity.
- Health separates critical, warning, informational, and resolved Watcher findings.
- Explorer exposes semantic areas, devices, capabilities, relationships, entities, and health context.
- Timeline shows stored snapshot history and report links expose audit, semantic, and Watcher exports.
- Dashboard data remains usable when registries are incomplete and is derived from local SQLite records.
- Tests cover dashboard grouping, health classification, semantic rendering, and existing web endpoints.

## Feature: Curator (Version 0.5)

Curator is the canonical human-oriented organization projection over the Semantic Knowledge Foundation and Watcher evidence. It must remain rebuildable, read-only, and provenance-preserving.

### Acceptance criteria

- Area views organize devices and entities by registered area and expose `Unassigned` when area data is absent.
- Human concepts are deterministic groupings layered above Home Assistant domains and labels.
- Explicit relationships are navigable in both dependency directions and retain source evidence and confidence.
- Watcher findings include likely cause, impact, dependencies, recommended read-only repair guidance, confidence, evidence, and provenance.
- Curator data is available in Ingress and as a machine-readable JSON export.
- Missing configuration or registry data degrades to unknown rather than inferred dependencies.
- Tests cover area grouping, concepts, relationship extraction, actionable finding enrichment, export routes, and empty-state behavior.

### Non-goals

- Home Assistant writes, automatic repair, YAML generation, AI reasoning, notifications, or a replacement source of truth.
