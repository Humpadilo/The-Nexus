"""Configurable local background snapshot scheduling."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from archivist.collector.service import Collector

logger = logging.getLogger(__name__)


class WatcherScheduler:
    """Run the existing read-only collector at a configured interval."""

    def __init__(self, collector_factory: Callable[[], Collector], interval_hours: int) -> None:
        self.collector_factory = collector_factory
        self.interval_seconds = interval_hours * 60 * 60

    async def run(self) -> None:
        while True:
            await asyncio.sleep(self.interval_seconds)
            try:
                result = await self.collector_factory().run()
                logger.info("scheduled_watcher_check_completed", extra={"snapshot_id": result.snapshot_id})
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("scheduled_watcher_check_failed")

