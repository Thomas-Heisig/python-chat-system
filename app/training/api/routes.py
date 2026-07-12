from datetime import datetime, timezone
import ipaddress
import json
import re
import socket
import shutil
from pathlib import Path, PurePosixPath
from typing import cast
from urllib.parse import parse_qsl, quote, urlencode, urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.chat.service import clean_model_output_text
from app.database.repositories.training_dataset_repository import TrainingDatasetRepository
from app.database.repositories.training_job_repository import TrainingJobRepository
from app.database.repositories.user_repository import UserRepository
from app.db_models.model_config import ModelConfig
from app.db_models.training_dataset import TrainingDataset
from app.db_models.training_job import TrainingJob
from app.models.path_security import normalize_base_directories, validate_model_path_against_allowed_bases
from app.models.loader import create_backend
from app.training.datasets.adapter import DatasetAdapter, DatasetValidationError
from app.training.jobs.lifecycle import CANCELLABLE_STATUSES, TERMINAL_STATUSES, TrainingStatus
from app.training.jobs.worker import training_worker
from app.training.trainers.registry import TrainerRegistry
from app.schemas.training import (
    CreateTrainingDatasetRequest,
    TrainingAdapterCompareRequest,
    TrainingAdapterCompareResponse,
    TrainingAdapterRegisterResponse,
    ImportTrainingDatasetUrlRequest,
    RegisterTrainingDatasetFileRequest,
    CreateTrainingJobRequest,
    TrainingDatasetFileItem,
    TrainingDatasetFileListResponse,
    TrainingPreflightRequest,
    TrainingPreflightResponse,
    TrainingDatasetItem,
    TrainingDatasetListResponse,
    TrainingJobItem,
    TrainingJobListResponse,
)
from app.settings.service import SettingsService

router = APIRouter(prefix="/api/training", tags=["training"])

_TRAINING_SOURCE_EXTENSIONS = {
    ".jsonl",
    ".json",
    ".csv",
    ".md",
    ".markdown",
    ".txt",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".htm",
    ".pdf",
    ".docx",
}

_ALLOWED_DATASET_SOURCE_BASES = {
    "raw.githubusercontent.com": "https://raw.githubusercontent.com",
    "huggingface.co": "https://huggingface.co",
}


def _verify_peft_artifact(saved_info: dict[str, object], hyperparameters: dict[str, object]) -> dict[str, object]:
    adapter_path = Path(_as_string(saved_info.get("artifact_path"))).resolve(strict=False)
    tokenizer_path = Path(_as_string(saved_info.get("tokenizer_path"))).resolve(strict=False)
    manifest_path = Path(_as_string(saved_info.get("manifest_path"))).resolve(strict=False)
    base_model_path = _as_string(hyperparameters.get("base_model"))

    checks = {
        "adapter_dir": adapter_path.is_dir(),
        "adapter_config": (adapter_path / "adapter_config.json").is_file(),
        "adapter_weights": (adapter_path / "adapter_model.safetensors").is_file(),
        "tokenizer_dir": tokenizer_path.is_dir(),
        "manifest": manifest_path.is_file(),
        "metrics": (manifest_path.parent / "metrics.json").is_file(),
        "trainer_state": (manifest_path.parent / "trainer-state.json").is_file(),
    }

    adapter_load_ok = False
    adapter_load_error: str | None = None
    if base_model_path and checks["adapter_dir"] and checks["adapter_config"] and checks["adapter_weights"]:
        try:
            import importlib

            peft_module = importlib.import_module("peft")
            PeftConfig = getattr(peft_module, "PeftConfig")
            PeftModel = getattr(peft_module, "PeftModel")
            transformers_module = importlib.import_module("transformers")
            AutoModelForCausalLM = getattr(transformers_module, "AutoModelForCausalLM")

            PeftConfig.from_pretrained(str(adapter_path))
            base_model = AutoModelForCausalLM.from_pretrained(base_model_path, local_files_only=True, device_map="cpu")
            PeftModel.from_pretrained(base_model, str(adapter_path), is_trainable=False)
            adapter_load_ok = True
        except Exception:
            adapter_load_error = "adapter_load_failed"

    return {
        "checks": checks,
        "adapter_load_ok": adapter_load_ok,
        "adapter_load_error": adapter_load_error,
    }


def _adapter_model_name(*, base_model_name: str, dataset_name: str) -> str:
    return f"{base_model_name} - {dataset_name}"


def _evaluate_compare_outputs(*, base_raw: str, adapter_raw: str, base_clean: str, adapter_clean: str) -> dict[str, object]:
    return {
        "base_has_reasoning_artifacts": "<think>" in base_raw.lower() or "thinking process" in base_raw.lower(),
        "adapter_has_reasoning_artifacts": "<think>" in adapter_raw.lower() or "thinking process" in adapter_raw.lower(),
        "base_cleaned_nonempty": bool(base_clean.strip()),
        "adapter_cleaned_nonempty": bool(adapter_clean.strip()),
        "base_mentions_vinegar_risk": any(token in base_clean.lower() for token in ["essig", "säure", "saeure", "schäd", "schaed"]),
        "adapter_mentions_vinegar_risk": any(token in adapter_clean.lower() for token in ["essig", "säure", "saeure", "schäd", "schaed"]),
    }


