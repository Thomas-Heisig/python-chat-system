import json

from sqlalchemy import select

from app.database.repositories.base_repository import BaseRepository
from app.db_models.training_job import TrainingJob


class TrainingJobRepository(BaseRepository):
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

    async def list_by_user(self, *, user_id: int, limit: int = 200) -> list[TrainingJob]:
        result = await self.session.execute(
            select(TrainingJob)
            .where(TrainingJob.user_id == user_id)
            .order_by(TrainingJob.updated_at.desc())
            .limit(limit)
        )
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

    async def claim_next_queued(self) -> TrainingJob | None:
        result = await self.session.execute(
            select(TrainingJob)
            .where(TrainingJob.status == "queued")
            .order_by(TrainingJob.created_at.asc())
            .limit(1)
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None

        existing_result = self._json_dict(job.result_json)
        runtime = self._json_dict(existing_result.get("runtime") if isinstance(existing_result.get("runtime"), str) else None)
        if not runtime and isinstance(existing_result.get("runtime"), dict):
            runtime = {str(key): value for key, value in existing_result["runtime"].items()}

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

    async def cancel_pending_queued(self) -> int:
        result = await self.session.execute(
            select(TrainingJob).where(TrainingJob.status == "cancelling")
        )
        changed = 0
        for job in list(result.scalars().all()):
            runtime = self._json_dict(job.result_json).get("runtime")
            if isinstance(runtime, dict) and int(runtime.get("current_step") or 0) > 0:
                continue
            metadata = self._json_dict(job.result_json)
            logs = metadata.get("logs")
            if not isinstance(logs, list):
                logs = []
            logs.append("cancel requested before run")
            metadata["logs"] = logs
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
            runtime_raw = payload.get("runtime")
            runtime: dict[str, object] = {str(key): value for key, value in runtime_raw.items()} if isinstance(runtime_raw, dict) else {}
            logs_value = runtime.get("logs")
            logs: list[object] = logs_value if isinstance(logs_value, list) else []
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
        job.result_json = json.dumps(result) if result is not None else None
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
        runtime_raw = payload.get("runtime")
        runtime: dict[str, object]
        if isinstance(runtime_raw, dict):
            runtime = {str(key): value for key, value in runtime_raw.items()}
        else:
            runtime = {}

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

        logs_value = runtime.get("logs")
        logs: list[object]
        if isinstance(logs_value, list):
            logs = logs_value
        else:
            logs = []
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
            logs = metadata.get("logs")
            if not isinstance(logs, list):
                logs = []
            logs.append("cancel requested")
            metadata["logs"] = logs
            job.result_json = json.dumps(metadata)
            await self.session.flush()
        return job

    async def retry_from(self, *, source_job: TrainingJob) -> TrainingJob:
        copied_hyperparameters: dict[str, object] | None = None
        if source_job.hyperparameters_json:
            try:
                parsed = json.loads(source_job.hyperparameters_json)
                if isinstance(parsed, dict):
                    copied_hyperparameters = {str(key): value for key, value in parsed.items()}
            except json.JSONDecodeError:
                copied_hyperparameters = None

        return await self.create(
            user_id=source_job.user_id,
            dataset_id=source_job.dataset_id,
            base_model_id=source_job.base_model_id,
            trainer_name=source_job.trainer_name,
            status="queued",
            hyperparameters=copied_hyperparameters,
        )
