from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.core.auth_token import verify_access_token
from app.database.repositories.appointment_repository import AppointmentRepository
from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.knowledge_repository import KnowledgeRepository
from app.database.repositories.project_repository import ProjectRepository
from app.database.repositories.user_repository import UserRepository
from app.db_models.appointment import Appointment
from app.db_models.conversation import Conversation
from app.db_models.knowledge_document import KnowledgeDocument
from app.db_models.message import Message
from app.db_models.project import Project
from app.db_models.setting import Setting
from app.db_models.training_dataset import TrainingDataset
from app.settings.service import SettingsService
from app.startup import initialize_runtime

router = APIRouter(prefix="/api/workspace", tags=["workspace"])
CONVERSATION_PROJECT_MAP_SETTING_KEY = "conversation_project_map"
WORKSPACE_SEED_DEMO_DATA_SETTING_KEY = "seed_demo_data"
WORKSPACE_PROJECT_META_MAP_SETTING_KEY = "project_meta_map"
_ALLOWED_SOURCE_EXTENSIONS = {".pdf", ".md", ".txt", ".docx"}


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    token = authorization[len(prefix) :].strip()
    return token or None


class CreateProjectRequest(BaseModel):
    name: str
    user_id: int = 1
    parent_project_id: int | None = None
    scope_kind: str = "project"
    area_key: str | None = None
    tenant_key: str | None = None
    owner_user_id: int | None = None


class UpdateProjectRequest(BaseModel):
    name: str
    user_id: int = 1


class UpdateProjectHierarchyRequest(BaseModel):
    user_id: int = 1
    parent_project_id: int | None = None
    scope_kind: str = "project"
    area_key: str | None = None
    tenant_key: str | None = None
    owner_user_id: int | None = None


def _normalize_scope_kind(raw: str) -> str:
    normalized = raw.strip().lower()
    if normalized in {"tenant", "user", "area", "project"}:
        return normalized
    return "project"


def _normalize_optional_text(raw: str | None, max_len: int = 120) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    return cleaned[:max_len]


def _project_meta_default(project_id: int) -> dict[str, object]:
    return {
        "project_id": project_id,
        "parent_project_id": None,
        "scope_kind": "project",
        "area_key": None,
        "tenant_key": None,
        "owner_user_id": None,
    }


def _coerce_project_meta(raw: object, project_id: int) -> dict[str, object]:
    base = _project_meta_default(project_id)
    if not isinstance(raw, dict):
        return base

    typed_raw = cast(dict[object, object], raw)

    raw_parent = typed_raw.get("parent_project_id")
    parent_project_id: int | None = None
    if isinstance(raw_parent, int) and raw_parent > 0 and raw_parent != project_id:
        parent_project_id = raw_parent

    raw_scope = typed_raw.get("scope_kind")
    scope_kind = "project"
    if isinstance(raw_scope, str):
        scope_kind = _normalize_scope_kind(raw_scope)

    raw_area = typed_raw.get("area_key")
    area_key = _normalize_optional_text(raw_area if isinstance(raw_area, str) else None)

    raw_tenant = typed_raw.get("tenant_key")
    tenant_key = _normalize_optional_text(raw_tenant if isinstance(raw_tenant, str) else None)

    raw_owner = typed_raw.get("owner_user_id")
    owner_user_id: int | None = None
    if isinstance(raw_owner, int) and raw_owner > 0:
        owner_user_id = raw_owner

    return {
        "project_id": project_id,
        "parent_project_id": parent_project_id,
        "scope_kind": scope_kind,
        "area_key": area_key,
        "tenant_key": tenant_key,
        "owner_user_id": owner_user_id,
    }


async def _load_project_meta_map(settings_service: SettingsService, user_id: int) -> dict[int, dict[str, object]]:
    raw = await settings_service.get(
        category="workspace",
        key=WORKSPACE_PROJECT_META_MAP_SETTING_KEY,
        user_id=user_id,
    )
    if not isinstance(raw, dict):
        return {}

    out: dict[int, dict[str, object]] = {}
    typed_raw = cast(dict[object, object], raw)
    for raw_project_id, raw_meta in typed_raw.items():
        project_id_text = str(raw_project_id)
        if not project_id_text.isdigit():
            continue
        project_id = int(project_id_text)
        out[project_id] = _coerce_project_meta(raw_meta, project_id=project_id)
    return out


