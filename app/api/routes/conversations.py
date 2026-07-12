from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.api.errors import api_http_error
from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.project_repository import ProjectRepository
from app.database.repositories.user_repository import UserRepository
from app.schemas.conversation import (
	ActivateConversationGenerationProfileRequest,
	ConversationGenerationProfileHistoryEvent,
	ConversationGenerationProfilesResponse,
	ConversationGenerationProfileVersion,
	ConversationItem,
	ConversationListResponse,
	CreateConversationGenerationProfileRequest,
	CreateConversationRequest,
	CreateConversationResponse,
	UpdateConversationProjectRequest,
	UpdateConversationRequest,
	UpdateConversationResponse,
)
from app.settings.service import SettingsService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
GENERATION_PROFILES_SETTING_KEY = "conversation_generation_profiles_map"
CONVERSATION_PROJECT_MAP_SETTING_KEY = "conversation_project_map"


def _parse_generation_profiles_map(raw: object) -> dict[str, object]:
	if isinstance(raw, dict):
		return dict(raw)
	return {}


def _coerce_versions(entry: object) -> list[dict[str, object]]:
	if not isinstance(entry, dict):
		return []
	versions_raw = entry.get("versions")
	if not isinstance(versions_raw, list):
		return []
	return [item for item in versions_raw if isinstance(item, dict)]


def _coerce_history(entry: object) -> list[dict[str, object]]:
	if not isinstance(entry, dict):
		return []
	history_raw = entry.get("history")
	if not isinstance(history_raw, list):
		return []
	return [item for item in history_raw if isinstance(item, dict)]


def _parse_conversation_project_map(raw: object) -> dict[str, int]:
	if not isinstance(raw, dict):
		return {}

	parsed: dict[str, int] = {}
	for raw_conversation_id, raw_project_id in raw.items():
		conversation_id = str(raw_conversation_id)
		if not conversation_id.isdigit() or not isinstance(raw_project_id, int):
			continue
		parsed[conversation_id] = raw_project_id
	return parsed


async def _load_private_conversation_ids(settings_service: SettingsService) -> list[int]:
	visibility_raw = await settings_service.get(category="chat", key="conversation_visibility_map")
	private_ids: list[int] = []
	if isinstance(visibility_raw, dict):
		for conversation_id_raw, visibility in visibility_raw.items():
			if str(conversation_id_raw).isdigit() and visibility == "private":
				private_ids.append(int(conversation_id_raw))
	return private_ids


def _format_generation_profiles_response(
	*,
	conversation_id: int,
	entry: dict[str, object],
) -> ConversationGenerationProfilesResponse:
	active_version_id_raw = entry.get("active_version_id")
	active_version_id = active_version_id_raw if isinstance(active_version_id_raw, str) else None

	versions: list[ConversationGenerationProfileVersion] = []
	for item in _coerce_versions(entry):
		created_at_raw = item.get("created_at")
		created_at = (
			datetime.fromisoformat(created_at_raw)
			if isinstance(created_at_raw, str)
			else datetime.now(timezone.utc)
		)
		params = item.get("params") if isinstance(item.get("params"), dict) else {}
		versions.append(
			ConversationGenerationProfileVersion.model_validate(
				{
					"id": str(item.get("id", "")),
					"name": str(item.get("name", "Version")),
					"created_at": created_at,
					"created_by_user_id": int(item.get("created_by_user_id", 1)),
					"params": params,
				}
			)
		)

	history: list[ConversationGenerationProfileHistoryEvent] = []
	for item in _coerce_history(entry):
		created_at_raw = item.get("created_at")
		created_at = (
			datetime.fromisoformat(created_at_raw)
			if isinstance(created_at_raw, str)
			else datetime.now(timezone.utc)
		)
		history.append(
			ConversationGenerationProfileHistoryEvent.model_validate(
				{
					"id": str(item.get("id", "")),
					"action": str(item.get("action", "unknown")),
					"version_id": str(item.get("version_id", "")),
					"created_at": created_at,
					"user_id": int(item.get("user_id", 1)),
				}
			)
		)

	versions.sort(key=lambda value: value.created_at, reverse=True)
	history.sort(key=lambda value: value.created_at, reverse=True)

	return ConversationGenerationProfilesResponse(
		conversation_id=conversation_id,
		active_version_id=active_version_id,
		versions=versions,
		history=history,
	)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
	user_id: int = 1,
	limit: int = 100,
	session: AsyncSession = Depends(db_session_dependency),
) -> ConversationListResponse:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)
	message_repo = MessageRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=user_id)
	private_ids = await _load_private_conversation_ids(settings_service)
	project_map_raw = await settings_service.get(
		category="chat",
		key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
		user_id=user_id,
	)
	project_map = _parse_conversation_project_map(project_map_raw)
	conversations = await conversation_repo.list_visible_for_user(
		user_id=user_id,
		private_conversation_ids=private_ids,
		limit=limit,
	)

	items: list[ConversationItem] = []
	for conversation in conversations:
		latest = await message_repo.get_latest_by_conversation(conversation.id)
		owner = await user_repo.get_by_id(conversation.user_id)
		title = conversation.title or "Neue Konversation"
		items.append(
			ConversationItem(
				id=conversation.id,
				title=title,
				updated_at=conversation.updated_at,
				last_message=latest.content if latest else None,
				owner_user_id=conversation.user_id,
				owner_username=owner.username if owner is not None else f"user-{conversation.user_id}",
				project_id=project_map.get(str(conversation.id)),
			)
		)

	return ConversationListResponse(items=items)


