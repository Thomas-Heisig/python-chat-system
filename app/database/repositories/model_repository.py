from sqlalchemy import select
from app.database.repositories.base_repository import BaseRepository
from app.db_models.model_config import ModelConfig


class ModelRepository(BaseRepository):
    async def list_models(self) -> list[ModelConfig]:
        result = await self.session.execute(select(ModelConfig).order_by(ModelConfig.name.asc()))
        return list(result.scalars().all())

    async def get_active_model(self) -> ModelConfig | None:
        result = await self.session.execute(select(ModelConfig).where(ModelConfig.is_active.is_(True)).limit(1))
        return result.scalar_one_or_none()
