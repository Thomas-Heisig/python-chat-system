from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol


class TrainingCancelledError(Exception):
    pass


@dataclass(slots=True)
class TrainingRunContext:
    job_id: str
    dataset_id: str
    base_model_id: str
    output_dir: str
    hyperparameters: dict[str, Any]


class TrainingBackend(Protocol):
    name: str
    is_simulation: bool

    async def prepare(self, job: TrainingRunContext, dataset: dict[str, object]) -> object:
        ...

    async def train(
        self,
        job: TrainingRunContext,
        dataset: dict[str, object],
        progress_callback: Callable[[dict[str, object]], Awaitable[None]],
        cancel_token: Callable[[], Awaitable[bool]],
    ) -> object:
        ...

    async def evaluate(self, job: TrainingRunContext, artifact: object) -> dict[str, float]:
        ...

    async def save(self, job: TrainingRunContext, artifact: object) -> dict[str, object]:
        ...
