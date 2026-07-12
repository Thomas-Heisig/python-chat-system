import json

from sqlalchemy import select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.training_dataset import TrainingDataset


class TrainingDatasetRepository(BaseRepository):
    @staticmethod
    def _json_dict(value: str | None) -> dict[str, object]:
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {str(key): item for key, item in parsed.items()}

    async def create(
        self,
        *,
        user_id: int,
        name: str,
        description: str | None,
        project_id: int | None,
        source_type: str,
        status: str,
        version: int,
        metadata: dict[str, object] | None,
    ) -> TrainingDataset:
        dataset = TrainingDataset(
            user_id=user_id,
            name=name,
            description=description,
            project_id=project_id,
            source_type=source_type,
            status=status,
            version=version,
            metadata_json=json.dumps(metadata) if metadata is not None else None,
        )
        self.session.add(dataset)
        await self.session.flush()
        return dataset

    async def list_by_user(self, *, user_id: int, limit: int = 200) -> list[TrainingDataset]:
        result = await self.session.execute(
            select(TrainingDataset)
            .where(TrainingDataset.user_id == user_id)
            .order_by(TrainingDataset.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, *, user_id: int, dataset_id: int) -> TrainingDataset | None:
        result = await self.session.execute(
            select(TrainingDataset)
            .where(TrainingDataset.id == dataset_id)
            .where(TrainingDataset.user_id == user_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id_any(self, *, dataset_id: int) -> TrainingDataset | None:
        result = await self.session.execute(
            select(TrainingDataset)
            .where(TrainingDataset.id == dataset_id)
            .limit(1)
        )
        return result.scalar_one_or_none()
