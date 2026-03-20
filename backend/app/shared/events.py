from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator

import structlog

logger = structlog.get_logger()


class EventBus:
    """Server-Sent Events broadcasting system.

    Channels are typically keyed by user ID or resource type.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """Subscribe to a channel. Yields events as they arrive."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[channel].append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._subscribers[channel].remove(queue)

    async def publish(self, channel: str, event: dict) -> None:
        """Publish event to all subscribers of a channel."""
        for queue in self._subscribers[channel]:
            await queue.put(event)

    @property
    def subscriber_count(self) -> int:
        return sum(len(subs) for subs in self._subscribers.values())


# Global event bus instance
event_bus = EventBus()
