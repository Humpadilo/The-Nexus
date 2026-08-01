# The Archivist

The Archivist is a local Home Assistant app/add-on that creates read-only snapshots of entity state and registry data. It runs without Codex or ChatGPT and stores app-owned data under `/data`.

The long-term project documentation is maintained under [`docs/`](docs/README.md). Start with the [Nexus documentation overview](docs/README.md), then use the [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), [project rules](docs/PROJECT_RULES.md), and [decisions](docs/DECISIONS.md) for context.

## Version 0.6.0 — Raven

The Ingress page now includes Raven, a read-only diagnostic layer that investigates selected entities, helpers, automations, scripts, scenes, and concepts using snapshot evidence and available Home Assistant configuration reads. It traces explicit execution paths, identifies broken or unavailable dependencies, persists human-readable diagnoses, and provides downloadable evidence. It does not add automatic repair, AI reasoning, or Home Assistant writes.

Watcher checks run daily by default. The Home Assistant app options `schedule_enabled`, `schedule_interval_hours`, and `finding_retention_days` control local scheduling and resolved-finding retention. Semantic projections are rebuildable from stored Home Assistant state and registry data; raw snapshots remain authoritative. All behavior remains read-only.

The current architecture includes implemented modules `Archivist`, `Watcher`, `Semantic Layer`, `Dashboard / Nexus Experience`, `Curator`, and `Raven`, plus the first bounded Engineer proposal workflow. Planned modules are `Planner`, `Oracle`, and `Tracy`. Broad AI analysis and automatic repair remain out of scope; this workflow cannot write production without explicit approval.

## Home Assistant OS installation

1. Use the public repository URL: `https://github.com/Humpadilo/The-Nexus`.
2. In Home Assistant, open **Settings → Apps → App store**, choose the menu in the upper-right, and add the repository URL.
3. Find **The Archivist**, install it, and start it.
4. Open the app through the **Ingress** button in its Home Assistant app page.

The app requests only the Home Assistant Core API proxy permission. Supervisor injects `SUPERVISOR_TOKEN` at runtime; do not add a token to the repository or app options. The app stores its SQLite database and generated bundles in its persistent `/data` directory.

For local development, place the repository in Home Assistant's local app repository, then reload the app store and install **The Archivist** from the local repository.

## Local container development

1. Build the image with Docker: `docker build -t the-archivist .`
2. Run it with a persistent data directory and a token: `docker run --rm -p 8099:8099 -v archivist-data:/data -e SUPERVISOR_TOKEN=... the-archivist`
3. Open `http://localhost:8099/`.

The app definition enables Ingress on port 8099 and maps the add-on data directory. The Dockerfile uses an explicit Python 3.12 base image; the obsolete `build.yaml` file is no longer required by current Home Assistant app builds.

Sprint 1 was verified live on Home Assistant OS and is tagged `v0.1.0-verified`. Version 0.2 adds Watcher comparison and scheduling. Version 0.3 adds the rebuildable semantic projection and is tagged `v0.3.0-verified`. Version 0.4 adds The Nexus Dashboard and is tagged `v0.4.0-verified`. Version 0.4.5 adds The Nexus Experience and is tagged `v0.4.5-verified`. Version 0.5 adds Curator and is tagged `v0.5.0-verified`. Version 0.6 adds Raven and is tagged `v0.6.0-verified` after live Home Assistant diagnosis verification.

## Safety and permissions

The app only calls read-only API endpoints. It does not read `secrets.yaml`, authentication files, access tokens beyond the injected Supervisor token, integration credentials, backups, or `core.config_entries`, and it does not write Home Assistant configuration. Registry commands depend on the Home Assistant version and token scope.

## Development

```text
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
pytest
python -m archivist.main
```

Structured logs are emitted as JSON to stdout. SQLite, generated bundles, and future app configuration belong in `/data` in the container (override with `ARCHIVIST_DATA_DIR` for local development).

