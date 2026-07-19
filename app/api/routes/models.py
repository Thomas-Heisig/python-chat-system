import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import cast
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.api.dependencies import db_session_dependency
from app.api.errors import api_http_error
from app.models.scanner import ModelScanner
from app.models.registry import ModelRegistry
from app.models.path_security import normalize_base_directories, validate_runtime_model_paths
from app.models.manager import model_manager
from app.models.health_check import check_backend_health
from app.models.loader import create_backend, list_supported_backends
from app.models.loader_registry import ModelLoaderRegistry
from app.models.openai_integration import discover_openai_models, parse_openai_model_ref, resolve_openai_api_key
from app.models.ollama_integration import (
    discover_ollama_models,
    get_ollama_local_models_payload,
    is_ollama_model_installed,
    parse_ollama_model_ref,
    stream_ollama_lines,
)
from app.models.ollama_pull_registry import ACTIVE_PULL_STATES, TERMINAL_PULL_STATES, ollama_pull_registry
from app.models.capabilities import REQUIRED_CHAT_CAPABILITIES
from app.models.metadata import infer_model_capabilities
from app.database.session import get_session_maker
from app.db_models.conversation import Conversation
from app.db_models.message import Message
from app.db_models.model_config import ModelConfig
from app.settings.service import SettingsService

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelRelevanceUpdateRequest(BaseModel):
    relevance: str | None
    user_id: int | None = 1


class CustomCodeTrustUpdateRequest(BaseModel):
    trusted: bool


GROUP_ORDER = {
    "Text / Chat": 1,
    "GGUF - Text / Chat": 2,
    "Multimodal": 3,
    "Embeddings": 4,
    "Reranker": 5,
    "Speech-to-Text": 6,
    "Text-to-Speech": 7,
    "Audio / Musik": 8,
    "Bild": 9,
    "OCR": 10,
    "Hilfsmodelle": 11,
}

RELEVANCE_ORDER = {
    "active": 0,
    "favorite": 1,
    "relevant": 2,
    "unavailable": 3,
    "irrelevant": 4,
}


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


def _gpu_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _as_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return default


def _resolve_path_value(raw: object) -> Path:
    return Path(str(raw or "")).expanduser().resolve(strict=False)


def _canonical_model_path(raw: object) -> Path:
    resolved = _resolve_path_value(raw)
    if resolved.suffix:
        return resolved.parent
    return resolved


def _paths_related(existing_path_raw: object, scanned_path_raw: object) -> bool:
    existing_path = _resolve_path_value(existing_path_raw)
    scanned_path = _resolve_path_value(scanned_path_raw)
    if existing_path == scanned_path:
        return True
    # Legacy rows may point to a model file while the scanner now returns the model directory.
    if existing_path.suffix and existing_path.parent == scanned_path:
        return True
    # Handle the inverse migration direction defensively.
    if scanned_path.suffix and scanned_path.parent == existing_path:
        return True
    return False


def _find_related_existing_model(
    *,
    rows: list[ModelConfig],
    scanned_model_path: str,
) -> ModelConfig | None:
    for candidate in rows:
        if _paths_related(candidate.model_path, scanned_model_path):
            return candidate
    return None


async def _cleanup_legacy_model_rows(
    *,
    session: AsyncSession,
    rows: list[ModelConfig],
) -> list[ModelConfig]:
    grouped: dict[Path, list[ModelConfig]] = {}
    for row in rows:
        key = _canonical_model_path(row.model_path)
        grouped.setdefault(key, []).append(row)

    cleaned_rows = list(rows)

    for canonical_path, group in grouped.items():
        if len(group) <= 1:
            continue

        canonical_path_str = str(canonical_path)
        keeper = next((row for row in group if _resolve_path_value(row.model_path) == canonical_path), None)
        if keeper is None:
            keeper = min(group, key=lambda row: row.id)

        keeper_metadata = _parse_metadata(keeper.metadata_json)
        trusted = _as_bool(keeper_metadata.get("custom_code_trusted"))

        for candidate in group:
            if candidate.id == keeper.id:
                continue

            candidate_metadata = _parse_metadata(candidate.metadata_json)
            trusted = trusted or _as_bool(candidate_metadata.get("custom_code_trusted"))

            if candidate.is_active and not keeper.is_active:
                keeper.is_active = True
                keeper.load_status = candidate.load_status
                keeper.last_loaded_at = candidate.last_loaded_at

            await session.execute(
                update(Conversation)
                .where(Conversation.active_model_id == candidate.id)
                .values(active_model_id=keeper.id)
            )
            await session.execute(
                update(Message)
                .where(Message.model_id == candidate.id)
                .values(model_id=keeper.id)
            )

            await session.delete(candidate)
            cleaned_rows = [row for row in cleaned_rows if row.id != candidate.id]

        if keeper.model_path != canonical_path_str:
            keeper.model_path = canonical_path_str

        keeper_metadata["custom_code_trusted"] = trusted
        keeper.metadata_json = json.dumps(keeper_metadata)

    return cleaned_rows


