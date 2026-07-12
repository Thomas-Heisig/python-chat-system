from app.training.datasets.models import DatasetRecord


class DatasetRepository:
    async def list(self) -> list[DatasetRecord]:
        # Placeholder repository to be replaced by SQLAlchemy-backed implementation.
        return []
