"""Read-only Home Assistant REST and WebSocket client."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class HomeAssistantApiError(RuntimeError):
    """Raised when Home Assistant cannot satisfy a read-only request."""


class HomeAssistantClient:
    def __init__(self, rest_url: str, ws_url: str, token: str | None, timeout: float = 20.0) -> None:
        self.rest_url, self.ws_url, self.token = rest_url.rstrip("/"), ws_url, token
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"} if self.token else {}

    async def get_states(self) -> list[dict[str, Any]]:
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.rest_url}/states") as response:
                    if response.status != 200:
                        raise HomeAssistantApiError(f"states request returned HTTP {response.status}")
                    return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HomeAssistantApiError(str(exc)) from exc

    async def get_json(self, path: str) -> Any:
        """Read a JSON endpoint through the Home Assistant API proxy."""
        if not path.startswith("/"):
            path = f"/{path}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.rest_url}{path}") as response:
                    if response.status != 200:
                        raise HomeAssistantApiError(f"{path} request returned HTTP {response.status}")
                    return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HomeAssistantApiError(str(exc)) from exc

    async def get_text(self, path: str) -> str:
        """Read a text endpoint through the Home Assistant API proxy."""
        if not path.startswith("/"):
            path = f"/{path}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.rest_url}{path}") as response:
                    if response.status != 200:
                        raise HomeAssistantApiError(f"{path} request returned HTTP {response.status}")
                    return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HomeAssistantApiError(str(exc)) from exc

    async def get_supervisor_json(self, path: str) -> Any:
        """Read a Supervisor API endpoint; this is only used for GET requests."""
        if not self.token:
            raise HomeAssistantApiError("SUPERVISOR_TOKEN is not configured")
        if not path.startswith("/"):
            path = f"/{path}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"http://supervisor{path}") as response:
                    if response.status != 200:
                        raise HomeAssistantApiError(f"Supervisor {path} request returned HTTP {response.status}")
                    return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HomeAssistantApiError(str(exc)) from exc

    async def get_configuration(self, domain: str, object_id: str) -> dict[str, Any]:
        """Read one UI-managed automation/script/scene configuration."""
        if domain not in {"automation", "script", "scene"}:
            raise HomeAssistantApiError(f"unsupported configuration domain: {domain}")
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.rest_url}/config/{domain}/config/{object_id}") as response:
                    if response.status != 200:
                        raise HomeAssistantApiError(
                            f"{domain} configuration request returned HTTP {response.status}"
                        )
                    payload = await response.json()
                    return payload if isinstance(payload, dict) else {"value": payload}
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HomeAssistantApiError(str(exc)) from exc

    async def get_configurations(self, states: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Best-effort read of loaded UI-managed configurations for diagnosis."""
        configurations: dict[str, dict[str, Any]] = {}
        for state in states:
            entity_id = str(state.get("entity_id", ""))
            domain, separator, object_id = entity_id.partition(".")
            config_id = (state.get("attributes") or {}).get("id")
            if not separator or domain not in {"automation", "script", "scene"} or not config_id:
                continue
            try:
                configurations[entity_id] = await self.get_configuration(domain, str(config_id))
            except HomeAssistantApiError:
                continue
        return configurations

    async def save_configuration(self, domain: str, object_id: str, configuration: dict[str, Any]) -> dict[str, Any]:
        """Persist one UI-managed configuration after an explicit approval."""
        if domain not in {"automation", "script", "scene"}:
            raise HomeAssistantApiError(f"unsupported configuration domain: {domain}")
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.post(f"{self.rest_url}/config/{domain}/config/{object_id}", json=configuration) as response:
                    if response.status != 200:
                        raise HomeAssistantApiError(f"{domain} configuration save returned HTTP {response.status}")
                    payload = await response.json()
                    return payload if isinstance(payload, dict) else {"value": payload}
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HomeAssistantApiError(str(exc)) from exc

    async def reload_domain(self, domain: str) -> None:
        """Reload only the approved Home Assistant domain."""
        if domain not in {"automation", "script", "scene"}:
            raise HomeAssistantApiError(f"unsupported reload domain: {domain}")
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.post(f"{self.rest_url}/services/{domain}/reload", json={}) as response:
                    if response.status not in {200, 201}:
                        raise HomeAssistantApiError(f"{domain} reload returned HTTP {response.status}")
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HomeAssistantApiError(str(exc)) from exc

    async def websocket_command(self, command: str, **payload: Any) -> Any:
        if not self.token:
            raise HomeAssistantApiError("SUPERVISOR_TOKEN is not configured")
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                async with session.ws_connect(self.ws_url) as websocket:
                    greeting = await websocket.receive_json()
                    if greeting.get("type") != "auth_required":
                        raise HomeAssistantApiError("unexpected Home Assistant WebSocket greeting")
                    await websocket.send_json({"type": "auth", "access_token": self.token})
                    auth = await websocket.receive_json()
                    if auth.get("type") != "auth_ok":
                        raise HomeAssistantApiError("Home Assistant WebSocket authentication failed")
                    await websocket.send_json({"id": 1, "type": command, **payload})
                    result = await websocket.receive_json()
                    if not result.get("success"):
                        raise HomeAssistantApiError(result.get("error", {}).get("message", "WebSocket command failed"))
                    return result.get("result") or []
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                raise HomeAssistantApiError(str(exc)) from exc

    async def get_registries(self) -> dict[str, list[dict[str, Any]]]:
        registries: dict[str, list[dict[str, Any]]] = {}
        commands = {
            "entities": "config/entity_registry/list",
            "devices": "config/device_registry/list",
            "areas": "config/area_registry/list",
            "floors": "config/floor_registry/list",
            "labels": "config/label_registry/list",
        }
        for name, command in commands.items():
            try:
                registries[name] = await self.websocket_command(command)
            except HomeAssistantApiError:
                registries[name] = []
        return registries
