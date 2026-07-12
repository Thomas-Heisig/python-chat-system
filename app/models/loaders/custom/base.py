from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CustomModelDetection:
    loader_id: str
    model_format: str
    task_type: str
    model_family: str
    backend: str
    custom_code_available: bool
    custom_code_entrypoint: str | None


class CustomModelLoaderPlugin:
    loader_id: str
    display_name: str
    supported_formats: set[str]
    supported_tasks: set[str]

    def detect(self, *, name: str, model_path: Path) -> CustomModelDetection | None:
        raise NotImplementedError

    def runtime_available(self) -> tuple[bool, str | None]:
        raise NotImplementedError