def _merged_scan_metadata(
    *,
    existing_metadata: dict[str, object],
    scanned_metadata: dict[str, object],
) -> dict[str, object]:
    merged = dict(scanned_metadata)
    if "custom_code_trusted" in existing_metadata:
        merged["custom_code_trusted"] = _as_bool(existing_metadata.get("custom_code_trusted"))
    if str(scanned_metadata.get("model_format") or "") == "ollama":
        for key in ("ollama_installed", "context_length", "parameter_size", "quantization_level", "embedding_length"):
            if key in existing_metadata:
                merged[key] = existing_metadata[key]
    return merged


def _custom_code_gate(metadata: dict[str, object]) -> str | None:
    requires_custom_code = _as_bool(metadata.get("requires_custom_code"))
    if not requires_custom_code:
        return None
    custom_code_available = _as_bool(metadata.get("custom_code_available"))
    if not custom_code_available:
        return "Benutzerdefinierter Loader-Code fehlt fuer dieses Modell."
    custom_code_trusted = _as_bool(metadata.get("custom_code_trusted"))
    if not custom_code_trusted:
        return "Custom-Code ist nicht als vertrauenswuerdig markiert."
    return None


def _relevance_for_row(*, is_active: bool, loadable: bool, user_flag: str | None) -> str:
    if is_active:
        return "active"
    if user_flag == "favorite":
        return "favorite"
    if user_flag == "irrelevant":
        return "irrelevant"
    if loadable:
        return "relevant"
    return "unavailable"


def _status_for_row(
    *,
    is_active: bool,
    load_status: str | None,
    relevance: str,
    reason_unavailable: str | None,
    loader_found: bool,
) -> tuple[str, str]:
    normalized = (load_status or "").strip().lower()
    if is_active:
        return "aktiv", "green"
    if normalized == "ready":
        return "bereit", "blue"
    if normalized == "loading":
        return "laedt", "yellow"
    if normalized == "error":
        return "fehler", "red"
    if loader_found and reason_unavailable:
        return "eingeschraenkt", "yellow"
    if relevance == "unavailable" or reason_unavailable:
        return "nicht verfuegbar", "gray"
    return "inaktiv", "blue"


def _source_for_row(row: ModelConfig, metadata: dict[str, object]) -> tuple[str, str]:
    source_kind = str(metadata.get("source_kind") or "").strip().lower()
    source_label = str(metadata.get("source_label") or "").strip()
    if source_kind and source_label:
        return source_kind, source_label
    if source_kind == "ollama_local":
        return "ollama_local", "Ollama Local"
    if source_kind == "ollama_cloud":
        return "ollama_cloud", "Ollama Cloud"
    if str(row.model_path).startswith(("http://", "https://")):
        return "remote", "Remote"
    return "lokal", "Lokal"


def _ollama_pull_payload(metadata: dict[str, object], model_path: str) -> tuple[str, str, dict[str, object] | None]:
    source_kind = str(metadata.get("source_kind") or "").strip().lower()
    if str(metadata.get("backend") or "") != "ollama":
        return "", source_kind, None
    model_name, source_kind = parse_ollama_model_ref(model_path, metadata)
    if not model_name:
        return "", source_kind, None
    pull_status = ollama_pull_registry.get(model_path)
    return model_name, source_kind, pull_status.as_dict() if pull_status is not None else None


def _openai_payload(metadata: dict[str, object], model_path: str) -> tuple[str, str]:
    if str(metadata.get("backend") or "") != "openai":
        return "", ""
    return parse_openai_model_ref(model_path, metadata), str(metadata.get("source_kind") or "remote").strip().lower()