def _to_training_job_item(job: TrainingJob) -> TrainingJobItem:
    result_payload = _json_to_dict(job.result_json) if job.result_json else None
    runtime_payload = _runtime_from_result(result_payload)
    return TrainingJobItem(
        id=job.id,
        dataset_id=job.dataset_id,
        base_model_id=job.base_model_id,
        trainer_name=job.trainer_name,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        hyperparameters=_json_to_dict(job.hyperparameters_json),
        result=result_payload,
        error_message=job.error_message,
        progress=_as_float(runtime_payload.get("progress")),
        current_step=_as_int(runtime_payload.get("current_step")),
        total_steps=_as_int(runtime_payload.get("total_steps")),
        current_epoch=_as_float(runtime_payload.get("current_epoch")),
        loss=_as_float(runtime_payload.get("loss")),
        learning_rate=_as_float(runtime_payload.get("learning_rate")),
        logs=_as_string_list(runtime_payload.get("logs")),
        is_simulation=_as_bool(result_payload.get("is_simulation") if result_payload else None),
        estimated_vram_mb=_as_float(runtime_payload.get("estimated_vram_mb")),
        peak_vram_mb=_as_float(runtime_payload.get("peak_vram_mb")),
        samples_per_second=_as_float(runtime_payload.get("samples_per_second")),
        steps_per_second=_as_float(runtime_payload.get("steps_per_second")),
        elapsed_seconds=_as_float(runtime_payload.get("elapsed_seconds")),
    )


def _json_to_dict(value: str | None) -> dict[str, object]:
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


def _runtime_from_result(result_payload: dict[str, object] | None) -> dict[str, object]:
    if result_payload is None:
        return {}
    runtime = result_payload.get("runtime")
    if not isinstance(runtime, dict):
        return {}
    normalized: dict[str, object] = {}
    for key, item in cast(dict[object, object], runtime).items():
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


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in cast(list[object], value):
        if item is not None:
            normalized.append(str(item))
    return normalized


def _as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _as_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_trainer_available(trainer_name: str) -> tuple[bool, str | None]:
    normalized = trainer_name.strip().lower()
    if normalized == "peft_lora":
        missing = [
            module_name
            for module_name in ("transformers", "peft", "datasets", "accelerate")
            if not _has_module(module_name)
        ]
        if missing:
            return False, f"Fehlende Module fuer peft_lora: {', '.join(missing)}"
        return True, None
    if normalized in {"reference", "lora", "qlora"}:
        return True, None
    if normalized in {"unsloth", "unsloth_lora"}:
        return False, "unsloth ist in dieser Runtime nicht produktiv verfuegbar."
    return False, "Unbekannter oder nicht verfuegbarer Trainer."


def _trainer_options() -> list[dict[str, object]]:
    registry = TrainerRegistry()
    supported_ids = ["peft_lora", "reference", "unsloth_lora"]
    options: list[dict[str, object]] = []
    summaries = registry.summaries()
    for trainer_id in supported_ids:
        summary = summaries.get(trainer_id)
        if summary is None:
            continue
        available, reason = _is_trainer_available(trainer_id)
        options.append(
            {
                "id": trainer_id,
                "label": str(summary.get("name") or trainer_id),
                "available": available,
                "reason_unavailable": None if available else reason,
                "is_simulation": bool(summary.get("is_simulation", False)),
            }
        )
    return options


def _model_training_compatibility(*, model: ModelConfig, trainer_name: str) -> tuple[bool, str | None]:
    normalized_trainer = trainer_name.strip().lower()
    if normalized_trainer != "peft_lora":
        if normalized_trainer in {"reference", "lora", "qlora"}:
            return True, None
        if normalized_trainer in {"unsloth", "unsloth_lora"}:
            return False, "unsloth ist in dieser Runtime deaktiviert."
        return False, "Trainer ist nicht bekannt."

    metadata = _json_to_dict(model.metadata_json)
    task_type = _as_string(metadata.get("task_type") or model.model_type).lower()
    if task_type == "any_to_any":
        return False, "Nicht mit PEFT-LoRA kompatibel. Benoetigt einen eigenen Supra-A2A-Trainer."

    if model.backend != "transformers":
        return False, "peft_lora benoetigt ein Transformers-Modell."

    model_format = (model.model_format or "").strip().lower()
    if model_format not in {"hf", "safetensors", "transformers_safetensors", "transformers", "transformers_pytorch"}:
        return False, "peft_lora unterstuetzt nur trainierbare Transformers-Formate."

    if task_type and task_type != "text_generation":
        return False, f"peft_lora erwartet text_generation (erhalten: {task_type})."

    supports_training = metadata.get("supports_training")
    if isinstance(supports_training, bool) and not supports_training:
        return False, "Modell ist laut Metadaten nicht fuer Training markiert."

    return True, None


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _dataset_source_path(dataset: TrainingDataset) -> str:
    metadata = _json_to_dict(dataset.metadata_json)
    for key in ("source_path", "dataset_path", "file_path", "path"):
        candidate = _as_string(metadata.get(key))
        if candidate:
            return candidate
    return ""


def _dataset_validation_source_path(dataset: TrainingDataset) -> str:
    metadata = _json_to_dict(dataset.metadata_json)
    return _as_string(metadata.get("validation_source_path"))


def _training_datasets_root(raw_value: str) -> Path:
    normalized = raw_value.strip()
    root = Path(normalized or "./training-datasets").expanduser().resolve(strict=False)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_dataset_filename(raw_name: str, *, fallback: str) -> str:
    candidate = Path(raw_name).name.strip()
    if not candidate:
        candidate = fallback
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", candidate).strip("._")
    return sanitized or fallback


def _resolve_dataset_file_under_root(root: Path, relative_name: str) -> Path:
    normalized = relative_name.strip().replace("\\", "/")
    if not normalized:
        raise HTTPException(status_code=400, detail="dataset_file_name_empty")
    candidate = (root / normalized).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="dataset_file_outside_root") from exc
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="dataset_file_not_found")
    if candidate.suffix.lower() not in _TRAINING_SOURCE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="dataset_file_type_not_supported")
    return candidate


