from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import base64
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Header
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.core.auth_token import verify_access_token
from app.database.repositories.plugin_confirmation_repository import PluginConfirmationRepository
from app.database.repositories.plugin_idempotency_repository import PluginIdempotencyRepository
from app.database.repositories.user_repository import UserRepository
from app.settings.service import SettingsService
from app.tools import PluginExecutionError, PluginExecutor
from app.tools.execution_policy import PluginExecutionPolicy, PluginPolicyError
from plugins.business_letter.services.artifacts import DEFAULT_PERSISTENCE

router = APIRouter(prefix="/api/plugins", tags=["plugins"])
IDEMPOTENCY_LEASE_SECONDS = 120


class PluginExecutionContextPayload(BaseModel):
    user_id: int | None = None
    team_id: int | None = None
    dry_run: bool = False
    confirmed: bool = False
    confirmation_id: str | None = None
    idempotency_key: str | None = None
    request_id: str | None = None
    granted_permissions: list[str] = Field(default_factory=list)
    allowed_plugins: list[str] = Field(default_factory=list)
    enforce_permissions: bool = False


class PluginExecuteRequest(PluginExecutionContextPayload):
    plugin_id: str = Field(min_length=1)
    plugin_input: dict[str, Any] = Field(default_factory=dict)
    plugin_settings: dict[str, Any] = Field(default_factory=dict)


class PluginMarkupExecuteRequest(BaseModel):
    assistant_output: str = Field(min_length=1)


class PluginFunctionExecuteRequest(PluginExecutionContextPayload):
    plugin_id: str = Field(min_length=1)
    function_name: str = Field(min_length=1)
    function_input: dict[str, Any] = Field(default_factory=dict)
    plugin_settings: dict[str, Any] = Field(default_factory=dict)


class PluginConfirmationDecisionRequest(BaseModel):
    user_id: int
    team_id: int | None = None
    request_id: str | None = None
    granted_permissions: list[str] = Field(default_factory=list)
    allowed_plugins: list[str] = Field(default_factory=list)
    enforce_permissions: bool = False


def _canonical_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_tenant_scope(tenant_id: str) -> tuple[str, str]:
    normalized = str(tenant_id or "").strip()
    if normalized == "shared":
        return ("shared", "")
    if ":" in normalized:
        scope, value = normalized.split(":", 1)
        return (scope.strip().lower(), value.strip())
    return ("unknown", normalized)


def _enforce_artifact_tenant_access(*, requester_user_id: int, requester: object, tenant_id: str) -> None:
    scope_kind, scope_value = _parse_tenant_scope(tenant_id)
    requester_is_admin = bool(getattr(requester, "is_admin", False))

    if scope_kind == "shared":
        return
    if scope_kind == "user":
        if requester_is_admin:
            return
        if scope_value.isdigit() and int(scope_value) == int(requester_user_id):
            return
        raise HTTPException(status_code=403, detail="Artifact access denied")
    if scope_kind == "team":
        if requester_is_admin:
            return
        raise HTTPException(status_code=403, detail="Team-scoped artifact access currently requires admin approval")

    if requester_is_admin:
        return
    raise HTTPException(status_code=403, detail="Artifact access denied")


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    token = authorization[len(prefix):].strip()
    return token or None


async def _require_authenticated_user(session: AsyncSession, authorization: str | None) -> tuple[int, object]:
    token = _extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Token user not found")
    if not bool(getattr(user, "is_active", False)):
        raise HTTPException(status_code=403, detail="User is disabled")
    return user_id, user


def _build_execution_context(payload: PluginExecutionContextPayload) -> dict[str, Any]:
    return {
        "user_id": payload.user_id,
        "team_id": payload.team_id,
        "dry_run": payload.dry_run,
        "confirmed": payload.confirmed,
        "confirmation_id": payload.confirmation_id,
        "idempotency_key": payload.idempotency_key,
        "request_id": payload.request_id,
        "granted_permissions": payload.granted_permissions,
        "allowed_plugins": payload.allowed_plugins,
        "enforce_permissions": payload.enforce_permissions,
    }


