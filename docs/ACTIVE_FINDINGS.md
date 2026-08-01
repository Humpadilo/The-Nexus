# Council Findings Register

found_date: 2026-08-01
project: The Nexus / The Archivist
scope: Curator setup, deployment, backend, application, automation, data quality, and testing
consumer: AI analysis, Raven, and Watcher
status_values: OPEN | IN_PROGRESS | READY_FOR_VERIFICATION | VERIFIED | CLOSED
severity_values: CRITICAL | HIGH | MEDIUM | LOW
category_values: SECURITY | DEPLOYMENT | BACKEND | APP | AUTOMATION | DATA_QUALITY | TESTING | DOCUMENTATION | COMPATIBILITY
office_values: Raven | Engineer | Watcher | Curator
source_values: Curator Report | Manual Review | Static Analysis | Live Testing | User Report

## Maintenance Rules

- This file contains verified or directly observed Curator issues only.
- Every issue has a stable ID. Do not reuse an ID after deletion.
- Never delete resolved findings. Move verified or closed findings into `Resolved/` while preserving their IDs, history, fix evidence, and resolution date.
- Use the lifecycle in order: `OPEN` → `IN_PROGRESS` → `READY_FOR_VERIFICATION` → `VERIFIED` → `CLOSED`.
- `first_seen` is immutable and records when the finding was first discovered. Add a future `last_updated` field only when update history requires it.
- Do not mark an issue `VERIFIED` without evidence from code, tests, or a live Home Assistant report.
- Raven and Watcher may parse the fields below. Keep field names stable and values concise.
- `source` identifies how the finding was discovered. `evidence` identifies the technical proof. `verification` identifies what must prove resolution.

## Issue Index

| ID | Severity | Category | Status | Office | Short description |
|---|---|---|---|---|---|
| CURATOR-SEC-001 | HIGH | SECURITY | READY_FOR_VERIFICATION | Raven | Export trigger and ZIP download have no authentication |
| CURATOR-DEP-001 | HIGH | DEPLOYMENT | OPEN | Engineer | Home Assistant service bridge requires manual installation |
| CURATOR-DEP-002 | HIGH | DEPLOYMENT | OPEN | Engineer | Default add-on hostname may not resolve from Home Assistant Core |
| CURATOR-COMP-001 | MEDIUM | COMPATIBILITY | READY_FOR_VERIFICATION | Engineer | Custom integration manifest does not declare service type |
| CURATOR-DATA-001 | HIGH | DATA_QUALITY | READY_FOR_VERIFICATION | Curator | Integration device counts use the wrong identifier relationship |
| CURATOR-DATA-002 | MEDIUM | DATA_QUALITY | OPEN | Curator | Recorder history summary is a permanent placeholder |
| CURATOR-DATA-003 | MEDIUM | DATA_QUALITY | OPEN | Curator | Registry failures are indistinguishable from empty registries |
| CURATOR-BACK-001 | MEDIUM | BACKEND | OPEN | Curator | WebSocket result handling changes valid falsey values to lists |
| CURATOR-BACK-002 | MEDIUM | BACKEND | VERIFIED | Curator | Same-minute exports overwrite an earlier ZIP |
| CURATOR-APP-001 | MEDIUM | APP | OPEN | Engineer | Export requests wait for the complete export operation |
| CURATOR-APP-002 | LOW | APP | OPEN | Engineer | Service calls do not report the generated archive to the user |
| CURATOR-APP-003 | MEDIUM | APP | OPEN | Engineer | Service bridge has no explicit HTTP timeout |
| CURATOR-AUTO-001 | MEDIUM | AUTOMATION | OPEN | Watcher | Concurrent triggers return an error instead of sharing job status |
| CURATOR-TEST-001 | HIGH | TESTING | VERIFIED | Engineer | New Curator trigger routes lack committed automated tests |
| CURATOR-TEST-002 | HIGH | TESTING | OPEN | Engineer | Custom integration is not tested inside Home Assistant |
| CURATOR-TEST-003 | MEDIUM | TESTING | OPEN | Engineer | Full local test suite is not green because of temp-directory permissions |

## Issues

## CURATOR-SEC-001

