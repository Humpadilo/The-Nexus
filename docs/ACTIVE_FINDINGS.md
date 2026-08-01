# Curator Issue Register

found_date: 2026-08-01
project: The Nexus / The Archivist
scope: Curator setup, deployment, backend, application, automation, data quality, and testing
consumer: AI analysis, Raven, and Watcher
status_values: OPEN | BLOCKED | VERIFIED
severity_values: CRITICAL | HIGH | MEDIUM | LOW
category_values: SECURITY | DEPLOYMENT | BACKEND | APP | AUTOMATION | DATA_QUALITY | TESTING | DOCUMENTATION | COMPATIBILITY

## Maintenance Rules

- This file contains verified or directly observed Curator issues only.
- Every issue has a stable ID. Do not reuse an ID after deletion.
- When an issue is fixed, verify the fix, then delete the entire issue block.
- Do not mark an issue fixed without evidence from code, tests, or a live Home Assistant report.
- Raven and Watcher may parse the fields below. Keep field names stable and values concise.
- `source` identifies the code or documentation evidence. `verification` identifies what must prove resolution.

## Issue Index

| ID | Severity | Category | Status | Short description |
|---|---|---|---|---|
| CURATOR-SEC-001 | HIGH | SECURITY | OPEN | Export trigger and ZIP download have no authentication |
| CURATOR-DEP-001 | HIGH | DEPLOYMENT | OPEN | Home Assistant service bridge requires manual installation |
| CURATOR-DEP-002 | HIGH | DEPLOYMENT | OPEN | Default add-on hostname may not resolve from Home Assistant Core |
| CURATOR-COMP-001 | MEDIUM | COMPATIBILITY | OPEN | Custom integration manifest does not declare service type |
| CURATOR-DATA-001 | HIGH | DATA_QUALITY | OPEN | Integration device counts use the wrong identifier relationship |
| CURATOR-DATA-002 | MEDIUM | DATA_QUALITY | OPEN | Recorder history summary is a permanent placeholder |
| CURATOR-DATA-003 | MEDIUM | DATA_QUALITY | OPEN | Registry failures are indistinguishable from empty registries |
| CURATOR-BACK-001 | MEDIUM | BACKEND | OPEN | WebSocket result handling changes valid falsey values to lists |
| CURATOR-BACK-002 | MEDIUM | BACKEND | OPEN | Same-minute exports overwrite an earlier ZIP |
| CURATOR-APP-001 | MEDIUM | APP | OPEN | Export requests wait for the complete export operation |
| CURATOR-APP-002 | LOW | APP | OPEN | Service calls do not report the generated archive to the user |
| CURATOR-APP-003 | MEDIUM | APP | OPEN | Service bridge has no explicit HTTP timeout |
| CURATOR-AUTO-001 | MEDIUM | AUTOMATION | OPEN | Concurrent triggers return an error instead of sharing job status |
| CURATOR-TEST-001 | HIGH | TESTING | OPEN | New Curator trigger routes lack committed automated tests |
| CURATOR-TEST-002 | HIGH | TESTING | OPEN | Custom integration is not tested inside Home Assistant |
| CURATOR-TEST-003 | MEDIUM | TESTING | OPEN | Full local test suite is not green because of temp-directory permissions |

## Issues

## CURATOR-SEC-001

severity: HIGH
category: SECURITY
status: OPEN
title: Export trigger and ZIP download have no authentication
found_date: 2026-08-01
impact: Any caller that can reach the Archivist HTTP port may trigger a full house intelligence export and download the latest ZIP.
evidence: `archivist/main.py` exposes `POST /curator/export` and `GET /curator/export/latest.zip` without a token, session check, or origin check.
root_cause: The service bridge trusts network reachability as authorization.
recommended_fix: Require a dedicated internal token or authenticated request for both routes. Send the token from the Home Assistant custom integration and dashboard path.
verification: Unauthenticated requests return 401/403; authorized dashboard and Home Assistant service requests succeed; ingress continues to work.

## CURATOR-DEP-001

severity: HIGH
category: DEPLOYMENT
status: OPEN
title: Home Assistant service bridge requires manual installation
found_date: 2026-08-01
impact: Updating the Archivist add-on does not automatically install or register `archivist.run_curator`.
evidence: `custom_components/archivist/` is separate from the add-on image and README instructions require copying it into `/config/custom_components/archivist/` and restarting Home Assistant.
root_cause: Home Assistant custom integrations and add-ons have separate installation lifecycles.
recommended_fix: Provide a documented, repeatable installation path and a startup health check that clearly reports whether the service bridge is installed and reachable. Consider a companion integration repository or managed package later.
verification: A clean installation can update the add-on and obtain a working `archivist.run_curator` service without undocumented manual steps.