async def _persist_ollama_install_state(model_id: int, *, installed: bool, metadata_patch: dict[str, object] | None = None) -> None:
    session_maker = get_session_maker()
    async with session_maker() as session:
        model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
        if model is None:
            return
        metadata = _parse_metadata(model.metadata_json)
        metadata["ollama_installed"] = installed
        if metadata_patch:
            metadata.update(metadata_patch)
        model.metadata_json = json.dumps(metadata)
        if installed and model.load_status == "loading":
            model.load_status = "unloaded"
        if not installed and model.load_status == "ready":
            model.load_status = "unloaded"
        await session.commit()


def _run_ollama_pull_sync(*, model_id: int, model_path: str, model_name: str) -> tuple[str, str | None, dict[str, object] | None]:
    progress = 0
    metadata_patch: dict[str, object] = {}
    cancel_event = ollama_pull_registry.begin(
        model_path,
        state="queued",
        detail="Download wird vorbereitet",
        progress_percent=0,
    )
    response = None
    try:
        if is_ollama_model_installed(model_name):
            ollama_pull_registry.set(model_path, state="completed", detail="Modell ist bereits lokal verfuegbar", progress_percent=100)
            return "completed", None, {"ollama_installed": True}

        ollama_pull_registry.set(model_path, state="pulling", detail="Download startet", progress_percent=1)
        response = stream_ollama_lines("/api/pull", {"model": model_name}, timeout=900.0)
        for raw_line in response:
            if cancel_event.is_set():
                ollama_pull_registry.set(model_path, state="cancelled", detail="Download abgebrochen", progress_percent=progress or None)
                return "cancelled", None, {"ollama_installed": False}

            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                chunk_raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(chunk_raw, dict):
                continue
            chunk = cast(dict[str, object], chunk_raw)
            detail = str(chunk.get("status") or "Download laeuft")
            total_raw = chunk.get("total")
            completed_raw = chunk.get("completed")
            total = int(total_raw) if isinstance(total_raw, (int, float)) else None
            completed = int(completed_raw) if isinstance(completed_raw, (int, float)) else None
            if total and completed is not None and total > 0:
                progress = max(1, min(100, int((completed / total) * 100)))
            elif "verifying" in detail.lower():
                progress = max(progress, 95)
            elif "writing" in detail.lower():
                progress = max(progress, 97)
            else:
                progress = max(progress, 5)

            ollama_pull_registry.set(
                model_path,
                state="pulling",
                detail=detail,
                progress_percent=progress,
                total=total,
                completed=completed,
            )

            if cancel_event.is_set():
                ollama_pull_registry.set(model_path, state="cancelled", detail="Download abgebrochen", progress_percent=progress or None)
                return "cancelled", None, {"ollama_installed": False}

            if bool(chunk.get("done")):
                break

        installed = is_ollama_model_installed(model_name)
        if not installed:
            raise RuntimeError("Ollama meldet den Download als abgeschlossen, aber das Modell ist lokal noch nicht sichtbar.")

        ollama_pull_registry.set(model_path, state="completed", detail="Download abgeschlossen", progress_percent=100)
        metadata_patch["ollama_installed"] = True
        return "completed", None, metadata_patch
    except Exception as exc:
        if cancel_event.is_set():
            ollama_pull_registry.set(model_path, state="cancelled", detail="Download abgebrochen", progress_percent=progress or None)
            return "cancelled", None, {"ollama_installed": False}
        message = str(exc).strip() or "Download fehlgeschlagen"
        ollama_pull_registry.set(model_path, state="error", detail=message, progress_percent=None)
        return "error", message, None
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


async def _run_ollama_pull_task(*, model_id: int, model_path: str, model_name: str) -> None:
    state, error_message, metadata_patch = await asyncio.to_thread(
        _run_ollama_pull_sync,
        model_id=model_id,
        model_path=model_path,
        model_name=model_name,
    )
    if state == "completed":
        await _persist_ollama_install_state(model_id, installed=True, metadata_patch=metadata_patch)
        return

    if state == "cancelled":
        session_maker = get_session_maker()
        async with session_maker() as session:
            model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
            if model is None:
                return
            metadata = _parse_metadata(model.metadata_json)
            metadata["ollama_installed"] = False
            model.metadata_json = json.dumps(metadata)
            model.last_error = None
            model.load_status = "unloaded"
            await session.commit()
        return

    session_maker = get_session_maker()
    async with session_maker() as session:
        model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
        if model is None:
            return
        model.last_error = error_message
        model.load_status = "error"
        await session.commit()


