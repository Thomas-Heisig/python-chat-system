import json
from typing import cast

from sqlalchemy import func, select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.training_job import TrainingJob


class TrainingJobRepository(BaseRepository):
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

    @staticmethod
    def _object_list(value: object | None) -> list[object]:
        if not isinstance(value, list):
            return []
        return list(cast(list[object], value))

    @staticmethod
    def _to_int(value: object, default: int = 0) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return default
        return default

    async def create(
        self,
        *,
        user_id: int,
        dataset_id: int,
        base_model_id: str,
        trainer_name: str,
        status: str,
        hyperparameters: dict[str, object] | None,
    ) -> TrainingJob:
        job = TrainingJob(
            user_id=user_id,
            dataset_id=dataset_id,
            base_model_id=base_model_id,
            trainer_name=trainer_name,
            status=status,
            hyperparameters_json=json.dumps(hyperparameters) if hyperparameters is not None else None,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def list_by_user(self, *, user_id: int, limit: int = 200, include_archived: bool = False) -> list[TrainingJob]:
        statement = (
            select(TrainingJob)
            .where(TrainingJob.user_id == user_id)
            .order_by(TrainingJob.updated_at.desc())
            .limit(limit)
        )
        if not include_archived:
            statement = statement.where(TrainingJob.status != "archived")

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, *, user_id: int, job_id: int) -> TrainingJob | None:
        result = await self.session.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job_id)
            .where(TrainingJob.user_id == user_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id_any(self, *, job_id: int) -> TrainingJob | None:
        result = await self.session.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_dataset_id(self, *, dataset_id: int) -> int:
        result = await self.session.execute(
            select(func.count(TrainingJob.id)).where(TrainingJob.dataset_id == dataset_id)
        )
        return int(result.scalar_one() or 0)

    async def find_by_training_fingerprint(self, *, user_id: int, fingerprint: str) -> TrainingJob | None:
        result = await self.session.execute(
            select(TrainingJob)
            .where(TrainingJob.user_id == user_id)
            .where(TrainingJob.status.in_(["queued", "preparing", "running", "evaluating", "saving", "completed", "archived"]))
            .order_by(TrainingJob.id.desc())
        )
        for job in result.scalars().all():
            if str(self._json_dict(job.hyperparameters_json).get("training_fingerprint") or "") == fingerprint:
                return job
        return None

    async def find_active_or_successful_by_dataset_id(self, *, user_id: int, dataset_id: int) -> TrainingJob | None:
        result = await self.session.execute(
            select(TrainingJob)
            .where(TrainingJob.user_id == user_id)
            .where(TrainingJob.dataset_id == dataset_id)
            .where(TrainingJob.status.in_(["queued", "preparing", "running", "evaluating", "saving", "completed", "archived"]))
            .order_by(TrainingJob.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def claim_next_queued(self) -> TrainingJob | None:
        statement = (
            select(TrainingJob)
            .where(TrainingJob.status == "queued")
            .order_by(TrainingJob.created_at.asc())
            .limit(1)
        )
        dialect_name = self.session.bind.dialect.name
        if dialect_name in {"postgresql", "mysql", "mariadb", "oracle"}:
            statement = statement.with_for_update(skip_locked=True)

        result = await self.session.execute(statement)
        job = result.scalar_one_or_none()
        if job is None:
            return None

        existing_result = self._json_dict(job.result_json)
        runtime = self._json_dict(existing_result.get("runtime"))

        runtime.update({
            "progress": 0.0,
            "current_step": 0,
            "total_steps": 0,
            "current_epoch": 0.0,
            "loss": None,
            "learning_rate": None,
            "logs": ["job claimed by worker"],
        })
        existing_result["runtime"] = runtime
        job.result_json = json.dumps(existing_result)
        job.status = "preparing"
        job.error_message = None
        await self.session.flush()
        return job

    async def peek_next_queued(self) -> TrainingJob | None:
        result = await self.session.execute(
            select(TrainingJob)
            .where(TrainingJob.status == "queued")
            .order_by(TrainingJob.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def cancel_pending_queued(self) -> int:
        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.status == "cancelling")
        )
        changed = 0
        for job in list(result.scalars().all()):
            runtime = self._json_dict(self._json_dict(job.result_json).get("runtime"))
            if self._to_int(runtime.get("current_step")) > 0:
                continue
            metadata = self._json_dict(job.result_json)
            runtime = self._json_dict(metadata.get("runtime"))
            logs = self._object_list(runtime.get("logs"))
            logs.append("cancel requested before run")
            runtime["logs"] = logs[-200:]
            metadata["runtime"] = runtime
            job.result_json = json.dumps(metadata)
            job.status = "cancelled"
            changed += 1

        if changed:
            await self.session.flush()
        return changed

    async def recover_interrupted_jobs(self) -> int:
        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.status.in_(["preparing", "running", "evaluating", "saving"]))
        )
        changed = 0
        for job in list(result.scalars().all()):
            payload = self._json_dict(job.result_json)
            runtime = self._json_dict(payload.get("runtime"))
            logs = self._object_list(runtime.get("logs"))
            logs.append("job recovered after worker restart")
            runtime["logs"] = logs[-200:]
            payload["runtime"] = runtime
            job.result_json = json.dumps(payload)
            job.status = "queued"
            changed += 1

        if changed:
            await self.session.flush()
        return changed

    async def update_status(
        self,
        *,
        job: TrainingJob,
        status: str,
        error_message: str | None = None,
        result: dict[str, object] | None = None,
    ) -> TrainingJob:
        job.status = status
        job.error_message = error_message
        if result is not None:
            job.result_json = json.dumps(result)
        await self.session.flush()
        return job

    async def update_runtime(
        self,
        *,
        job: TrainingJob,
        status: str | None = None,
        progress: float | None = None,
        current_step: int | None = None,
        total_steps: int | None = None,
        current_epoch: float | None = None,
        loss: float | None = None,
        learning_rate: float | None = None,
        estimated_vram_mb: float | None = None,
        peak_vram_mb: float | None = None,
        samples_per_second: float | None = None,
        steps_per_second: float | None = None,
        elapsed_seconds: float | None = None,
        log_line: str | None = None,
        artifact_path: str | None = None,
        is_simulation: bool | None = None,
        metrics: dict[str, object] | None = None,
        error_message: str | None = None,
    ) -> TrainingJob:
        payload = self._json_dict(job.result_json)
        runtime = self._json_dict(payload.get("runtime"))

        if progress is not None:
            runtime["progress"] = max(0.0, min(100.0, progress))
        if current_step is not None:
            runtime["current_step"] = max(0, current_step)
        if total_steps is not None:
            runtime["total_steps"] = max(0, total_steps)
        if current_epoch is not None:
            runtime["current_epoch"] = max(0.0, current_epoch)
        if loss is not None:
            runtime["loss"] = loss
        if learning_rate is not None:
            runtime["learning_rate"] = learning_rate
        if estimated_vram_mb is not None:
            runtime["estimated_vram_mb"] = max(0.0, estimated_vram_mb)
        if peak_vram_mb is not None:
            runtime["peak_vram_mb"] = max(0.0, peak_vram_mb)
        if samples_per_second is not None:
            runtime["samples_per_second"] = max(0.0, samples_per_second)
        if steps_per_second is not None:
            runtime["steps_per_second"] = max(0.0, steps_per_second)
        if elapsed_seconds is not None:
            runtime["elapsed_seconds"] = max(0.0, elapsed_seconds)

        logs = self._object_list(runtime.get("logs"))
        if log_line:
            logs.append(log_line)
            runtime["logs"] = logs[-200:]

        payload["runtime"] = runtime
        if artifact_path:
            payload["artifact_path"] = artifact_path
        if is_simulation is not None:
            payload["is_simulation"] = bool(is_simulation)
        if metrics is not None:
            payload["metrics"] = metrics

        if status is not None:
            job.status = status
        if error_message is not None:
            job.error_message = error_message

        job.result_json = json.dumps(payload)
        await self.session.flush()
        return job

    async def is_cancel_requested(self, *, job_id: int) -> bool:
        job = await self.get_by_id_any(job_id=job_id)
        if job is None:
            return False
        return job.status == "cancelling"

    async def request_cancel(self, *, job: TrainingJob) -> TrainingJob:
        if job.status in {"completed", "cancelled", "failed", "validation_failed"}:
            return job
        if job.status != "cancelling":
            job.status = "cancelling"
            metadata = self._json_dict(job.result_json)
            runtime = self._json_dict(metadata.get("runtime"))
            logs = self._object_list(runtime.get("logs"))
            logs.append("cancel requested")
            runtime["logs"] = logs[-200:]
            metadata["runtime"] = runtime
            job.result_json = json.dumps(metadata)
            await self.session.flush()
        return job

    async def retry_from(self, *, source_job: TrainingJob) -> TrainingJob:
        copied_hyperparameters: dict[str, object] | None = None
        if source_job.hyperparameters_json:
            copied_hyperparameters = self._json_dict(source_job.hyperparameters_json)

        return await self.create(
            user_id=source_job.user_id,
            dataset_id=source_job.dataset_id,
            base_model_id=source_job.base_model_id,
            trainer_name=source_job.trainer_name,
            status="queued",
            hyperparameters=copied_hyperparameters,
        )