async def _load_integration_keys(
    settings_service: SettingsService,
    *,
    user_id: int,
    keys: list[str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in keys:
        value = await settings_service.get(
            category="integrations",
            key=key,
            user_id=user_id,
        )
        if isinstance(value, (str, bool, int, float, dict)):
            payload[key] = value
    return payload


async def _load_merged_plugin_settings(
    *,
    session: AsyncSession,
    plugin_id: str,
    plugin_settings: dict[str, Any],
    user_id: int | None,
) -> dict[str, Any]:
    persisted_settings: dict[str, Any] = {}
    integration_settings: dict[str, Any] = {}

    if user_id is not None:
        settings_service = SettingsService(session)
        raw = await settings_service.get(
            category="plugins",
            key=f"{plugin_id}_profile",
            user_id=user_id,
        )
        if isinstance(raw, dict):
            persisted_settings = raw

        integration_map: dict[str, list[str]] = {
            "weather": [
                "openweather_api_key",
                "weatherapi_api_key",
                "tomorrowio_api_key",
            ],
            "websearch": [
                "exa_api_key",
                "brave_search_api_key",
                "bing_search_api_key",
            ],
            "bing_search": [
                "bing_search_api_key",
            ],
        }
        keys = integration_map.get(plugin_id, [])
        if keys:
            integration_settings = await _load_integration_keys(
                settings_service,
                user_id=user_id,
                keys=keys,
            )

    merged_settings = {**persisted_settings, **plugin_settings}
    if integration_settings:
        existing_integrations = merged_settings.get("integrations")
        existing_integrations_map = existing_integrations if isinstance(existing_integrations, dict) else {}
        merged_settings["integrations"] = {
            **integration_settings,
            **existing_integrations_map,
        }

    return merged_settings


def _is_confirmation_required(function_meta: dict[str, Any], context: dict[str, Any]) -> bool:
    if bool(context.get("dry_run", False)):
        return False
    if bool(context.get("confirmed", False)):
        return False
    return bool(function_meta.get("requires_confirmation", False))


async def _maybe_create_pending_confirmation(
    *,
    session: AsyncSession,
    executor: PluginExecutor,
    policy: PluginExecutionPolicy,
    route_kind: str,
    plugin_id: str,
    function_name: str,
    function_meta: dict[str, Any],
    input_data: dict[str, Any],
    plugin_settings: dict[str, Any],
    execution_context: dict[str, Any],
    definition: Any,
) -> dict[str, Any] | None:
    if not _is_confirmation_required(function_meta, execution_context):
        return None

    user_id = execution_context.get("user_id")
    if user_id is None:
        raise PluginExecutionError(
            "plugin_confirmation_user_required",
            "Confirmation flow requires a user_id in execution_context.",
        )

    preflight_context = dict(execution_context)
    preflight_context["confirmed"] = True
    try:
        policy.validate(
            definition=definition,
            function_meta=function_meta,
            input_data=input_data,
            plugin_settings=plugin_settings,
            execution_context=preflight_context,
        )
    except PluginPolicyError as exc:
        raise PluginExecutionError(exc.code, exc.message) from exc

    confirmation_id = f"conf_{uuid4().hex[:24]}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    context_payload = dict(execution_context)
    context_payload["confirmed"] = False

    repo = PluginConfirmationRepository(session)
    await repo.create_pending(
        confirmation_id=confirmation_id,
        user_id=int(user_id),
        team_id=execution_context.get("team_id"),
        plugin_id=plugin_id,
        function_name=function_name,
        route_kind=route_kind,
        arguments_json=input_data,
        arguments_hash=_canonical_hash(input_data),
        plugin_settings_json=plugin_settings,
        execution_context_json=context_payload,
        idempotency_key=str(execution_context.get("idempotency_key") or "").strip() or None,
        expires_at=expires_at,
    )

    await session.commit()
    return {
        "status": "pending_confirmation",
        "plugin_id": plugin_id,
        "function_name": function_name,
        "confirmation": {
            "confirmation_id": confirmation_id,
            "user_id": int(user_id),
            "team_id": execution_context.get("team_id"),
            "plugin_id": plugin_id,
            "function_name": function_name,
            "arguments": input_data,
            "arguments_hash": _canonical_hash(input_data),
            "idempotency_key": str(execution_context.get("idempotency_key") or "").strip() or None,
            "status": "pending",
            "expires_at": expires_at.isoformat(),
        },
    }


async def _execute_with_idempotency(
    *,
    session: AsyncSession,
    plugin_id: str,
    function_name: str,
    input_data: dict[str, Any],
    execution_context: dict[str, Any],
    execute_call: Any,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    idempotency_key = str(execution_context.get("idempotency_key") or "").strip()
    if not idempotency_key or bool(execution_context.get("dry_run", False)):
        return await execute_call(), None

    repository = PluginIdempotencyRepository(session)
    user_id = execution_context.get("user_id")
    team_id = execution_context.get("team_id")
    user_scope = repository.user_scope(user_id if isinstance(user_id, int) else None)
    team_scope = repository.team_scope(team_id if isinstance(team_id, int) else None)
    arguments_hash = _canonical_hash(input_data)
    lease_expires_at = _utc_now() + timedelta(seconds=IDEMPOTENCY_LEASE_SECONDS)

    record = await repository.get_record(
        plugin_id=plugin_id,
        function_name=function_name,
        user_scope=user_scope,
        team_scope=team_scope,
        idempotency_key=idempotency_key,
    )

    if record is not None:
        if record.arguments_hash != arguments_hash:
            raise PluginExecutionError(
                "plugin_idempotency_conflict",
                "Idempotency key was already used with different input.",
            )
        status = str(record.status or "").strip().lower()
        if status == "completed" and isinstance(record.response_json, dict):
            return dict(record.response_json), {"status": "replayed", "key": idempotency_key}
        if status == "in_progress":
            active_lease = _as_aware_utc(record.lease_expires_at)
            if active_lease is not None and active_lease > _utc_now():
                raise PluginExecutionError(
                    "plugin_idempotency_in_progress",
                    "Execution with the same idempotency key is currently in progress.",
                )
        await repository.mark_in_progress(
            record,
            arguments_hash=arguments_hash,
            lease_expires_at=lease_expires_at,
        )
    else:
        try:
            async with session.begin_nested():
                record = await repository.create_in_progress(
                    plugin_id=plugin_id,
                    function_name=function_name,
                    user_id=user_id if isinstance(user_id, int) else None,
                    team_id=team_id if isinstance(team_id, int) else None,
                    user_scope=user_scope,
                    team_scope=team_scope,
                    idempotency_key=idempotency_key,
                    arguments_hash=arguments_hash,
                    lease_expires_at=lease_expires_at,
                )
        except IntegrityError:
            record = await repository.get_record(
                plugin_id=plugin_id,
                function_name=function_name,
                user_scope=user_scope,
                team_scope=team_scope,
                idempotency_key=idempotency_key,
            )
            if record is None:
                raise PluginExecutionError(
                    "plugin_idempotency_reservation_failed",
                    "Could not reserve idempotency key.",
                )
            if record.arguments_hash != arguments_hash:
                raise PluginExecutionError(
                    "plugin_idempotency_conflict",
                    "Idempotency key was already used with different input.",
                )
            status = str(record.status or "").strip().lower()
            if status == "completed" and isinstance(record.response_json, dict):
                return dict(record.response_json), {"status": "replayed", "key": idempotency_key}
            if status == "in_progress":
                active_lease = _as_aware_utc(record.lease_expires_at)
                if active_lease is not None and active_lease > _utc_now():
                    raise PluginExecutionError(
                        "plugin_idempotency_in_progress",
                        "Execution with the same idempotency key is currently in progress.",
                    )
            await repository.mark_in_progress(
                record,
                arguments_hash=arguments_hash,
                lease_expires_at=lease_expires_at,
            )

    try:
        result = await execute_call()
    except PluginExecutionError as exc:
        await repository.mark_failed(record, code=exc.code, message=exc.message)
        raise
    except Exception as exc:  # pragma: no cover - safety net
        await repository.mark_failed(record, code="plugin_execution_failed", message=str(exc))
        raise

    await repository.mark_completed(record, response_json=result)
    return result, {"status": "completed", "key": idempotency_key}


def _ensure_pending_for_user(item: Any, user_id: int) -> None:
    if int(item.user_id) != int(user_id):
        raise HTTPException(
            status_code=403,
            detail={"code": "plugin_confirmation_forbidden", "message": "Confirmation does not belong to this user."},
        )


def _ensure_team_binding(item: Any, team_id: int | None) -> None:
    stored_team = item.team_id
    if stored_team is None and team_id is None:
        return
    if stored_team is None and team_id is not None:
        raise HTTPException(
            status_code=403,
            detail={"code": "plugin_confirmation_team_mismatch", "message": "Confirmation team mismatch."},
        )
    if stored_team is not None and team_id is None:
        raise HTTPException(
            status_code=403,
            detail={"code": "plugin_confirmation_team_mismatch", "message": "Confirmation team mismatch."},
        )
    if int(stored_team) != int(team_id):
        raise HTTPException(
            status_code=403,
            detail={"code": "plugin_confirmation_team_mismatch", "message": "Confirmation team mismatch."},
        )


async def _get_pending_confirmation_or_raise(
    *,
    session: AsyncSession,
    confirmation_id: str,
    user_id: int,
    team_id: int | None,
) -> Any:
    repo = PluginConfirmationRepository(session)
    item = await repo.get_by_confirmation_id(confirmation_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "plugin_confirmation_not_found", "message": f"Unknown confirmation: {confirmation_id}"},
        )

    _ensure_pending_for_user(item, user_id)
    _ensure_team_binding(item, team_id)

    status = str(item.status or "").strip().lower()
    if status != "pending":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "plugin_confirmation_not_pending",
                "message": f"Confirmation is not pending (status={status}).",
            },
        )

    now = _utc_now()
    expires_at = item.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        await repo.mark_expired(item)
        await session.commit()
        raise HTTPException(
            status_code=409,
            detail={"code": "plugin_confirmation_expired", "message": "Confirmation has expired."},
        )

    return item


