"""Application configuration sourced from environment variables."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


def _options() -> dict[str, Any]:
    """Read only app options written by Supervisor, when available."""
    path = Path(os.getenv("ARCHIVIST_OPTIONS_FILE", "/data/options.json"))
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


_APP_OPTIONS = _options()


def _running_in_home_assistant_addon() -> bool:
    """Detect the Supervisor-injected add-on runtime without requiring a token value."""
    return bool(os.getenv("SUPERVISOR_TOKEN") or os.getenv("SUPERVISOR_CORE_API") or Path("/data/options.json").exists())


def _option_bool(name: str, default: bool) -> bool:
    value = os.getenv(f"ARCHIVIST_{name.upper()}")
    if value is None:
        value = _APP_OPTIONS.get(name, default)
    return str(value).lower() in {"1", "true", "yes", "on"}


def _option_int(name: str, default: int) -> int:
    value = os.getenv(f"ARCHIVIST_{name.upper()}", _APP_OPTIONS.get(name, default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("ARCHIVIST_DATA_DIR", "/data"))
    host: str = os.getenv("ARCHIVIST_HOST", "0.0.0.0")
    port: int = int(os.getenv("ARCHIVIST_PORT", "8099"))
    ha_rest_url: str = os.getenv("SUPERVISOR_CORE_API", "http://supervisor/core/api")
    ha_ws_url: str = os.getenv("SUPERVISOR_CORE_WS", "ws://supervisor/core/websocket")
    supervisor_token: str | None = os.getenv("SUPERVISOR_TOKEN") or None
    runtime_environment: str = "home_assistant_addon" if _running_in_home_assistant_addon() else "standalone"
    schedule_enabled: bool = _option_bool("schedule_enabled", True)
    schedule_interval_hours: int = max(1, _option_int("schedule_interval_hours", 24))
    finding_retention_days: int = max(30, _option_int("finding_retention_days", 365))

    @property
    def database_path(self) -> Path:
        return self.data_dir / "archivist.db"

    @property
    def bundles_dir(self) -> Path:
        return self.data_dir / "bundles"

    @property
    def curator_export_dir(self) -> Path:
        """Use persistent add-on storage, while retaining a convenient local default."""
        configured = os.getenv("ARCHIVIST_EXPORT_DIR")
        if configured:
            return Path(configured)
        if self.runtime_environment == "home_assistant_addon":
            return self.data_dir / "Inventory" / "Exports"
        return Path.cwd() / "Inventory" / "Exports"
