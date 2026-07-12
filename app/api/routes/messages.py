from fastapi import APIRouter, Depends, HTTPException
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import chat_service_dependency, db_session_dependency
from app.chat.service import ChatService
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.user_repository import UserRepository
from app.settings.service import SettingsService
from app.schemas.chat import ChatRequest
from app.schemas.message import (
	MessageItem,
	MessageListResponse,
	PostUserMessageRequest,
	PostUserMessageResponse,
	SendMessageRequest,
	SendMessageResponse,
)
from app.db_models.model_config import ModelConfig
from app.db_models.conversation import Conversation
from app.models.manager import model_manager

router = APIRouter(prefix="/api/messages", tags=["messages"])


def _build_title_from_message(message: str) -> str:
	compact = " ".join(message.strip().split())
	if not compact:
		return "Neue Konversation"
	if len(compact) <= 60:
		return compact
	return f"{compact[:57].rstrip()}..."


async def _load_private_conversation_ids(settings_service: SettingsService) -> list[int]:
	visibility_raw = await settings_service.get(category="chat", key="conversation_visibility_map")
	private_ids: list[int] = []
	if isinstance(visibility_raw, dict):
		for conversation_id_raw, visibility in visibility_raw.items():
			parsed_id = int(conversation_id_raw) if str(conversation_id_raw).isdigit() else None
			if parsed_id is not None and visibility == "private":
				private_ids.append(parsed_id)
	return private_ids


async def _resolve_visible_conversation(
	*,
	payload_user_id: int,
	payload_conversation_id: int | None,
	payload_message: str,
	conversation_repo: ConversationRepository,
	settings_service: SettingsService,
) -> Conversation:
	if payload_conversation_id is None:
		return await conversation_repo.create(
			user_id=payload_user_id,
			title=_build_title_from_message(payload_message),
		)

	private_ids = await _load_private_conversation_ids(settings_service)
	conversation = await conversation_repo.get_visible_by_id(
		conversation_id=payload_conversation_id,
		user_id=payload_user_id,
		private_conversation_ids=private_ids,
	)
	if conversation is None:
		raise HTTPException(status_code=404, detail="Conversation not found")
	return conversation


@router.get("", response_model=MessageListResponse)
async def list_messages(
	conversation_id: int,
	user_id: int = 1,
	limit: int = 100,
	session: AsyncSession = Depends(db_session_dependency),
) -> MessageListResponse:
	def parse_author_username(raw_metadata: str | None) -> str | None:
		if not raw_metadata:
			return None
		try:
			payload = json.loads(raw_metadata)
		except json.JSONDecodeError:
			return None
		if isinstance(payload, dict) and isinstance(payload.get("author_username"), str):
			return payload["author_username"]
		return None

	repo = MessageRepository(session)
	conversation_repo = ConversationRepository(session)
	user_repo = UserRepository(session)
	settings_service = SettingsService(session)

	private_ids = await _load_private_conversation_ids(settings_service)

	conversation = await conversation_repo.get_visible_by_id(
		conversation_id=conversation_id,
		user_id=user_id,
		private_conversation_ids=private_ids,
	)
	if conversation is None:
		raise HTTPException(status_code=404, detail="Conversation not found")

	items = await repo.list_by_conversation(conversation_id=conversation_id, limit=limit)
	owner_username = None
	if conversation is not None:
		owner = await user_repo.get_by_id(conversation.user_id)
		owner_username = owner.username if owner is not None else f"user-{conversation.user_id}"

	return MessageListResponse(
		items=[
			MessageItem(
				id=item.id,
				conversation_id=item.conversation_id,
				role=item.role,
				content=item.content,
				created_at=item.created_at,
				author_username=(parse_author_username(item.metadata_json) if item.role == "user" else None)
				or (owner_username if item.role == "user" else None),
			)
			for item in items
		]
	)


@router.post("/user-only", response_model=PostUserMessageResponse)
async def post_user_only_message(
	payload: PostUserMessageRequest,
	session: AsyncSession = Depends(db_session_dependency),
) -> PostUserMessageResponse:
	if not payload.message.strip():
		raise HTTPException(status_code=400, detail="Message must not be empty")

	user_repo = UserRepository(session)
	message_repo = MessageRepository(session)
	conversation_repo = ConversationRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=payload.user_id)
	conversation = await _resolve_visible_conversation(
		payload_user_id=payload.user_id,
		payload_conversation_id=payload.conversation_id,
		payload_message=payload.message,
		conversation_repo=conversation_repo,
		settings_service=settings_service,
	)

	if not conversation.title:
		await conversation_repo.update_title(conversation, _build_title_from_message(payload.message))

	author = await user_repo.get_by_id(payload.user_id)
	author_username = author.username if author is not None else f"user-{payload.user_id}"
	metadata_json = json.dumps(
		{
			"author_user_id": payload.user_id,
			"author_username": author_username,
		},
		ensure_ascii=True,
		separators=(",", ":"),
	)

	stored_message = await message_repo.add_message(
		conversation_id=conversation.id,
		role="user",
		content=payload.message,
		metadata_json=metadata_json,
	)
	await session.commit()

	return PostUserMessageResponse(conversation_id=conversation.id, message_id=stored_message.id)


@router.post("", response_model=SendMessageResponse)
async def send_message(
	payload: SendMessageRequest,
	session: AsyncSession = Depends(db_session_dependency),
	service: ChatService = Depends(chat_service_dependency),
) -> SendMessageResponse:
	if not payload.message.strip():
		raise HTTPException(status_code=400, detail="Message must not be empty")

	user_repo = UserRepository(session)
	message_repo = MessageRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=payload.user_id)

	if payload.model_id is not None and payload.model_id != model_manager.active_model_id:
		model = (await session.execute(select(ModelConfig).where(ModelConfig.id == payload.model_id))).scalar_one_or_none()
		if model is None:
			raise HTTPException(status_code=404, detail="Selected model not found")

		await model_manager.load_model(model_id=model.id, model_path=model.model_path, backend_name=model.backend, config={})
		all_models = (await session.execute(select(ModelConfig))).scalars().all()
		for row in all_models:
			row.is_active = row.id == model.id
			row.load_status = "ready" if row.id == model.id else "unloaded"
		await settings_service.update("model", "active_model_id", model.id)
		await session.flush()

	try:
		response = await service.generate_response(
			ChatRequest(
				user_id=payload.user_id,
				conversation_id=payload.conversation_id,
				message=payload.message,
				stream=False,
				idempotency_key=payload.idempotency_key,
				model_id=payload.model_id,
				temperature=payload.temperature,
				max_new_tokens=payload.max_new_tokens,
			)
		)
	except ValueError as exc:
		if str(exc) == "conversation_not_found":
			raise HTTPException(status_code=404, detail="Conversation not found")
		raise

	messages = await message_repo.list_by_conversation(conversation_id=response.conversation_id, limit=2)
	if len(messages) < 2:
		raise HTTPException(status_code=500, detail="Failed to persist generated messages")

	user_message = messages[-2]
	assistant_message = messages[-1]

	return SendMessageResponse(
		conversation_id=response.conversation_id,
		user_message_id=user_message.id,
		assistant_message_id=assistant_message.id,
		message=response.message,
		model_id=response.model_id,
	)
