from __future__ import annotations

import asyncio

import pytest

from app.shared.events import EventBus


@pytest.mark.asyncio
async def test_event_bus_publish_delivers_event_and_cleans_up() -> None:
    bus = EventBus()
    stream = bus.subscribe("jobs")

    receive_task = asyncio.create_task(anext(stream))
    await asyncio.sleep(0)
    assert bus.subscriber_count == 1

    payload = {"type": "job_updated", "id": "abc123"}
    await bus.publish("jobs", payload)

    assert await asyncio.wait_for(receive_task, timeout=1) == payload
    await stream.aclose()
    await asyncio.sleep(0)
    assert bus.subscriber_count == 0


@pytest.mark.asyncio
async def test_event_bus_publish_without_subscribers_is_noop() -> None:
    bus = EventBus()
    await bus.publish("empty", {"type": "noop"})
    assert bus.subscriber_count == 0
