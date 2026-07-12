from dataclasses import dataclass
from enum import StrEnum


class TrainingJobStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class TrainingJobRecord:
    job_id: str
    dataset_id: str
    base_model_id: str
    status: TrainingJobStatus
