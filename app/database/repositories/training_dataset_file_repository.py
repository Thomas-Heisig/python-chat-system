import hashlib
import json
from pathlib import Path

from sqlalchemy import delete, select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.training_dataset_file import TrainingDatasetFile


class TrainingDatasetFileRepository(BaseRepository):
    @staticmethod
    def _safe_record_count(path: Path) -> int | None:
        suffix = path.suffix.lower()
        if suffix != ".jsonl":
            return None
        count = 0
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        count += 1
            return count
        except Exception:
            return None

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    async def replace_for_dataset(
        self,
        *,
        dataset_id: int,
        datasets_root: Path,
        files: dict[str, Path],
        validation_report: dict[str, object] | None = None,
    ) -> None:
        await self.session.execute(delete(TrainingDatasetFile).where(TrainingDatasetFile.dataset_id == dataset_id))

        for role, path in files.items():
            resolved = path.resolve(strict=False)
            try:
                relative_path = resolved.relative_to(datasets_root).as_posix()
            except ValueError:
                relative_path = resolved.as_posix()

            split = "none"
            if role in {"training", "validation", "test"}:
                split = role

            file_status = "validated" if role in {"training", "validation", "test"} else "imported"
            if role == "manifest":
                file_status = "parsed"

            report_json = json.dumps(validation_report) if validation_report is not None and role in {"training", "validation", "test"} else None

            self.session.add(
                TrainingDatasetFile(
                    dataset_id=dataset_id,
                    split=split,
                    file_role=role,
                    relative_path=relative_path,
                    original_name=path.name,
                    sha256=self._sha256(resolved),
                    size_bytes=int(resolved.stat().st_size),
                    record_count=self._safe_record_count(resolved),
                    status=file_status,
                    validation_report_json=report_json,
                )
            )

        await self.session.flush()

    async def list_for_dataset(self, *, dataset_id: int) -> list[TrainingDatasetFile]:
        result = await self.session.execute(
            select(TrainingDatasetFile)
            .where(TrainingDatasetFile.dataset_id == dataset_id)
            .order_by(TrainingDatasetFile.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_for_dataset(self, *, dataset_id: int) -> int:
        result = await self.session.execute(
            delete(TrainingDatasetFile).where(TrainingDatasetFile.dataset_id == dataset_id)
        )
        return int(getattr(result, "rowcount", 0) or 0)
