from datetime import datetime

from pydantic import BaseModel


class ConversationItem(BaseModel):
	id: int
	title: str
	updated_at: datetime
	last_message: str | None = None
	owner_user_id: int
	owner_username: str
	project_id: int | None = None


class ConversationListResponse(BaseModel):
	items: list[ConversationItem]


class CreateConversationRequest(BaseModel):
	user_id: int = 1
	title: str | None = None
	project_id: int | None = None


class CreateConversationResponse(BaseModel):
	id: int
	title: str
	updated_at: datetime
	owner_user_id: int
	owner_username: str
	project_id: int | None = None


class UpdateConversationRequest(BaseModel):
	user_id: int = 1
	title: str | None = None


class UpdateConversationResponse(BaseModel):
	updated: bool
	id: int
	title: str
	updated_at: datetime


class ConversationGenerationParams(BaseModel):
	system_prompt: str
	temperature: float
	top_k: int
	top_p: float
	repetition_penalty: float
	stop_sequences: list[str]
	seed: int
	do_sample: bool
	max_new_tokens: int
	retrieval_top_k: int


class ConversationGenerationProfileVersion(BaseModel):
	id: str
	name: str
	created_at: datetime
	created_by_user_id: int
	params: ConversationGenerationParams


class ConversationGenerationProfileHistoryEvent(BaseModel):
	id: str
	action: str
	version_id: str
	created_at: datetime
	user_id: int


class ConversationGenerationProfilesResponse(BaseModel):
	conversation_id: int
	active_version_id: str | None
	versions: list[ConversationGenerationProfileVersion]
	history: list[ConversationGenerationProfileHistoryEvent]


class CreateConversationGenerationProfileRequest(BaseModel):
	user_id: int = 1
	name: str | None = None
	params: ConversationGenerationParams
	activate: bool = True


class ActivateConversationGenerationProfileRequest(BaseModel):
	user_id: int = 1


class UpdateConversationProjectRequest(BaseModel):
	user_id: int = 1
	project_id: int | None = None
