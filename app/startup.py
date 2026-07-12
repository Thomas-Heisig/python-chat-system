from datetime import datetime, timezone
from importlib import import_module
import json
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import Base
from app.database.connection import get_engine
from app.database.session import get_session_maker
from app.db_models.model_config import ModelConfig
from app.database.repositories.user_repository import UserRepository
from app.models.manager import model_manager
from app.models.path_security import normalize_base_directories, validate_runtime_model_paths
from app.models.registry import ModelRegistry
from app.models.scanner import ModelScanner
from app.settings.seed import seed_default_settings
from app.settings.service import SettingsService


def _parse_metadata(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    if isinstance(parsed, dict):
        return cast(dict[str, object], parsed)
    return {}


async def initialize_runtime(run_model_scan: bool = True) -> dict[str, int]:
    import_module("app.db_models")

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = get_session_maker()
    async with session_maker() as session:
        await seed_default_settings(session)
        await UserRepository(session).ensure_default_user(user_id=1)
        scan_stats = {"discovered": 0, "inserted": 0, "updated": 0}

        if run_model_scan:
            scan_stats = await _scan_and_sync_models(session)

        await _restore_last_active_model(session)

        await session.commit()
        return scan_stats


async def _scan_and_sync_models(session: AsyncSession) -> dict[str, int]:
    scanner = ModelScanner()
    registry = ModelRegistry()
    settings = SettingsService(session)
    directories_value = await settings.get("model", "base_directories")
    directories = normalize_base_directories(directories_value)
    discovered = scanner.scan_directories(directories)

    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for item in discovered:
        valid, _reason = registry.validate_entry(item, allowed_base_directories=directories)
        if not valid:
            continue

        stmt = select(ModelConfig).where(ModelConfig.model_path == item["model_path"]).limit(1)
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing is None:
            session.add(
                ModelConfig(
                    name=item["name"],
                    model_path=item["model_path"],
                    backend=item["backend"],
                    model_format=item.get("model_format"),
                    is_available=True,
                    load_status="unloaded",
                    last_scanned_at=now,
                )
            )
            inserted += 1
        else:
            existing.name = item["name"]
            existing.backend = item["backend"]
            existing.model_format = item.get("model_format")
            existing.is_available = True
            existing.last_scanned_at = now
            updated += 1

    return {"discovered": len(discovered), "inserted": inserted, "updated": updated}


async def _restore_last_active_model(session: AsyncSession) -> None:
    settings = SettingsService(session)
    directories_raw = await settings.get("model", "base_directories")
    directories = normalize_base_directories(directories_raw)

    active_model_id_raw = await settings.get("model", "active_model_id")
    requested_active_model_id = int(active_model_id_raw) if isinstance(active_model_id_raw, int) and active_model_id_raw > 0 else None

    model: ModelConfig | None = None
    if requested_active_model_id is not None:
        model = (
            await session.execute(
                select(ModelConfig)
                .where(ModelConfig.id == requested_active_model_id)
                .where(ModelConfig.is_available.is_(True))
                .limit(1)
            )
        ).scalar_one_or_none()

    if model is None:
        stmt = (
            select(ModelConfig)
            .where(ModelConfig.is_active.is_(True))
            .where(ModelConfig.is_available.is_(True))
            .limit(1)
        )
        model = (await session.execute(stmt)).scalar_one_or_none()

    if model is None:
        return

    metadata = _parse_metadata(model.metadata_json)
    path_valid, _path_reason = validate_runtime_model_paths(
        model_path=model.model_path,
        model_format=str(metadata.get("model_format") or model.model_format or ""),
        metadata=metadata,
        allowed_base_directories=directories,
    )
    if not path_valid:
        model.is_active = False
        model.load_status = "error"
        model.last_error = "invalid_model_path"
        await settings.update("model", "active_model_id", None)
        return

    try:
        await model_manager.load_model(
            model_id=model.id,
            model_path=model.model_path,
            backend_name=model.backend,
            config={"metadata": metadata},
        )
        model.is_active = True
        model.load_status = "ready"
        model.last_error = None
        await settings.update("model", "active_model_id", model.id)
    except Exception:
        model.is_active = False
        model.load_status = "error"
        await settings.update("model", "active_model_id", None)
