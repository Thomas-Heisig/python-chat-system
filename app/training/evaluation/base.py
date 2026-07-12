from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class EvaluationReport:
    score: float
    passed: bool


class Evaluator(Protocol):
    name: str

    async def evaluate(self, model_artifact_path: str) -> EvaluationReport:
        ...