def _dataset_item_response(item: TrainingDataset) -> TrainingDatasetItem:
    return TrainingDatasetItem(
        id=item.id,
        name=item.name,
        description=item.description,
        source_type=item.source_type,
        status=item.status,
        version=item.version,
        project_id=item.project_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
        metadata=_json_to_dict(item.metadata_json),
    )


def _merge_dataset_metadata(
    metadata: dict[str, object] | None,
    *,
    source_path: Path,
    validation_source_path: Path | None = None,
) -> dict[str, object]:
    merged = dict(metadata or {})
    merged["source_path"] = str(source_path)
    if validation_source_path is not None:
        merged["validation_source_path"] = str(validation_source_path)
    return merged


def _is_public_ip_address(address: str) -> bool:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return False
    return not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )


def _canonicalize_allowed_dataset_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="dataset_url_scheme_invalid")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="dataset_url_host_invalid")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="dataset_url_auth_not_allowed")

    host = parsed.hostname.lower().rstrip(".")
    trusted_base = _ALLOWED_DATASET_SOURCE_BASES.get(host)
    if trusted_base is None:
        raise HTTPException(status_code=400, detail="dataset_url_host_not_allowed")

    if parsed.port not in {None, 80, 443}:
        raise HTTPException(status_code=400, detail="dataset_url_port_not_allowed")

    try:
        candidates = {entry[4][0] for entry in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="dataset_url_host_unresolvable") from exc

    if not candidates or not all(_is_public_ip_address(address) for address in candidates):
        raise HTTPException(status_code=400, detail="dataset_url_host_not_allowed")

    raw_path = parsed.path or "/"
    if any(part == ".." for part in PurePosixPath(raw_path).parts):
        raise HTTPException(status_code=400, detail="dataset_url_path_invalid")

    safe_path = quote(raw_path, safe="/-._~")
    safe_query = urlencode(parse_qsl(parsed.query, keep_blank_values=True), doseq=True)
    return f"{trusted_base}{safe_path}" + (f"?{safe_query}" if safe_query else "")


def _download_training_source(url: str, destination: Path) -> None:
    safe_url = _canonicalize_allowed_dataset_url(url)
    request = Request(safe_url, headers={"User-Agent": "python-chat-system/1.0"})
    with urlopen(request, timeout=30) as response:
        _canonicalize_allowed_dataset_url(response.geturl())
        payload = response.read()
    if not payload:
        raise HTTPException(status_code=400, detail="dataset_url_empty")
    destination.write_bytes(payload)


async def _resolve_registered_model(session: AsyncSession, requested: str) -> ModelConfig | None:
    normalized = requested.strip()
    if not normalized:
        return None
    if normalized.isdigit():
        return (
            await session.execute(select(ModelConfig).where(ModelConfig.id == int(normalized)).limit(1))
        ).scalar_one_or_none()
    return (
        await session.execute(select(ModelConfig).where(ModelConfig.name == normalized).limit(1))
    ).scalar_one_or_none()


def _has_4bit_dependencies() -> bool:
    try:
        import importlib.util

        return (
            importlib.util.find_spec("bitsandbytes") is not None
            and importlib.util.find_spec("accelerate") is not None
            and importlib.util.find_spec("transformers") is not None
        )
    except Exception:
        return False


def _has_module(module_name: str) -> bool:
    try:
        import importlib.util

        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