@router.get("")
async def list_plugins() -> dict[str, Any]:
    executor = PluginExecutor()
    plugins = executor.list_plugins()
    items: list[dict[str, Any]] = []
    for item in plugins:
        items.append(
            {
                "id": item.plugin_id,
                "name": item.name,
                "description": item.description,
                "category": item.category,
                "status": item.status,
                "api_key_required": item.api_key_required,
                "intent_pattern": item.intent_pattern,
                "settings_fields": item.settings_fields,
                "plugin_frontend": item.plugin_frontend,
                "input_schema": item.input_schema,
                "output_schema": item.output_schema,
            }
        )

    return {"items": items}


@router.get("/capabilities")
async def list_capabilities(query: str | None = None, limit: int = 3) -> dict[str, Any]:
    executor = PluginExecutor()
    if isinstance(query, str) and query.strip():
        return {
            "query": query,
            "items": executor.search_plugins(query.strip(), limit=limit),
        }
    return {"items": executor.list_capabilities()}


@router.get("/{plugin_id}/manifest")
async def describe_plugin(plugin_id: str) -> dict[str, Any]:
    executor = PluginExecutor()
    manifest = executor.describe_plugin(plugin_id)
    if manifest is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "plugin_not_found", "message": f"Unknown plugin: {plugin_id}"},
        )
    return manifest


