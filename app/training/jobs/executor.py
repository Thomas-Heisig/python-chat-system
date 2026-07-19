import json
import os
import gc
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from sqlalchemy import select

from app.database.repositories.training_artifact_repository import TrainingArtifactRepository
from app.database.repositories.training_dataset_repository import TrainingDatasetRepository
from app.database.repositories.training_job_repository import TrainingJobRepository
from app.database.session import get_session_maker
from app.settings.service import SettingsService
from app.db_models.model_config import ModelConfig
from app.models.manager import model_manager
from app.training.datasets.adapter import DatasetValidationError
from app.training.jobs.lifecycle import TrainingStatus
from app.training.trainers.base import TrainingRunContext
from app.training.trainers.registry import TrainerRegistry
from app.training.trainers.base import TrainingCancelledError


class TrainingJobExecutor:
    def __init__(self, trainer_registry: TrainerRegistry | None = None) -> None:
        self._trainers = trainer_registry or TrainerRegistry()

    async def run(self, job_id: int) -> None:
        if "PYTORCH_CUDA_ALLOC_CONF" not in os.environ:
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

        job_context, dataset_payload = await self._load_context(job_id)
        if job_context is None:
            return

        # Training and chat inference share the same GPU. Keeping the active model
        # loaded can make an otherwise valid run fail only during optimizer/save
        # peaks and trigger an extremely slow CPU restart.
        if model_manager.active_backend is not None:
            await self._patch_runtime(job_id, log_line="active inference model unloaded before training")
            await model_manager.unload()
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
            except Exception:
                pass

        trainer = self._trainers.resolve(job_context.hyperparameters.get("trainer_type", "") or "reference")

        await self._patch_runtime(
            job_id,
            status=TrainingStatus.PREPARING,
            log_line=(
                f"continual training resumes model {job_context.hyperparameters.get('continual_model_id')}"
                if job_context.hyperparameters.get("resume_adapter_path")
                else "preparing training run"
            ),
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

            if bool(job_context.hyperparameters.get("auto_evaluate", True)):
                await self._patch_runtime(job_id, status=TrainingStatus.EVALUATING, log_line="evaluating run")
                metrics = await trainer.evaluate(job_context, artifact)
            else:
                metrics = {}
                await self._patch_runtime(job_id, log_line="automatic evaluation skipped by setting")
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
            await self._register_artifacts(job_id=job_id, saved_info=saved_info, metrics=metrics)
            await self._finalize_success(job_id=job_id, job_context=job_context, saved_info=saved_info)
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
            error_message = _format_training_error(exc, hyperparameters=job_context.hyperparameters)
            await self._patch_runtime(
                job_id,
                status=TrainingStatus.FAILED,
                error_message=error_message,
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

            settings_service = SettingsService(session)
            artifacts_directory_raw = await settings_service.get("training", "artifacts_directory", user_id=job.user_id)
            artifacts_root = Path(str(artifacts_directory_raw or "./training-artifacts")).expanduser().resolve(strict=False)

            if bool(hyperparameters.get("continual_training", False)):
                continual_model_id = _as_int(
                    await settings_service.get("training", "continual_model_id", user_id=job.user_id)
                )
                if continual_model_id is not None:
                    continual_model = (
                        await session.execute(
                            select(ModelConfig).where(ModelConfig.id == continual_model_id).limit(1)
                        )
                    ).scalar_one_or_none()
                    if continual_model is not None and continual_model.backend == "transformers_peft":
                        continual_metadata = _json_dict(continual_model.metadata_json)
                        expected_base_id = _as_int(hyperparameters.get("base_model_registry_id"))
                        actual_base_id = _as_int(continual_metadata.get("base_model_registry_id"))
                        if expected_base_id is None or actual_base_id == expected_base_id:
                            hyperparameters["continual_model_id"] = continual_model.id
                            hyperparameters["continual_model_name"] = continual_model.name
                            adapter_path = Path(continual_model.model_path).expanduser().resolve(strict=False)
                            if adapter_path.is_dir() and not bool(hyperparameters.get("restart_from_base", False)):
                                hyperparameters["resume_adapter_path"] = str(adapter_path)

            dataset_slug = _slugify(dataset.name)
            dataset_version = _dataset_version_tag(dataset.version)
            run_folder = _run_folder_name(job_id=job.id, hyperparameters=hyperparameters)
            output_dir = artifacts_root / dataset_slug / dataset_version / run_folder

            context = TrainingRunContext(
                job_id=str(job.id),
                dataset_id=str(job.dataset_id),
                base_model_id=job.base_model_id,
                output_dir=str(output_dir),
                hyperparameters=hyperparameters,
            )

            dataset_metadata = _json_dict(dataset.metadata_json)
            metadata_files = _metadata_files(dataset_metadata)

            source_origin_path = _as_string(dataset_metadata.get("source_path")).strip()
            training_source_path = _as_string(
                metadata_files.get("training") or dataset_metadata.get("training_source_path")
            ).strip()
            validation_source_path = _as_string(
                metadata_files.get("validation") or dataset_metadata.get("validation_source_path")
            ).strip()
            test_source_path = _as_string(
                metadata_files.get("test") or dataset_metadata.get("test_source_path")
            ).strip()

            effective_training_source = training_source_path or source_origin_path
            if effective_training_source:
                hyperparameters.setdefault("source_path", effective_training_source)
            if validation_source_path:
                hyperparameters.setdefault("validation_source_path", validation_source_path)
            if test_source_path:
                hyperparameters.setdefault("test_source_path", test_source_path)
            dataset_payload: dict[str, object] = {
                "id": dataset.id,
                "name": dataset.name,
                "source_type": dataset.source_type,
                "status": dataset.status,
                "source_path": effective_training_source,
                "training_source_path": training_source_path,
                "source_origin_path": source_origin_path,
                "validation_source_path": validation_source_path,
                "test_source_path": test_source_path,
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

    async def _register_artifacts(self, *, job_id: int, saved_info: dict[str, object], metrics: dict[str, float]) -> None:
        session_maker = get_session_maker()
        async with session_maker() as session:
            job_repo = TrainingJobRepository(session)
            artifact_repo = TrainingArtifactRepository(session)
            settings_service = SettingsService(session)

            job = await job_repo.get_by_id_any(job_id=job_id)
            if job is None:
                return

            artifacts_directory_raw = await settings_service.get("training", "artifacts_directory", user_id=job.user_id)
            artifacts_root = Path(str(artifacts_directory_raw or "./training-artifacts")).expanduser().resolve(strict=False)

            path_keys = {
                "adapter": saved_info.get("artifact_path"),
                "tokenizer": saved_info.get("tokenizer_path"),
                "manifest": saved_info.get("manifest_path"),
                "metrics": saved_info.get("metrics_path"),
            }
            for artifact_type, raw_path in path_keys.items():
                path_str = _as_string(raw_path).strip()
                if not path_str:
                    continue
                await artifact_repo.upsert(
                    job_id=job_id,
                    artifacts_root=artifacts_root,
                    artifact_type=artifact_type,
                    path=Path(path_str),
                    metadata={"source": "trainer.save"},
                )

            if "metrics_path" not in saved_info:
                metrics_path = _as_string(saved_info.get("manifest_path")).strip()
                if metrics_path:
                    metrics_file = Path(metrics_path).parent / "metrics.json"
                    if metrics_file.is_file():
                        await artifact_repo.upsert(
                            job_id=job_id,
                            artifacts_root=artifacts_root,
                            artifact_type="metrics",
                            path=metrics_file,
                            metadata={"keys": list(metrics.keys())},
                        )

            await session.commit()

    async def _archive_dataset(self, job_context: TrainingRunContext) -> None:
        session_maker = get_session_maker()
        async with session_maker() as session:
            dataset_repo = TrainingDatasetRepository(session)
            dataset_id = _as_int(job_context.dataset_id)
            if dataset_id is None:
                return

            dataset = await dataset_repo.archive_by_id(dataset_id=dataset_id)
            if dataset is None:
                return

            await session.commit()

    async def _finalize_success(
        self,
        *,
        job_id: int,
        job_context: TrainingRunContext,
        saved_info: dict[str, object],
    ) -> None:
        """Register and activate the real adapter, then archive consumed work."""
        should_register = bool(job_context.hyperparameters.get("auto_register_model", False))
        is_simulation = bool(saved_info.get("is_simulation", False))
        registered: ModelConfig | None = None
        metadata_payload: dict[str, object] = {}
        session_maker = get_session_maker()
        async with session_maker() as session:
            job_repo = TrainingJobRepository(session)
            dataset_repo = TrainingDatasetRepository(session)
            job = await job_repo.get_by_id_any(job_id=job_id)
            dataset_id = _as_int(job_context.dataset_id)
            dataset = await dataset_repo.get_by_id_any(dataset_id=dataset_id) if dataset_id is not None else None

            if should_register and not is_simulation and job is not None and dataset is not None:
                adapter_path = str(Path(_as_string(saved_info.get("artifact_path"))).expanduser().resolve(strict=False))
                continual_training = bool(job_context.hyperparameters.get("continual_training", False))
                settings_service = SettingsService(session)
                continual_model_id = _as_int(job_context.hyperparameters.get("continual_model_id"))
                if continual_model_id is None and continual_training:
                    continual_model_id = _as_int(
                        await settings_service.get("training", "continual_model_id", user_id=job.user_id)
                    )
                if continual_training and continual_model_id is not None:
                    registered = (
                        await session.execute(select(ModelConfig).where(ModelConfig.id == continual_model_id).limit(1))
                    ).scalar_one_or_none()
                if registered is None and not continual_training:
                    registered = (
                        await session.execute(select(ModelConfig).where(ModelConfig.model_path == adapter_path).limit(1))
                    ).scalar_one_or_none()
                base_model = (
                    await session.execute(select(ModelConfig).where(ModelConfig.name == job.base_model_id).limit(1))
                ).scalar_one_or_none()
                if registered is not None and continual_training and base_model is not None:
                    registered_base_id = _as_int(_json_dict(registered.metadata_json).get("base_model_registry_id"))
                    if registered_base_id != base_model.id:
                        registered = None
                if base_model is not None and adapter_path:
                    base_metadata = _json_dict(base_model.metadata_json)
                    existing_metadata = _json_dict(registered.metadata_json) if registered is not None else {}
                    history_raw = existing_metadata.get("training_history")
                    history: list[dict[str, object]] = []
                    if isinstance(history_raw, list):
                        for item in cast(list[object], history_raw):
                            if isinstance(item, dict):
                                normalized_item = {
                                    str(key): value
                                    for key, value in cast(dict[object, object], item).items()
                                }
                                history.append(normalized_item)
                    history.append(
                        {
                            "job_id": job.id,
                            "dataset_id": dataset.id,
                            "dataset_name": dataset.name,
                            "artifact_path": adapter_path,
                            "training_fingerprint": job_context.hyperparameters.get("training_fingerprint"),
                            "continued_from": job_context.hyperparameters.get("resume_adapter_path"),
                            "completed_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    metadata_payload = {
                        "model_format": "peft_adapter", "model_family": base_metadata.get("model_family") or "peft",
                        "task_type": "text_generation", "group": "Text / Chat", "supports_inference": True,
                        "supports_training": continual_training, "supports_peft_training": continual_training, "supports_4bit": True,
                        "supports_chat": True, "supports_embeddings": False, "supports_reranking": False,
                        "supports_vision": False, "supports_audio": False, "adapter_path": adapter_path,
                        "base_model_registry_id": base_model.id, "base_model_name": base_model.name,
                        "base_model_path": base_model.model_path, "training_job_id": job.id,
                        "dataset_id": dataset.id, "dataset_name": dataset.name,
                        "training_fingerprint": job_context.hyperparameters.get("training_fingerprint"),
                        "load_in_4bit": bool(job_context.hyperparameters.get("load_in_4bit", True)),
                        "registration_status": "trained",
                        "continual_training": continual_training,
                        "training_history": history,
                    }
                    if registered is None:
                        registered = ModelConfig(
                            name=(
                                f"{base_model.name} - Fortlaufend trainiert"
                                if continual_training
                                else f"{base_model.name} - {dataset.name}"
                            ),
                            model_path=adapter_path,
                            backend="transformers_peft", model_format="peft_adapter", model_type="text_generation",
                            metadata_json=json.dumps(metadata_payload), is_available=True, load_status="unloaded",
                            last_scanned_at=datetime.now(timezone.utc),
                        )
                        session.add(registered)
                    else:
                        registered.model_path = adapter_path
                        registered.metadata_json = json.dumps(metadata_payload)
                        registered.is_available = True
                        registered.load_status = "unloaded"
                        registered.last_error = None
                        registered.last_scanned_at = datetime.now(timezone.utc)
                    await session.flush()
                    if continual_training:
                        await settings_service.update("training", "continual_model_id", registered.id, user_id=job.user_id)

            if bool(job_context.hyperparameters.get("archive_dataset_on_success", False)) and dataset is not None:
                dataset.status = "archived"

            if registered is not None and bool(job_context.hyperparameters.get("auto_activate_model", False)):
                for model in (await session.execute(select(ModelConfig))).scalars().all():
                    model.is_active = model.id == registered.id
                settings_service = SettingsService(session)
                await settings_service.update("model", "active_model_id", registered.id)

            if job is not None:
                result = _json_dict(job.result_json)
                result["finalization"] = {
                    "model_id": registered.id if registered is not None else None,
                    "model_name": registered.name if registered is not None else None,
                    "dataset_archived": bool(dataset is not None and dataset.status == "archived"),
                    "activated": bool(registered is not None and job_context.hyperparameters.get("auto_activate_model", False)),
                }
                job.result_json = json.dumps(result)
                if bool(job_context.hyperparameters.get("archive_job_on_success", False)):
                    job.status = "archived"
            await session.commit()

        if registered is not None and bool(job_context.hyperparameters.get("auto_activate_model", False)):
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            try:
                await model_manager.load_model(
                    registered.id, registered.model_path, registered.backend,
                    {"metadata": metadata_payload, "prefer_gpu": True},
                )
                async with session_maker() as session:
                    row = (await session.execute(select(ModelConfig).where(ModelConfig.id == registered.id))).scalar_one_or_none()
                    if row is not None:
                        row.load_status = "ready"
                        row.last_error = None
                        row.last_loaded_at = datetime.now(timezone.utc)
                    await session.commit()
            except Exception as exc:
                async with session_maker() as session:
                    row = (await session.execute(select(ModelConfig).where(ModelConfig.id == registered.id))).scalar_one_or_none()
                    if row is not None:
                        row.load_status = "error"
                        row.last_error = f"Automatisches Laden nach Training fehlgeschlagen: {exc}"
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


def _metadata_files(metadata: dict[str, object]) -> dict[str, str]:
    raw = metadata.get("files")
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, item in cast(dict[object, object], raw).items():
        role = str(key).strip().lower()
        path = _as_string(item).strip()
        if role and path:
            normalized[role] = path
    return normalized


def _as_string(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _slugify(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "-" for ch in value.strip().lower())
    squashed = "-".join(part for part in normalized.split("-") if part)
    return squashed or "dataset"


def _dataset_version_tag(version: int) -> str:
    safe_version = max(1, int(version))
    return f"v{safe_version}.0.0"


def _run_folder_name(*, job_id: int, hyperparameters: dict[str, object]) -> str:
    run_profile = _as_string(hyperparameters.get("run_profile")).strip().upper()
    run_label = _slugify(_as_string(hyperparameters.get("run_label"))) if hyperparameters.get("run_label") else ""

    epochs_raw = _as_float(hyperparameters.get("num_train_epochs"))
    lr_raw = _as_float(hyperparameters.get("learning_rate"))
    epochs_tag = f"epoch{int(epochs_raw)}" if epochs_raw is not None and float(epochs_raw).is_integer() else (
        f"epoch{epochs_raw}" if epochs_raw is not None else "epochNA"
    )
    lr_tag = f"lr{lr_raw:g}" if lr_raw is not None else "lrNA"

    prefix = f"run-{job_id:06d}"
    parts = [prefix]
    if run_profile in {"A", "B", "C"}:
        parts.append(f"profile{run_profile.lower()}")
    if run_label:
        parts.append(run_label)
    parts.extend([epochs_tag, lr_tag])
    return "-".join(parts)


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


def _format_training_error(exc: Exception, *, hyperparameters: dict[str, object]) -> str:
    message = str(exc).strip()
    lowered = message.lower()
    is_cuda_oom = "out of memory" in lowered and "cuda" in lowered
    if not is_cuda_oom:
        return message

    batch_size = _as_int(hyperparameters.get("per_device_train_batch_size"))
    grad_acc = _as_int(hyperparameters.get("gradient_accumulation_steps"))
    max_seq_len = _as_int(hyperparameters.get("max_seq_length"))

    hints = [
        "OOM-Hinweis: per_device_train_batch_size reduzieren (z. B. auf 1).",
        "OOM-Hinweis: max_seq_length reduzieren (z. B. 256/384/512).",
        "OOM-Hinweis: gradient_accumulation_steps erhoehen, um effektive Batchgroesse zu halten.",
        "OOM-Hinweis: 4-bit/8-bit Quantisierung oder Gradient Checkpointing aktivieren.",
        "OOM-Hinweis: Vor einem erneuten Lauf GPU-Speicher freigeben (andere Prozesse/Modelle entladen).",
    ]

    if batch_size is not None:
        hints.append(f"Aktuell per_device_train_batch_size={batch_size}")
    if grad_acc is not None:
        hints.append(f"Aktuell gradient_accumulation_steps={grad_acc}")
    if max_seq_len is not None:
        hints.append(f"Aktuell max_seq_length={max_seq_len}")

    return "\n".join([message, "", *hints])