@router.get("/capabilities")
async def model_capabilities() -> dict[str, object]:
    backends: list[dict[str, object]] = []
    for backend_name in list_supported_backends():
        try:
            backend = create_backend(backend_name)
            capabilities = backend.get_capabilities()
        except Exception:
            capabilities = {}

        backends.append(
            {
                "backend": backend_name,
                "capabilities": capabilities,
            }
        )

    active_capabilities: dict[str, object] | None = None
    if model_manager.active_backend is not None:
        try:
            active_capabilities = dict(model_manager.active_backend.get_capabilities())
        except Exception:
            active_capabilities = None

    return {
        "required_chat_capabilities": REQUIRED_CHAT_CAPABILITIES,
        "runtime": {
            "gpu_available": _gpu_available(),
        },
        "active": {
            "model_id": model_manager.active_model_id,
            "backend": model_manager.active_backend_name,
            "loaded": model_manager.active_backend is not None,
            "capabilities": active_capabilities,
        },
        "backends": backends,
    }


@router.post("/scan")
async def scan_models(session: AsyncSession = Depends(db_session_dependency)) -> dict[str, object]:
    settings_service = SettingsService(session)
    directories_raw = await settings_service.get("model", "base_directories")
    directories = normalize_base_directories(directories_raw)
    chatgpt_api_key_raw = await settings_service.get("integrations", "chatgpt_api_key", user_id=1)
    chatgpt_api_key = chatgpt_api_key_raw if isinstance(chatgpt_api_key_raw, str) else ""
    scanner = ModelScanner()
    registry = ModelRegistry()

    discovered = scanner.scan_directories(directories)
    discovered.extend(discover_ollama_models())
    discovered.extend(discover_openai_models(api_key=chatgpt_api_key))
    inserted = 0
    all_rows = cast(
        list[ModelConfig],
        (await session.execute(select(ModelConfig).order_by(ModelConfig.id.asc()))).scalars().all(),
    )
    all_rows = await _cleanup_legacy_model_rows(session=session, rows=all_rows)

    for item in discovered:
        valid, _ = registry.validate_entry(item, allowed_base_directories=directories)
        if not valid:
            continue

        existing_by_path_stmt = (
            select(ModelConfig)
            .where(ModelConfig.model_path == item["model_path"])
            .order_by(ModelConfig.id.asc())
            .limit(1)
        )
        existing = (await session.execute(existing_by_path_stmt)).scalar_one_or_none()

        if existing is None:
            existing_by_name_stmt = (
                select(ModelConfig)
                .where(ModelConfig.name == item["name"])
                .order_by(ModelConfig.id.asc())
                .limit(1)
            )
            existing = (await session.execute(existing_by_name_stmt)).scalar_one_or_none()

        if existing is None:
            existing = _find_related_existing_model(
                rows=all_rows,
                scanned_model_path=str(item["model_path"]),
            )
        if existing is None:
            metadata_payload = item.get("metadata", {})
            entity = ModelConfig(
                name=item["name"],
                model_path=item["model_path"],
                backend=item["backend"],
                model_format=item.get("model_format"),
                model_type=item.get("task_type"),
                metadata_json=json.dumps(metadata_payload),
                is_available=True,
                load_status="unloaded",
                last_scanned_at=datetime.now(timezone.utc),
            )
            session.add(entity)
            all_rows.append(entity)
            inserted += 1
        else:
            existing.name = str(item.get("name") or existing.name)
            existing.model_path = str(item.get("model_path") or existing.model_path)
            existing.is_available = True
            existing.backend = str(item.get("backend") or existing.backend)
            existing.model_format = str(item.get("model_format") or existing.model_format or "") or existing.model_format
            existing.model_type = str(item.get("task_type") or existing.model_type or "") or existing.model_type
            existing_metadata = _parse_metadata(existing.metadata_json)
            scanned_metadata = item.get("metadata", {})
            metadata_payload = _merged_scan_metadata(
                existing_metadata=existing_metadata,
                scanned_metadata=scanned_metadata,
            )
            existing.metadata_json = json.dumps(metadata_payload)
            existing.last_scanned_at = datetime.now(timezone.utc)

    await session.commit()

    return {"discovered": len(discovered), "inserted": inserted, "models": discovered}