@router.post("", response_model=CreateConversationResponse)
async def create_conversation(
	payload: CreateConversationRequest,
	session: AsyncSession = Depends(db_session_dependency),
) -> CreateConversationResponse:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)
	project_repo = ProjectRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=payload.user_id)
	if payload.project_id is not None:
		project = await project_repo.get_by_id(user_id=payload.user_id, project_id=payload.project_id)
		if project is None:
			raise api_http_error(
				status_code=404,
				code="project.not_found",
				message="Project not found",
				details={"project_id": payload.project_id, "user_id": payload.user_id},
			)

	conversation = await conversation_repo.create(user_id=payload.user_id, title=payload.title or "Neue Konversation")
	if payload.project_id is not None:
		project_map_raw = await settings_service.get(
			category="chat",
			key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
			user_id=payload.user_id,
		)
		project_map = _parse_conversation_project_map(project_map_raw)
		project_map[str(conversation.id)] = payload.project_id
		await settings_service.update(
			category="chat",
			key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
			value=project_map,
			user_id=payload.user_id,
		)
	owner = await user_repo.get_by_id(payload.user_id)
	await session.commit()

	return CreateConversationResponse(
		id=conversation.id,
		title=conversation.title or "Neue Konversation",
		updated_at=conversation.updated_at,
		owner_user_id=payload.user_id,
		owner_username=owner.username if owner is not None else f"user-{payload.user_id}",
		project_id=payload.project_id,
	)


@router.patch("/{conversation_id}/project")
async def update_conversation_project(
	conversation_id: int,
	payload: UpdateConversationProjectRequest,
	session: AsyncSession = Depends(db_session_dependency),
) -> dict:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)
	project_repo = ProjectRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=payload.user_id)
	private_ids = await _load_private_conversation_ids(settings_service)
	conversation = await conversation_repo.get_visible_by_id(
		conversation_id=conversation_id,
		user_id=payload.user_id,
		private_conversation_ids=private_ids,
	)
	if conversation is None:
		raise api_http_error(
			status_code=404,
			code="conversation.not_found",
			message="Conversation not found",
			details={"conversation_id": conversation_id, "user_id": payload.user_id},
		)

	if payload.project_id is not None:
		project = await project_repo.get_by_id(user_id=payload.user_id, project_id=payload.project_id)
		if project is None:
			raise api_http_error(
				status_code=404,
				code="project.not_found",
				message="Project not found",
				details={"project_id": payload.project_id, "user_id": payload.user_id},
			)

	project_map_raw = await settings_service.get(
		category="chat",
		key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
		user_id=payload.user_id,
	)
	project_map = _parse_conversation_project_map(project_map_raw)
	if payload.project_id is None:
		project_map.pop(str(conversation_id), None)
	else:
		project_map[str(conversation_id)] = payload.project_id

	await settings_service.update(
		category="chat",
		key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
		value=project_map,
		user_id=payload.user_id,
	)
	await session.commit()

	return {"updated": True, "conversation_id": conversation_id, "project_id": payload.project_id}


