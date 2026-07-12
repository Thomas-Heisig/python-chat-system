from pydantic import BaseModel
from typing import Any


class SettingUpdateRequest(BaseModel):
    category: str
    key: str
    value: Any
    user_id: int | None = None
    team_id: int | None = None


class SettingUpdateResponse(BaseModel):
    updated: bool
    effect: str