severity: HIGH
category: SECURITY
status: READY_FOR_VERIFICATION
office: Raven
source: Manual Review
depends_on: []
title: Export trigger and ZIP download have no authentication
first_seen: 2026-08-01
impact: Any caller that can reach the Archivist HTTP port may trigger a full house intelligence export and download the latest ZIP.
risk: House intelligence data could be exposed or exports could be triggered by an unauthorized caller.
evidence: `archivist/main.py` exposes `POST /curator/export` and `GET /curator/export/latest.zip` without a token, session check, or origin check.
root_cause: The service bridge trusts network reachability as authorization.
recommended_fix: Require a dedicated internal token or authenticated request for both routes. Send the token from the Home Assistant custom integration and dashboard path.
fix_evidence: Added bearer-token enforcement to both routes, configured the dashboard to send the token, and configured the Home Assistant bridge to send the token.
verification: Unauthenticated requests return 401/403; authorized dashboard and Home Assistant service requests succeed; ingress continues to work.

## CURATOR-DEP-001

severity: HIGH
category: DEPLOYMENT
status: OPEN
office: Engineer
source: User Report
depends_on: []
title: Home Assistant service bridge requires manual installation
first_seen: 2026-08-01
impact: Updating the Archivist add-on does not automatically install or register `archivist.run_curator`.
risk: Users may believe the official execution path is available when the service is not installed.
evidence: `custom_components/archivist/` is separate from the add-on image and README instructions require copying it into `/config/custom_components/archivist/` and restarting Home Assistant.
root_cause: Home Assistant custom integrations and add-ons have separate installation lifecycles.
fix_evidence: Add-on version `0.8.2` now publishes `curator_trigger_token` in both `options` and `schema`; application settings already consume the Supervisor-provided option.
recommended_fix: Provide a documented, repeatable installation path and a startup health check that clearly reports whether the service bridge is installed and reachable. Consider a companion integration repository or managed package later.
verification: A clean installation can update the add-on and obtain a working `archivist.run_curator` service without undocumented manual steps.

## CURATOR-DEP-002

severity: HIGH
category: DEPLOYMENT
status: OPEN
office: Engineer
source: User Report
depends_on: CURATOR-DEP-001
title: Default add-on hostname may not resolve from Home Assistant Core
first_seen: 2026-08-01
impact: The Home Assistant service can fail even while the add-on is running.
risk: Automated or user-triggered reports may silently remain unavailable after deployment.
evidence: `custom_components/archivist/__init__.py` defaults to `http://the_archivist:8099`, while the installed add-on may have a generated hostname. README already instructs users to replace the hostname if necessary.
root_cause: The service bridge depends on an environment-specific container DNS name.
recommended_fix: Determine the stable Home Assistant add-on hostname or expose the endpoint through a supported internal address. Add a connectivity diagnostic to the service bridge.
verification: From Home Assistant Core, the configured endpoint resolves and `archivist.run_curator` completes successfully.

## CURATOR-COMP-001

severity: MEDIUM
category: COMPATIBILITY
status: READY_FOR_VERIFICATION
office: Engineer
source: Static Analysis
depends_on: []
title: Custom integration manifest does not declare service type
first_seen: 2026-08-01
impact: Home Assistant currently falls back to treating the integration as a hub, which is semantically incorrect and may become stricter in a future release.
risk: A future Home Assistant release may reject or mishandle the integration manifest.
evidence: `custom_components/archivist/manifest.json` has no `integration_type` field.
root_cause: The service-only integration manifest is incomplete.
fix_evidence: Added `integration_type: service` to the custom integration manifest.
recommended_fix: Add `integration_type: service` and validate the manifest against the target Home Assistant release.
verification: Home Assistant validates the manifest without warnings and displays the integration as a service integration.

## CURATOR-DATA-001

severity: HIGH
category: DATA_QUALITY
status: READY_FOR_VERIFICATION
office: Curator
source: Static Analysis
depends_on: []
title: Integration device counts use the wrong identifier relationship
first_seen: 2026-08-01
impact: `integrations.json` can report zero devices for integrations that own devices.
risk: AI analysis may draw incorrect conclusions about integration coverage and device ownership.
evidence: `archivist/curator/exporter.py` compares an integration name with each device's `config_entries`; those values are configuration-entry IDs, not integration names.
root_cause: Device registry relationships are being interpreted as integration names.
fix_evidence: Integration counts now resolve device config-entry IDs through `config_entries/get`; an automated regression test verifies the mapping.
recommended_fix: Resolve device config-entry IDs through config entries, then map each entry to its integration domain before counting.
verification: Integration device totals reconcile with device registry relationships in a live report.