async def _save_project_meta_map(settings_service: SettingsService, user_id: int, meta_map: dict[int, dict[str, object]]) -> None:
    encoded: dict[str, dict[str, object]] = {str(project_id): meta for project_id, meta in meta_map.items()}
    await settings_service.update(
        category="workspace",
        key=WORKSPACE_PROJECT_META_MAP_SETTING_KEY,
        value=encoded,
        user_id=user_id,
    )


def _build_depth_map(meta_map: dict[int, dict[str, object]]) -> dict[int, int]:
    depth_cache: dict[int, int] = {}

    def resolve_depth(project_id: int, seen: set[int]) -> int:
        if project_id in depth_cache:
            return depth_cache[project_id]
        if project_id in seen:
            return 0

        meta = meta_map.get(project_id)
        if meta is None:
            depth_cache[project_id] = 0
            return 0

        parent_raw = meta.get("parent_project_id")
        if not isinstance(parent_raw, int) or parent_raw <= 0:
            depth_cache[project_id] = 0
            return 0

        next_seen = set(seen)
        next_seen.add(project_id)
        depth = 1 + resolve_depth(parent_raw, next_seen)
        depth_cache[project_id] = depth
        return depth

    for project_id in meta_map:
        resolve_depth(project_id, set())

    return depth_cache


def _build_project_ancestry(meta_map: dict[int, dict[str, object]], project_id: int) -> list[int]:
    lineage: list[int] = []
    cursor: int | None = project_id
    seen: set[int] = set()

    while isinstance(cursor, int) and cursor > 0 and cursor not in seen:
        lineage.append(cursor)
        seen.add(cursor)
        meta = meta_map.get(cursor)
        if meta is None:
            break
        parent_raw = meta.get("parent_project_id")
        cursor = parent_raw if isinstance(parent_raw, int) and parent_raw > 0 else None

    return list(reversed(lineage))


async def _seed_workspace_if_empty(session: AsyncSession, user_id: int) -> None:
    settings_service = SettingsService(session)
    seed_demo_data = await settings_service.get(
        category="workspace",
        key=WORKSPACE_SEED_DEMO_DATA_SETTING_KEY,
        user_id=user_id,
    )
    if seed_demo_data is False:
        return

    project_repo = ProjectRepository(session)
    appointment_repo = AppointmentRepository(session)
    knowledge_repo = KnowledgeRepository(session)

    try:
        await knowledge_repo.delete_seed_mock_documents(user_id=user_id)
        existing_projects = await project_repo.list_by_user(user_id=user_id)
        existing_appointments = await appointment_repo.list_by_user(user_id=user_id, limit=1)
        existing_documents = await knowledge_repo.list_documents(user_id=user_id, limit=1)
    except OperationalError:
        await session.rollback()
        await initialize_runtime(run_model_scan=False)
        await knowledge_repo.delete_seed_mock_documents(user_id=user_id)
        existing_projects = await project_repo.list_by_user(user_id=user_id)
        existing_appointments = await appointment_repo.list_by_user(user_id=user_id, limit=1)
        existing_documents = await knowledge_repo.list_documents(user_id=user_id, limit=1)

    if existing_projects or existing_appointments or existing_documents:
        return

    heisig = await project_repo.create(user_id=user_id, name="Heisig Naturstein")
    await project_repo.create(user_id=user_id, name="Fussball")
    await project_repo.create(user_id=user_id, name="Restaurierung")

    await appointment_repo.create(user_id=user_id, title="Baustelle Klaener", status="Vorgeschlagen", project_id=heisig.id)
    await appointment_repo.create(
        user_id=user_id,
        title="Mannschaftsbesprechung",
        status="Bestaetigt",
    )

    await knowledge_repo.create_document(
        user_id=user_id,
        file_name="Angebot_Klaener.pdf",
        source="seed_mock",
        status="Bereit",
        metadata={"position": "Seite 3", "relevance": "91 %"},
        project_id=heisig.id,
    )
    await knowledge_repo.create_document(
        user_id=user_id,
        file_name="Materialliste_Lemwerder.docx",
        source="seed_mock",
        status="Bereit",
        metadata={"position": "Abschnitt 8", "relevance": "84 %"},
        project_id=heisig.id,
    )

    await session.commit()


