# The Archivist

The Archivist is a local Home Assistant app/add-on that creates read-only snapshots of entity state and registry data. It runs without Codex or ChatGPT and stores app-owned data under `/data`.

The long-term project documentation is maintained under [`docs/`](docs/README.md). Start with the [Nexus documentation overview](docs/README.md), then use the [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), [project rules](docs/PROJECT_RULES.md), and [decisions](docs/DECISIONS.md) for context.

## Version 0.4 — The Nexus Dashboard

The Ingress page provides a polished read-only dashboard with Overview, Health, Explorer, Timeline, and Reports sections. It provides a manual **Run Snapshot** action, a health endpoint at `/health`, and downloadable JSON audit, findings, and semantic projection bundles. The dashboard uses versioned semantic entity, device, area, capability, and health facts plus Watcher findings; it does not add AI reasoning or Home Assistant writes.

Watcher checks run daily by default. The Home Assistant app options `schedule_enabled`, `schedule_interval_hours`, and `finding_retention_days` control local scheduling and resolved-finding retention. Semantic projections are rebuildable from stored Home Assistant state and registry data; raw snapshots remain authoritative. All behavior remains read-only.

The foundation reserves these future module names: `Archivist`, `Watcher`, `Curator`, `Oracle`, and `Steward`. AI analysis and configuration repair are intentionally out of scope.

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

Sprint 1 was verified live on Home Assistant OS and is tagged `v0.1.0-verified`. Version 0.2 adds Watcher comparison and scheduling. Version 0.3 adds the rebuildable semantic projection and is tagged `v0.3.0-verified`. Version 0.4 adds The Nexus Dashboard.

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