## CURATOR-DEP-002

severity: HIGH
category: DEPLOYMENT
status: OPEN
title: Default add-on hostname may not resolve from Home Assistant Core
found_date: 2026-08-01
impact: The Home Assistant service can fail even while the add-on is running.
evidence: `custom_components/archivist/__init__.py` defaults to `http://the_archivist:8099`, while the installed add-on may have a generated hostname. README already instructs users to replace the hostname if necessary.
root_cause: The service bridge depends on an environment-specific container DNS name.
recommended_fix: Determine the stable Home Assistant add-on hostname or expose the endpoint through a supported internal address. Add a connectivity diagnostic to the service bridge.
verification: From Home Assistant Core, the configured endpoint resolves and `archivist.run_curator` completes successfully.

## CURATOR-COMP-001

severity: MEDIUM
category: COMPATIBILITY
status: OPEN
title: Custom integration manifest does not declare service type
found_date: 2026-08-01
impact: Home Assistant currently falls back to treating the integration as a hub, which is semantically incorrect and may become stricter in a future release.
evidence: `custom_components/archivist/manifest.json` has no `integration_type` field.
root_cause: The service-only integration manifest is incomplete.
recommended_fix: Add `integration_type: service` and validate the manifest against the target Home Assistant release.
verification: Home Assistant validates the manifest without warnings and displays the integration as a service integration.

## CURATOR-DATA-001

severity: HIGH
category: DATA_QUALITY
status: OPEN
title: Integration device counts use the wrong identifier relationship
found_date: 2026-08-01
impact: `integrations.json` can report zero devices for integrations that own devices.
evidence: `archivist/curator/exporter.py` compares an integration name with each device's `config_entries`; those values are configuration-entry IDs, not integration names.
root_cause: Device registry relationships are being interpreted as integration names.
recommended_fix: Resolve device config-entry IDs through config entries, then map each entry to its integration domain before counting.
verification: Integration device totals reconcile with device registry relationships in a live report.

## CURATOR-DATA-002

severity: MEDIUM
category: DATA_QUALITY
status: OPEN
title: Recorder history summary is a permanent placeholder
found_date: 2026-08-01
impact: The report does not provide first recorded date, latest recorded date, recorder status, or event/logbook history summaries.
evidence: `archivist/curator/exporter.py` returns `available: false` and null dates from `history_summary()`.
root_cause: The exporter currently collects statistics metadata but not recorder history metadata.
recommended_fix: Add safe recorder metadata/history-summary queries without exporting months of raw history.
verification: A live report contains real recorder dates and explicitly distinguishes unavailable recorder data from an empty database.

## CURATOR-DATA-003

severity: MEDIUM
category: DATA_QUALITY
status: OPEN
title: Registry failures are indistinguishable from empty registries
found_date: 2026-08-01
impact: Missing entities, devices, areas, floors, or labels may be misinterpreted as genuinely absent.
evidence: `archivist/api/home_assistant.py:get_registries()` catches API errors and substitutes empty lists without recording which request failed.
root_cause: The registry client has no per-source failure result.
recommended_fix: Return structured registry results containing `available`, `items`, and `error`, and preserve failures in `errors.json`.
verification: An intentionally unavailable registry endpoint produces a named error rather than an empty successful list.

## CURATOR-BACK-001

severity: MEDIUM
category: BACKEND
status: OPEN
title: WebSocket result handling changes valid falsey values to lists
found_date: 2026-08-01
impact: Empty objects, false values, or other valid falsey Home Assistant results are converted to `[]`, creating schema ambiguity.
evidence: `archivist/api/home_assistant.py:websocket_command()` returns `result.get("result") or []`.
root_cause: The client uses a collection default for every WebSocket command.
recommended_fix: Return the actual result value and only normalize missing results when the command contract explicitly requires a list.
verification: Empty mappings and falsey scalar results retain their original JSON types.

## CURATOR-BACK-002

severity: MEDIUM
category: BACKEND
status: OPEN
title: Same-minute exports overwrite an earlier ZIP
found_date: 2026-08-01
impact: Repeated exports within the same minute can destroy the previous report by reusing its filename.
evidence: `archivist/curator/exporter.py:_write_zip()` names archives with `%Y-%m-%d_%H%M` only.
root_cause: Archive identity is based on minute-level wall-clock time.
recommended_fix: Include seconds and/or a unique suffix in the archive filename. Preserve the latest-report pointer separately.
verification: Two exports started within one minute produce two distinct ZIP files.

