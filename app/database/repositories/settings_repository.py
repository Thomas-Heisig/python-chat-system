import json
from sqlalchemy import select
from app.database.repositories.base_repository import BaseRepository
from app.db_models.setting import Setting


class SettingsRepository(BaseRepository):
    async def get_setting(self, category: str, key: str, user_id: int | None = None, team_id: int | None = None) -> Setting | None:
        stmt = (
            select(Setting)
            .where(Setting.category == category)
            .where(Setting.key == key)
            .where(Setting.user_id == user_id)
            .where(Setting.team_id == team_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_setting(
        self,
        category: str,
        key: str,
        value: object,
        user_id: int | None = None,
        team_id: int | None = None,
        description: str | None = None,
    ) -> Setting:
        item = await self.get_setting(category, key, user_id=user_id, team_id=team_id)
        if item is None:
            item = Setting(
                category=category,
                key=key,
                user_id=user_id,
                team_id=team_id,
                value_json=json.dumps(value, ensure_ascii=False),
                description=description,
            )
            self.session.add(item)
        else:
            item.value_json = json.dumps(value, ensure_ascii=False)
            item.description = description
        await self.session.flush()
        return item
