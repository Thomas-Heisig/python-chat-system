from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Coroutine, TypeVar, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models.model_config import ModelConfig
from app.models.metadata import infer_model_capabilities
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


async def _seed_custom_model(session: AsyncSession, model_dir: Path) -> int:
    settings = SettingsService(session)
    await settings.update("model", "base_directories", [str(model_dir.parent)])
    await session.commit()

    capabilities = infer_model_capabilities(name=model_dir.name, model_path=model_dir)
    model = ModelConfig(
        name=model_dir.name,
        model_path=str(model_dir.resolve(strict=False)),
        backend=str(capabilities.get("backend") or "custom_pytorch"),
        model_format=str(capabilities.get("model_format") or "custom_safetensors"),
        model_type=str(capabilities.get("task_type") or "any_to_any"),
        metadata_json=json.dumps(capabilities),
        is_available=True,
        is_active=False,
        load_status="unloaded",
    )
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model.id


async def _read_model_metadata(session: AsyncSession, model_id: int) -> dict[str, object]:
    row = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one()
    if not row.metadata_json:
        return {}
    payload = json.loads(row.metadata_json)
    if not isinstance(payload, dict):
        return {}
    return cast(dict[str, object], payload)


async def _seed_legacy_duplicate_models(session: AsyncSession, model_dir: Path) -> tuple[int, int]:
    settings = SettingsService(session)
    await settings.update("model", "base_directories", [str(model_dir.parent)])
    await session.commit()

    capabilities = dict(infer_model_capabilities(name=model_dir.name, model_path=model_dir))

    legacy_metadata = dict(capabilities)
    legacy_metadata["custom_code_trusted"] = True

    canonical_metadata = dict(capabilities)
    canonical_metadata["custom_code_trusted"] = False

    legacy_row = ModelConfig(
        name=model_dir.name,
        model_path=str((model_dir / "model.safetensors").resolve(strict=False)),
        backend=str(capabilities.get("backend") or "custom_pytorch"),
        model_format=str(capabilities.get("model_format") or "custom_safetensors"),
        model_type=str(capabilities.get("task_type") or "any_to_any"),
        metadata_json=json.dumps(legacy_metadata),
        is_available=True,
        is_active=False,
        load_status="unloaded",
    )

    canonical_row = ModelConfig(
        name=model_dir.name,
        model_path=str(model_dir.resolve(strict=False)),
        backend=str(capabilities.get("backend") or "custom_pytorch"),
        model_format=str(capabilities.get("model_format") or "custom_safetensors"),
        model_type=str(capabilities.get("task_type") or "any_to_any"),
        metadata_json=json.dumps(canonical_metadata),
        is_available=True,
        is_active=False,
        load_status="unloaded",
    )

    session.add(legacy_row)
    session.add(canonical_row)
    await session.commit()
    await session.refresh(legacy_row)
    await session.refresh(canonical_row)
    return legacy_row.id, canonical_row.id


async def _list_models_by_name(session: AsyncSession, name: str) -> list[ModelConfig]:
    return list((await session.execute(select(ModelConfig).where(ModelConfig.name == name).order_by(ModelConfig.id.asc()))).scalars().all())


def test_custom_loader_trust_and_peft_compatibility(app_client: Any, tmp_path: Path) -> None:
    model_dir = tmp_path / "Supra-A2A-Nano-Exp"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "model.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "vqvae.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (model_dir / "modeling_supra.py").write_text(
        "def load_model(model_path, config):\n"
        "    return {'model_path': model_path, 'loaded': True}\n\n"
        "def generate(runtime, prompt, config):\n"
        "    return f'custom:{prompt}'\n\n"
        "def stream(runtime, prompt, config):\n"
        "    yield 'custom:'\n"
        "    yield prompt\n\n"
        "def health_check(runtime):\n"
        "    return bool(runtime.get('loaded'))\n",
        encoding="utf-8",
    )

    model_id = _with_session(lambda session: _seed_custom_model(session, model_dir))

    models_response = app_client.get("/api/models")
    assert models_response.status_code == 200
    items = models_response.json()["items"]
    current = next(item for item in items if item["id"] == model_id)
    assert current["model_format"] == "custom_safetensors"
    assert current["task_type"] == "any_to_any"
    assert current["requires_custom_code"] is True
    assert current["custom_code_trusted"] is False
    assert "vertrauenswuerdig" in (current["reason_unavailable"] or "")

    compatibility = app_client.get("/api/training/compatibility", params={"trainer_name": "peft_lora"})
    assert compatibility.status_code == 200
    compatibility_items = compatibility.json()["items"]
    compatibility_current = next(item for item in compatibility_items if item["model_id"] == model_id)
    assert compatibility_current["compatible"] is False
    assert "Nicht mit PEFT-LoRA kompatibel" in (compatibility_current["reason"] or "")

    trust_response = app_client.post(f"/api/models/{model_id}/trust-custom-code", json={"trusted": True})
    assert trust_response.status_code == 200
    assert trust_response.json()["custom_code_trusted"] is True

    scan_response = app_client.post("/api/models/scan")
    assert scan_response.status_code == 200

    models_after_scan = app_client.get("/api/models")
    assert models_after_scan.status_code == 200
    after_scan_items = models_after_scan.json()["items"]
    current_after_scan = next(item for item in after_scan_items if item["id"] == model_id)
    assert current_after_scan["custom_code_trusted"] is True

    activation_response = app_client.post(f"/api/models/{model_id}/activate")
    assert activation_response.status_code == 200
    assert activation_response.json()["active_model_id"] == model_id

    metadata = _with_session(lambda session: _read_model_metadata(session, model_id))
    assert metadata.get("custom_code_trusted") is True


def test_scan_cleans_up_legacy_file_vs_directory_rows(app_client: Any, tmp_path: Path) -> None:
    model_dir = tmp_path / "Supra-A2A-Nano-Exp"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "model.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "vqvae.safetensors").write_text("stub", encoding="utf-8")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    (model_dir / "modeling_supra.py").write_text("def load_model(model_path, config):\n    return {'loaded': True}\n", encoding="utf-8")

    legacy_id, canonical_id = _with_session(lambda session: _seed_legacy_duplicate_models(session, model_dir))
    assert legacy_id != canonical_id

    scan_response = app_client.post("/api/models/scan")
    assert scan_response.status_code == 200

    rows = _with_session(lambda session: _list_models_by_name(session, model_dir.name))
    related_rows: list[ModelConfig] = []
    for row in rows:
        row_path = Path(row.model_path).resolve(strict=False)
        canonical_row_path = row_path.parent if row_path.suffix else row_path
        if canonical_row_path == model_dir.resolve(strict=False):
            related_rows.append(row)

    assert len(related_rows) == 1

    remaining = related_rows[0]
    assert remaining.id == canonical_id
    assert Path(remaining.model_path).resolve(strict=False) == model_dir.resolve(strict=False)

    metadata_raw: object = json.loads(remaining.metadata_json) if remaining.metadata_json else {}
    metadata: dict[str, object] = cast(dict[str, object], metadata_raw) if isinstance(metadata_raw, dict) else {}
    assert metadata.get("custom_code_trusted") is True
