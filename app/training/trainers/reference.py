import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

from app.training.trainers.base import TrainingBackend, TrainingCancelledError, TrainingRunContext


@dataclass(slots=True)
class TrainingArtifact:
    artifact_path: str


class ReferenceTrainer(TrainingBackend):
    name = "reference"
    is_simulation = True

    async def prepare(self, job: TrainingRunContext, dataset: dict[str, object]) -> TrainingArtifact:
        del dataset
        output_path = Path(job.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return TrainingArtifact(artifact_path=str(output_path))

    async def train(
        self,
        job: TrainingRunContext,
        dataset: dict[str, object],
        progress_callback: Callable[[dict[str, object]], Awaitable[None]],
        cancel_token: Callable[[], Awaitable[bool]],
    ) -> TrainingArtifact:
        del dataset
        total_steps = int(job.hyperparameters.get("max_steps", 20))
        if total_steps < 1:
            total_steps = 20

        for step in range(1, total_steps + 1):
            if await cancel_token():
                raise TrainingCancelledError()
            progress = round((step / total_steps) * 100, 2)
            epoch = round((step / total_steps) * float(job.hyperparameters.get("num_train_epochs", 2.0)), 3)
            await progress_callback(
                {
                    "progress": progress,
                    "current_step": step,
                    "total_steps": total_steps,
                    "current_epoch": epoch,
                    "loss": round(1.2 / (1 + (step / 10)), 4),
                    "learning_rate": float(job.hyperparameters.get("learning_rate", 0.0002)),
                    "log_line": f"reference step {step}/{total_steps}",
                }
            )
            await asyncio.sleep(0.25)

        return TrainingArtifact(artifact_path=str(Path(job.output_dir)))

    async def evaluate(self, job: TrainingRunContext, artifact: TrainingArtifact) -> dict[str, float]:
        del artifact
        base = 0.82
        if str(job.hyperparameters.get("task_type", "")).strip().lower() == "agent_tool_router":
            base = 0.87
        return {
            "intent_accuracy": round(base + 0.05, 3),
            "agent_selection_f1": round(base, 3),
            "tool_selection_f1": round(base - 0.01, 3),
            "json_schema_validity": 0.99,
        }

    async def save(self, job: TrainingRunContext, artifact: TrainingArtifact) -> dict[str, object]:
        model_name = str(job.hyperparameters.get("output_model_name") or f"training-job-{job.job_id}")
        return {
            "artifact_path": artifact.artifact_path,
            "output_model_name": model_name,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "status": "ready_for_registration",
            "is_simulation": True,
        }