@router.get("")
async def list_models(
    user_id: int | None = 1,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    rows = (await session.execute(select(ModelConfig).order_by(ModelConfig.id.asc()))).scalars().all()
    settings_service = SettingsService(session)
    relevance_flags_raw = await settings_service.get("model", "relevance_flags", user_id=user_id)
    relevance_flags = cast(dict[str, str], relevance_flags_raw if isinstance(relevance_flags_raw, dict) else {})
    loader_registry = ModelLoaderRegistry()
    chatgpt_api_key_raw = await settings_service.get("integrations", "chatgpt_api_key", user_id=user_id)
    chatgpt_api_key = resolve_openai_api_key(chatgpt_api_key_raw if isinstance(chatgpt_api_key_raw, str) else None)
    ollama_local_models = get_ollama_local_models_payload()
    ollama_installed_names = {
        _normalize_name
        for _normalize_name in (
            str(item.get("model") or item.get("name") or "").strip().lower()
            for item in ollama_local_models
        )
        if _normalize_name
    }
    items: list[dict[str, object]] = []

    for row in rows:
        metadata = _parse_metadata(row.metadata_json)
        if not metadata:
            inferred = infer_model_capabilities(name=row.name, model_path=Path(row.model_path))
            metadata = dict(inferred)

        model_format = str(metadata.get("model_format") or row.model_format or "unknown")
        task_type = str(metadata.get("task_type") or row.model_type or "text_generation")
        model_family = str(metadata.get("model_family") or "unknown")
        model_name, source_kind, pull_status = _ollama_pull_payload(metadata, row.model_path)
        openai_model_name, openai_source_kind = _openai_payload(metadata, row.model_path)
        ollama_installed = bool(metadata.get("ollama_installed"))
        if source_kind == "ollama_cloud" and model_name:
            ollama_installed = ollama_installed or model_name.lower() in ollama_installed_names
            metadata["ollama_installed"] = ollama_installed

        loader = loader_registry.resolve(model_format=model_format, task_type=task_type)
        loader_id = loader.loader_id if loader is not None else None
        loader_available = bool(loader.available) if loader is not None else False
        reason_unavailable = loader.reason_unavailable if loader is not None else "Kein kompatibler Loader registriert."

        if model_format == "openai":
            loader_available = bool(chatgpt_api_key)
            reason_unavailable = None if chatgpt_api_key else "ChatGPT/OpenAI API-Key fehlt in den Integrationen."

        custom_code_reason = _custom_code_gate(metadata)
        if custom_code_reason is not None:
            loader_available = False
            reason_unavailable = custom_code_reason

        if source_kind == "ollama_cloud" and not ollama_installed:
            loader_available = False
            reason_unavailable = "Noch nicht lokal heruntergeladen. Bitte zuerst herunterladen."

        if openai_source_kind == "remote" and openai_model_name and not chatgpt_api_key:
            loader_available = False
            reason_unavailable = "ChatGPT/OpenAI API-Key fehlt in den Integrationen."

        if pull_status is not None and str(pull_status.get("state") or "") in ACTIVE_PULL_STATES:
            loader_available = False
            reason_unavailable = str(pull_status.get("detail") or "Download laeuft")
        elif pull_status is not None and str(pull_status.get("state") or "") == "cancelled" and not ollama_installed:
            loader_available = False
            reason_unavailable = "Download abgebrochen. Erneut herunterladen, um das Modell zu aktivieren."
        elif pull_status is not None and str(pull_status.get("state") or "") == "error" and not ollama_installed:
            loader_available = False
            reason_unavailable = str(pull_status.get("detail") or "Download fehlgeschlagen. Bitte erneut versuchen.")

        loadable = loader_available
        user_flag = relevance_flags.get(str(row.id))
        relevance = _relevance_for_row(is_active=row.is_active, loadable=loadable, user_flag=user_flag)
        status_label, status_color = _status_for_row(
            is_active=row.is_active,
            load_status=row.load_status,
            relevance=relevance,
            reason_unavailable=reason_unavailable if not loadable else None,
            loader_found=loader is not None,
        )

        group = str(metadata.get("group") or "Hilfsmodelle")
        source_kind, source_label = _source_for_row(row, metadata)
        context_length = metadata.get("context_length")
        items.append(
            {
                "id": row.id,
                "name": row.name,
                "model_path": row.model_path,
                "backend": row.backend,
                "load_status": row.load_status,
                "is_active": row.is_active,
            "source_kind": source_kind,
            "source_label": source_label,
                "model_format": model_format,
                "model_family": model_family,
                "task_type": task_type,
                "group": group,
                "ollama_installed": ollama_installed,
                "ollama_capabilities": metadata.get("ollama_capabilities") if isinstance(metadata.get("ollama_capabilities"), list) else [],
                "tool_calling": _as_bool(metadata.get("tool_calling")),
                "structured_output": _as_bool(metadata.get("structured_output")),
                "reasoning": _as_bool(metadata.get("reasoning")),
                "parameter_size": str(metadata.get("parameter_size") or "") or None,
                "quantization_level": str(metadata.get("quantization_level") or "") or None,
                "context_length": context_length if isinstance(context_length, int) else None,
                "pull_status": pull_status,
                "loader": loader_id,
                "relevance": relevance,
                "relevance_flag": user_flag,
                "status_label": status_label,
                "status_color": status_color,
                "reason_unavailable": None if loadable else reason_unavailable,
                "requires_custom_code": _as_bool(metadata.get("requires_custom_code")),
                "custom_code_trusted": _as_bool(metadata.get("custom_code_trusted")),
                "custom_loader_id": str(metadata.get("custom_loader_id") or "") or None,
                "capabilities": {
                    "supports_inference": loadable,
                    "supports_training": _as_bool(metadata.get("supports_training")),
                    "supports_peft_training": _as_bool(metadata.get("supports_peft_training")),
                    "supports_4bit": _as_bool(metadata.get("supports_4bit")),
                    "supports_chat": _as_bool(metadata.get("supports_chat")),
                    "supports_embeddings": _as_bool(metadata.get("supports_embeddings")),
                    "supports_reranking": _as_bool(metadata.get("supports_reranking")),
                    "supports_vision": _as_bool(metadata.get("supports_vision")),
                    "supports_audio": _as_bool(metadata.get("supports_audio")),
                },
            }
        )

    items.sort(
        key=lambda item: (
            GROUP_ORDER.get(str(item.get("group") or ""), 99),
            RELEVANCE_ORDER.get(str(item.get("relevance") or "relevant"), 9),
            str(item.get("name") or "").lower(),
        )
    )
    return {"items": items}


@router.post("/{model_id}/relevance")
async def set_model_relevance(
    model_id: int,
    payload: ModelRelevanceUpdateRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if model is None:
        raise api_http_error(status_code=404, code="model.not_found", message="Model not found")

    settings_service = SettingsService(session)
    current_raw = await settings_service.get("model", "relevance_flags", user_id=payload.user_id)
    current_map = cast(dict[str, str], current_raw if isinstance(current_raw, dict) else {})
    updated_map = dict(current_map)

    normalized = payload.relevance.strip().lower() if isinstance(payload.relevance, str) else None
    if normalized in {"favorite", "irrelevant"}:
        updated_map[str(model_id)] = normalized
    else:
        updated_map.pop(str(model_id), None)

    await settings_service.update("model", "relevance_flags", updated_map, user_id=payload.user_id)
    await session.commit()
    return {
        "updated": True,
        "model_id": model_id,
        "relevance": updated_map.get(str(model_id)),
    }


@router.post("/{model_id}/activate")
async def activate_model(model_id: int, session: AsyncSession = Depends(db_session_dependency)) -> dict[str, object]:
    settings_service = SettingsService(session)
    directories_raw = await settings_service.get("model", "base_directories")
    directories = normalize_base_directories(directories_raw)
    chatgpt_api_key_raw = await settings_service.get("integrations", "chatgpt_api_key", user_id=1)
    chatgpt_api_key = resolve_openai_api_key(chatgpt_api_key_raw if isinstance(chatgpt_api_key_raw, str) else None)

    model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if model is None:
        raise api_http_error(status_code=404, code="model.not_found", message="Model not found")

    metadata = _parse_metadata(model.metadata_json)
    if not metadata:
        metadata = dict(infer_model_capabilities(name=model.name, model_path=Path(model.model_path)))

    _, source_kind, pull_status = _ollama_pull_payload(metadata, model.model_path)
    if source_kind == "ollama_cloud" and pull_status is not None and str(pull_status.get("state") or "") in ACTIVE_PULL_STATES:
        raise api_http_error(
            status_code=409,
            code="model.pull_in_progress",
            message=str(pull_status.get("detail") or "Ollama-Download laeuft noch."),
            details={"model_id": model.id, "pull_status": pull_status},
        )

    model_format = str(metadata.get("model_format") or model.model_format or "unknown")
    task_type = str(metadata.get("task_type") or model.model_type or "text_generation")

    loader_registry = ModelLoaderRegistry()
    loader = loader_registry.resolve(model_format=model_format, task_type=task_type)
    if loader is None:
        raise api_http_error(
            status_code=409,
            code="model.loader_not_found",
            message="No compatible loader registered for this model",
            details={"model_id": model.id, "model_format": model_format, "task_type": task_type},
        )
    if model_format == "openai" and not chatgpt_api_key:
        raise api_http_error(
            status_code=409,
            code="model.api_key_missing",
            message="ChatGPT/OpenAI API-Key fehlt in den Integrationen.",
            details={"model_id": model.id, "loader_id": loader.loader_id, "model_format": model_format, "task_type": task_type},
        )
    if model_format != "openai" and not loader.available:
        raise api_http_error(
            status_code=409,
            code="model.loader_unavailable",
            message=loader.reason_unavailable or "Required runtime dependencies are missing",
            details={
                "model_id": model.id,
                "loader_id": loader.loader_id,
                "model_format": model_format,
                "task_type": task_type,
            },
        )

    custom_code_reason = _custom_code_gate(metadata)
    if custom_code_reason is not None:
        raise api_http_error(
            status_code=409,
            code="model.custom_code_not_trusted",
            message=custom_code_reason,
            details={"model_id": model.id},
        )

    path_valid, path_reason = validate_runtime_model_paths(
        model_path=model.model_path,
        model_format=str(metadata.get("model_format") or model.model_format or ""),
        metadata=metadata,
        allowed_base_directories=directories,
    )
    if not path_valid:
        raise api_http_error(
            status_code=400,
            code="model.invalid_path",
            message="Model path is invalid or outside allowed base directories",
            details={"model_id": model.id, "reason": path_reason},
        )

    previous_active_id = model_manager.active_model_id
    previous_model: ModelConfig | None = None
    if previous_active_id is not None:
        previous_model = (await session.execute(select(ModelConfig).where(ModelConfig.id == previous_active_id))).scalar_one_or_none()

    model.load_status = "loading"
    model.last_error = None
    await session.flush()

    runtime_config: dict[str, object] = {"metadata": metadata}
    if model.backend == "openai":
        if not chatgpt_api_key:
            raise api_http_error(
                status_code=409,
                code="model.api_key_missing",
                message="ChatGPT/OpenAI API-Key fehlt in den Integrationen.",
                details={"model_id": model.id},
            )
        runtime_config["api_key"] = chatgpt_api_key

    try:
        await model_manager.load_model(
            model_id=model.id,
            model_path=model.model_path,
            backend_name=model.backend,
            config=runtime_config,
        )
        if not check_backend_health(model_manager.active_backend):
            raise RuntimeError("health_check_failed")
    except Exception as exc:
        rollback_restored = False
        rollback_error: str | None = None

        if previous_model is not None:
            try:
                await model_manager.load_model(
                    model_id=previous_model.id,
                    model_path=previous_model.model_path,
                    backend_name=previous_model.backend,
                    config={"metadata": _parse_metadata(previous_model.metadata_json)},
                )
                rollback_restored = check_backend_health(model_manager.active_backend)
            except Exception as restore_exc:
                rollback_error = str(restore_exc)
                rollback_restored = False

        all_models = (await session.execute(select(ModelConfig))).scalars().all()
        active_id = model_manager.active_model_id if rollback_restored else None
        for row in all_models:
            row.is_active = active_id is not None and row.id == active_id
            row.load_status = "ready" if row.is_active else "unloaded"
            if row.id == model.id:
                row.load_status = "error"
                row.last_error = str(exc)
            elif row.is_active:
                row.last_error = None

        await session.commit()

        root_cause = str(exc).strip() or "unknown_error"
        detail = f"Model activation failed: {root_cause}"
        if rollback_restored and active_id is not None:
            detail = f"Model activation failed: {root_cause}; rolled back to model {active_id}"
        elif rollback_error:
            detail = f"Model activation failed: {root_cause}; rollback failed: {rollback_error}"

        raise HTTPException(status_code=409, detail=detail) from exc

    all_models = (await session.execute(select(ModelConfig))).scalars().all()
    for row in all_models:
        row.is_active = row.id == model.id
        row.load_status = "ready" if row.id == model.id else "unloaded"
        if row.id == model.id:
            row.last_loaded_at = datetime.now(timezone.utc)
            row.last_error = None

    await settings_service.update("model", "active_model_id", model.id)

    await session.commit()
    return {"updated": True, "active_model_id": model_manager.active_model_id}


@router.post("/deactivate")
async def deactivate_model(session: AsyncSession = Depends(db_session_dependency)) -> dict[str, object]:
    settings_service = SettingsService(session)
    await model_manager.unload()
    rows = (await session.execute(select(ModelConfig))).scalars().all()
    for row in rows:
        row.is_active = False
        row.load_status = "unloaded"
    await settings_service.update("model", "active_model_id", None)
    await session.commit()
    return {"updated": True}


@router.post("/{model_id}/pull")
async def pull_ollama_model(model_id: int, session: AsyncSession = Depends(db_session_dependency)) -> dict[str, object]:
    model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if model is None:
        raise api_http_error(status_code=404, code="model.not_found", message="Model not found")

    metadata = _parse_metadata(model.metadata_json)
    if str(metadata.get("backend") or model.backend) != "ollama":
        raise api_http_error(status_code=400, code="model.not_ollama", message="Model is not an Ollama model")

    model_name, source_kind = parse_ollama_model_ref(model.model_path, metadata)
    if source_kind != "ollama_cloud":
        raise api_http_error(status_code=400, code="model.pull_not_supported", message="Nur Ollama-Cloud-Modelle koennen heruntergeladen werden.")

    if is_ollama_model_installed(model_name):
        metadata["ollama_installed"] = True
        model.metadata_json = json.dumps(metadata)
        model.last_error = None
        await session.commit()
        ollama_pull_registry.set(model.model_path, state="completed", detail="Modell ist bereits lokal verfuegbar", progress_percent=100)
        return {"started": False, "state": "completed", "detail": "Modell ist bereits lokal verfuegbar"}

    if ollama_pull_registry.is_active(model.model_path):
        status = ollama_pull_registry.get(model.model_path)
        return {"started": False, "state": status.state if status is not None else "queued", "detail": status.detail if status is not None else None}

    existing_status = ollama_pull_registry.get(model.model_path)
    if existing_status is not None and existing_status.state in TERMINAL_PULL_STATES:
        ollama_pull_registry.clear(model.model_path)

    model.load_status = "loading"
    model.last_error = None
    await session.commit()
    ollama_pull_registry.set(model.model_path, state="queued", detail="Download wird vorbereitet", progress_percent=0)
    asyncio.create_task(_run_ollama_pull_task(model_id=model.id, model_path=model.model_path, model_name=model_name))
    return {"started": True, "state": "queued", "detail": "Download wird vorbereitet"}


@router.post("/{model_id}/pull/cancel")
async def cancel_ollama_model_pull(model_id: int, session: AsyncSession = Depends(db_session_dependency)) -> dict[str, object]:
    model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if model is None:
        raise api_http_error(status_code=404, code="model.not_found", message="Model not found")

    metadata = _parse_metadata(model.metadata_json)
    if str(metadata.get("backend") or model.backend) != "ollama":
        raise api_http_error(status_code=400, code="model.not_ollama", message="Model is not an Ollama model")

    _, source_kind = parse_ollama_model_ref(model.model_path, metadata)
    if source_kind != "ollama_cloud":
        raise api_http_error(status_code=400, code="model.pull_not_supported", message="Nur Ollama-Cloud-Downloads koennen abgebrochen werden.")

    status = ollama_pull_registry.request_cancel(model.model_path)
    if status is None:
        current = ollama_pull_registry.get(model.model_path)
        return {
            "cancelled": False,
            "state": current.state if current is not None else "idle",
            "detail": current.detail if current is not None else "Kein aktiver Download gefunden",
        }

    model.load_status = "unloaded"
    model.last_error = None
    await session.commit()
    return {
        "cancelled": True,
        "state": status.state,
        "detail": status.detail,
    }


@router.post("/{model_id}/trust-custom-code")
async def update_custom_code_trust(
    model_id: int,
    payload: CustomCodeTrustUpdateRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, object]:
    model = (await session.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if model is None:
        raise api_http_error(status_code=404, code="model.not_found", message="Model not found")

    metadata = _parse_metadata(model.metadata_json)
    if not metadata:
        metadata = dict(infer_model_capabilities(name=model.name, model_path=Path(model.model_path)))

    if not _as_bool(metadata.get("requires_custom_code")):
        raise api_http_error(
            status_code=400,
            code="model.not_custom_code",
            message="This model does not require custom code trust.",
            details={"model_id": model.id},
        )

    metadata["custom_code_trusted"] = bool(payload.trusted)
    model.metadata_json = json.dumps(metadata)
    await session.commit()

    return {
        "updated": True,
        "model_id": model.id,
        "custom_code_trusted": bool(metadata.get("custom_code_trusted")),
    }
