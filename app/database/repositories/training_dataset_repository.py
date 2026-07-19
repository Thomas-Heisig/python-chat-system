import json
from typing import cast

from sqlalchemy import select, update

from app.database.repositories.base_repository import BaseRepository
from app.db_models.training_dataset import TrainingDataset


class TrainingDatasetRepository(BaseRepository):

    async def assign_project(
        self,
        *,
        user_id: int,
        project_id: int | None,
        dataset_ids: list[int] | None = None,
        include_archived: bool = True,
    ) -> int:
        statement = update(TrainingDataset).where(TrainingDataset.user_id == user_id)
        if dataset_ids:
            statement = statement.where(TrainingDataset.id.in_(dataset_ids))
        if not include_archived:
            statement = statement.where(TrainingDataset.status != "archived")
        result = await self.session.execute(statement.values(project_id=project_id))
        return int(getattr(result, "rowcount", 0) or 0)
    @staticmethod
    def _json_dict(value: object | None) -> dict[str, object]:
        if value is None:
            return {}

        parsed: object
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return {}
        elif isinstance(value, dict):
            parsed = cast(dict[object, object], value)
        else:
            return {}

        if not isinstance(parsed, dict):
            return {}

        parsed_dict: dict[object, object] = cast(dict[object, object], parsed)
        return {str(key): item for key, item in parsed_dict.items()}

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

    async def list_by_user(self, *, user_id: int, limit: int = 200, include_archived: bool = False) -> list[TrainingDataset]:
        statement = (
            select(TrainingDataset)
            .where(TrainingDataset.user_id == user_id)
            .order_by(TrainingDataset.updated_at.desc())
            .limit(limit)
        )
        if not include_archived:
            statement = statement.where(TrainingDataset.status != "archived")

        result = await self.session.execute(statement)
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

    async def archive_by_id(self, *, dataset_id: int) -> TrainingDataset | None:
        dataset = await self.get_by_id_any(dataset_id=dataset_id)
        if dataset is None:
            return None
        dataset.status = "archived"
        await self.session.flush()
        return dataset