async def _run_preflight(
    *,
    session: AsyncSession,
    user_id: int,
    dataset: TrainingDataset,
    requested_base_model: str,
    trainer_name: str,
    hyperparameters: dict[str, object],
) -> TrainingPreflightResponse:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    selected_model = await _resolve_registered_model(session, requested_base_model)
    if selected_model is None:
        errors.append(
            _issue(
                "training.model_not_registered",
                "Das ausgewaehlte Basismodell ist nicht im Model Manager registriert.",
            )
        )

    settings_service = SettingsService(session)
    base_dirs = normalize_base_directories(await settings_service.get("model", "base_directories", user_id=user_id))
    artifacts_directory = _as_string(await settings_service.get("training", "artifacts_directory", user_id=user_id)) or "./training-artifacts"
    output_root = Path(artifacts_directory).expanduser().resolve(strict=False)

    cuda_available = False
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
    except Exception:
        cuda_available = False
        warnings.append(_issue("training.torch_unavailable", "Torch ist nicht verfuegbar, CUDA-Check konnte nicht vollstaendig geprueft werden."))

    requested_4bit = bool(hyperparameters.get("load_in_4bit", True))
    allow_cpu_training = bool(hyperparameters.get("allow_cpu_training", False))
    deps_4bit = _has_4bit_dependencies()
    supports_4bit = bool(cuda_available and deps_4bit)

    missing_core_dependencies = [
        module_name
        for module_name in ("transformers", "peft", "datasets", "accelerate")
        if not _has_module(module_name)
    ]
    if missing_core_dependencies:
        errors.append(
            _issue(
                "training.missing_core_dependencies",
                f"Fehlende Trainingsabhaengigkeiten: {', '.join(missing_core_dependencies)}",
            )
        )

    if not cuda_available:
        if requested_4bit:
            errors.append(_issue("training.cuda_unavailable", "CUDA ist nicht verfuegbar; 4-bit-Training kann nicht gestartet werden."))
        elif allow_cpu_training:
            warnings.append(_issue("training.cpu_training_enabled", "CUDA ist nicht verfuegbar; Training wird im CPU-Modus zugelassen."))
        else:
            errors.append(
                _issue(
                    "training.cuda_unavailable",
                    "CUDA ist nicht verfuegbar. Setze allow_cpu_training=true fuer einen bewusst limitierten CPU-Smoke-Run.",
                )
            )
    if requested_4bit and not deps_4bit:
        errors.append(_issue("training.missing_4bit_dependencies", "4-bit-Abhaengigkeiten fehlen (bitsandbytes/accelerate/transformers)."))

    model_format = selected_model.model_format if selected_model is not None else None
    model_path = _as_string(selected_model.model_path if selected_model is not None else "")
    model_name = selected_model.name if selected_model is not None else None
    model_id = selected_model.id if selected_model is not None else None

    if selected_model is not None:
        path_ok, reason = validate_model_path_against_allowed_bases(model_path, base_dirs)
        if not path_ok:
            errors.append(
                _issue(
                    "training.model_path_invalid",
                    f"Modellpfad ist ungueltig oder ausserhalb erlaubter Basisverzeichnisse ({reason or 'invalid_path'}).",
                )
            )

        if selected_model.backend != "transformers" or (selected_model.model_format or "").lower() not in {
            "hf",
            "safetensors",
            "transformers_safetensors",
            "transformers_pytorch",
            "transformers",
        }:
            errors.append(
                _issue(
                    "training.unsupported_model_format",
                    "GGUF-Modelle koennen mit dem PEFT-Trainer nicht trainiert werden.",
                )
            )

        config_path = Path(model_path) / "config.json"
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception:
            errors.append(_issue("training.config_unreadable", "config.json ist nicht lesbar oder ungueltig."))

        try:
            import importlib

            transformers_module = importlib.import_module("transformers")
            auto_tokenizer = getattr(transformers_module, "AutoTokenizer")
            auto_config = getattr(transformers_module, "AutoConfig")
            auto_model_for_causal_lm = getattr(transformers_module, "AutoModelForCausalLM")

            tokenizer = auto_tokenizer.from_pretrained(model_path, local_files_only=True)
            cfg = auto_config.from_pretrained(model_path, local_files_only=True)
            model_type = _as_string(getattr(cfg, "model_type", ""))
            supported_types: set[str] = set()
            try:
                mapping = getattr(auto_model_for_causal_lm, "_model_mapping", None)
                internal_mapping = getattr(mapping, "_model_mapping", None)
                if isinstance(internal_mapping, dict):
                    typed_mapping = cast(dict[object, object], internal_mapping)
                    supported_types = {str(key) for key in typed_mapping.keys()}
            except Exception:
                supported_types = set()

            auto_map = getattr(cfg, "auto_map", {})
            has_remote_causal_lm = isinstance(auto_map, dict) and "AutoModelForCausalLM" in auto_map
            if model_type not in supported_types and not has_remote_causal_lm:
                errors.append(
                    _issue(
                        "training.unsupported_architecture",
                        f"Architektur '{model_type or 'unknown'}' wird von AutoModelForCausalLM nicht unterstuetzt.",
                    )
                )

            try:
                vocab_size = len(tokenizer)
            except Exception:
                vocab_size = None
                warnings.append(
                    _issue(
                        "training.tokenizer_vocab_size_unknown",
                        "Tokenizer-Vokabulargroesse konnte nicht bestimmt werden; Special-Token-Range-Checks wurden uebersprungen.",
                    )
                )

            if isinstance(vocab_size, int) and vocab_size > 0:
                for field in ("pad_token_id", "eos_token_id", "bos_token_id"):
                    token_id = getattr(cfg, field, None)
                    if token_id is None:
                        continue
                    if not isinstance(token_id, int) or not 0 <= token_id < vocab_size:
                        errors.append(
                            _issue(
                                "training.invalid_special_token_id",
                                f"{field}={token_id} liegt ausserhalb des Tokenizer-Vokabulars (0..{max(0, vocab_size - 1)}).",
                            )
                        )
        except Exception as exc:
            errors.append(
                _issue(
                    "training.tokenizer_or_model_check_failed",
                    f"Tokenizer/Transformers-Kompatibilitaet konnte nicht geprueft werden: {exc}",
                )
            )

    source_path = _dataset_source_path(dataset)
    validation_source_path = _dataset_validation_source_path(dataset)
    dataset_valid = False
    if not source_path:
        errors.append(_issue("training.dataset_source_missing", "Dataset besitzt keinen gueltigen source_path in den Metadaten."))
    else:
        try:
            DatasetAdapter().load_samples(source_path=source_path)
            if validation_source_path:
                DatasetAdapter().load_samples(source_path=validation_source_path)
            dataset_valid = True
        except DatasetValidationError as exc:
            errors.append(_issue("training.dataset_invalid", f"Dataset-Validierung fehlgeschlagen: {exc}"))
        except Exception as exc:
            errors.append(_issue("training.dataset_check_failed", f"Dataset-Pruefung fehlgeschlagen: {exc}"))

    try:
        output_root.mkdir(parents=True, exist_ok=True)
        test_file = output_root / ".preflight-write-test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except Exception:
        errors.append(_issue("training.output_not_writable", "Artefaktverzeichnis ist nicht beschreibbar."))

    try:
        free_bytes = int(shutil.disk_usage(output_root).free)
        free_gb = free_bytes / (1024.0 * 1024.0 * 1024.0)
        if free_gb < 1.0:
            errors.append(_issue("training.insufficient_disk_space", f"Zu wenig freier Speicherplatz: {free_gb:.2f} GB."))
        elif free_gb < 5.0:
            warnings.append(_issue("training.low_disk_space", f"Wenig freier Speicherplatz: {free_gb:.2f} GB."))
    except Exception:
        warnings.append(_issue("training.disk_check_failed", "Freier Speicherplatz konnte nicht geprueft werden."))

    if trainer_name != "peft_lora":
        warnings.append(_issue("training.preflight_trainer_scope", f"Preflight ist auf peft_lora optimiert (aktueller Trainer: {trainer_name})."))

    trainer_available, trainer_reason = _is_trainer_available(trainer_name)
    if not trainer_available:
        errors.append(_issue("training.trainer_unavailable", trainer_reason or "Trainer ist nicht verfuegbar."))

    if selected_model is not None:
        compatible, reason = _model_training_compatibility(model=selected_model, trainer_name=trainer_name)
        if not compatible:
            errors.append(_issue("training.model_incompatible", reason or "Modell und Trainer sind nicht kompatibel."))

    return TrainingPreflightResponse(
        ready=len(errors) == 0,
        model_id=model_id,
        model_name=model_name,
        model_format=model_format,
        trainer=trainer_name,
        cuda_available=cuda_available,
        supports_4bit=supports_4bit,
        dataset_valid=dataset_valid,
        warnings=warnings,
        errors=errors,
    )


