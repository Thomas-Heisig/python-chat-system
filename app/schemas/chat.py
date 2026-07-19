from typing import Literal

from pydantic import BaseModel, Field


class ChatImageInput(BaseModel):
    name: str | None = None
    mime_type: str | None = None
    data_base64: str


class ChatRequest(BaseModel):
    user_id: int = Field(default=1)
    team_id: int | None = None
    conversation_id: int | None = None
    message: str
    images: list[ChatImageInput] = Field(default_factory=lambda: [])
    stream: bool = True
    idempotency_key: str | None = None
    document_scope: Literal["user", "team", "shared"] = "user"
    model_id: int | None = None
    temperature: float | None = None
    max_new_tokens: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    message: str
    model_id: int | None = None