@router.get("/{plugin_id}/functions/{function_name}")
async def describe_plugin_function(plugin_id: str, function_name: str) -> dict[str, Any]:
    executor = PluginExecutor()
    function = executor.describe_function(plugin_id, function_name)
    if function is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "plugin_function_not_found",
                "message": f"Unknown function '{function_name}' for plugin: {plugin_id}",
            },
        )
    return function


@router.get("/business-letter/documents/{document_id}/artifacts/{artifact_kind}")
async def download_business_letter_artifact(
    document_id: str,
    artifact_kind: str,
    tenant_id: str | None = None,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(db_session_dependency),
) -> Response:
    requester_user_id, requester = await _require_authenticated_user(session, authorization)
    resolved_tenant_id = tenant_id.strip() if isinstance(tenant_id, str) and tenant_id.strip() else f"user:{requester_user_id}"
    _enforce_artifact_tenant_access(requester_user_id=requester_user_id, requester=requester, tenant_id=resolved_tenant_id)
    item = DEFAULT_PERSISTENCE.get_artifact_by_document_and_kind(
        tenant_id=resolved_tenant_id,
        document_id=document_id,
        artifact_kind=artifact_kind,
    )
    if item is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "business_letter_artifact_not_found", "message": "Artifact not found."},
        )

    payload_text = str(item.get("payload_text") or "")
    if not payload_text:
        raise HTTPException(
            status_code=404,
            detail={"code": "business_letter_artifact_payload_missing", "message": "Artifact payload is missing."},
        )

    mime_type = str(item.get("mime_type") or "application/octet-stream").strip() or "application/octet-stream"
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    artifact_meta = metadata.get("artifact") if isinstance(metadata.get("artifact"), dict) else {}
    file_name = str(
        artifact_meta.get("file_name")
        or item.get("storage_key")
        or f"{document_id}.{artifact_kind}"
    ).strip().split("/")[-1]

    content: bytes
    if str(item.get("artifact_kind") or "").strip().lower() == "pdf":
        try:
            content = base64.b64decode(payload_text.encode("ascii"), validate=True)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={"code": "business_letter_artifact_invalid_payload", "message": "Artifact payload is invalid."},
            ) from exc
    else:
        content = payload_text.encode("utf-8")

    DEFAULT_PERSISTENCE.record_document_event(
        tenant_id=resolved_tenant_id,
        document_id=document_id,
        document_number=str(item.get("document_number") or "").strip(),
        event_type="artifact_downloaded",
        event_payload={
            "artifact_id": str(item.get("artifact_id") or "").strip(),
            "artifact_kind": str(item.get("artifact_kind") or artifact_kind).strip(),
            "storage_key": str(item.get("storage_key") or "").strip(),
            "mime_type": mime_type,
            "actor_user_id": requester_user_id,
            "tenant_scope": resolved_tenant_id,
        },
        created_by=f"user:{requester_user_id}",
    )

    headers = {"Content-Disposition": f'inline; filename="{file_name}"'}
    return Response(content=content, media_type=mime_type, headers=headers)


