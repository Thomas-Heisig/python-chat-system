from dataclasses import dataclass


@dataclass(slots=True)
class LoRATrainingConfig:
    base_model: str
    output_name: str
    task_type: str
    learning_rate: float
    num_train_epochs: float
    per_device_train_batch_size: int
    gradient_accumulation_steps: int
    max_sequence_length: int
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    warmup_ratio: float
    weight_decay: float
    target_modules: list[str]
    load_in_4bit: bool
    eval_steps: int
    save_steps: int
    logging_steps: int
    logging_first_step: bool
    max_steps: int | None
    validation_split: float
    load_best_model_at_end: bool
    metric_for_best_model: str
    greater_is_better: bool
    resume_adapter_path: str
    seed: int

    @classmethod
    def from_hyperparameters(cls, *, base_model_id: str, job_id: str, hyperparameters: dict[str, object]) -> "LoRATrainingConfig":
        base_model = str(hyperparameters.get("base_model") or base_model_id).strip()
        if not base_model:
            raise ValueError("base_model_missing")

        output_name = str(hyperparameters.get("output_model_name") or f"job-{job_id}").strip()
        if not output_name:
            output_name = f"job-{job_id}"

        task_type = str(hyperparameters.get("task_type") or "chat_completion").strip().lower()

        return cls(
            base_model=base_model,
            output_name=output_name,
            task_type=task_type,
            learning_rate=float(hyperparameters.get("learning_rate", 0.0002)),
            num_train_epochs=float(hyperparameters.get("num_train_epochs", 3.0)),
            per_device_train_batch_size=max(1, int(hyperparameters.get("per_device_train_batch_size", 1))),
            gradient_accumulation_steps=max(1, int(hyperparameters.get("gradient_accumulation_steps", 8))),
            max_sequence_length=max(128, int(hyperparameters.get("max_sequence_length", 768))),
            lora_r=max(1, int(hyperparameters.get("lora_r", 16))),
            lora_alpha=max(1, int(hyperparameters.get("lora_alpha", 32))),
            lora_dropout=max(0.0, min(0.8, float(hyperparameters.get("lora_dropout", 0.05)))),
            warmup_ratio=max(0.0, min(0.5, float(hyperparameters.get("warmup_ratio", 0.05)))),
            weight_decay=max(0.0, min(1.0, float(hyperparameters.get("weight_decay", 0.01)))),
            target_modules=[str(item) for item in (hyperparameters.get("target_modules") or ["auto"])],
            load_in_4bit=bool(hyperparameters.get("load_in_4bit", True)),
            eval_steps=max(1, int(hyperparameters.get("eval_steps", 10))),
            save_steps=max(10, int(hyperparameters.get("save_steps", 100))),
            logging_steps=max(1, int(hyperparameters.get("logging_steps", 5))),
            logging_first_step=bool(hyperparameters.get("logging_first_step", True)),
            max_steps=(
                max(1, int(hyperparameters.get("max_steps", 0)))
                if int(hyperparameters.get("max_steps", 0) or 0) > 0
                else None
            ),
            validation_split=max(0.02, min(0.3, float(hyperparameters.get("validation_split", 0.1)))),
            load_best_model_at_end=bool(hyperparameters.get("load_best_model_at_end", True)),
            metric_for_best_model=str(hyperparameters.get("metric_for_best_model", "eval_loss")).strip() or "eval_loss",
            greater_is_better=bool(hyperparameters.get("greater_is_better", False)),
            resume_adapter_path=str(hyperparameters.get("resume_adapter_path") or "").strip(),
            seed=max(0, int(hyperparameters.get("seed", 42))),
        )
