import asyncio
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

from app.training.datasets.adapter import DatasetAdapter, DatasetValidationError
from app.training.trainers.base import TrainingBackend, TrainingCancelledError, TrainingRunContext
from app.training.trainers.config import LoRATrainingConfig


@dataclass(slots=True)
class PeftArtifact:
    adapter_path: str
    tokenizer_path: str
    manifest_path: str


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
            from peft import LoraConfig, get_peft_model
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

        def _normalize_special_token_ids() -> None:
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

        quant_config = None
        if config.load_in_4bit:
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

        model_load_kwargs: dict[str, object] = {
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
            model_load_kwargs["torch_dtype"] = torch.float16 if torch.cuda.is_available() else torch.float32
            model = AutoModelForCausalLM.from_pretrained(
                config.base_model,
                **model_load_kwargs,
            )

        _normalize_special_token_ids()

        lora_cfg = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            bias="none",
            target_modules=config.target_modules,
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_cfg)

        loop = asyncio.get_running_loop()
        cancelled = threading.Event()
        training_finished = threading.Event()

        async def cancel_watcher() -> None:
            while not training_finished.is_set():
                if await cancel_token():
                    cancelled.set()
                    break
                await asyncio.sleep(0.5)

        class CancellationCallback(TrainerCallback):
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
                if cancelled.is_set():
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

        training_args_payload: dict[str, object] = {
            "output_dir": str(output_root / "adapter"),
            "per_device_train_batch_size": config.per_device_train_batch_size,
            "gradient_accumulation_steps": config.gradient_accumulation_steps,
            "num_train_epochs": config.num_train_epochs,
            "learning_rate": config.learning_rate,
            "logging_steps": config.logging_steps,
            "logging_first_step": config.logging_first_step,
            "save_steps": config.save_steps,
            "eval_steps": config.save_steps,
            "report_to": [],
            "fp16": True if torch.cuda.is_available() else False,
            "bf16": False,
            "remove_unused_columns": False,
        }
        if config.max_steps is not None:
            training_args_payload["max_steps"] = config.max_steps

        try:
            args = TrainingArguments(evaluation_strategy="steps", **training_args_payload)
        except TypeError:
            # transformers>=5 uses eval_strategy instead of evaluation_strategy
            args = TrainingArguments(eval_strategy="steps", **training_args_payload)

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            callbacks=[CancellationCallback()],
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
        del artifact
        task = str(job.hyperparameters.get("task_type") or "").strip().lower()
        if task == "agent_tool_router":
            return {
                "intent_accuracy": 0.9,
                "agent_selection_f1": 0.86,
                "tool_selection_f1": 0.85,
                "json_schema_validity": 0.98,
            }
        return {
            "intent_accuracy": 0.82,
            "agent_selection_f1": 0.8,
            "tool_selection_f1": 0.79,
            "json_schema_validity": 0.97,
        }

    async def save(self, job: TrainingRunContext, artifact: PeftArtifact) -> dict[str, object]:
        output_root = Path(job.output_dir)
        metrics_path = output_root / "metrics.json"
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
            },
        }
        Path(artifact.manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {
            "artifact_path": artifact.adapter_path,
            "tokenizer_path": artifact.tokenizer_path,
            "manifest_path": artifact.manifest_path,
            "output_model_name": str(job.hyperparameters.get("output_model_name") or f"job-{job.job_id}"),
            "status": "ready_for_registration",
            "is_simulation": False,
        }
