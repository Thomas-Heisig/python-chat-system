import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


EventPayload = dict[str, Any]
EventHandler = Callable[[EventPayload], Awaitable[None]]


@dataclass
class Event:
    name: str
    payload: EventPayload


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    async def publish(self, event_name: str, payload: EventPayload) -> None:
        handlers = self._handlers.get(event_name, [])
        if not handlers:
            return
        await asyncio.gather(*(handler(payload) for handler in handlers))


event_bus = EventBus()
