from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Any


class PromptDiagnosticsStore:
    def __init__(self, max_entries: int = 200) -> None:
        self._max_entries = max_entries
        self._entries: deque[dict[str, Any]] = deque(maxlen=max_entries)
        self._lock = Lock()

    def add(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._entries.append(payload)

    def list_entries(self, *, user_id: int | None = None, limit: int = 20) -> list[dict[str, Any]]:
        limit_normalized = max(1, min(200, int(limit)))
        with self._lock:
            items = list(self._entries)

        if user_id is not None:
            items = [entry for entry in items if entry.get("user_id") == user_id]

        return items[-limit_normalized:]


prompt_diagnostics_store = PromptDiagnosticsStore()
