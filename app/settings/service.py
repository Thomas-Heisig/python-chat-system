import json
from typing import TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_config
from app.core.events import event_bus
from app.database.repositories.settings_repository import SettingsRepository
from app.settings.cache import SettingsCache
from app.settings.defaults import DEFAULT_SETTINGS
from app.settings.validator import validate_setting


CandidateScope: TypeAlias = tuple[int | None, int | None]


def _strip_model_key_prefix(key: str) -> str:
    if not key.startswith("model_"):
        return key

    rest = key[len("model_"):]
    model_id_raw, separator, suffix = rest.partition("_")
    if separator != "_" or not model_id_raw.isdigit() or not suffix:
        return key
    return suffix


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        cfg = get_config()
        self.repo = SettingsRepository(session)
        self.cache = SettingsCache(ttl_seconds=cfg.settings_cache_ttl_seconds)

    async def get(
        self,
        category: str,
        key: str,
        user_id: int | None = None,
        team_id: int | None = None,
        request_value: object | None = None,
    ) -> object:
        normalized_key = _strip_model_key_prefix(key)

        if request_value is not None:
            return validate_setting(category, key, request_value)

        cached = self.cache.get(category, key, user_id, team_id)
        if cached is not None:
            return cached

        candidates: list[CandidateScope] = [
            (user_id, team_id),
            (None, team_id),
            (None, None),
        ]

        for c_user, c_team in candidates:
            item = await self.repo.get_setting(category, key, user_id=c_user, team_id=c_team)
            if item is not None:
                value = json.loads(item.value_json)
                value = validate_setting(category, key, value)
                self.cache.set(category, key, value, user_id, team_id)
                return value

        if normalized_key != key:
            for c_user, c_team in candidates:
                item = await self.repo.get_setting(category, normalized_key, user_id=c_user, team_id=c_team)
                if item is not None:
                    value = json.loads(item.value_json)
                    value = validate_setting(category, key, value)
                    self.cache.set(category, key, value, user_id, team_id)
                    return value

        fallback = DEFAULT_SETTINGS.get((category, key))
        if fallback is None and normalized_key != key:
            fallback = DEFAULT_SETTINGS.get((category, normalized_key))
        value = validate_setting(category, key, fallback)
        self.cache.set(category, key, value, user_id, team_id)
        return value

    async def update(
        self,
        category: str,
        key: str,
        value: object,
        user_id: int | None = None,
        team_id: int | None = None,
    ) -> str:
        normalized = validate_setting(category, key, value)
        await self.repo.upsert_setting(category, key, normalized, user_id=user_id, team_id=team_id)
        self.cache.invalidate(category=category, key=key, user_id=user_id, team_id=team_id)
        await event_bus.publish("settings_updated", {"category": category, "key": key})

        if category == "model" and key in {"base_directories"}:
            return "model_rescan_required"
        if category == "model" and key in {"active_model_id", "backend"}:
            return "model_reload_required"
        if category == "database" and key == "url":
            return "restart_required"
        return "applied"
