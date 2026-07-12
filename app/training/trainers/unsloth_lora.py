from app.training.trainers.base import TrainingBackend, TrainingRunContext


class UnslothLoRATrainer(TrainingBackend):
    name = "unsloth_lora"
    is_simulation = False

    async def prepare(self, job: TrainingRunContext, dataset: dict[str, object]) -> object:
        del job, dataset
        raise RuntimeError("unsloth_not_implemented")

    async def train(self, job: TrainingRunContext, dataset: dict[str, object], progress_callback, cancel_token) -> object:
        del job, dataset, progress_callback, cancel_token
        raise RuntimeError("unsloth_not_implemented")

    async def evaluate(self, job: TrainingRunContext, artifact: object) -> dict[str, float]:
        del job, artifact
        raise RuntimeError("unsloth_not_implemented")

    async def save(self, job: TrainingRunContext, artifact: object) -> dict[str, object]:
        del job, artifact
        raise RuntimeError("unsloth_not_implemented")
