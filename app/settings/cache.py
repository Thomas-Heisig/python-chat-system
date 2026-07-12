import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    value: object
    expires_at: float


class SettingsCache:
    def __init__(self, ttl_seconds: int = 5) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, CacheEntry] = {}

    def _key(self, category: str, key: str, user_id: int | None, team_id: int | None) -> str:
        return f"{category}:{key}:u:{user_id}:t:{team_id}"

    def get(self, category: str, key: str, user_id: int | None, team_id: int | None) -> object | None:
        cache_key = self._key(category, key, user_id, team_id)
        entry = self._store.get(cache_key)
        if entry is None:
            return None
        if time.time() > entry.expires_at:
            self._store.pop(cache_key, None)
            return None
        return entry.value

    def set(self, category: str, key: str, value: object, user_id: int | None, team_id: int | None) -> None:
        cache_key = self._key(category, key, user_id, team_id)
        self._store[cache_key] = CacheEntry(value=value, expires_at=time.time() + self.ttl_seconds)

    def invalidate(self, category: str, key: str, user_id: int | None = None, team_id: int | None = None) -> None:
        prefix = f"{category}:{key}:"
        for item_key in list(self._store.keys()):
            if item_key.startswith(prefix):
                self._store.pop(item_key, None)

    def clear(self) -> None:
        self._store.clear()