@router.get("/projects")
async def list_projects(
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = ProjectRepository(session)
    conversation_repo = ConversationRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=user_id)
    await _seed_workspace_if_empty(session, user_id=user_id)
    items = await repo.list_by_user(user_id=user_id)
    meta_map = await _load_project_meta_map(settings_service, user_id=user_id)
    depth_map = _build_depth_map(meta_map)

    project_map_raw = await settings_service.get(
        category="chat",
        key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
        user_id=user_id,
    )
    conversations = await conversation_repo.list_by_user(user_id=user_id, limit=500)
    active_conversation_ids = {conversation.id for conversation in conversations}

    chat_counts: dict[int, int] = {}
    if isinstance(project_map_raw, dict):
        project_map_typed = cast(dict[object, object], project_map_raw)
        for raw_conversation_id, raw_project_id in project_map_typed.items():
            conversation_id_text = str(raw_conversation_id)
            conversation_id = int(conversation_id_text) if conversation_id_text.isdigit() else None
            if conversation_id is None or conversation_id not in active_conversation_ids:
                continue
            if not isinstance(raw_project_id, int):
                continue
            chat_counts[raw_project_id] = chat_counts.get(raw_project_id, 0) + 1

    enriched_items: list[dict[str, object]] = []
    for item in items:
        project_id = int(item["id"])
        meta = meta_map.get(project_id, _project_meta_default(project_id))
        enriched_items.append(
            {
                "id": project_id,
                "name": str(item["name"]),
                "chats": int(chat_counts.get(project_id, 0)),
                "documents": int(item["documents"]),
                "parent_project_id": meta.get("parent_project_id"),
                "scope_kind": meta.get("scope_kind"),
                "area_key": meta.get("area_key"),
                "tenant_key": meta.get("tenant_key"),
                "owner_user_id": meta.get("owner_user_id"),
                "depth": int(depth_map.get(project_id, 0)),
            }
        )

    return {"items": enriched_items}


