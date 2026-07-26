# The Archivist

The Archivist is a local Home Assistant app/add-on that creates read-only snapshots of entity state and registry data. It runs without Codex or ChatGPT and stores app-owned data under `/data`.

## Version 1

The Ingress page provides a manual **Run Snapshot** action, a health endpoint at `/health`, a summary of entity health, and a downloadable JSON audit bundle. The collector uses `SUPERVISOR_TOKEN` with the Home Assistant REST API for states and the WebSocket API for entity, device, and area registries. Registry failures are tolerated and recorded as empty collections.

The foundation reserves these future module names: `Archivist`, `Watcher`, `Curator`, `Oracle`, and `Steward`. AI analysis and configuration repair are intentionally out of scope.

## Local installation

1. Build the image with Docker: `docker build --build-arg BUILD_FROM=python:3.12-slim-bookworm -t the-archivist .`
2. Run it with a persistent data directory and a token: `docker run --rm -p 8099:8099 -v archivist-data:/data -e SUPERVISOR_TOKEN=... the-archivist`
3. Open `http://localhost:8099/`.

For Home Assistant, place this repository in a local add-on repository, install **The Archivist**, and open it through the Ingress panel. The app definition enables Ingress and maps the add-on data directory. The token is normally injected by Supervisor; do not put it in the repository or app options.

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