@router.post("/execute")
async def execute_plugin(
    payload: PluginExecuteRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    executor = PluginExecutor()
    policy = PluginExecutionPolicy()
    try:
        merged_settings = await _load_merged_plugin_settings(
            session=session,
            plugin_id=payload.plugin_id,
            plugin_settings=payload.plugin_settings,
            user_id=payload.user_id,
        )
        execution_context = _build_execution_context(payload)

        definition, function_meta, normalized_input, resolved_function_name = executor.resolve_execution_target(
            payload.plugin_id,
            payload.plugin_input,
        )

        pending = await _maybe_create_pending_confirmation(
            session=session,
            executor=executor,
            policy=policy,
            route_kind="execute",
            plugin_id=payload.plugin_id,
            function_name=resolved_function_name,
            function_meta=function_meta,
            input_data=normalized_input,
            plugin_settings=merged_settings,
            execution_context=execution_context,
            definition=definition,
        )
        if pending is not None:
            return pending

        plugin_response, idempotency_meta = await _execute_with_idempotency(
            session=session,
            plugin_id=payload.plugin_id,
            function_name=resolved_function_name,
            input_data=normalized_input,
            execution_context=execution_context,
            execute_call=lambda: executor.execute(
                payload.plugin_id,
                normalized_input,
                merged_settings,
                execution_context=execution_context,
            ),
        )
        await session.commit()
    except PluginExecutionError as exc:
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc
    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail={"code": "plugin_execution_failed", "message": str(exc)},
        ) from exc

    return {
        "plugin_id": payload.plugin_id,
        "plugin_input": normalized_input,
        "plugin_settings": merged_settings,
        "plugin_response": plugin_response,
        "idempotency": idempotency_meta,
    }


