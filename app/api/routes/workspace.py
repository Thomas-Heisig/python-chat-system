from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.database.repositories.appointment_repository import AppointmentRepository
from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.knowledge_repository import KnowledgeRepository
from app.database.repositories.project_repository import ProjectRepository
from app.database.repositories.user_repository import UserRepository
from app.settings.service import SettingsService
from app.startup import initialize_runtime

router = APIRouter(prefix="/api/workspace", tags=["workspace"])
CONVERSATION_PROJECT_MAP_SETTING_KEY = "conversation_project_map"
_ALLOWED_SOURCE_EXTENSIONS = {".pdf", ".md", ".txt", ".docx"}


class CreateProjectRequest(BaseModel):
    name: str
    user_id: int = 1


class UpdateProjectRequest(BaseModel):
    name: str
    user_id: int = 1


async def _seed_workspace_if_empty(session: AsyncSession, user_id: int) -> None:
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

    for item in items:
        item["chats"] = int(chat_counts.get(int(item["id"]), 0))

    return {"items": items}


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

    created = await repo.create(user_id=payload.user_id, name=name)
    await session.commit()
    return {
        "id": created.id,
        "name": created.name,
        "chats": 0,
        "documents": 0,
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
    await repo.delete_with_detach(project)
    await session.commit()
    return {"deleted": True}


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
    return {"items": await repo.list_documents(user_id=user_id, limit=200)}


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