@router.patch("/{conversation_id}", response_model=UpdateConversationResponse)
async def update_conversation(
	conversation_id: int,
	payload: UpdateConversationRequest,
	session: AsyncSession = Depends(db_session_dependency),
) -> UpdateConversationResponse:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)
	try:
		await user_repo.ensure_default_user(user_id=payload.user_id)
		conversation = await conversation_repo.get_by_id(conversation_id=conversation_id, user_id=payload.user_id)
		if conversation is None:
			raise api_http_error(
				status_code=404,
				code="conversation.not_found",
				message="Conversation not found",
				details={"conversation_id": conversation_id, "user_id": payload.user_id},
			)

		normalized_title = (payload.title or "").strip()
		if not normalized_title:
			raise api_http_error(
				status_code=400,
				code="conversation.title_empty",
				message="Title must not be empty",
				details={"conversation_id": conversation_id, "user_id": payload.user_id},
			)

		updated = await conversation_repo.update_title(conversation=conversation, title=normalized_title)
		response = UpdateConversationResponse(
			updated=True,
			id=updated.id,
			title=updated.title or "Neue Konversation",
			updated_at=updated.updated_at,
		)
		await session.commit()
		return response
	except HTTPException:
		raise
	except SQLAlchemyError:
		await session.rollback()
		raise api_http_error(
			status_code=500,
			code="conversation.rename_failed",
			message="Conversation title update failed",
			retryable=True,
			retry_after_seconds=1,
			details={"conversation_id": conversation_id, "user_id": payload.user_id},
		)


@router.delete("/{conversation_id}")
@router.delete("/{conversation_id}/")
async def delete_conversation(
	conversation_id: int,
	user_id: int = 1,
	session: AsyncSession = Depends(db_session_dependency),
) -> dict:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)

	await user_repo.ensure_default_user(user_id=user_id)
	deleted = await conversation_repo.archive_by_id(conversation_id=conversation_id, user_id=user_id)
	if not deleted:
		raise api_http_error(
			status_code=404,
			code="conversation.not_found",
			message="Conversation not found",
			details={"conversation_id": conversation_id, "user_id": user_id},
		)

	await session.commit()
	return {"deleted": True}


@router.post("/{conversation_id}/delete")
async def delete_conversation_compat(
	conversation_id: int,
	user_id: int = 1,
	session: AsyncSession = Depends(db_session_dependency),
) -> dict:
	return await delete_conversation(conversation_id=conversation_id, user_id=user_id, session=session)


@router.get("/{conversation_id}/generation-profiles", response_model=ConversationGenerationProfilesResponse)
async def get_conversation_generation_profiles(
	conversation_id: int,
	user_id: int = 1,
	session: AsyncSession = Depends(db_session_dependency),
) -> ConversationGenerationProfilesResponse:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=user_id)
	private_ids = await _load_private_conversation_ids(settings_service)
	conversation = await conversation_repo.get_visible_by_id(
		conversation_id=conversation_id,
		user_id=user_id,
		private_conversation_ids=private_ids,
	)
	if conversation is None:
		raise api_http_error(
			status_code=404,
			code="conversation.not_found",
			message="Conversation not found",
			details={"conversation_id": conversation_id, "user_id": user_id},
		)

	raw_map = await settings_service.get(category="chat", key=GENERATION_PROFILES_SETTING_KEY, user_id=user_id)
	profiles_map = _parse_generation_profiles_map(raw_map)
	entry_raw = profiles_map.get(str(conversation_id))
	entry = entry_raw if isinstance(entry_raw, dict) else {"active_version_id": None, "versions": [], "history": []}
	return _format_generation_profiles_response(conversation_id=conversation_id, entry=entry)