@router.get("/health")
async def training_health() -> dict[str, object]:
    registry = TrainerRegistry()
    trainers = registry.summaries()
    return {
        "status": "ok",
        "phase": "worker",
        "worker": {
            "running": training_worker.is_running,
        },
        "trainers": trainers,
        "message": "Training worker lifecycle is active.",
    }


@router.get("/trainers")
async def list_trainers() -> dict[str, object]:
    return {"items": _trainer_options()}


@router.get("/compatibility")
async def training_model_compatibility(
    trainer_name: str,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    normalized_trainer = trainer_name.strip().lower()
    rows = (await session.execute(select(ModelConfig).order_by(ModelConfig.id.asc()))).scalars().all()
    items: list[dict[str, object]] = []
    for row in rows:
        compatible, reason = _model_training_compatibility(model=row, trainer_name=normalized_trainer)
        items.append(
            {
                "model_id": row.id,
                "model_name": row.name,
                "compatible": compatible,
                "reason": reason,
            }
        )
    return {"trainer": normalized_trainer, "items": items}


@router.get("/datasets", response_model=TrainingDatasetListResponse)
async def list_datasets(
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingDatasetListResponse:
    user_repo = UserRepository(session)
    dataset_repo = TrainingDatasetRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    datasets = await dataset_repo.list_by_user(user_id=user_id, limit=200)
    items = [
        TrainingDatasetItem(
            id=item.id,
            name=item.name,
            description=item.description,
            source_type=item.source_type,
            status=item.status,
            version=item.version,
            project_id=item.project_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
            metadata=_json_to_dict(item.metadata_json),
        )
        for item in datasets
    ]
    return TrainingDatasetListResponse(items=items)


@router.get("/datasets/files", response_model=TrainingDatasetFileListResponse)
async def list_dataset_files(
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingDatasetFileListResponse:
    user_repo = UserRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=user_id)
    root = _training_datasets_root(_as_string(await settings_service.get("training", "datasets_directory", user_id=user_id)))
    items: list[TrainingDatasetFileItem] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _TRAINING_SOURCE_EXTENSIONS:
            continue
        stat = path.stat()
        items.append(
            TrainingDatasetFileItem(
                relative_path=path.relative_to(root).as_posix(),
                size_bytes=int(stat.st_size),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
            )
        )
    return TrainingDatasetFileListResponse(items=items)


@router.post("/datasets", response_model=TrainingDatasetItem)
async def create_dataset(
    payload: CreateTrainingDatasetRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingDatasetItem:
    user_repo = UserRepository(session)
    dataset_repo = TrainingDatasetRepository(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="dataset_name_empty")

    created = await dataset_repo.create(
        user_id=payload.user_id,
        name=name,
        description=payload.description.strip() if isinstance(payload.description, str) and payload.description.strip() else None,
        project_id=payload.project_id,
        source_type=payload.source_type.strip() or "manual",
        status=payload.status.strip() or "ready",
        version=max(1, payload.version),
        metadata=payload.metadata,
    )
    await session.commit()
    return _dataset_item_response(created)


@router.post("/datasets/register-file", response_model=TrainingDatasetItem)
async def register_dataset_file(
    payload: RegisterTrainingDatasetFileRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingDatasetItem:
    user_repo = UserRepository(session)
    dataset_repo = TrainingDatasetRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    root = _training_datasets_root(_as_string(await settings_service.get("training", "datasets_directory", user_id=payload.user_id)))
    source_path = _resolve_dataset_file_under_root(root, payload.file_name)
    validation_path = _resolve_dataset_file_under_root(root, payload.validation_file_name) if payload.validation_file_name else None

    created = await dataset_repo.create(
        user_id=payload.user_id,
        name=payload.name.strip(),
        description=payload.description.strip() if isinstance(payload.description, str) and payload.description.strip() else None,
        project_id=payload.project_id,
        source_type=payload.source_type.strip() or "local_file",
        status=payload.status.strip() or "ready",
        version=max(1, payload.version),
        metadata=_merge_dataset_metadata(payload.metadata, source_path=source_path, validation_source_path=validation_path),
    )
    await session.commit()
    return _dataset_item_response(created)


@router.post("/datasets/upload", response_model=TrainingDatasetItem)
async def upload_dataset_file(
    user_id: int = Form(default=1),
    name: str = Form(...),
    description: str | None = Form(default=None),
    project_id: int | None = Form(default=None),
    version: int = Form(default=1),
    metadata_json: str | None = Form(default=None),
    source_file: UploadFile = File(...),
    validation_file: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingDatasetItem:
    user_repo = UserRepository(session)
    dataset_repo = TrainingDatasetRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=user_id)
    root = _training_datasets_root(_as_string(await settings_service.get("training", "datasets_directory", user_id=user_id)))
    metadata_raw: object = json.loads(metadata_json) if metadata_json else {}
    metadata: dict[str, object]
    if isinstance(metadata_raw, dict):
        metadata = {str(key): value for key, value in cast(dict[object, object], metadata_raw).items()}
    else:
        metadata = {}

    source_name = _safe_dataset_filename(source_file.filename or name, fallback=f"{name.strip() or 'dataset'}.jsonl")
    if Path(source_name).suffix.lower() not in _TRAINING_SOURCE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="dataset_file_type_not_supported")
    source_path = root / source_name
    source_path.write_bytes(await source_file.read())

    validation_path: Path | None = None
    if validation_file is not None:
        validation_name = _safe_dataset_filename(validation_file.filename or f"{name.strip() or 'dataset'}_validation.jsonl", fallback=f"{name.strip() or 'dataset'}_validation.jsonl")
        if Path(validation_name).suffix.lower() not in _TRAINING_SOURCE_EXTENSIONS:
            raise HTTPException(status_code=400, detail="validation_file_type_not_supported")
        validation_path = root / validation_name
        validation_path.write_bytes(await validation_file.read())

    created = await dataset_repo.create(
        user_id=user_id,
        name=name.strip(),
        description=description.strip() if isinstance(description, str) and description.strip() else None,
        project_id=project_id,
        source_type="upload",
        status="ready",
        version=max(1, version),
        metadata=_merge_dataset_metadata(metadata, source_path=source_path, validation_source_path=validation_path),
    )
    await session.commit()
    return _dataset_item_response(created)


@router.post("/datasets/import-url", response_model=TrainingDatasetItem)
async def import_dataset_url(
    payload: ImportTrainingDatasetUrlRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingDatasetItem:
    user_repo = UserRepository(session)
    dataset_repo = TrainingDatasetRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    root = _training_datasets_root(_as_string(await settings_service.get("training", "datasets_directory", user_id=payload.user_id)))

    source_name = _safe_dataset_filename(Path(urlparse(payload.source_url).path).name or f"{payload.name}.jsonl", fallback=f"{payload.name}.jsonl")
    source_path = root / source_name
    _download_training_source(payload.source_url, source_path)

    validation_path: Path | None = None
    if payload.validation_source_url:
        validation_name = _safe_dataset_filename(Path(urlparse(payload.validation_source_url).path).name or f"{payload.name}_validation.jsonl", fallback=f"{payload.name}_validation.jsonl")
        validation_path = root / validation_name
        _download_training_source(payload.validation_source_url, validation_path)

    created = await dataset_repo.create(
        user_id=payload.user_id,
        name=payload.name.strip(),
        description=payload.description.strip() if isinstance(payload.description, str) and payload.description.strip() else None,
        project_id=payload.project_id,
        source_type=payload.source_type.strip() or "url",
        status=payload.status.strip() or "ready",
        version=max(1, payload.version),
        metadata=_merge_dataset_metadata(payload.metadata, source_path=source_path, validation_source_path=validation_path),
    )
    await session.commit()
    return _dataset_item_response(created)


@router.get("/jobs", response_model=TrainingJobListResponse)
async def list_jobs(
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingJobListResponse:
    user_repo = UserRepository(session)
    job_repo = TrainingJobRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    jobs = await job_repo.list_by_user(user_id=user_id, limit=200)
    items = [_to_training_job_item(item) for item in jobs]
    return TrainingJobListResponse(items=items)


@router.post("/jobs", response_model=TrainingJobItem)
async def submit_job(
    payload: CreateTrainingJobRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingJobItem:
    user_repo = UserRepository(session)
    dataset_repo = TrainingDatasetRepository(session)
    job_repo = TrainingJobRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    dataset = await dataset_repo.get_by_id(user_id=payload.user_id, dataset_id=payload.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset_not_found")

    training_enabled = await settings_service.get(category="training", key="enabled", user_id=payload.user_id)
    if not bool(training_enabled):
        raise HTTPException(status_code=409, detail="training_disabled")

    requested_base_model = payload.base_model_id.strip() if isinstance(payload.base_model_id, str) else ""
    if not requested_base_model:
        configured_base_model = await settings_service.get(category="training", key="base_model", user_id=payload.user_id)
        requested_base_model = str(configured_base_model).strip() if configured_base_model is not None else ""

    if not requested_base_model:
        raise HTTPException(status_code=400, detail="base_model_not_configured")

    selected_model = await _resolve_registered_model(session, requested_base_model)
    if selected_model is None:
        raise HTTPException(status_code=404, detail="base_model_not_found")

    resolved_base_model_id = selected_model.name

    default_trainer = await settings_service.get(category="training", key="default_trainer", user_id=payload.user_id)
    trainer_name = payload.trainer_name.strip().lower() if isinstance(payload.trainer_name, str) and payload.trainer_name.strip() else str(default_trainer)
    trainer_available, trainer_reason = _is_trainer_available(trainer_name)
    if not trainer_available:
        raise HTTPException(status_code=400, detail={"code": "training.trainer_unavailable", "message": trainer_reason or "Trainer nicht verfuegbar"})

    enriched_hyperparameters: dict[str, object] = {str(key): value for key, value in payload.hyperparameters.items()}
    enriched_hyperparameters.setdefault("base_model", selected_model.model_path)
    enriched_hyperparameters.setdefault("base_model_name", selected_model.name)
    enriched_hyperparameters.setdefault("base_model_registry_id", selected_model.id)
    enriched_hyperparameters.setdefault("base_model_backend", selected_model.backend)

    preflight = await _run_preflight(
        session=session,
        user_id=payload.user_id,
        dataset=dataset,
        requested_base_model=selected_model.name,
        trainer_name=trainer_name,
        hyperparameters=enriched_hyperparameters,
    )
    if not preflight.ready:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "training.preflight_failed",
                "message": "Preflight fehlgeschlagen. Job wurde nicht gestartet.",
                "preflight": preflight.model_dump(),
            },
        )

    created = await job_repo.create(
        user_id=payload.user_id,
        dataset_id=payload.dataset_id,
        base_model_id=resolved_base_model_id,
        trainer_name=trainer_name,
        status=TrainingStatus.QUEUED,
        hyperparameters=enriched_hyperparameters,
    )
    await session.commit()
    return _to_training_job_item(created)


@router.post("/preflight", response_model=TrainingPreflightResponse)
async def training_preflight(
    payload: TrainingPreflightRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingPreflightResponse:
    user_repo = UserRepository(session)
    dataset_repo = TrainingDatasetRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    dataset = await dataset_repo.get_by_id(user_id=payload.user_id, dataset_id=payload.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset_not_found")

    requested_base_model = payload.base_model_id.strip() if isinstance(payload.base_model_id, str) else ""
    if not requested_base_model:
        configured_base_model = await settings_service.get(category="training", key="base_model", user_id=payload.user_id)
        requested_base_model = str(configured_base_model).strip() if configured_base_model is not None else ""
    if not requested_base_model:
        raise HTTPException(status_code=400, detail="base_model_not_configured")

    default_trainer = await settings_service.get(category="training", key="default_trainer", user_id=payload.user_id)
    trainer_name = payload.trainer_name.strip().lower() if isinstance(payload.trainer_name, str) and payload.trainer_name.strip() else str(default_trainer)

    trainer_available, trainer_reason = _is_trainer_available(trainer_name)
    if not trainer_available:
        raise HTTPException(status_code=400, detail={"code": "training.trainer_unavailable", "message": trainer_reason or "Trainer nicht verfuegbar"})

    return await _run_preflight(
        session=session,
        user_id=payload.user_id,
        dataset=dataset,
        requested_base_model=requested_base_model,
        trainer_name=trainer_name,
        hyperparameters={str(key): value for key, value in payload.hyperparameters.items()},
    )


@router.get("/jobs/{job_id}", response_model=TrainingJobItem)
async def get_job(
    job_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingJobItem:
    user_repo = UserRepository(session)
    job_repo = TrainingJobRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    job = await job_repo.get_by_id(user_id=user_id, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    return _to_training_job_item(job)


@router.post("/jobs/{job_id}/cancel", response_model=TrainingJobItem)
async def cancel_job(
    job_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingJobItem:
    user_repo = UserRepository(session)
    job_repo = TrainingJobRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    job = await job_repo.get_by_id(user_id=user_id, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if job.status in TERMINAL_STATUSES:
        raise HTTPException(status_code=409, detail="job_already_terminal")
    if job.status not in CANCELLABLE_STATUSES:
        raise HTTPException(status_code=409, detail="job_not_cancellable")

    updated = await job_repo.request_cancel(job=job)
    await session.commit()
    return _to_training_job_item(updated)


@router.post("/jobs/{job_id}/retry", response_model=TrainingJobItem)
async def retry_job(
    job_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingJobItem:
    user_repo = UserRepository(session)
    job_repo = TrainingJobRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=user_id)
    source_job = await job_repo.get_by_id(user_id=user_id, job_id=job_id)
    if source_job is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    training_enabled = await settings_service.get(category="training", key="enabled", user_id=user_id)
    if not bool(training_enabled):
        raise HTTPException(status_code=409, detail="training_disabled")

    retried = await job_repo.retry_from(source_job=source_job)
    await session.commit()
    return _to_training_job_item(retried)


@router.get("/jobs/{job_id}/artifact-check")
async def check_job_artifacts(
    job_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    job_repo = TrainingJobRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    job = await job_repo.get_by_id(user_id=user_id, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    result_payload = _json_to_dict(job.result_json)
    saved_info = cast(dict[str, object], result_payload.get("saved")) if isinstance(result_payload.get("saved"), dict) else {}
    hyperparameters = _json_to_dict(job.hyperparameters_json)

    verification = _verify_peft_artifact(saved_info, hyperparameters)
    return {
        "job_id": job.id,
        "status": job.status,
        "base_model_id": job.base_model_id,
        "saved": saved_info,
        "verification": verification,
    }


@router.post("/jobs/{job_id}/register", response_model=TrainingAdapterRegisterResponse)
async def register_training_adapter(
    job_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingAdapterRegisterResponse:
    user_repo = UserRepository(session)
    job_repo = TrainingJobRepository(session)
    dataset_repo = TrainingDatasetRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    job = await job_repo.get_by_id(user_id=user_id, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if job.status != TrainingStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="job_not_completed")

    result_payload = _json_to_dict(job.result_json)
    saved_info = cast(dict[str, object], result_payload.get("saved")) if isinstance(result_payload.get("saved"), dict) else {}
    hyperparameters = _json_to_dict(job.hyperparameters_json)
    verification = _verify_peft_artifact(saved_info, hyperparameters)
    if not bool(verification.get("adapter_load_ok")):
        raise HTTPException(status_code=409, detail={"code": "training.adapter_check_failed"})

    adapter_path = str(Path(_as_string(saved_info.get("artifact_path"))).expanduser().resolve(strict=False))
    if not adapter_path:
        raise HTTPException(status_code=409, detail="adapter_artifact_missing")

    existing = (await session.execute(select(ModelConfig).where(ModelConfig.model_path == adapter_path).limit(1))).scalar_one_or_none()
    if existing is not None:
        metadata = _json_to_dict(existing.metadata_json)
        base_model_registry_id = _as_int(metadata.get("base_model_registry_id")) or 0
        return TrainingAdapterRegisterResponse(
            registered=True,
            model_id=existing.id,
            name=existing.name,
            model_type=str(existing.model_type or "peft_adapter"),
            base_model_id=base_model_registry_id,
            adapter_path=adapter_path,
        )

    base_model_name = _as_string(job.base_model_id)
    base_model = await _resolve_registered_model(session, base_model_name)
    if base_model is None:
        raise HTTPException(status_code=404, detail="base_model_not_found")

    dataset = await dataset_repo.get_by_id_any(dataset_id=job.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset_not_found")

    adapter_name = _adapter_model_name(base_model_name=base_model.name, dataset_name=dataset.name)
    metadata_payload: dict[str, object] = {
        "model_format": "peft_adapter",
        "model_family": _json_to_dict(base_model.metadata_json).get("model_family") or "peft",
        "task_type": "text_generation",
        "group": "Text / Chat",
        "supports_inference": True,
        "supports_training": False,
        "supports_peft_training": False,
        "supports_4bit": True,
        "supports_chat": True,
        "supports_embeddings": False,
        "supports_reranking": False,
        "supports_vision": False,
        "supports_audio": False,
        "adapter_path": adapter_path,
        "base_model_registry_id": base_model.id,
        "base_model_name": base_model.name,
        "base_model_path": base_model.model_path,
        "training_job_id": job.id,
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "specialist_domain": _as_string(_json_to_dict(dataset.metadata_json).get("task_type") or "domain_qa"),
        "load_in_4bit": bool(hyperparameters.get("load_in_4bit", True)),
        "registration_status": "experimental",
    }

    entity = ModelConfig(
        name=adapter_name,
        model_path=adapter_path,
        backend="transformers_peft",
        model_format="peft_adapter",
        model_type="text_generation",
        metadata_json=json.dumps(metadata_payload),
        is_available=True,
        load_status="unloaded",
        last_scanned_at=datetime.now(timezone.utc),
    )
    session.add(entity)
    await session.flush()
    await session.commit()

    return TrainingAdapterRegisterResponse(
        registered=True,
        model_id=entity.id,
        name=entity.name,
        model_type="peft_adapter",
        base_model_id=base_model.id,
        adapter_path=adapter_path,
    )


@router.post("/jobs/{job_id}/compare", response_model=TrainingAdapterCompareResponse)
async def compare_training_adapter(
    job_id: int,
    payload: TrainingAdapterCompareRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> TrainingAdapterCompareResponse:
    user_repo = UserRepository(session)
    job_repo = TrainingJobRepository(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    job = await job_repo.get_by_id(user_id=payload.user_id, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if job.status != TrainingStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="job_not_completed")

    result_payload = _json_to_dict(job.result_json)
    saved_info = cast(dict[str, object], result_payload.get("saved")) if isinstance(result_payload.get("saved"), dict) else {}
    hyperparameters = _json_to_dict(job.hyperparameters_json)
    verification = _verify_peft_artifact(saved_info, hyperparameters)
    if not bool(verification.get("adapter_load_ok")):
        raise HTTPException(status_code=409, detail={"code": "training.adapter_check_failed", "verification": verification})

    base_backend = create_backend("transformers")
    adapter_backend = create_backend("transformers_peft")
    base_model_name = _as_string(job.base_model_id)
    base_model = await _resolve_registered_model(session, base_model_name)
    if base_model is None:
        raise HTTPException(status_code=404, detail="base_model_not_found")

    base_metadata = _json_to_dict(base_model.metadata_json)
    adapter_metadata: dict[str, object] = {
        "adapter_path": str(Path(_as_string(saved_info.get("artifact_path"))).expanduser().resolve(strict=False)),
        "base_model_path": _as_string(hyperparameters.get("base_model")),
        "load_in_4bit": bool(hyperparameters.get("load_in_4bit", True)),
    }
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="compare_prompt_empty")

    base_backend.load(base_model.model_path, {"metadata": base_metadata, "prefer_gpu": True})
    try:
        base_response = base_backend.generate(prompt, {"max_new_tokens": payload.max_new_tokens, "temperature": payload.temperature})
    finally:
        base_backend.unload()

    adapter_backend.load(_as_string(adapter_metadata["adapter_path"]), {"metadata": adapter_metadata, "prefer_gpu": True})
    try:
        adapter_response = adapter_backend.generate(prompt, {"max_new_tokens": payload.max_new_tokens, "temperature": payload.temperature})
    finally:
        adapter_backend.unload()

    base_response_cleaned = clean_model_output_text(base_response)
    adapter_response_cleaned = clean_model_output_text(adapter_response)
    evaluation = _evaluate_compare_outputs(
        base_raw=base_response,
        adapter_raw=adapter_response,
        base_clean=base_response_cleaned,
        adapter_clean=adapter_response_cleaned,
    )

    dataset_repo = TrainingDatasetRepository(session)
    dataset = await dataset_repo.get_by_id_any(dataset_id=job.dataset_id)
    adapter_model_name = _adapter_model_name(base_model_name=base_model.name, dataset_name=dataset.name if dataset is not None else f"job-{job.id}")
    return TrainingAdapterCompareResponse(
        job_id=job.id,
        base_model_name=base_model.name,
        adapter_model_name=adapter_model_name,
        prompt=prompt,
        base_response=base_response,
        adapter_response=adapter_response,
        base_response_cleaned=base_response_cleaned,
        adapter_response_cleaned=adapter_response_cleaned,
        evaluation=evaluation,
    )