### Curator intelligence export

Inside the Home Assistant add-on, run `python -m archivist.curator.exporter`; it automatically uses the Supervisor-injected `SUPERVISOR_TOKEN`, the internal Core API proxy, and persistent `/data/Inventory/Exports/` storage. For standalone development, the same command uses `./Inventory/Exports/` (or `--output-dir`) and records missing tokens, unreachable APIs, and unavailable sections in `system.json` and `errors.json`. No service calls or recorder-history bulk export are performed.

### Deploy and verify Curator in Home Assistant

The Curator must be executed inside the Archivist app container for a production report. The add-on manifest requests both the Home Assistant Core API proxy and the Supervisor API, and version `0.8.2` is the deployment marker for the trigger-token configuration and trigger-based exporter.

1. Build the updated add-on. If using a local Home Assistant add-on repository, copy or pull this repository into the local repository directory, then build it from the Home Assistant host:

   ```bash
   ha addons rebuild the_archivist
   ```

   If the Home Assistant installation does not provide `rebuild`, reload the local add-on repository, open **Settings → Apps → The Archivist**, and use **Rebuild** from the add-on menu. For a standalone Docker build, run `docker build -t the-archivist:0.8.0 .`; that image is not a production Home Assistant verification.

2. Install or update the add-on from **Settings → Apps → The Archivist**. Confirm that the installed version is `0.8.2`, start the add-on, and wait until its health/status is running. The add-on must retain `homeassistant_api: true` and `hassio_api: true` in its manifest.

3. Run the Curator inside the add-on. From the Home Assistant host terminal or an SSH session, identify the container with `docker ps --format '{{.Names}}' | grep archivist`, then run:

   ```bash
   docker exec <archivist-container-name> /usr/local/bin/curator-export
   ```

   The command is also available as `python -m archivist.curator.exporter`. It writes to `/data/Inventory/Exports/` inside the add-on and performs read-only Core and Supervisor API reads.

4. Retrieve the ZIP from the add-on's mapped data directory. From the Home Assistant host, use:

   ```bash
   docker cp <archivist-container-name>:/data/Inventory/Exports/Curator_Report_YYYY-MM-DD_HHMM.zip .
   ```

   Alternatively, copy the file from the Home Assistant `/data` mapping used by the add-on. Do not use a report generated from the repository workstation as a production report.

5. Verify the report is executing inside Home Assistant. Inspect `system.json` and confirm:

   ```json
   {
     "environment": "home_assistant_addon",
     "supervisor_token_available": true,
     "degraded": false
   }
   ```

   Also confirm that `entity_count`, `device_count`, and `area_count` are populated, `errors.json` has no base API/token errors, and `supervisor.json`, `config.json`, `entities.json`, and `devices.json` contain real installation data. If the report says `standalone`, the command was run outside the add-on container.

### Official trigger path

The exporter remains unchanged and the shell command is retained for debugging, but normal use no longer requires shell access. The Archivist ingress page now provides **Generate intelligence ZIP**, which calls `POST /curator/export` and downloads the newest package.

The Curator trigger is bearer-token protected. Set a long random `curator_trigger_token` in the add-on configuration, then use the same value in the Home Assistant bridge configuration below. The dashboard receives the configured token server-side and uses it for the button and ZIP download.

For the Home Assistant service `archivist.run_curator`, copy `custom_components/archivist/` into `/config/custom_components/archivist/`, then add this to `configuration.yaml`:

```yaml
archivist:
  endpoint_url: http://the_archivist:8099
  trigger_token: REPLACE_WITH_THE_SAME_RANDOM_TOKEN
```

Restart Home Assistant, then call:

```yaml
service: archivist.run_curator
```

If `the_archivist` is not resolvable from Core, set `endpoint_url` to the Archivist app hostname shown on the app information page, retaining port `8099`. The bridge performs only an authenticated HTTP POST to the add-on's read-only trigger. The ZIP download also requires the bearer token.
