from dataclasses import dataclass


@dataclass(slots=True)
class TrainingModelRegistryEntry:
    model_id: str
    source_job_id: str
    artifact_path: str
