from pydantic import BaseModel


class ModelScanResult(BaseModel):
    discovered: int
    models: list[dict[str, str]]


class ModelSwitchRequest(BaseModel):
    model_id: int


class ModelStatus(BaseModel):
    active_model_id: int | None
    loaded: bool
    backend: str | None
