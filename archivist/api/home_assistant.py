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

    async def websocket_command(self, command: str, **payload: Any) -> list[dict[str, Any]]:
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
        commands = {"entities": "config/entity_registry/list", "devices": "config/device_registry/list", "areas": "config/area_registry/list"}
        for name, command in commands.items():
            try:
                registries[name] = await self.websocket_command(command)
            except HomeAssistantApiError:
                registries[name] = []
        return registries
