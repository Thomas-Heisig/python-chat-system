from datetime import datetime

from pydantic import BaseModel


class MessageItem(BaseModel):
	id: int
	conversation_id: int
	role: str
	content: str
	created_at: datetime
	author_username: str | None = None


class MessageListResponse(BaseModel):
	items: list[MessageItem]


class SendMessageRequest(BaseModel):
	user_id: int = 1
	conversation_id: int | None = None
	message: str
	idempotency_key: str | None = None
	model_id: int | None = None
	temperature: float | None = None
	max_new_tokens: int | None = None


class SendMessageResponse(BaseModel):
	conversation_id: int
	user_message_id: int
	assistant_message_id: int
	message: str
	model_id: int | None = None


class PostUserMessageRequest(BaseModel):
	user_id: int = 1
	conversation_id: int | None = None
	message: str


class PostUserMessageResponse(BaseModel):
	conversation_id: int
	message_id: int
