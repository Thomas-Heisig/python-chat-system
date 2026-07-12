from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.training_job_repository import TrainingJobRepository
from app.training.jobs.models import TrainingJobRecord, TrainingJobStatus


class TrainingService:
    def __init__(self, session: AsyncSession) -> None:
        self.job_repo = TrainingJobRepository(session)

    async def submit(self, user_id: int, dataset_id: int, base_model_id: str, trainer_name: str) -> TrainingJobRecord:
        created = await self.job_repo.create(
            user_id=user_id,
            dataset_id=dataset_id,
            base_model_id=base_model_id,
            trainer_name=trainer_name,
            status=TrainingJobStatus.CREATED.value,
            hyperparameters=None,
        )
        return TrainingJobRecord(
            job_id=str(created.id),
            dataset_id=str(created.dataset_id),
            base_model_id=created.base_model_id,
            status=TrainingJobStatus(created.status),
        )
