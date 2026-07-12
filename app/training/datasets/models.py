from dataclasses import dataclass


@dataclass(slots=True)
class DatasetRecord:
    dataset_id: str
    name: str
    version: int
    sample_count: int