@router.post("/projects")
async def create_project(
    payload: CreateProjectRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = ProjectRepository(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    name = payload.name.strip()
    if not name:
        return {"error": "project_name_empty"}

    parent_project_id: int | None = payload.parent_project_id
    if isinstance(parent_project_id, int):
        if parent_project_id <= 0:
            return {"error": "project_parent_invalid"}
        parent_project = await repo.get_by_id(user_id=payload.user_id, project_id=parent_project_id)
        if parent_project is None:
            return {"error": "project_parent_not_found"}

    created = await repo.create(user_id=payload.user_id, name=name)

    settings_service = SettingsService(session)
    meta_map = await _load_project_meta_map(settings_service, user_id=payload.user_id)
    meta_map[created.id] = {
        "project_id": created.id,
        "parent_project_id": parent_project_id,
        "scope_kind": _normalize_scope_kind(payload.scope_kind),
        "area_key": _normalize_optional_text(payload.area_key),
        "tenant_key": _normalize_optional_text(payload.tenant_key),
        "owner_user_id": payload.owner_user_id if payload.owner_user_id and payload.owner_user_id > 0 else payload.user_id,
    }
    await _save_project_meta_map(settings_service, user_id=payload.user_id, meta_map=meta_map)

    await session.commit()
    return {
        "id": created.id,
        "name": created.name,
        "chats": 0,
        "documents": 0,
        "parent_project_id": parent_project_id,
        "scope_kind": _normalize_scope_kind(payload.scope_kind),
        "area_key": _normalize_optional_text(payload.area_key),
        "tenant_key": _normalize_optional_text(payload.tenant_key),
        "owner_user_id": payload.owner_user_id if payload.owner_user_id and payload.owner_user_id > 0 else payload.user_id,
        "depth": 0,
    }


@router.patch("/projects/{project_id}/hierarchy")
async def update_project_hierarchy(
    project_id: int,
    payload: UpdateProjectHierarchyRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = ProjectRepository(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    project = await repo.get_by_id(user_id=payload.user_id, project_id=project_id)
    if project is None:
        return {"updated": False, "error": "project_not_found"}

    settings_service = SettingsService(session)
    meta_map = await _load_project_meta_map(settings_service, user_id=payload.user_id)
    current_meta = meta_map.get(project_id, _project_meta_default(project_id))

    requested_parent: int | None = payload.parent_project_id
    if isinstance(requested_parent, int):
        if requested_parent <= 0 or requested_parent == project_id:
            requested_parent = None
        else:
            parent_project = await repo.get_by_id(user_id=payload.user_id, project_id=requested_parent)
            if parent_project is None:
                return {"updated": False, "error": "project_parent_not_found"}

    if isinstance(requested_parent, int):
        # Prevent hierarchy cycles by rejecting parents that are descendants of the current project.
        cursor: int | None = requested_parent
        seen: set[int] = set()
        while isinstance(cursor, int) and cursor > 0 and cursor not in seen:
            if cursor == project_id:
                return {"updated": False, "error": "project_parent_cycle"}
            seen.add(cursor)
            cursor_meta = meta_map.get(cursor)
            if cursor_meta is None:
                break
            parent_raw = cursor_meta.get("parent_project_id")
            cursor = parent_raw if isinstance(parent_raw, int) and parent_raw > 0 else None

    current_meta["parent_project_id"] = requested_parent
    current_meta["scope_kind"] = _normalize_scope_kind(payload.scope_kind)
    current_meta["area_key"] = _normalize_optional_text(payload.area_key)
    current_meta["tenant_key"] = _normalize_optional_text(payload.tenant_key)
    current_meta["owner_user_id"] = payload.owner_user_id if payload.owner_user_id and payload.owner_user_id > 0 else payload.user_id

    meta_map[project_id] = current_meta
    await _save_project_meta_map(settings_service, user_id=payload.user_id, meta_map=meta_map)

    await session.commit()
    return {
        "updated": True,
        "project_id": project_id,
        "parent_project_id": current_meta["parent_project_id"],
        "scope_kind": current_meta["scope_kind"],
        "area_key": current_meta["area_key"],
        "tenant_key": current_meta["tenant_key"],
        "owner_user_id": current_meta["owner_user_id"],
    }


@router.patch("/projects/{project_id}")
async def rename_project(
    project_id: int,
    payload: UpdateProjectRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = ProjectRepository(session)

    await user_repo.ensure_default_user(user_id=payload.user_id)
    project = await repo.get_by_id(user_id=payload.user_id, project_id=project_id)
    if project is None:
        return {"error": "project_not_found"}

    name = payload.name.strip()
    if not name:
        return {"error": "project_name_empty"}

    updated = await repo.rename(project=project, name=name)
    await session.commit()
    return {
        "id": updated.id,
        "name": updated.name,
    }


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = ProjectRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    project = await repo.get_by_id(user_id=user_id, project_id=project_id)
    if project is None:
        return {"deleted": False, "error": "project_not_found"}

    settings_service = SettingsService(session)
    map_raw = await settings_service.get(
        category="chat",
        key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
        user_id=user_id,
    )
    next_map: dict[str, int] = {}
    if isinstance(map_raw, dict):
        map_raw_typed = cast(dict[object, object], map_raw)
        for key, value in map_raw_typed.items():
            conversation_id = str(key)
            if not conversation_id.isdigit():
                continue
            if isinstance(value, int) and value != project_id:
                next_map[conversation_id] = value

    await settings_service.update(
        category="chat",
        key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
        value=next_map,
        user_id=user_id,
    )

    project_meta_map = await _load_project_meta_map(settings_service, user_id=user_id)
    deleted_meta = project_meta_map.get(project_id)
    deleted_parent_project_id: int | None = None
    if deleted_meta is not None:
        deleted_parent_raw = deleted_meta.get("parent_project_id")
        if isinstance(deleted_parent_raw, int) and deleted_parent_raw > 0:
            deleted_parent_project_id = deleted_parent_raw

    project_meta_map.pop(project_id, None)
    for item_project_id, meta in project_meta_map.items():
        parent_raw = meta.get("parent_project_id")
        if isinstance(parent_raw, int) and parent_raw == project_id:
            next_parent: int | None = deleted_parent_project_id if deleted_parent_project_id != item_project_id else None
            meta["parent_project_id"] = next_parent
            project_meta_map[item_project_id] = meta

    await _save_project_meta_map(settings_service, user_id=user_id, meta_map=project_meta_map)

    await repo.delete_with_detach(project)
    await session.commit()
    return {"deleted": True}


@router.post("/reset-clean-start")
async def reset_workspace_for_clean_start(
    user_id: int = 1,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    def _safe_rowcount(result: object) -> int:
        rowcount = getattr(result, "rowcount", None)
        if isinstance(rowcount, int) and rowcount > 0:
            return rowcount
        return 0

    user_repo = UserRepository(session)
    settings_service = SettingsService(session)

    token = _extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    requester_user_id = verify_access_token(token)
    if requester_user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    requester = await user_repo.get_by_id(requester_user_id)
    if requester is None:
        raise HTTPException(status_code=401, detail="Token user not found")
    if not requester.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
    if not requester.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can run global reset")

    await user_repo.ensure_default_user(user_id=user_id)

    # Hard reset is intentionally global: all chats/projects are removed from DB.
    conversation_ids = list((await session.execute(select(Conversation.id))).scalars().all())
    project_ids = list((await session.execute(select(Project.id))).scalars().all())

    detached_appointment_conversations = 0
    deleted_messages = 0
    deleted_conversations = 0
    detached_appointment_projects = 0
    detached_documents = 0
    detached_training_datasets = 0
    deleted_projects = 0

    if conversation_ids:
        detached_appointment_conversations_result = await session.execute(
            update(Appointment)
            .where(Appointment.conversation_id.in_(conversation_ids))
            .values(conversation_id=None)
        )
        detached_appointment_conversations = _safe_rowcount(detached_appointment_conversations_result)

        deleted_messages_result = await session.execute(
            delete(Message).where(Message.conversation_id.in_(conversation_ids))
        )
        deleted_messages = _safe_rowcount(deleted_messages_result)

        deleted_conversations_result = await session.execute(
            delete(Conversation).where(Conversation.id.in_(conversation_ids))
        )
        deleted_conversations = _safe_rowcount(deleted_conversations_result)

    if project_ids:
        detached_appointment_projects_result = await session.execute(
            update(Appointment)
            .where(Appointment.project_id.in_(project_ids))
            .values(project_id=None)
        )
        detached_appointment_projects = _safe_rowcount(detached_appointment_projects_result)

        detached_documents_result = await session.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.project_id.in_(project_ids))
            .values(project_id=None)
        )
        detached_documents = _safe_rowcount(detached_documents_result)

        detached_training_datasets_result = await session.execute(
            update(TrainingDataset)
            .where(TrainingDataset.project_id.in_(project_ids))
            .values(project_id=None)
        )
        detached_training_datasets = _safe_rowcount(detached_training_datasets_result)

        deleted_projects_result = await session.execute(
            delete(Project).where(Project.id.in_(project_ids))
        )
        deleted_projects = _safe_rowcount(deleted_projects_result)

    reset_chat_keys = (
        "conversation_project_map",
        "conversation_context_limit_map",
        "conversation_generation_profiles_map",
        "conversation_visibility_map",
        "conversation_ai_participation_map",
        "conversation_ai_intent_markers_map",
    )
    await session.execute(
        delete(Setting)
        .where(Setting.category == "chat")
        .where(Setting.key.in_(reset_chat_keys))
    )

    await settings_service.update(
        category="workspace",
        key=WORKSPACE_SEED_DEMO_DATA_SETTING_KEY,
        value=False,
        user_id=None,
        team_id=None,
    )

    await session.commit()

    return {
        "reset": True,
        "deleted": {
            "messages": deleted_messages,
            "conversations": deleted_conversations,
            "projects": deleted_projects,
        },
        "detached": {
            "appointment_conversations": detached_appointment_conversations,
            "appointment_projects": detached_appointment_projects,
            "knowledge_documents": detached_documents,
            "training_datasets": detached_training_datasets,
        },
    }


@router.get("/appointments")
async def list_appointments(
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = AppointmentRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    await _seed_workspace_if_empty(session, user_id=user_id)
    return {"items": await repo.list_by_user(user_id=user_id, limit=100)}


@router.get("/sources")
async def list_sources(
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = KnowledgeRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)
    await _seed_workspace_if_empty(session, user_id=user_id)
    project_repo = ProjectRepository(session)
    project_rows = await project_repo.list_by_user(user_id=user_id)
    project_names = {int(row["id"]): str(row["name"]) for row in project_rows}

    items = await repo.list_documents(user_id=user_id, limit=200)
    for item in items:
        raw_project_id = item.get("project_id")
        project_id = raw_project_id if isinstance(raw_project_id, int) else None
        item["project_name"] = project_names.get(project_id) if isinstance(project_id, int) else None

    return {"items": items}


@router.patch("/sources/{source_id}/project")
async def assign_source_project(
    source_id: int,
    project_id: int | None = None,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    project_repo = ProjectRepository(session)
    knowledge_repo = KnowledgeRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)

    if isinstance(project_id, int):
        project = await project_repo.get_by_id(user_id=user_id, project_id=project_id)
        if project is None:
            return {"updated": False, "error": "project_not_found"}

    document = await knowledge_repo.get_document_by_id(user_id=user_id, document_id=source_id)
    if document is None:
        return {"updated": False, "error": "source_not_found"}

    updated = await knowledge_repo.assign_document_project(document=document, project_id=project_id)
    await session.commit()
    return {
        "updated": True,
        "source_id": updated.id,
        "project_id": updated.project_id,
    }


@router.get("/projects/{project_id}/sources/effective")
async def list_effective_sources_for_project(
    project_id: int,
    user_id: int = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    project_repo = ProjectRepository(session)
    knowledge_repo = KnowledgeRepository(session)
    settings_service = SettingsService(session)

    await user_repo.ensure_default_user(user_id=user_id)
    project = await project_repo.get_by_id(user_id=user_id, project_id=project_id)
    if project is None:
        return {"items": [], "error": "project_not_found"}

    meta_map = await _load_project_meta_map(settings_service, user_id=user_id)
    lineage = _build_project_ancestry(meta_map, project_id=project_id)
    if not lineage:
        lineage = [project_id]

    documents = await knowledge_repo.list_documents_for_projects(user_id=user_id, project_ids=lineage, limit=500)
    level_by_project_id = {lineage_id: idx for idx, lineage_id in enumerate(lineage)}

    project_rows = await project_repo.list_by_user(user_id=user_id)
    project_names = {int(row["id"]): str(row["name"]) for row in project_rows}

    items: list[dict[str, object]] = []
    for row in documents:
        assigned_project_id = row.project_id if isinstance(row.project_id, int) else None
        inherited_from_depth = level_by_project_id.get(assigned_project_id, 0) if isinstance(assigned_project_id, int) else 0
        items.append(
            {
                "id": row.id,
                "file": row.file_name,
                "status": row.status,
                "source": row.source,
                "assigned_project_id": assigned_project_id,
                "assigned_project_name": project_names.get(assigned_project_id) if isinstance(assigned_project_id, int) else None,
                "inherited_from_depth": inherited_from_depth,
            }
        )

    return {
        "project_id": project_id,
        "lineage_project_ids": lineage,
        "items": items,
    }


@router.post("/sources/upload")
async def upload_source(
    user_id: int = Form(default=1),
    project_id: int | None = Form(default=None),
    source_file: UploadFile = File(...),
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    user_repo = UserRepository(session)
    repo = KnowledgeRepository(session)

    await user_repo.ensure_default_user(user_id=user_id)

    raw_name = str(source_file.filename or "").strip()
    file_name = Path(raw_name).name if raw_name else "source-file"
    suffix = Path(file_name).suffix.lower()
    if suffix not in _ALLOWED_SOURCE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="source_file_type_not_supported")

    payload = await source_file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="source_file_empty")

    created = await repo.create_document(
        user_id=user_id,
        file_name=file_name,
        source="upload",
        status="Bereit",
        metadata={"position": "Datei", "relevance": "n/a"},
        project_id=project_id,
    )
    await session.commit()
    return {
        "uploaded": True,
        "id": created.id,
        "file": created.file_name,
        "source": created.source,
        "status": created.status,
    }
