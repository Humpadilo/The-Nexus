# The Archivist

The Archivist is a local Home Assistant app/add-on that creates read-only snapshots of entity state and registry data. It runs without Codex or ChatGPT and stores app-owned data under `/data`.

The long-term project documentation is maintained under [`docs/`](docs/README.md). Start with the [Nexus documentation overview](docs/README.md), then use the [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), [project rules](docs/PROJECT_RULES.md), and [decisions](docs/DECISIONS.md) for context.

## Version 1

The Ingress page provides a manual **Run Snapshot** action, a health endpoint at `/health`, a summary of entity health, and a downloadable JSON audit bundle. The collector uses `SUPERVISOR_TOKEN` with the Home Assistant REST API for states and the WebSocket API for entity, device, and area registries. Registry failures are tolerated and recorded as empty collections.

The foundation reserves these future module names: `Archivist`, `Watcher`, `Curator`, `Oracle`, and `Steward`. AI analysis and configuration repair are intentionally out of scope.

## Home Assistant OS installation

1. Publish this repository to a Git host, keeping `repository.yaml` at the repository root.
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

Sprint 1 verification covers health, Ingress rendering, static assets, manual snapshot execution with a fake Home Assistant client, SQLite persistence, and JSON audit downloads. A real Home Assistant OS installation and live API collection still require a Home Assistant host.

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
