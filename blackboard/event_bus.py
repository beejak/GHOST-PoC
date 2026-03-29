"""asyncio.Queue wrapper for Watcher -> Healer events."""

from __future__ import annotations

import asyncio
from typing import Any

from skills.watcher_skills import EVENT_SCHEMA


class EventBus:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def publish(self, event: dict[str, Any]) -> None:
        self._validate_event(event)
        await self._queue.put(event)

    async def consume(self) -> dict[str, Any]:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    @staticmethod
    def _validate_event(event: dict[str, Any]) -> None:
        for key, typ in EVENT_SCHEMA.items():
            if key not in event:
                raise KeyError(f"Event missing key {key!r}")
            if not isinstance(event[key], typ):
                raise TypeError(
                    f"Event[{key!r}] expected {typ.__name__}, got {type(event[key]).__name__}"
                )
