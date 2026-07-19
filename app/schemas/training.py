from datetime import datetime
from typing import Literal, cast
from pydantic import BaseModel, Field


class TrainingDatasetItem(BaseModel):
    id: int
    name: str
    description: str | None
    source_type: str
    status: str
    version: int
    project_id: int | None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, object]


class TrainingDatasetListResponse(BaseModel):
    items: list[TrainingDatasetItem]


class TrainingDatasetFileItem(BaseModel):
    relative_path: str
    size_bytes: int
    modified_at: datetime


class DatasetFileReference(BaseModel):
    role: Literal["source", "training", "validation", "test", "manifest", "canonical"]
    file_name: str


class TrainingDatasetFileListResponse(BaseModel):
    items: list[TrainingDatasetFileItem]


class CreateTrainingDatasetRequest(BaseModel):
    user_id: int = 1
    name: str
    description: str | None = None
    project_id: int | None = None
    source_type: str = "manual"
    status: str = "imported"
    version: int = 1
    metadata: dict[str, object] = Field(default_factory=dict)


class RegisterTrainingDatasetFileRequest(BaseModel):
    user_id: int = 1
    name: str
    file_name: str = ""
    validation_file_name: str | None = None
    test_file_name: str | None = None
    files: list[DatasetFileReference] = Field(default_factory=lambda: cast(list[DatasetFileReference], []))
    description: str | None = None
    project_id: int | None = None
    source_type: str = "local_file"
    status: str = "imported"
    version: int = 1
    metadata: dict[str, object] = Field(default_factory=dict)


class ImportTrainingDatasetUrlRequest(BaseModel):
    user_id: int = 1
    name: str
    source_url: str
    validation_source_url: str | None = None
    test_source_url: str | None = None
    description: str | None = None
    project_id: int | None = None
    source_type: str = "url"
    status: str = "imported"
    version: int = 1
    metadata: dict[str, object] = Field(default_factory=dict)


class TrainingJobItem(BaseModel):
    id: int
    dataset_id: int
    base_model_id: str
    trainer_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    hyperparameters: dict[str, object]
    result: dict[str, object] | None
    error_message: str | None
    progress: float | None = None
    current_step: int | None = None
    total_steps: int | None = None
    current_epoch: float | None = None
    loss: float | None = None
    learning_rate: float | None = None
    logs: list[str] = Field(default_factory=list)
    is_simulation: bool | None = None
    estimated_vram_mb: float | None = None
    peak_vram_mb: float | None = None
    samples_per_second: float | None = None
    steps_per_second: float | None = None
    elapsed_seconds: float | None = None


class TrainingJobListResponse(BaseModel):
    items: list[TrainingJobItem]


class CreateTrainingJobRequest(BaseModel):
    user_id: int = 1
    dataset_id: int
    base_model_id: str | None = None
    trainer_name: str | None = None
    run_profile: Literal["A", "B", "C"] | None = None
    run_label: str | None = None
    hyperparameters: dict[str, object] = Field(default_factory=dict)


class BatchTrainingFolderRequest(BaseModel):
    user_id: int = 1
    base_model_id: str | None = None
    trainer_name: str | None = None
    project_id: int | None = None
    new_cycle: bool = False
    hyperparameters: dict[str, object] = Field(default_factory=dict)


class AssignTrainingProjectRequest(BaseModel):
    user_id: int = 1
    project_id: int | None = None
    dataset_ids: list[int] = Field(default_factory=lambda: cast(list[int], []))
    include_archived: bool = True


class TrainingPreflightResponse(BaseModel):
    ready: bool
    model_id: int | None = None
    model_name: str | None = None
    model_format: str | None = None
    trainer: str
    target_modules_mode: str = "auto"
    resolved_target_modules: list[str] = Field(default_factory=list)
    target_modules_source: str = "fallback"
    cuda_available: bool
    supports_4bit: bool
    dataset_valid: bool
    warnings: object = Field(default_factory=list)
    errors: object = Field(default_factory=list)


class TrainingPreflightRequest(BaseModel):
    user_id: int = 1
    dataset_id: int
    base_model_id: str | None = None
    trainer_name: str | None = None
    run_profile: Literal["A", "B", "C"] | None = None
    run_label: str | None = None
    hyperparameters: dict[str, object] = Field(default_factory=dict)


class TrainingAdapterRegisterResponse(BaseModel):
    registered: bool
    model_id: int
    name: str
    model_type: str
    base_model_id: int
    adapter_path: str


class TrainingAdapterCompareRequest(BaseModel):
    user_id: int = 1
    prompt: str
    max_new_tokens: int = 256
    temperature: float = 0.2


class TrainingAdapterCompareResponse(BaseModel):
    job_id: int
    base_model_name: str
    adapter_model_name: str
    prompt: str
    base_response: str
    adapter_response: str
    base_response_cleaned: str
    adapter_response_cleaned: str
    evaluation: dict[str, object] = Field(default_factory=dict)
