from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading


TERMINAL_PULL_STATES = {"completed", "error", "cancelled"}
ACTIVE_PULL_STATES = {"queued", "pulling", "cancelling"}


@dataclass(slots=True)
class OllamaPullStatus:
    state: str
    detail: str | None = None
    progress_percent: int | None = None
    total: int | None = None
    completed: int | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "detail": self.detail,
            "progress_percent": self.progress_percent,
            "total": self.total,
            "completed": self.completed,
            "updated_at": self.updated_at,
        }


class OllamaPullRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, OllamaPullStatus] = {}
        self._cancel_events: dict[str, threading.Event] = {}

    def get(self, key: str) -> OllamaPullStatus | None:
        with self._lock:
            return self._items.get(key)

    def is_active(self, key: str) -> bool:
        status = self.get(key)
        return status is not None and status.state in ACTIVE_PULL_STATES

    def begin(
        self,
        key: str,
        *,
        state: str,
        detail: str | None = None,
        progress_percent: int | None = None,
    ) -> threading.Event:
        cancel_event = threading.Event()
        with self._lock:
            self._cancel_events[key] = cancel_event
        self.set(key, state=state, detail=detail, progress_percent=progress_percent)
        return cancel_event

    def get_cancel_event(self, key: str) -> threading.Event | None:
        with self._lock:
            return self._cancel_events.get(key)

    def request_cancel(self, key: str) -> OllamaPullStatus | None:
        with self._lock:
            cancel_event = self._cancel_events.get(key)
        if cancel_event is None:
            return None
        cancel_event.set()
        return self.set(key, state="cancelling", detail="Abbruch angefordert")

    def set(
        self,
        key: str,
        *,
        state: str,
        detail: str | None = None,
        progress_percent: int | None = None,
        total: int | None = None,
        completed: int | None = None,
    ) -> OllamaPullStatus:
        status = OllamaPullStatus(
            state=state,
            detail=detail,
            progress_percent=progress_percent,
            total=total,
            completed=completed,
        )
        with self._lock:
            self._items[key] = status
            if state in TERMINAL_PULL_STATES:
                self._cancel_events.pop(key, None)
        return status

    def clear(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)
            self._cancel_events.pop(key, None)


ollama_pull_registry = OllamaPullRegistry()