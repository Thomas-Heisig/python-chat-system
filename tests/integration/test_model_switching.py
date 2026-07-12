from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Sequence, TypeVar, cast

from _pytest.monkeypatch import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models.model_config import ModelConfig
from app.settings.service import SettingsService
from tests.integration.async_utils import run_async

T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
	return run_async(coro)


def _with_session(fn: Callable[[AsyncSession], Coroutine[Any, Any, T]]) -> T:
	from app.database.session import get_session_maker

	async def _runner() -> T:
		session_maker = get_session_maker()
		async with session_maker() as session:
			return await fn(session)

	return _run(_runner())


async def _create_model(session: AsyncSession, *, name: str, model_path: Path, is_active: bool = False) -> ModelConfig:
	model = ModelConfig(
		name=name,
		model_path=str(model_path.resolve(strict=False)),
		backend="llama_cpp",
		model_format="gguf",
		is_available=True,
		is_active=is_active,
		load_status="ready" if is_active else "unloaded",
		last_scanned_at=datetime.now(timezone.utc),
	)
	session.add(model)
	await session.commit()
	await session.refresh(model)
	return model


def test_activate_model_rejects_path_outside_allowed_base_directories(app_client: Any, tmp_path: Path):
	allowed_dir = tmp_path / "allowed"
	disallowed_dir = tmp_path / "disallowed"
	allowed_dir.mkdir(parents=True, exist_ok=True)
	disallowed_dir.mkdir(parents=True, exist_ok=True)
	disallowed_model = disallowed_dir / "blocked.gguf"
	disallowed_model.write_text("dummy", encoding="utf-8")

	async def _prepare(session: AsyncSession) -> ModelConfig:
		settings = SettingsService(session)
		await settings.update("model", "base_directories", [str(allowed_dir)])
		await session.commit()
		return await _create_model(session, name="blocked", model_path=disallowed_model)

	model = _with_session(_prepare)

	response = app_client.post(f"/api/models/{model.id}/activate")
	assert response.status_code == 400

	body = response.json()
	assert body["error"]["code"] == "model.invalid_path"
	assert body["error"]["details"]["reason"] == "outside_allowed_base_directories"


def test_model_switch_failure_rolls_back_to_previous_active_model(app_client: Any, tmp_path: Path, monkeypatch: MonkeyPatch):
	allowed_dir = tmp_path / "allowed"
	allowed_dir.mkdir(parents=True, exist_ok=True)
	previous_model_path = allowed_dir / "previous.gguf"
	target_model_path = allowed_dir / "target.gguf"
	previous_model_path.write_text("dummy", encoding="utf-8")
	target_model_path.write_text("dummy", encoding="utf-8")

	async def _prepare(session: AsyncSession) -> tuple[ModelConfig, ModelConfig]:
		settings = SettingsService(session)
		await settings.update("model", "base_directories", [str(allowed_dir)])
		await session.commit()
		previous_model = await _create_model(session, name="previous", model_path=previous_model_path, is_active=True)
		target_model = await _create_model(session, name="target", model_path=target_model_path)
		return previous_model, target_model

	previous_model, target_model = _with_session(_prepare)

	from app.models.manager import model_manager

	class _HealthyBackend:
		def health_check(self) -> bool:
			return True

		def unload(self) -> None:
			return None

	async def _fake_load_model(*, model_id: int, model_path: str, backend_name: str, config: dict[str, Any]) -> None:
		if model_id == target_model.id:
			raise RuntimeError("switch_failed")
		if model_id == previous_model.id:
			model_manager.active_model_id = previous_model.id
			model_manager.active_backend = cast(Any, _HealthyBackend())
			model_manager.active_backend_name = "llama_cpp"
			return
		raise RuntimeError("unexpected_model")

	model_manager.active_model_id = previous_model.id
	model_manager.active_backend = cast(Any, _HealthyBackend())
	model_manager.active_backend_name = "llama_cpp"
	monkeypatch.setattr(model_manager, "load_model", _fake_load_model)

	response = app_client.post(f"/api/models/{target_model.id}/activate")
	assert response.status_code == 409
	body = response.json()
	assert body["error"]["code"] in {"conflict", "http_409"}
	assert "rolled back" in body["error"]["message"].lower()

	async def _load_rows(session: AsyncSession) -> Sequence[ModelConfig]:
		result = await session.execute(select(ModelConfig).order_by(ModelConfig.id.asc()))
		return result.scalars().all()

	rows = _with_session(_load_rows)
	state_by_id = {row.id: row for row in rows}

	assert state_by_id[previous_model.id].is_active is True
	assert state_by_id[previous_model.id].load_status == "ready"
	assert state_by_id[target_model.id].is_active is False
	assert state_by_id[target_model.id].load_status == "error"

