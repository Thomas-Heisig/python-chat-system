import json
from pathlib import Path
from typing import Any, cast

from app.database.repositories.training_dataset_repository import TrainingDatasetRepository
from app.database.repositories.training_job_repository import TrainingJobRepository
from app.database.session import get_session_maker
from app.training.datasets.adapter import DatasetValidationError
from app.training.jobs.lifecycle import TrainingStatus
from app.training.trainers.base import TrainingRunContext
from app.training.trainers.registry import TrainerRegistry
from app.training.trainers.base import TrainingCancelledError


class TrainingJobExecutor:
    def __init__(self, trainer_registry: TrainerRegistry | None = None) -> None:
        self._trainers = trainer_registry or TrainerRegistry()

    async def run(self, job_id: int) -> None:
        job_context, dataset_payload = await self._load_context(job_id)
        if job_context is None:
            return

        trainer = self._trainers.resolve(job_context.hyperparameters.get("trainer_type", "") or "reference")

        await self._patch_runtime(
            job_id,
            status=TrainingStatus.PREPARING,
            log_line="preparing training run",
            is_simulation=trainer.is_simulation,
        )

        try:
            prepared_payload = await trainer.prepare(job_context, dataset_payload)
            training_payload = dataset_payload
            if isinstance(prepared_payload, dict):
                training_payload = cast(dict[str, object], cast(dict[str, Any], prepared_payload))
            await self._patch_runtime(job_id, status=TrainingStatus.RUNNING, log_line="training started")

            artifact = await trainer.train(
                job_context,
                training_payload,
                progress_callback=lambda payload: self._patch_runtime(job_id, **payload),
                cancel_token=lambda: self._cancel_requested(job_id),
            )

            await self._patch_runtime(job_id, status=TrainingStatus.EVALUATING, log_line="evaluating run")
            metrics = await trainer.evaluate(job_context, artifact)
            await self._patch_runtime(job_id, status=TrainingStatus.SAVING, log_line="saving artifacts")
            saved_info = await trainer.save(job_context, artifact)

            await self._patch_runtime(
                job_id,
                status=TrainingStatus.COMPLETED,
                progress=100.0,
                metrics=metrics,
                artifact_path=str(saved_info.get("artifact_path") or ""),
                is_simulation=bool(saved_info.get("is_simulation", trainer.is_simulation)),
                log_line="training completed",
            )
            await self._set_result(job_id, metrics=metrics, saved_info=saved_info)
        except TrainingCancelledError:
            await self._patch_runtime(job_id, status=TrainingStatus.CANCELLED, log_line="training cancelled")
        except DatasetValidationError as exc:
            await self._patch_runtime(
                job_id,
                status=TrainingStatus.VALIDATION_FAILED,
                error_message=str(exc),
                log_line="dataset validation failed",
            )
        except Exception as exc:
            await self._patch_runtime(
                job_id,
                status=TrainingStatus.FAILED,
                error_message=str(exc),
                log_line="training failed",
            )

    async def _load_context(self, job_id: int) -> tuple[TrainingRunContext | None, dict[str, object]]:
        session_maker = get_session_maker()
        async with session_maker() as session:
            job_repo = TrainingJobRepository(session)
            dataset_repo = TrainingDatasetRepository(session)

            job = await job_repo.get_by_id_any(job_id=job_id)
            if job is None:
                return None, {}

            dataset = await dataset_repo.get_by_id_any(dataset_id=job.dataset_id)
            if dataset is None:
                await job_repo.update_runtime(
                    job=job,
                    status=TrainingStatus.FAILED,
                    error_message="dataset_not_found",
                    log_line="dataset not found",
                )
                await session.commit()
                return None, {}

            hyperparameters = _json_dict(job.hyperparameters_json)
            trainer_type = str(hyperparameters.get("trainer_type") or job.trainer_name or "reference").strip().lower()
            hyperparameters["trainer_type"] = trainer_type
            output_model_name = str(hyperparameters.get("output_model_name") or f"training-job-{job.id}")
            hyperparameters["output_model_name"] = output_model_name

            context = TrainingRunContext(
                job_id=str(job.id),
                dataset_id=str(job.dataset_id),
                base_model_id=job.base_model_id,
                output_dir=str(Path("artifacts") / "jobs" / str(job.id)),
                hyperparameters=hyperparameters,
            )

            dataset_metadata = _json_dict(dataset.metadata_json)
            dataset_payload: dict[str, object] = {
                "id": dataset.id,
                "name": dataset.name,
                "source_type": dataset.source_type,
                "status": dataset.status,
                "source_path": str(dataset_metadata.get("source_path") or "").strip(),
                "validation_source_path": str(dataset_metadata.get("validation_source_path") or "").strip(),
                "metadata": dataset_metadata,
            }
            return context, dataset_payload

    async def _patch_runtime(self, job_id: int, **payload: object) -> None:
        session_maker = get_session_maker()
        async with session_maker() as session:
            repo = TrainingJobRepository(session)
            job = await repo.get_by_id_any(job_id=job_id)
            if job is None:
                return

            status = str(payload["status"]) if isinstance(payload.get("status"), str) else None
            progress = _as_float(payload.get("progress"))
            current_step = _as_int(payload.get("current_step"))
            total_steps = _as_int(payload.get("total_steps"))
            current_epoch = _as_float(payload.get("current_epoch"))
            loss = _as_float(payload.get("loss"))
            learning_rate = _as_float(payload.get("learning_rate"))
            estimated_vram_mb = _as_float(payload.get("estimated_vram_mb"))
            peak_vram_mb = _as_float(payload.get("peak_vram_mb"))
            samples_per_second = _as_float(payload.get("samples_per_second"))
            steps_per_second = _as_float(payload.get("steps_per_second"))
            elapsed_seconds = _as_float(payload.get("elapsed_seconds"))
            log_line = str(payload["log_line"]) if payload.get("log_line") is not None else None
            artifact_path = str(payload["artifact_path"]) if payload.get("artifact_path") is not None else None
            error_message = str(payload["error_message"]) if payload.get("error_message") is not None else None
            metrics = cast(dict[str, object], payload.get("metrics")) if isinstance(payload.get("metrics"), dict) else None
            is_simulation = bool(payload["is_simulation"]) if payload.get("is_simulation") is not None else None

            await repo.update_runtime(
                job=job,
                status=status,
                progress=progress,
                current_step=current_step,
                total_steps=total_steps,
                current_epoch=current_epoch,
                loss=loss,
                learning_rate=learning_rate,
                estimated_vram_mb=estimated_vram_mb,
                peak_vram_mb=peak_vram_mb,
                samples_per_second=samples_per_second,
                steps_per_second=steps_per_second,
                elapsed_seconds=elapsed_seconds,
                log_line=log_line,
                artifact_path=artifact_path,
                is_simulation=is_simulation,
                metrics=metrics,
                error_message=error_message,
            )
            await session.commit()

    async def _set_result(self, job_id: int, *, metrics: dict[str, float], saved_info: dict[str, object]) -> None:
        session_maker = get_session_maker()
        async with session_maker() as session:
            repo = TrainingJobRepository(session)
            job = await repo.get_by_id_any(job_id=job_id)
            if job is None:
                return
            runtime_envelope = _json_dict(job.result_json)
            runtime_envelope["metrics"] = metrics
            runtime_envelope["saved"] = saved_info
            await repo.update_status(job=job, status=TrainingStatus.COMPLETED, result=runtime_envelope)
            await session.commit()

    async def _cancel_requested(self, job_id: int) -> bool:
        session_maker = get_session_maker()
        async with session_maker() as session:
            repo = TrainingJobRepository(session)
            return await repo.is_cancel_requested(job_id=job_id)


def _json_dict(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    normalized: dict[str, object] = {}
    for key, item in cast(dict[object, object], parsed).items():
        normalized[str(key)] = item
    return normalized


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None