@router.post("/execute-function")
async def execute_plugin_function(
    payload: PluginFunctionExecuteRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    executor = PluginExecutor()
    policy = PluginExecutionPolicy()
    try:
        merged_settings = await _load_merged_plugin_settings(
            session=session,
            plugin_id=payload.plugin_id,
            plugin_settings=payload.plugin_settings,
            user_id=payload.user_id,
        )
        execution_context = _build_execution_context(payload)

        definition, function_meta, normalized_input, resolved_function_name = executor.resolve_execution_target(
            payload.plugin_id,
            payload.function_input,
            function_name=payload.function_name,
        )

        pending = await _maybe_create_pending_confirmation(
            session=session,
            executor=executor,
            policy=policy,
            route_kind="execute_function",
            plugin_id=payload.plugin_id,
            function_name=resolved_function_name,
            function_meta=function_meta,
            input_data=normalized_input,
            plugin_settings=merged_settings,
            execution_context=execution_context,
            definition=definition,
        )
        if pending is not None:
            return pending

        plugin_response, idempotency_meta = await _execute_with_idempotency(
            session=session,
            plugin_id=payload.plugin_id,
            function_name=resolved_function_name,
            input_data=normalized_input,
            execution_context=execution_context,
            execute_call=lambda: executor.execute_function(
                payload.plugin_id,
                resolved_function_name,
                normalized_input,
                merged_settings,
                execution_context=execution_context,
            ),
        )
        await session.commit()
    except PluginExecutionError as exc:
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc
    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail={"code": "plugin_function_execution_failed", "message": str(exc)},
        ) from exc

    return {
        "plugin_id": payload.plugin_id,
        "function_name": resolved_function_name,
        "function_input": normalized_input,
        "plugin_settings": merged_settings,
        "plugin_response": plugin_response,
        "idempotency": idempotency_meta,
    }


