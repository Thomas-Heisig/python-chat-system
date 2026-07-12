from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import db_session_dependency
from app.schemas.setting import SettingUpdateRequest
from app.settings.service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("")
async def update_setting(payload: SettingUpdateRequest, session: AsyncSession = Depends(db_session_dependency)) -> dict:
    service = SettingsService(session)
    effect = await service.update(
        category=payload.category,
        key=payload.key,
        value=payload.value,
        user_id=payload.user_id,
        team_id=payload.team_id,
    )
    await session.commit()
    return {"updated": True, "effect": effect}


@router.get("/{category}/{key}")
async def get_setting(
    category: str,
    key: str,
    user_id: int | None = None,
    team_id: int | None = None,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict:
    service = SettingsService(session)
    value = await service.get(category=category, key=key, user_id=user_id, team_id=team_id)
    return {"category": category, "key": key, "value": value}