## CURATOR-APP-001

severity: MEDIUM
category: APP
status: OPEN
title: Export requests wait for the complete export operation
found_date: 2026-08-01
impact: Dashboard and Home Assistant callers remain blocked while every Curator section is collected.
evidence: `archivist/main.py` awaits `create_export()` directly inside `POST /curator/export`.
root_cause: There is no background job or asynchronous export status model.
recommended_fix: Start a tracked background job, return a job ID, expose status, and retain the completed archive URL.
verification: Trigger requests return promptly and callers can observe queued, running, failed, and completed states.

## CURATOR-APP-002

severity: LOW
category: APP
status: OPEN
title: Service calls do not report the generated archive to the user
found_date: 2026-08-01
impact: A successful `archivist.run_curator` call gives no filename, download link, or completion event.
evidence: `custom_components/archivist/__init__.py` checks the HTTP status but discards the response JSON.
root_cause: Home Assistant service calls have no user-facing result contract in the bridge.
recommended_fix: Fire a completion event or create a persistent notification containing the filename and download location.
verification: A service call produces an observable completion result without shell access.

## CURATOR-APP-003

severity: MEDIUM
category: APP
status: OPEN
title: Service bridge has no explicit HTTP timeout
found_date: 2026-08-01
impact: A network failure or stalled export endpoint may leave the Home Assistant service call waiting too long.
evidence: `custom_components/archivist/__init__.py` creates `aiohttp.ClientSession()` without an explicit timeout.
root_cause: Request duration is left to library defaults rather than an application policy.
recommended_fix: Configure a bounded connect and total timeout, with a clear logged error.
verification: A stalled endpoint fails within the documented timeout and Home Assistant remains responsive.

## CURATOR-AUTO-001

severity: MEDIUM
category: AUTOMATION
status: OPEN
title: Concurrent triggers return an error instead of sharing job status
found_date: 2026-08-01
impact: A dashboard click, service call, or future automation triggered during an existing export receives HTTP 409 and no way to follow the active job.
evidence: `archivist/main.py` uses a process-local lock and returns 409 when it is locked.
root_cause: The trigger has a mutual exclusion guard but no durable job state.
recommended_fix: Return the active job status or job ID for duplicate triggers and make the lock state observable.
verification: Concurrent calls do not lose the caller's request; they receive a clear active-job response.

## CURATOR-TEST-001

severity: HIGH
category: TESTING
status: OPEN
title: New Curator trigger routes lack committed automated tests
found_date: 2026-08-01
impact: Regressions in POST triggering, locking, ZIP retrieval, and failure responses can reach production unnoticed.
evidence: `tests/test_web.py` covers older Curator snapshot routes but not `/curator/export` or `/curator/export/latest.zip`.
root_cause: The endpoint was smoke-tested manually but the test was not added to the repository.
recommended_fix: Add tests with a mocked exporter for success, failure, concurrent calls, and latest ZIP download.
verification: The route tests run in CI and cover all trigger outcomes.

## CURATOR-TEST-002

severity: HIGH
category: TESTING
status: OPEN
title: Custom integration is not tested inside Home Assistant
found_date: 2026-08-01
impact: Syntax checks do not prove that the service registers, resolves the endpoint, or works with the installed Home Assistant release.
evidence: The repository only performs Python syntax validation for `custom_components/archivist`; no Home Assistant integration test exists.
root_cause: The add-on and Home Assistant Core are tested as separate environments.
recommended_fix: Add a minimal Home Assistant test or a documented live verification checklist covering integration load and service invocation.
verification: The target Home Assistant version loads the integration and exposes `archivist.run_curator` after restart.

## CURATOR-TEST-003

severity: MEDIUM
category: TESTING
status: OPEN
title: Full local test suite is not green because of temp-directory permissions
found_date: 2026-08-01
impact: Repository health cannot be established from the current Windows test run.
evidence: `python -m pytest -q` produced 15 passed and 11 setup errors, all involving `PermissionError: [WinError 5]` for `C:\Users\matth\AppData\Local\Temp\pytest-of-matth`.
root_cause: The pytest temporary directory is inaccessible, likely due to permissions or a process lock.
recommended_fix: Configure a repository-local test temp directory or repair the Windows temp-directory permissions, then rerun the complete suite.
verification: `python -m pytest -q` completes with zero errors.
