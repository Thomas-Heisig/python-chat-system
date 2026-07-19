import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.training_artifact import TrainingArtifact


class TrainingArtifactRepository(BaseRepository):
    @staticmethod
    def _sha256(path: Path) -> str | None:
        if not path.is_file():
            return None
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    async def upsert(
        self,
        *,
        job_id: int,
        artifacts_root: Path,
        artifact_type: str,
        path: Path,
        status: str = "ready",
        metadata: dict[str, object] | None = None,
    ) -> TrainingArtifact:
        resolved = path.resolve(strict=False)
        try:
            relative_path = resolved.relative_to(artifacts_root).as_posix()
        except ValueError:
            relative_path = resolved.as_posix()

        existing = (
            await self.session.execute(
                select(TrainingArtifact)
                .where(TrainingArtifact.job_id == job_id)
                .where(TrainingArtifact.artifact_type == artifact_type)
                .limit(1)
            )
        ).scalar_one_or_none()

        sha256 = self._sha256(resolved)
        size_bytes = int(resolved.stat().st_size) if resolved.exists() and resolved.is_file() else None
        metadata_json = json.dumps(metadata) if metadata is not None else None

        if existing is None:
            artifact = TrainingArtifact(
                job_id=job_id,
                artifact_type=artifact_type,
                relative_path=relative_path,
                sha256=sha256,
                size_bytes=size_bytes,
                status=status,
                metadata_json=metadata_json,
            )
            self.session.add(artifact)
            await self.session.flush()
            return artifact

        existing.relative_path = relative_path
        existing.sha256 = sha256
        existing.size_bytes = size_bytes
        existing.status = status
        existing.metadata_json = metadata_json
        await self.session.flush()
        return existing
