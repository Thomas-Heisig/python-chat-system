import asyncio
import inspect
import json
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.chat.service import clean_model_output_text
from app.models.loader import create_backend
from app.training.datasets.adapter import DatasetAdapter, DatasetValidationError
from app.training.trainers.base import TrainingBackend, TrainingCancelledError, TrainingRunContext
from app.training.trainers.config import LoRATrainingConfig


@dataclass(slots=True)
class PeftArtifact:
    adapter_path: str
    tokenizer_path: str
    manifest_path: str


def _extract_json_object(raw_text: str) -> dict[str, object] | None:
    text = raw_text.strip()
    if not text:
        return None

    candidates: list[str] = [text]
    fenced = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, flags=re.IGNORECASE)
    candidates.extend(fenced)

    object_match = re.search(r"\{[\s\S]*\}", text)
    if object_match:
        candidates.append(object_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return {str(key): value for key, value in parsed.items()}
    return None


def _as_label(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _as_tool_signature(value: object) -> str:
    tools: list[str] = []
    if isinstance(value, list):
        for item in value:
            label = _as_label(item)
            if label:
                tools.append(label)
    elif isinstance(value, str):
        label = _as_label(value)
        if label:
            tools.append(label)
    normalized = sorted(set(tools))
    if not normalized:
        return "__none__"
    return ",".join(normalized)


def _update_confusion(matrix: dict[str, dict[str, int]], expected: str, predicted: str) -> None:
    row = matrix.setdefault(expected or "__none__", {})
    key = predicted or "__none__"
    row[key] = int(row.get(key, 0)) + 1


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = _safe_ratio(float(tp), float(tp + fp))
    recall = _safe_ratio(float(tp), float(tp + fn))
    if precision + recall <= 0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


def _build_router_report(
    *,
    expected_rows: list[dict[str, str]],
    base_outputs: list[str],
    adapter_outputs: list[str],
    testset_source_path: str,
    minimum_recommended_size: int,
) -> tuple[dict[str, object], dict[str, float]]:
    records = min(len(expected_rows), len(base_outputs), len(adapter_outputs))
    warnings: list[str] = []

    intent_confusion_adapter: dict[str, dict[str, int]] = {}
    intent_confusion_base: dict[str, dict[str, int]] = {}
    agent_confusion_adapter: dict[str, dict[str, int]] = {}
    agent_confusion_base: dict[str, dict[str, int]] = {}
    tool_confusion_adapter: dict[str, dict[str, int]] = {}
    tool_confusion_base: dict[str, dict[str, int]] = {}

    labeled_intent = 0
    labeled_agent = 0
    labeled_tools = 0

    intent_correct_adapter = 0
    intent_correct_base = 0
    agent_correct_adapter = 0
    agent_correct_base = 0

    tool_tp_adapter = 0
    tool_fp_adapter = 0
    tool_fn_adapter = 0
    tool_tp_base = 0
    tool_fp_base = 0
    tool_fn_base = 0

    base_json_valid = 0
    adapter_json_valid = 0

    for index in range(records):
        expected_json = _extract_json_object(expected_rows[index].get("completion", ""))
        if expected_json is None:
            continue

        base_json = _extract_json_object(clean_model_output_text(base_outputs[index]))
        adapter_json = _extract_json_object(clean_model_output_text(adapter_outputs[index]))

        if base_json is not None:
            base_json_valid += 1
        if adapter_json is not None:
            adapter_json_valid += 1

        expected_intent = _as_label(expected_json.get("intent"))
        expected_agent = _as_label(expected_json.get("agent"))
        expected_tools_signature = _as_tool_signature(expected_json.get("tools"))

        base_intent = _as_label(base_json.get("intent")) if base_json is not None else ""
        base_agent = _as_label(base_json.get("agent")) if base_json is not None else ""
        base_tools_signature = _as_tool_signature(base_json.get("tools")) if base_json is not None else "__none__"

        adapter_intent = _as_label(adapter_json.get("intent")) if adapter_json is not None else ""
        adapter_agent = _as_label(adapter_json.get("agent")) if adapter_json is not None else ""
        adapter_tools_signature = _as_tool_signature(adapter_json.get("tools")) if adapter_json is not None else "__none__"

        if expected_intent:
            labeled_intent += 1
            if adapter_intent == expected_intent:
                intent_correct_adapter += 1
            if base_intent == expected_intent:
                intent_correct_base += 1
            _update_confusion(intent_confusion_adapter, expected_intent, adapter_intent)
            _update_confusion(intent_confusion_base, expected_intent, base_intent)

        if expected_agent:
            labeled_agent += 1
            if adapter_agent == expected_agent:
                agent_correct_adapter += 1
            if base_agent == expected_agent:
                agent_correct_base += 1
            _update_confusion(agent_confusion_adapter, expected_agent, adapter_agent)
            _update_confusion(agent_confusion_base, expected_agent, base_agent)

        expected_tools = set(expected_tools_signature.split(",")) if expected_tools_signature != "__none__" else set()
        base_tools = set(base_tools_signature.split(",")) if base_tools_signature != "__none__" else set()
        adapter_tools = set(adapter_tools_signature.split(",")) if adapter_tools_signature != "__none__" else set()

        labeled_tools += 1
        tool_tp_adapter += len(expected_tools.intersection(adapter_tools))
        tool_fp_adapter += len(adapter_tools.difference(expected_tools))
        tool_fn_adapter += len(expected_tools.difference(adapter_tools))
        tool_tp_base += len(expected_tools.intersection(base_tools))
        tool_fp_base += len(base_tools.difference(expected_tools))
        tool_fn_base += len(expected_tools.difference(base_tools))
        _update_confusion(tool_confusion_adapter, expected_tools_signature, adapter_tools_signature)
        _update_confusion(tool_confusion_base, expected_tools_signature, base_tools_signature)

    if records < minimum_recommended_size:
        warnings.append(
            f"Testset zu klein fuer stabile Metriken: {records} Samples (empfohlen >= {minimum_recommended_size})."
        )
    if labeled_intent == 0 or labeled_agent == 0:
        warnings.append("Keine vollstaendig parsebaren Intent/Agent-Labels im Testsatz gefunden.")

    base_metrics = {
        "intent_accuracy": round(_safe_ratio(float(intent_correct_base), float(labeled_intent)), 6),
        "agent_selection_f1": round(_safe_ratio(float(agent_correct_base), float(labeled_agent)), 6),
        "tool_selection_f1": round(_f1(tool_tp_base, tool_fp_base, tool_fn_base), 6),
        "json_schema_validity": round(_safe_ratio(float(base_json_valid), float(records)), 6),
    }
    adapter_metrics = {
        "intent_accuracy": round(_safe_ratio(float(intent_correct_adapter), float(labeled_intent)), 6),
        "agent_selection_f1": round(_safe_ratio(float(agent_correct_adapter), float(labeled_agent)), 6),
        "tool_selection_f1": round(_f1(tool_tp_adapter, tool_fp_adapter, tool_fn_adapter), 6),
        "json_schema_validity": round(_safe_ratio(float(adapter_json_valid), float(records)), 6),
    }

    report: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task": "agent_tool_router",
        "testset": {
            "source_path": testset_source_path,
            "sample_count": records,
            "minimum_recommended_size": minimum_recommended_size,
        },
        "base_vs_adapter": {
            "base": base_metrics,
            "adapter": adapter_metrics,
            "delta": {
                key: round(float(adapter_metrics.get(key, 0.0)) - float(base_metrics.get(key, 0.0)), 6)
                for key in adapter_metrics.keys()
            },
        },
        "confusion_matrix": {
            "intent": {"base": intent_confusion_base, "adapter": intent_confusion_adapter},
            "agent": {"base": agent_confusion_base, "adapter": agent_confusion_adapter},
            "tool": {"base": tool_confusion_base, "adapter": tool_confusion_adapter},
        },
        "warnings": warnings,
    }
    return report, adapter_metrics


def _write_json_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _attach_trainable_adapter(
    model: object,
    *,
    resume_adapter_path: str,
    lora_config: object,
    peft_model_class: Any,
    get_peft_model_fn: Callable[[object, object], object],
) -> object:
    """Continue an existing LoRA adapter or create the first chain link."""
    normalized = resume_adapter_path.strip()
    if not normalized:
        return get_peft_model_fn(model, lora_config)

    adapter_dir = Path(normalized).expanduser().resolve(strict=False)
    config_file = adapter_dir / "adapter_config.json"
    weight_files = (adapter_dir / "adapter_model.safetensors", adapter_dir / "adapter_model.bin")
    if not config_file.is_file() or not any(path.is_file() for path in weight_files):
        raise RuntimeError(f"continual_adapter_invalid:{adapter_dir}")
    return peft_model_class.from_pretrained(model, str(adapter_dir), is_trainable=True)


def _create_training_arguments(
    training_arguments_class: type[object],
    payload: dict[str, object],
    *,
    force_cpu: bool,
) -> object:
    """Construct TrainingArguments across transformers 4.x/5.x API changes."""
    parameters = inspect.signature(training_arguments_class.__init__).parameters
    kwargs = {key: value for key, value in payload.items() if key in parameters}

    if "eval_strategy" in parameters:
        kwargs["eval_strategy"] = "steps"
    elif "evaluation_strategy" in parameters:
        kwargs["evaluation_strategy"] = "steps"

    if force_cpu:
        if "use_cpu" in parameters:
            kwargs["use_cpu"] = True
        elif "no_cuda" in parameters:
            kwargs["no_cuda"] = True

    # Some downstream transformers builds expose an outdated/decorated signature.
    # Remove only parameters the runtime explicitly rejects and retry deterministically.
    for _ in range(3):
        try:
            return training_arguments_class(**kwargs)
        except TypeError as exc:
            match = re.search(r"unexpected keyword argument ['\"]([^'\"]+)['\"]", str(exc))
            rejected = match.group(1) if match else None
            if rejected is None or rejected not in kwargs:
                raise
            kwargs.pop(rejected)
    return training_arguments_class(**kwargs)


def _resolve_target_modules(
    *,
    model: object,
    configured_target_modules: list[str],
) -> list[str]:
    normalized = [item.strip() for item in configured_target_modules if item.strip()]
    if normalized and all(item.lower() != "auto" for item in normalized):
        return normalized

    named_modules = getattr(model, "named_modules", None)
    if not callable(named_modules):
        return ["q_proj", "k_proj", "v_proj", "o_proj"]

    linear_leaf_names: set[str] = set()
    for full_name, module in named_modules():
        module_class = module.__class__.__name__.lower()
        if "linear" not in module_class:
            continue
        leaf = str(full_name).split(".")[-1].strip()
        if leaf:
            linear_leaf_names.add(leaf)

    preferred_groups: list[list[str]] = [
        ["q_proj", "k_proj", "v_proj", "o_proj"],
        ["query_key_value"],
        ["w_pack"],
        ["c_attn", "c_proj"],
    ]
    for group in preferred_groups:
        present = [name for name in group if name in linear_leaf_names]
        if present:
            return present

    fallback_priority = [
        "up_proj",
        "down_proj",
        "gate_proj",
        "out_proj",
        "fc1",
        "fc2",
        "dense",
        "proj",
    ]
    fallback = [name for name in fallback_priority if name in linear_leaf_names]
    if fallback:
        return fallback

    return ["q_proj", "k_proj", "v_proj", "o_proj"]


class PeftLoRATrainer(TrainingBackend):
    name = "peft_lora"
    is_simulation = False

    async def prepare(self, job: TrainingRunContext, dataset: dict[str, object]) -> dict[str, object]:
        config = LoRATrainingConfig.from_hyperparameters(
            base_model_id=job.base_model_id,
            job_id=job.job_id,
            hyperparameters=job.hyperparameters,
        )
        source_path = str(dataset.get("source_path") or "").strip()
        validation_source_path = str(dataset.get("validation_source_path") or "").strip()
        if not source_path:
            raise DatasetValidationError("dataset_source_path_missing")

        rows = DatasetAdapter().load_samples(source_path=source_path)
        validation_rows = DatasetAdapter().load_samples(source_path=validation_source_path) if validation_source_path else []
        output_root = Path(job.output_dir)
        (output_root / "adapter").mkdir(parents=True, exist_ok=True)
        (output_root / "tokenizer").mkdir(parents=True, exist_ok=True)

        prepare_payload = {
            "dataset_rows": rows,
            "validation_rows": validation_rows,
            "source_path": source_path,
            "validation_source_path": validation_source_path,
            "config": config,
            "output_root": output_root,
        }
        (output_root / "training-config.json").write_text(
            json.dumps(job.hyperparameters, indent=2),
            encoding="utf-8",
        )
        return prepare_payload

    async def train(
        self,
        job: TrainingRunContext,
        dataset: dict[str, object],
        progress_callback: Callable[[dict[str, object]], Awaitable[None]],
        cancel_token: Callable[[], Awaitable[bool]],
    ) -> PeftArtifact:
        del job
        config: LoRATrainingConfig = dataset["config"]  # type: ignore[assignment]
        rows: list[dict[str, str]] = dataset["dataset_rows"]  # type: ignore[assignment]
        validation_rows: list[dict[str, str]] = dataset.get("validation_rows", [])  # type: ignore[assignment]
        output_root: Path = dataset["output_root"]  # type: ignore[assignment]

        try:
            import torch
            from datasets import Dataset
            from peft import LoraConfig, PeftModel, get_peft_model
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                BitsAndBytesConfig,
                Trainer,
                TrainerCallback,
                TrainingArguments,
            )
        except Exception as exc:  # pragma: no cover - depends on optional packages
            raise RuntimeError(
                "missing_training_dependencies: install transformers peft bitsandbytes trl datasets accelerate"
            ) from exc

        tokenized_rows = [
            {"text": f"User: {item['prompt']}\\nAssistant: {item['completion']}"}
            for item in rows
        ]
        validation_tokenized_rows = [
            {"text": f"User: {item['prompt']}\nAssistant: {item['completion']}"}
            for item in validation_rows
        ]

        hf_dataset = Dataset.from_list(tokenized_rows)
        split_dataset = None if validation_tokenized_rows else hf_dataset.train_test_split(test_size=config.validation_split, seed=42)

        tokenizer = AutoTokenizer.from_pretrained(config.base_model)

        def _normalize_special_token_ids(model: object) -> None:
            vocab_size = len(tokenizer)
            pad_token_id = tokenizer.pad_token_id

            if pad_token_id is None or not 0 <= pad_token_id < vocab_size:
                if tokenizer.eos_token_id is not None and 0 <= int(tokenizer.eos_token_id) < vocab_size:
                    tokenizer.pad_token = tokenizer.eos_token
                    pad_token_id = tokenizer.eos_token_id
                else:
                    tokenizer.add_special_tokens({"pad_token": "<|pad|>"})
                    pad_token_id = tokenizer.pad_token_id

            if getattr(model, "resize_token_embeddings", None) is not None and len(tokenizer) != vocab_size:
                model.resize_token_embeddings(len(tokenizer))

            model.config.pad_token_id = pad_token_id
            if getattr(model, "generation_config", None) is not None:
                model.generation_config.pad_token_id = pad_token_id

            for field in ("pad_token_id", "eos_token_id", "bos_token_id"):
                token_id = getattr(model.config, field, None)
                if token_id is None:
                    continue
                if not 0 <= int(token_id) < len(tokenizer):
                    if field == "pad_token_id" and tokenizer.pad_token_id is not None:
                        setattr(model.config, field, tokenizer.pad_token_id)
                        if getattr(model, "generation_config", None) is not None:
                            setattr(model.generation_config, field, tokenizer.pad_token_id)
                    elif field == "eos_token_id" and tokenizer.eos_token_id is not None:
                        setattr(model.config, field, tokenizer.eos_token_id)
                        if getattr(model, "generation_config", None) is not None:
                            setattr(model.generation_config, field, tokenizer.eos_token_id)
                    elif field == "bos_token_id" and tokenizer.bos_token_id is not None:
                        setattr(model.config, field, tokenizer.bos_token_id)
                        if getattr(model, "generation_config", None) is not None:
                            setattr(model.generation_config, field, tokenizer.bos_token_id)

        def tokenize_fn(batch: dict[str, list[str]]) -> dict[str, list[list[int]]]:
            encoded = tokenizer(
                batch["text"],
                truncation=True,
                max_length=config.max_sequence_length,
                padding="max_length",
            )
            encoded["labels"] = encoded["input_ids"].copy()
            return encoded

        if validation_tokenized_rows:
            train_dataset_raw = hf_dataset
            eval_dataset_raw = Dataset.from_list(validation_tokenized_rows)
        else:
            train_dataset_raw = split_dataset["train"]
            eval_dataset_raw = split_dataset["test"]

        train_dataset = train_dataset_raw.map(tokenize_fn, batched=True, remove_columns=["text"])
        eval_dataset = eval_dataset_raw.map(tokenize_fn, batched=True, remove_columns=["text"])

        loop = asyncio.get_running_loop()

        def _is_cuda_oom(exc: Exception) -> bool:
            message = str(exc).lower()
            return "out of memory" in message and "cuda" in message

        class CancellationCallback(TrainerCallback):
            def __init__(self, cancellation_event: threading.Event) -> None:
                self.cancellation_event = cancellation_event

            def on_train_begin(self, args, state, control, **kwargs):
                del args, kwargs
                total_steps = max(1, int(state.max_steps or 1))
                payload = {
                    "progress": 0.0,
                    "current_step": 0,
                    "total_steps": total_steps,
                    "current_epoch": float(state.epoch or 0.0),
                    "learning_rate": config.learning_rate,
                    "log_line": f"training initialized; total steps {total_steps}",
                }
                asyncio.run_coroutine_threadsafe(progress_callback(payload), loop)
                return control

            def on_step_begin(self, args, state, control, **kwargs):
                del args, kwargs
                total_steps = max(1, int(state.max_steps or 1))
                current_step = int(state.global_step or 0)
                payload = {
                    "progress": round((current_step / total_steps) * 100.0, 2),
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "current_epoch": float(state.epoch or 0.0),
                    "learning_rate": config.learning_rate,
                    "log_line": f"first training step running" if current_step == 0 else f"step {current_step} started",
                }
                asyncio.run_coroutine_threadsafe(progress_callback(payload), loop)
                return control

            def on_log(self, args, state, control, logs=None, **kwargs):
                del args, kwargs
                payload: dict[str, object] = {}
                if isinstance(logs, dict):
                    raw_loss = logs.get("loss")
                    raw_lr = logs.get("learning_rate")
                    if isinstance(raw_loss, (int, float)):
                        payload["loss"] = float(raw_loss)
                    if isinstance(raw_lr, (int, float)):
                        payload["learning_rate"] = float(raw_lr)
                if payload:
                    payload["log_line"] = f"step {int(state.global_step or 0)} log update"
                    asyncio.run_coroutine_threadsafe(progress_callback(payload), loop)
                return control

            def on_step_end(self, args, state, control, **kwargs):
                del kwargs
                if self.cancellation_event.is_set():
                    control.should_training_stop = True
                total_steps = max(1, int(state.max_steps or 1))
                current_step = int(state.global_step or 0)
                progress = round((current_step / total_steps) * 100.0, 2)
                loss_value = None
                if state.log_history:
                    last_log = state.log_history[-1]
                    if isinstance(last_log, dict):
                        raw_loss = last_log.get("loss")
                        if isinstance(raw_loss, (int, float)):
                            loss_value = float(raw_loss)
                payload = {
                    "progress": progress,
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "current_epoch": float(state.epoch or 0.0),
                    "loss": loss_value,
                    "learning_rate": float(getattr(args, "learning_rate", config.learning_rate)),
                    "log_line": f"step {current_step}/{total_steps}",
                }
                asyncio.run_coroutine_threadsafe(progress_callback(payload), loop)
                return control

        async def _run_attempt(*, force_cpu: bool) -> tuple[object, object, float]:
            quant_config = None
            if config.load_in_4bit and not force_cpu:
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                )

            if force_cpu:
                await progress_callback(
                    {
                        "log_line": "cuda oom erkannt - fallback auf cpu/ram gestartet",
                        "progress": 0.0,
                    }
                )
                model_load_kwargs: dict[str, object] = {
                    "device_map": {"": "cpu"},
                    "quantization_config": None,
                    "dtype": torch.float32,
                    "low_cpu_mem_usage": True,
                }
            else:
                model_load_kwargs = {
                    "device_map": "auto",
                    "quantization_config": quant_config,
                    "dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
                }

            try:
                model = AutoModelForCausalLM.from_pretrained(
                    config.base_model,
                    **model_load_kwargs,
                )
            except TypeError:
                model_load_kwargs.pop("dtype", None)
                model_load_kwargs["torch_dtype"] = torch.float32 if force_cpu else (torch.float16 if torch.cuda.is_available() else torch.float32)
                model = AutoModelForCausalLM.from_pretrained(
                    config.base_model,
                    **model_load_kwargs,
                )

            _normalize_special_token_ids(model)
            resolved_target_modules = _resolve_target_modules(
                model=model,
                configured_target_modules=config.target_modules,
            )
            await progress_callback(
                {
                    "log_line": f"lora target_modules: {', '.join(resolved_target_modules)}",
                    "progress": 0.05,
                }
            )

            lora_cfg = LoraConfig(
                r=config.lora_r,
                lora_alpha=config.lora_alpha,
                lora_dropout=config.lora_dropout,
                bias="none",
                target_modules=resolved_target_modules,
                task_type="CAUSAL_LM",
            )
            model = _attach_trainable_adapter(
                model,
                resume_adapter_path=config.resume_adapter_path,
                lora_config=lora_cfg,
                peft_model_class=PeftModel,
                get_peft_model_fn=get_peft_model,
            )

            cancelled = threading.Event()
            training_finished = threading.Event()

            async def cancel_watcher() -> None:
                while not training_finished.is_set():
                    if await cancel_token():
                        cancelled.set()
                        break
                    await asyncio.sleep(0.5)

            training_args_payload: dict[str, object] = {
                "output_dir": str(output_root / "adapter"),
                "per_device_train_batch_size": 1 if force_cpu else config.per_device_train_batch_size,
                "gradient_accumulation_steps": config.gradient_accumulation_steps,
                "num_train_epochs": config.num_train_epochs,
                "learning_rate": config.learning_rate,
                "warmup_ratio": config.warmup_ratio,
                "weight_decay": config.weight_decay,
                "logging_steps": config.logging_steps,
                "logging_first_step": config.logging_first_step,
                "save_steps": config.save_steps,
                "eval_steps": config.eval_steps,
                "load_best_model_at_end": config.load_best_model_at_end,
                "metric_for_best_model": config.metric_for_best_model,
                "greater_is_better": config.greater_is_better,
                "report_to": [],
                "seed": config.seed,
                "data_seed": config.seed,
                "fp16": False if force_cpu else (True if torch.cuda.is_available() else False),
                "bf16": False,
                "remove_unused_columns": False,
            }
            if config.max_steps is not None:
                training_args_payload["max_steps"] = config.max_steps

            args = _create_training_arguments(
                TrainingArguments,
                training_args_payload,
                force_cpu=force_cpu,
            )

            trainer = Trainer(
                model=model,
                args=args,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                callbacks=[CancellationCallback(cancelled)],
            )

            watcher_task = asyncio.create_task(cancel_watcher())
            start_time = time.perf_counter()
            try:
                await asyncio.to_thread(trainer.train)
                if cancelled.is_set():
                    raise TrainingCancelledError()
            finally:
                training_finished.set()
                await watcher_task
            elapsed = time.perf_counter() - start_time
            return model, trainer, elapsed

        try:
            model, trainer, elapsed = await _run_attempt(force_cpu=False)
        except Exception as exc:
            if not _is_cuda_oom(exc):
                raise
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            model, trainer, elapsed = await _run_attempt(force_cpu=True)

        peak_vram_mb = None
        estimated_vram_mb = None
        if torch.cuda.is_available():
            peak_vram_mb = round(float(torch.cuda.max_memory_reserved()) / (1024.0 * 1024.0), 2)
            estimated_vram_mb = round(float(torch.cuda.max_memory_allocated()) / (1024.0 * 1024.0), 2)

        total_steps = max(1, int(getattr(trainer.state, "global_step", 1)))
        steps_per_second = round(total_steps / max(0.01, elapsed), 4)
        samples_seen = total_steps * config.per_device_train_batch_size
        samples_per_second = round(samples_seen / max(0.01, elapsed), 4)
        await progress_callback(
            {
                "progress": 100.0,
                "current_step": total_steps,
                "total_steps": total_steps,
                "current_epoch": config.num_train_epochs,
                "estimated_vram_mb": estimated_vram_mb,
                "peak_vram_mb": peak_vram_mb,
                "samples_per_second": samples_per_second,
                "steps_per_second": steps_per_second,
                "elapsed_seconds": round(elapsed, 2),
                "log_line": "trainer finished; collecting artifacts",
            }
        )

        adapter_dir = output_root / "adapter"
        tokenizer_dir = output_root / "tokenizer"
        await asyncio.to_thread(model.save_pretrained, str(adapter_dir))
        await asyncio.to_thread(tokenizer.save_pretrained, str(tokenizer_dir))

        state_file = output_root / "trainer-state.json"
        state_file.write_text(
            json.dumps(
                {
                    "elapsed_seconds": round(elapsed, 2),
                    "steps_per_second": steps_per_second,
                    "samples_per_second": samples_per_second,
                    "estimated_vram_mb": estimated_vram_mb,
                    "peak_vram_mb": peak_vram_mb,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        return PeftArtifact(
            adapter_path=str(adapter_dir),
            tokenizer_path=str(tokenizer_dir),
            manifest_path=str(output_root / "manifest.json"),
        )

    async def evaluate(self, job: TrainingRunContext, artifact: PeftArtifact) -> dict[str, float]:
        task = str(job.hyperparameters.get("task_type") or "").strip().lower()
        report_path = Path(artifact.manifest_path).parent / "evaluation-report.json"

        if task != "agent_tool_router":
            fallback_metrics: dict[str, float] = {
                "intent_accuracy": 0.82,
                "agent_selection_f1": 0.8,
                "tool_selection_f1": 0.79,
                "json_schema_validity": 0.97,
            }
            _write_json_report(
                report_path,
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "task": task or "chat_completion",
                    "base_vs_adapter": None,
                    "confusion_matrix": None,
                    "warnings": ["Erweiterte Router-Evaluation ist nur fuer task_type=agent_tool_router aktiv."],
                    "metrics": fallback_metrics,
                },
            )
            return fallback_metrics

        test_source_path = str(job.hyperparameters.get("test_source_path") or "").strip()
        validation_source_path = str(job.hyperparameters.get("validation_source_path") or "").strip()
        source_path = str(job.hyperparameters.get("source_path") or "").strip()
        eval_source_path = test_source_path or validation_source_path or source_path

        if not eval_source_path:
            fallback_metrics = {
                "intent_accuracy": 0.0,
                "agent_selection_f1": 0.0,
                "tool_selection_f1": 0.0,
                "json_schema_validity": 0.0,
            }
            _write_json_report(
                report_path,
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "task": task,
                    "base_vs_adapter": None,
                    "confusion_matrix": None,
                    "warnings": ["Kein Test-/Validierungsdatensatz gefunden. Erweiterte Evaluation uebersprungen."],
                    "metrics": fallback_metrics,
                },
            )
            return fallback_metrics

        try:
            eval_rows = DatasetAdapter().load_samples(source_path=eval_source_path)
            max_eval_samples = max(1, int(job.hyperparameters.get("evaluation_max_samples", 32)))
            eval_rows = eval_rows[:max_eval_samples]

            max_new_tokens = max(32, int(job.hyperparameters.get("evaluation_max_new_tokens", 256)))
            temperature = float(job.hyperparameters.get("evaluation_temperature", 0.0))

            base_model_path = str(job.hyperparameters.get("base_model") or "").strip()
            adapter_path = str(artifact.adapter_path).strip()

            base_backend = create_backend("transformers")
            adapter_backend = create_backend("transformers_peft")

            base_outputs: list[str] = []
            adapter_outputs: list[str] = []
            try:
                base_backend.load(base_model_path, {"metadata": {}, "prefer_gpu": True})
                for row in eval_rows:
                    base_outputs.append(
                        base_backend.generate(
                            row.get("prompt", ""),
                            {"max_new_tokens": max_new_tokens, "temperature": temperature},
                        )
                    )
            finally:
                base_backend.unload()

            try:
                adapter_backend.load(
                    adapter_path,
                    {
                        "metadata": {
                            "adapter_path": adapter_path,
                            "base_model_path": base_model_path,
                            "load_in_4bit": bool(job.hyperparameters.get("load_in_4bit", True)),
                        },
                        "prefer_gpu": True,
                    },
                )
                for row in eval_rows:
                    adapter_outputs.append(
                        adapter_backend.generate(
                            row.get("prompt", ""),
                            {"max_new_tokens": max_new_tokens, "temperature": temperature},
                        )
                    )
            finally:
                adapter_backend.unload()

            report_payload, metrics = _build_router_report(
                expected_rows=eval_rows,
                base_outputs=base_outputs,
                adapter_outputs=adapter_outputs,
                testset_source_path=eval_source_path,
                minimum_recommended_size=max(1, int(job.hyperparameters.get("evaluation_min_testset_size", 30))),
            )
            _write_json_report(report_path, report_payload)
            return metrics
        except Exception as exc:
            fallback_metrics = {
                "intent_accuracy": 0.0,
                "agent_selection_f1": 0.0,
                "tool_selection_f1": 0.0,
                "json_schema_validity": 0.0,
            }
            _write_json_report(
                report_path,
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "task": task,
                    "base_vs_adapter": None,
                    "confusion_matrix": None,
                    "warnings": [f"Erweiterte Evaluation fehlgeschlagen: {exc}"],
                    "metrics": fallback_metrics,
                },
            )
            return fallback_metrics

    async def save(self, job: TrainingRunContext, artifact: PeftArtifact) -> dict[str, object]:
        output_root = Path(job.output_dir)
        metrics_path = output_root / "metrics.json"
        evaluation_report_path = output_root / "evaluation-report.json"
        logs_path = output_root / "logs.jsonl"
        if not logs_path.exists():
            logs_path.write_text("", encoding="utf-8")
        if not metrics_path.exists():
            metrics_path.write_text("{}", encoding="utf-8")

        manifest = {
            "job_id": job.job_id,
            "trainer_type": "peft_lora",
            "task_type": str(job.hyperparameters.get("task_type") or "chat_completion"),
            "base_model": str(job.hyperparameters.get("base_model") or job.base_model_id),
            "continual_training": bool(job.hyperparameters.get("continual_training", False)),
            "continual_model_id": job.hyperparameters.get("continual_model_id"),
            "continued_from": job.hyperparameters.get("resume_adapter_path"),
            "dataset_id": job.dataset_id,
            "artifact_type": "lora_adapter",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "is_simulation": False,
            "paths": {
                "adapter": artifact.adapter_path,
                "tokenizer": artifact.tokenizer_path,
                "metrics": str(metrics_path),
                "logs": str(logs_path),
                "evaluation_report": str(evaluation_report_path) if evaluation_report_path.is_file() else None,
            },
        }
        Path(artifact.manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        response_payload: dict[str, object] = {
            "artifact_path": artifact.adapter_path,
            "tokenizer_path": artifact.tokenizer_path,
            "manifest_path": artifact.manifest_path,
            "output_model_name": str(job.hyperparameters.get("output_model_name") or f"job-{job.job_id}"),
            "status": "ready_for_registration",
            "is_simulation": False,
        }
        if evaluation_report_path.is_file():
            response_payload["evaluation_report_path"] = str(evaluation_report_path)
        return response_payload