## CURATOR-DATA-002

severity: MEDIUM
category: DATA_QUALITY
status: OPEN
office: Curator
source: Static Analysis
depends_on: []
title: Recorder history summary is a permanent placeholder
first_seen: 2026-08-01
impact: The report does not provide first recorded date, latest recorded date, recorder status, or event/logbook history summaries.
risk: AI analysis cannot reliably reason about observation age, recorder health, or historical coverage.
evidence: `archivist/curator/exporter.py` returns `available: false` and null dates from `history_summary()`.
root_cause: The exporter currently collects statistics metadata but not recorder history metadata.
recommended_fix: Add safe recorder metadata/history-summary queries without exporting months of raw history.
verification: A live report contains real recorder dates and explicitly distinguishes unavailable recorder data from an empty database.

## CURATOR-DATA-003

severity: MEDIUM
category: DATA_QUALITY
status: OPEN
office: Curator
source: Static Analysis
depends_on: []
title: Registry failures are indistinguishable from empty registries
first_seen: 2026-08-01
impact: Missing entities, devices, areas, floors, or labels may be misinterpreted as genuinely absent.
risk: A partial or failed report may be treated as a complete representation of the house.
evidence: `archivist/api/home_assistant.py:get_registries()` catches API errors and substitutes empty lists without recording which request failed.
root_cause: The registry client has no per-source failure result.
recommended_fix: Return structured registry results containing `available`, `items`, and `error`, and preserve failures in `errors.json`.
verification: An intentionally unavailable registry endpoint produces a named error rather than an empty successful list.

## CURATOR-BACK-001

severity: MEDIUM
category: BACKEND
status: OPEN
office: Curator
source: Static Analysis
depends_on: []
title: WebSocket result handling changes valid falsey values to lists
first_seen: 2026-08-01
impact: Empty objects, false values, or other valid falsey Home Assistant results are converted to `[]`, creating schema ambiguity.
risk: Downstream AI and automation consumers may misparse valid Home Assistant responses.
evidence: `archivist/api/home_assistant.py:websocket_command()` returns `result.get("result") or []`.
root_cause: The client uses a collection default for every WebSocket command.
recommended_fix: Return the actual result value and only normalize missing results when the command contract explicitly requires a list.
verification: Empty mappings and falsey scalar results retain their original JSON types.

## CURATOR-BACK-002

severity: MEDIUM
category: BACKEND
status: VERIFIED
office: Curator
source: Static Analysis
depends_on: []
title: Same-minute exports overwrite an earlier ZIP
first_seen: 2026-08-01
impact: Repeated exports within the same minute can destroy the previous report by reusing its filename.
risk: Historical intelligence packages can be lost before they are analyzed.
evidence: `archivist/curator/exporter.py:_write_zip()` names archives with `%Y-%m-%d_%H%M` only.
root_cause: Archive identity is based on minute-level wall-clock time.
fix_evidence: Archive creation now preserves the original minute-based name and adds a numeric suffix when that name already exists; an automated regression test verifies two same-minute exports remain distinct.
recommended_fix: Include seconds and/or a unique suffix in the archive filename. Preserve the latest-report pointer separately.
verification: Two exports started within one minute produce two distinct ZIP files.

## CURATOR-APP-001

severity: MEDIUM
category: APP
status: OPEN
office: Engineer
source: Static Analysis
depends_on: CURATOR-AUTO-001
title: Export requests wait for the complete export operation
first_seen: 2026-08-01
impact: Dashboard and Home Assistant callers remain blocked while every Curator section is collected.
risk: Slow exports may cause UI timeouts or unreliable automation behavior.
evidence: `archivist/main.py` awaits `create_export()` directly inside `POST /curator/export`.
root_cause: There is no background job or asynchronous export status model.
recommended_fix: Start a tracked background job, return a job ID, expose status, and retain the completed archive URL.
verification: Trigger requests return promptly and callers can observe queued, running, failed, and completed states.

## CURATOR-APP-002

severity: LOW
category: APP
status: OPEN
office: Engineer
source: Static Analysis
depends_on: CURATOR-APP-001
title: Service calls do not report the generated archive to the user
first_seen: 2026-08-01
impact: A successful `archivist.run_curator` call gives no filename, download link, or completion event.
risk: Users and automations may not know whether a usable report was created.
evidence: `custom_components/archivist/__init__.py` checks the HTTP status but discards the response JSON.
root_cause: Home Assistant service calls have no user-facing result contract in the bridge.
recommended_fix: Fire a completion event or create a persistent notification containing the filename and download location.
verification: A service call produces an observable completion result without shell access.

