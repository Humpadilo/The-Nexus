"""Home Assistant service bridge for The Archivist add-on."""

from __future__ import annotations

import aiohttp
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall

DOMAIN = "archivist"
SERVICE_RUN_CURATOR = "run_curator"
CONF_ENDPOINT_URL = "endpoint_url"
CONF_TRIGGER_TOKEN = "trigger_token"
DEFAULT_ENDPOINT_URL = "http://the_archivist:8099"
LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    options = config.get(DOMAIN, {}) or {}
    endpoint_url = str(options.get(CONF_ENDPOINT_URL) or DEFAULT_ENDPOINT_URL).rstrip("/")
    raw_trigger_token = options.get(CONF_TRIGGER_TOKEN)
    trigger_token = str(raw_trigger_token).strip() if raw_trigger_token else ""
    trigger_token_prefix = trigger_token[:6] if trigger_token else "<none>"

    LOGGER.warning(
        "Archivist Curator bridge configured: endpoint_url=%s "
        "trigger_token_loaded=%s trigger_token_prefix=%s "
        "authorization_header_configured=%s",
        endpoint_url,
        bool(trigger_token),
        trigger_token_prefix,
        bool(trigger_token),
    )

    async def handle_run_curator(_: ServiceCall) -> None:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {trigger_token}"} if trigger_token else {}
            LOGGER.warning(
                "Archivist Curator request: endpoint_url=%s "
                "trigger_token_loaded=%s trigger_token_prefix=%s "
                "authorization_header_sent=%s",
                endpoint_url,
                bool(trigger_token),
                trigger_token_prefix,
                "Authorization" in headers,
            )
            async with session.post(f"{endpoint_url}/curator/export", headers=headers) as response:
                if response.status >= 400:
                    raise RuntimeError(await response.text())

    hass.services.async_register(DOMAIN, SERVICE_RUN_CURATOR, handle_run_curator, schema=vol.Schema({}))
    return True
