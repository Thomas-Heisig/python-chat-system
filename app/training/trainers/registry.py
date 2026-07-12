from app.training.trainers.base import TrainingBackend
from app.training.trainers.peft_lora import PeftLoRATrainer
from app.training.trainers.reference import ReferenceTrainer
from app.training.trainers.unsloth_lora import UnslothLoRATrainer


class TrainerRegistry:
    def __init__(self) -> None:
        reference = ReferenceTrainer()
        peft = PeftLoRATrainer()
        self._trainers: dict[str, TrainingBackend] = {
            "reference": reference,
            "peft_lora": peft,
            "unsloth_lora": UnslothLoRATrainer(),
            # Backward-compatible aliases for earlier jobs/settings.
            "lora": reference,
            "qlora": peft,
            "unsloth": reference,
        }

    def resolve(self, trainer_name: str) -> TrainingBackend:
        normalized = trainer_name.strip().lower()
        if normalized in self._trainers:
            return self._trainers[normalized]
        return self._trainers["reference"]

    def summaries(self) -> dict[str, dict[str, object]]:
        return {
            name: {
                "name": trainer.name,
                "is_simulation": trainer.is_simulation,
            }
            for name, trainer in self._trainers.items()
        }
