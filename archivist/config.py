"""Application configuration sourced from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("ARCHIVIST_DATA_DIR", "/data"))
    host: str = os.getenv("ARCHIVIST_HOST", "0.0.0.0")
    port: int = int(os.getenv("ARCHIVIST_PORT", "8099"))
    ha_rest_url: str = os.getenv("SUPERVISOR_CORE_API", "http://supervisor/core/api")
    ha_ws_url: str = os.getenv("SUPERVISOR_CORE_WS", "ws://supervisor/core/websocket")
    supervisor_token: str | None = os.getenv("SUPERVISOR_TOKEN")

    @property
    def database_path(self) -> Path:
        return self.data_dir / "archivist.db"

    @property
    def bundles_dir(self) -> Path:
        return self.data_dir / "bundles"