## CURATOR-APP-003

severity: MEDIUM
category: APP
status: OPEN
office: Engineer
source: Static Analysis
depends_on: []
title: Service bridge has no explicit HTTP timeout
first_seen: 2026-08-01
impact: A network failure or stalled export endpoint may leave the Home Assistant service call waiting too long.
risk: A stalled add-on could consume automation execution time and make the service appear hung.
evidence: `custom_components/archivist/__init__.py` creates `aiohttp.ClientSession()` without an explicit timeout.
root_cause: Request duration is left to library defaults rather than an application policy.
recommended_fix: Configure a bounded connect and total timeout, with a clear logged error.
verification: A stalled endpoint fails within the documented timeout and Home Assistant remains responsive.

## CURATOR-AUTO-001

severity: MEDIUM
category: AUTOMATION
status: OPEN
office: Watcher
source: Static Analysis
depends_on: CURATOR-APP-001
title: Concurrent triggers return an error instead of sharing job status
first_seen: 2026-08-01
impact: A dashboard click, service call, or future automation triggered during an existing export receives HTTP 409 and no way to follow the active job.
risk: Scheduled or overlapping triggers may produce missed reports and ambiguous automation outcomes.
evidence: `archivist/main.py` uses a process-local lock and returns 409 when it is locked.
root_cause: The trigger has a mutual exclusion guard but no durable job state.
recommended_fix: Return the active job status or job ID for duplicate triggers and make the lock state observable.
verification: Concurrent calls do not lose the caller's request; they receive a clear active-job response.

## CURATOR-TEST-001

severity: HIGH
category: TESTING
status: VERIFIED
office: Engineer
source: Static Analysis
depends_on: []
title: New Curator trigger routes lack committed automated tests
first_seen: 2026-08-01
impact: Regressions in POST triggering, locking, ZIP retrieval, and failure responses can reach production unnoticed.
risk: Trigger failures may only be discovered after a user attempts a production export.
evidence: `tests/test_web.py` covers older Curator snapshot routes but not `/curator/export` or `/curator/export/latest.zip`.
root_cause: The endpoint was smoke-tested manually but the test was not added to the repository.
fix_evidence: Added automated coverage for bearer authorization, successful trigger, latest ZIP download, and unauthorized download access.
recommended_fix: Add tests with a mocked exporter for success, failure, concurrent calls, and latest ZIP download.
verification: The route tests run in CI and cover all trigger outcomes.

## CURATOR-TEST-002

severity: HIGH
category: TESTING
status: OPEN
office: Engineer
source: Static Analysis
depends_on: CURATOR-DEP-001
title: Custom integration is not tested inside Home Assistant
first_seen: 2026-08-01
impact: Syntax checks do not prove that the service registers, resolves the endpoint, or works with the installed Home Assistant release.
risk: Deployment can appear successful while the official Home Assistant service remains unusable.
evidence: The repository only performs Python syntax validation for `custom_components/archivist`; no Home Assistant integration test exists.
root_cause: The add-on and Home Assistant Core are tested as separate environments.
recommended_fix: Add a minimal Home Assistant test or a documented live verification checklist covering integration load and service invocation.
verification: The target Home Assistant version loads the integration and exposes `archivist.run_curator` after restart.

## CURATOR-TEST-003

severity: MEDIUM
category: TESTING
status: OPEN
office: Engineer
source: Live Testing
depends_on: []
title: Full local test suite is not green because of temp-directory permissions
first_seen: 2026-08-01
impact: Repository health cannot be established from the current Windows test run.
risk: Real regressions may be hidden among environment-related test failures.
evidence: `python -m pytest -q` produced 15 passed and 11 setup errors, all involving `PermissionError: [WinError 5]` for `C:\Users\matth\AppData\Local\Temp\pytest-of-matth`.
root_cause: The pytest temporary directory is inaccessible, likely due to permissions or a process lock.
recommended_fix: Configure a repository-local test temp directory or repair the Windows temp-directory permissions, then rerun the complete suite.
verification: `python -m pytest -q` completes with zero errors.
