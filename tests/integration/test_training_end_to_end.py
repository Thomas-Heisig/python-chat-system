from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
from typing import Any, Callable, Coroutine, TypeVar

from _pytest.monkeypatch import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models.model_config import ModelConfig
from app.settings.service import SettingsService

T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


def _with_session(fn: Callable[[AsyncSession], Coroutine[Any, Any, T]]) -> T:
    from app.database.session import get_session_maker

    async def _runner() -> T:
        session_maker = get_session_maker()
        async with session_maker() as session:
            return await fn(session)

    return _run(_runner())


async def _seed_models_and_settings(
    session: AsyncSession,
    *,
    root: Path,
    dataset_path: Path,
) -> tuple[ModelConfig, ModelConfig, int]:
    settings = SettingsService(session)
    await settings.update("model", "base_directories", [str(root)])
    await settings.update("training", "enabled", True)
    await settings.update("training", "default_trainer", "reference")
    await session.commit()

    transformers_dir = root / "transformers-qwen"
    transformers_dir.mkdir(parents=True, exist_ok=True)
    (transformers_dir / "config.json").write_text(json.dumps({"model_type": "qwen3"}), encoding="utf-8")
    (transformers_dir / "model.safetensors").write_text("stub", encoding="utf-8")

    gguf_file = root / "demo.gguf"
    gguf_file.write_text("stub", encoding="utf-8")

    transformers_model = ModelConfig(
        name="qwen-transformers",
        model_path=str(transformers_dir),
        backend="transformers",
        model_format="transformers_safetensors",
        model_type="text_generation",
        metadata_json=json.dumps({"task_type": "text_generation", "supports_training": True}),
        is_available=True,
        is_active=False,
        load_status="unloaded",
    )
    gguf_model = ModelConfig(
        name="demo-gguf",
        model_path=str(gguf_file),
        backend="llama_cpp",
        model_format="gguf",
        model_type="text_generation",
        metadata_json=json.dumps({"task_type": "text_generation", "supports_training": False}),
        is_available=True,
        is_active=False,
        load_status="unloaded",
    )
    session.add_all([transformers_model, gguf_model])
    await session.flush()

    from app.database.repositories.training_dataset_repository import TrainingDatasetRepository

    dataset_repo = TrainingDatasetRepository(session)
    dataset = await dataset_repo.create(
        user_id=1,
        name="tiny-e2e",
        description=None,
        project_id=None,
        source_type="manual",
        status="ready",
        version=1,
        metadata={"source_path": str(dataset_path)},
    )
    await session.commit()

    await session.refresh(transformers_model)
    await session.refresh(gguf_model)
    await session.refresh(dataset)
    return transformers_model, gguf_model, dataset.id


def test_training_end_to_end_trainer_switch_compatibility_and_peft_job(
    app_client: Any,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    root = tmp_path / "models"
    root.mkdir(parents=True, exist_ok=True)

    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "hello"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    transformers_model, gguf_model, dataset_id = _with_session(
        lambda session: _seed_models_and_settings(session, root=root, dataset_path=dataset_path)
    )

    compatibility_reference = app_client.get("/api/training/compatibility", params={"trainer_name": "reference"})
    assert compatibility_reference.status_code == 200
    reference_items = {item["model_id"]: item for item in compatibility_reference.json()["items"]}
    assert reference_items[transformers_model.id]["compatible"] is True
    assert reference_items[gguf_model.id]["compatible"] is True

    compatibility_peft = app_client.get("/api/training/compatibility", params={"trainer_name": "peft_lora"})
    assert compatibility_peft.status_code == 200
    peft_items = {item["model_id"]: item for item in compatibility_peft.json()["items"]}
    assert peft_items[transformers_model.id]["compatible"] is True
    assert peft_items[gguf_model.id]["compatible"] is False

    monkeypatch.setattr("app.training.api.routes._has_module", lambda _name: True)
    monkeypatch.setattr("app.training.api.routes._has_4bit_dependencies", lambda: True)

    original_import_module = importlib.import_module

    class _FakeAutoTokenizer:
        @staticmethod
        def from_pretrained(*_args: object, **_kwargs: object) -> object:
            return object()

    class _FakeConfig:
        model_type = "qwen3"
        auto_map: dict[str, str] = {}

    class _FakeAutoConfig:
        @staticmethod
        def from_pretrained(*_args: object, **_kwargs: object) -> _FakeConfig:
            return _FakeConfig()

    class _FakeMapping:
        _model_mapping = {"qwen3": object()}

    class _FakeAutoModelForCausalLM:
        _model_mapping = _FakeMapping()

    class _FakeTransformersModule:
        AutoTokenizer = _FakeAutoTokenizer
        AutoConfig = _FakeAutoConfig
        AutoModelForCausalLM = _FakeAutoModelForCausalLM

    def _fake_import_module(name: str, package: str | None = None) -> Any:
        if name == "transformers":
            return _FakeTransformersModule
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module)

    preflight = app_client.post(
        "/api/training/preflight",
        json={
            "user_id": 1,
            "dataset_id": dataset_id,
            "base_model_id": transformers_model.name,
            "trainer_name": "peft_lora",
            "hyperparameters": {
                "load_in_4bit": False,
                "allow_cpu_training": True,
            },
        },
    )
    assert preflight.status_code == 200
    assert preflight.json()["ready"] is True

    submit = app_client.post(
        "/api/training/jobs",
        json={
            "user_id": 1,
            "dataset_id": dataset_id,
            "base_model_id": transformers_model.name,
            "trainer_name": "peft_lora",
            "hyperparameters": {
                "load_in_4bit": False,
                "allow_cpu_training": True,
            },
        },
    )
    assert submit.status_code == 200
    payload = submit.json()
    assert payload["trainer_name"] == "peft_lora"
    assert payload["status"] in {"queued", "preparing", "running"}