@router.post("/{conversation_id}/generation-profiles", response_model=ConversationGenerationProfilesResponse)
async def create_conversation_generation_profile(
	conversation_id: int,
	payload: CreateConversationGenerationProfileRequest,
	session: AsyncSession = Depends(db_session_dependency),
) -> ConversationGenerationProfilesResponse:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=payload.user_id)
	private_ids = await _load_private_conversation_ids(settings_service)
	conversation = await conversation_repo.get_visible_by_id(
		conversation_id=conversation_id,
		user_id=payload.user_id,
		private_conversation_ids=private_ids,
	)
	if conversation is None:
		raise api_http_error(
			status_code=404,
			code="conversation.not_found",
			message="Conversation not found",
			details={"conversation_id": conversation_id, "user_id": payload.user_id},
		)

	raw_map = await settings_service.get(category="chat", key=GENERATION_PROFILES_SETTING_KEY, user_id=payload.user_id)
	profiles_map = _parse_generation_profiles_map(raw_map)
	entry_raw = profiles_map.get(str(conversation_id))
	entry = dict(entry_raw) if isinstance(entry_raw, dict) else {"active_version_id": None, "versions": [], "history": []}

	versions = _coerce_versions(entry)
	history = _coerce_history(entry)
	now = datetime.now(timezone.utc).isoformat()
	version_id = str(uuid.uuid4())
	version_name = (payload.name or "").strip() or f"Version {len(versions) + 1}"

	versions.append(
		{
			"id": version_id,
			"name": version_name,
			"created_at": now,
			"created_by_user_id": payload.user_id,
			"params": payload.params.model_dump(),
		}
	)
	history.append(
		{
			"id": str(uuid.uuid4()),
			"action": "created",
			"version_id": version_id,
			"created_at": now,
			"user_id": payload.user_id,
		}
	)

	active_version_id = entry.get("active_version_id") if isinstance(entry.get("active_version_id"), str) else None
	if payload.activate:
		active_version_id = version_id
		history.append(
			{
				"id": str(uuid.uuid4()),
				"action": "activated",
				"version_id": version_id,
				"created_at": now,
				"user_id": payload.user_id,
			}
		)

	entry["versions"] = versions
	entry["history"] = history
	entry["active_version_id"] = active_version_id
	profiles_map[str(conversation_id)] = entry

	await settings_service.update(
		category="chat",
		key=GENERATION_PROFILES_SETTING_KEY,
		value=profiles_map,
		user_id=payload.user_id,
	)
	await session.commit()

	return _format_generation_profiles_response(conversation_id=conversation_id, entry=entry)


@router.post("/{conversation_id}/generation-profiles/{version_id}/activate", response_model=ConversationGenerationProfilesResponse)
async def activate_conversation_generation_profile(
	conversation_id: int,
	version_id: str,
	payload: ActivateConversationGenerationProfileRequest,
	session: AsyncSession = Depends(db_session_dependency),
) -> ConversationGenerationProfilesResponse:
	user_repo = UserRepository(session)
	conversation_repo = ConversationRepository(session)
	settings_service = SettingsService(session)

	await user_repo.ensure_default_user(user_id=payload.user_id)
	private_ids = await _load_private_conversation_ids(settings_service)
	conversation = await conversation_repo.get_visible_by_id(
		conversation_id=conversation_id,
		user_id=payload.user_id,
		private_conversation_ids=private_ids,
	)
	if conversation is None:
		raise api_http_error(
			status_code=404,
			code="conversation.not_found",
			message="Conversation not found",
			details={"conversation_id": conversation_id, "user_id": payload.user_id},
		)

	raw_map = await settings_service.get(category="chat", key=GENERATION_PROFILES_SETTING_KEY, user_id=payload.user_id)
	profiles_map = _parse_generation_profiles_map(raw_map)
	entry_raw = profiles_map.get(str(conversation_id))
	entry = dict(entry_raw) if isinstance(entry_raw, dict) else {"active_version_id": None, "versions": [], "history": []}

	versions = _coerce_versions(entry)
	if not any(str(item.get("id", "")) == version_id for item in versions):
		raise api_http_error(
			status_code=404,
			code="conversation.generation_profile_version_not_found",
			message="Conversation generation profile version not found",
			details={"conversation_id": conversation_id, "version_id": version_id},
		)

	now = datetime.now(timezone.utc).isoformat()
	history = _coerce_history(entry)
	history.append(
		{
			"id": str(uuid.uuid4()),
			"action": "activated",
			"version_id": version_id,
			"created_at": now,
			"user_id": payload.user_id,
		}
	)

	entry["versions"] = versions
	entry["history"] = history
	entry["active_version_id"] = version_id
	profiles_map[str(conversation_id)] = entry

	await settings_service.update(
		category="chat",
		key=GENERATION_PROFILES_SETTING_KEY,
		value=profiles_map,
		user_id=payload.user_id,
	)
	await session.commit()

	return _format_generation_profiles_response(conversation_id=conversation_id, entry=entry)
