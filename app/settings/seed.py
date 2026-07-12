from sqlalchemy.ext.asyncio import AsyncSession
from app.settings.defaults import DEFAULT_SETTINGS
from app.settings.service import SettingsService


async def seed_default_settings(session: AsyncSession) -> None:
    service = SettingsService(session)
    for (category, key), value in DEFAULT_SETTINGS.items():
        existing = await service.repo.get_setting(category=category, key=key, user_id=None, team_id=None)
        if existing is None:
            await service.update(category, key, value)