@router.post("/confirmations/{confirmation_id}/confirm")
async def confirm_plugin_execution(
    confirmation_id: str,
    payload: PluginConfirmationDecisionRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    executor = PluginExecutor()
    repo = PluginConfirmationRepository(session)
    now = _utc_now()
    item = await repo.claim_pending_for_execution(
        confirmation_id=confirmation_id,
        user_id=payload.user_id,
        team_id=payload.team_id,
        now=now,
    )
    if item is None:
        existing = await repo.get_by_confirmation_id(confirmation_id)
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "plugin_confirmation_not_found", "message": f"Unknown confirmation: {confirmation_id}"},
            )

        _ensure_pending_for_user(existing, payload.user_id)
        _ensure_team_binding(existing, payload.team_id)

        status = str(existing.status or "").strip().lower()
        expires_at = _as_aware_utc(existing.expires_at)
        if status == "pending" and expires_at is not None and expires_at < now:
            await repo.mark_expired(existing)
            await session.commit()
            raise HTTPException(
                status_code=409,
                detail={"code": "plugin_confirmation_expired", "message": "Confirmation has expired."},
            )

        raise HTTPException(
            status_code=409,
            detail={
                "code": "plugin_confirmation_not_pending",
                "message": f"Confirmation is not pending (status={status}).",
            },
        )

    stored_input = dict(item.arguments_json) if isinstance(item.arguments_json, dict) else {}
    stored_settings = dict(item.plugin_settings_json) if isinstance(item.plugin_settings_json, dict) else {}
    stored_context = dict(item.execution_context_json) if isinstance(item.execution_context_json, dict) else {}

    if _canonical_hash(stored_input) != str(item.arguments_hash):
        await repo.mark_executed_failure(
            item,
            code="plugin_confirmation_arguments_hash_mismatch",
            message="Stored confirmation arguments hash mismatch.",
        )
        await session.commit()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "plugin_confirmation_arguments_hash_mismatch",
                "message": "Stored confirmation arguments hash mismatch.",
            },
        )

    if executor.describe_plugin(str(item.plugin_id)) is None:
        await repo.mark_executed_failure(item, code="plugin_not_found", message="Plugin is no longer available.")
        await session.commit()
        raise HTTPException(
            status_code=409,
            detail={"code": "plugin_not_found", "message": "Plugin is no longer available."},
        )

    if executor.describe_function(str(item.plugin_id), str(item.function_name)) is None:
        await repo.mark_executed_failure(
            item,
            code="plugin_function_not_found",
            message="Plugin function is no longer available.",
        )
        await session.commit()
        raise HTTPException(
            status_code=409,
            detail={"code": "plugin_function_not_found", "message": "Plugin function is no longer available."},
        )

    stored_context["user_id"] = payload.user_id
    stored_context["team_id"] = payload.team_id
    stored_context["request_id"] = payload.request_id
    stored_context["granted_permissions"] = payload.granted_permissions
    stored_context["allowed_plugins"] = payload.allowed_plugins
    stored_context["enforce_permissions"] = payload.enforce_permissions
    stored_context["confirmed"] = True
    stored_context["confirmation_id"] = confirmation_id
    if item.idempotency_key:
        stored_context.setdefault("idempotency_key", item.idempotency_key)

    try:
        if str(item.route_kind) == "execute_function":
            plugin_response, idempotency_meta = await _execute_with_idempotency(
                session=session,
                plugin_id=str(item.plugin_id),
                function_name=str(item.function_name),
                input_data=stored_input,
                execution_context=stored_context,
                execute_call=lambda: executor.execute_function(
                    str(item.plugin_id),
                    str(item.function_name),
                    stored_input,
                    stored_settings,
                    execution_context=stored_context,
                ),
            )
        else:
            plugin_response, idempotency_meta = await _execute_with_idempotency(
                session=session,
                plugin_id=str(item.plugin_id),
                function_name=str(item.function_name),
                input_data=stored_input,
                execution_context=stored_context,
                execute_call=lambda: executor.execute(
                    str(item.plugin_id),
                    stored_input,
                    stored_settings,
                    execution_context=stored_context,
                ),
            )

        await repo.mark_executed_success(item, plugin_response)
        await session.commit()
    except PluginExecutionError as exc:
        await repo.mark_executed_failure(item, code=exc.code, message=exc.message)
        await session.commit()
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc
    except Exception as exc:
        await repo.mark_executed_failure(item, code="plugin_execution_failed", message=str(exc))
        await session.commit()
        raise HTTPException(
            status_code=500,
            detail={"code": "plugin_confirmation_execution_failed", "message": str(exc)},
        ) from exc

    return {
        "status": "executed",
        "confirmation": {
            "confirmation_id": confirmation_id,
            "plugin_id": str(item.plugin_id),
            "function_name": str(item.function_name),
            "arguments_hash": str(item.arguments_hash),
            "idempotency_key": item.idempotency_key,
            "decided_at": item.decided_at.isoformat() if item.decided_at else None,
        },
        "plugin_response": plugin_response,
        "idempotency": idempotency_meta,
    }


@router.post("/confirmations/{confirmation_id}/reject")
async def reject_plugin_execution(
    confirmation_id: str,
    payload: PluginConfirmationDecisionRequest,
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    repo = PluginConfirmationRepository(session)
    item = await _get_pending_confirmation_or_raise(
        session=session,
        confirmation_id=confirmation_id,
        user_id=payload.user_id,
        team_id=payload.team_id,
    )

    await repo.mark_rejected(item)
    await session.commit()

    return {
        "status": "rejected",
        "confirmation": {
            "confirmation_id": confirmation_id,
            "plugin_id": str(item.plugin_id),
            "function_name": str(item.function_name),
            "arguments_hash": str(item.arguments_hash),
            "decided_at": item.decided_at.isoformat() if item.decided_at else None,
        },
    }


@router.post("/execute-from-markup")
async def execute_plugin_from_markup(payload: PluginMarkupExecuteRequest) -> dict[str, Any]:
    executor = PluginExecutor()
    try:
        return await executor.execute_from_markup(payload.assistant_output)
    except PluginExecutionError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "plugin_markup_execution_failed", "message": str(exc)},
        ) from exc
