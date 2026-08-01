"""Home Assistant service bridge for The Archivist add-on."""

from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall

DOMAIN = "archivist"
SERVICE_RUN_CURATOR = "run_curator"
CONF_ENDPOINT_URL = "endpoint_url"
CONF_TRIGGER_TOKEN = "trigger_token"
DEFAULT_ENDPOINT_URL = "http://the_archivist:8099"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    options = config.get(DOMAIN, {}) or {}
    endpoint_url = str(options.get(CONF_ENDPOINT_URL, DEFAULT_ENDPOINT_URL)).rstrip("/")
    trigger_token = str(options.get(CONF_TRIGGER_TOKEN, "")).strip()

    async def handle_run_curator(_: ServiceCall) -> None:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {trigger_token}"} if trigger_token else {}
            async with session.post(f"{endpoint_url}/curator/export", headers=headers) as response:
                if response.status >= 400:
                    raise RuntimeError(await response.text())

    hass.services.async_register(DOMAIN, SERVICE_RUN_CURATOR, handle_run_curator, schema=vol.Schema({}))
    return True
