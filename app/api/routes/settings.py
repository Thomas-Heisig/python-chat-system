from __future__ import annotations

import math
from pathlib import PurePath
import re
from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session_dependency
from app.core.auth_token import verify_access_token
from app.database.repositories.user_repository import UserRepository
from app.schemas.setting import SettingUpdateRequest
from app.settings.repair import cleanup_obsolete_global_chat_settings, get_obsolete_global_chat_cleanup_stats
from app.settings.service import SettingsService
from app.settings.validator import is_secret_setting
from app.tools import PluginRegistry
from plugins.business_letter.services.numbering import NumberSequenceStore

router = APIRouter(prefix="/api/settings", tags=["settings"])
_plugin_registry = PluginRegistry()

_BUSINESS_LETTER_ALLOWED_NUMBER_TOKENS = {
    "prefix",
    "year",
    "month",
    "day",
    "sequence",
    "sequence_text",
}
_BUSINESS_LETTER_NUMBERING_SCOPES = (
    "document",
    "angebot",
    "auftragsbestaetigung",
    "lieferschein",
    "rechnung",
    "abschlagsrechnung",
    "schlussrechnung",
    "gutschrift",
    "stornorechnung",
    "mahnung",
)
_BUSINESS_LETTER_LOCKED_NUMBER_FIELDS = ("prefix", "sequence_kind", "pattern", "width", "start_value", "year_reset")


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
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
    return user_id, user


def _enforce_settings_scope_access(
    *,
    requester_user_id: int,
    requester: object,
    user_id: int | None,
    team_id: int | None,
) -> None:
    requester_is_admin = bool(getattr(requester, "is_admin", False))
    if user_id is None and team_id is None:
        if not requester_is_admin:
            raise HTTPException(status_code=403, detail="Only admins can access global settings")
        return

    if team_id is not None and user_id is None:
        if not requester_is_admin:
            raise HTTPException(status_code=403, detail="Only authorized users can access team settings")
        return

    if user_id is not None and user_id != requester_user_id and not requester_is_admin:
        raise HTTPException(status_code=403, detail="Users can only access their own settings")


def _business_letter_field_key(scope: str, suffix: str) -> str:
    if scope == "document":
        return f"document_number_{suffix}"
    return f"{scope}_document_number_{suffix}"


def _business_letter_numbering_scope_values(payload: dict[str, Any], scope: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for suffix in _BUSINESS_LETTER_LOCKED_NUMBER_FIELDS:
        key = _business_letter_field_key(scope, suffix)
        if key in payload:
            values[suffix] = payload.get(key)
    return values


def _business_letter_effective_numbering_values(payload: dict[str, Any], scope: str) -> dict[str, Any]:
    effective: dict[str, Any] = {}
    general = _business_letter_numbering_scope_values(payload, "document")
    scoped = _business_letter_numbering_scope_values(payload, scope)
    effective.update(general)
    effective.update(scoped)
    return effective


def _validate_business_letter_profile_fields(payload: dict[str, Any]) -> dict[str, str]:
    field_errors: dict[str, str] = {}

    if "document_number_pattern" in payload:
        raw_pattern = payload.get("document_number_pattern")
        if not isinstance(raw_pattern, str) or raw_pattern.strip() == "":
            field_errors["document_number_pattern"] = "Expected a non-empty pattern string."
        else:
            pattern = raw_pattern.strip()
            token_matches = [match.group(1) for match in re.finditer(r"\{([a-zA-Z0-9_]+)\}", pattern)]
            if "sequence_text" not in token_matches:
                field_errors["document_number_pattern"] = "Pattern must include the token {sequence_text}."
            else:
                unknown_tokens = sorted({token for token in token_matches if token not in _BUSINESS_LETTER_ALLOWED_NUMBER_TOKENS})
                if unknown_tokens:
                    field_errors["document_number_pattern"] = (
                        "Pattern contains unsupported tokens: " + ", ".join(unknown_tokens)
                    )

    if "document_number_width" in payload:
        raw_width = payload.get("document_number_width")
        width_value: int | None = None
        if isinstance(raw_width, bool) or not isinstance(raw_width, (int, float)):
            field_errors["document_number_width"] = "Expected an integer value between 1 and 12."
        else:
            numeric_width = float(raw_width)
            if not numeric_width.is_integer():
                field_errors["document_number_width"] = "Expected an integer value between 1 and 12."
            else:
                width_value = int(numeric_width)
                if width_value < 1 or width_value > 12:
                    field_errors["document_number_width"] = "Expected an integer value between 1 and 12."

        if width_value is not None:
            payload["document_number_width"] = width_value

    for key in [field for field in payload.keys() if field.endswith("_document_number_width") and field != "document_number_width"]:
        raw_width = payload.get(key)
        width_value: int | None = None
        if isinstance(raw_width, bool) or not isinstance(raw_width, (int, float)):
            field_errors[key] = "Expected an integer value between 1 and 12."
        else:
            numeric_width = float(raw_width)
            if not numeric_width.is_integer():
                field_errors[key] = "Expected an integer value between 1 and 12."
            else:
                width_value = int(numeric_width)
                if width_value < 1 or width_value > 12:
                    field_errors[key] = "Expected an integer value between 1 and 12."
        if width_value is not None:
            payload[key] = width_value

    for key in [field for field in payload.keys() if field.endswith("_document_number_start_value") or field == "document_number_start_value"]:
        raw_start_value = payload.get(key)
        normalized_start_value: int | None = None
        if isinstance(raw_start_value, bool) or not isinstance(raw_start_value, (int, float)):
            field_errors[key] = "Expected an integer start value greater than or equal to 1."
        else:
            numeric_start_value = float(raw_start_value)
            if not numeric_start_value.is_integer():
                field_errors[key] = "Expected an integer start value greater than or equal to 1."
            else:
                normalized_start_value = int(numeric_start_value)
                if normalized_start_value < 1:
                    field_errors[key] = "Expected an integer start value greater than or equal to 1."
        if normalized_start_value is not None:
            payload[key] = normalized_start_value

    for key in [field for field in payload.keys() if field.endswith("_document_number_year_reset") or field == "document_number_year_reset"]:
        if not isinstance(payload.get(key), bool):
            field_errors[key] = "Expected a boolean value."

    sequence_kind_map: dict[str, list[str]] = {}
    for scope in _BUSINESS_LETTER_NUMBERING_SCOPES:
        effective = _business_letter_effective_numbering_values(payload, scope)
        sequence_kind = str(effective.get("sequence_kind") or "").strip()
        if not sequence_kind:
            continue
        sequence_kind_map.setdefault(sequence_kind, []).append(scope)

    for sequence_kind, scopes in sequence_kind_map.items():
        if len(scopes) <= 1:
            continue
        for scope in scopes:
            field_key = _business_letter_field_key(scope, "sequence_kind")
            field_errors[field_key] = f"Sequence kind conflicts with another document type: {sequence_kind}."

    if "default_payment_days" in payload:
        raw_days = payload.get("default_payment_days")
        days_value: int | None = None
        if isinstance(raw_days, bool) or not isinstance(raw_days, (int, float)):
            field_errors["default_payment_days"] = "Expected an integer value between 0 and 365."
        else:
            numeric_days = float(raw_days)
            if not numeric_days.is_integer():
                field_errors["default_payment_days"] = "Expected an integer value between 0 and 365."
            else:
                days_value = int(numeric_days)
                if days_value < 0 or days_value > 365:
                    field_errors["default_payment_days"] = "Expected an integer value between 0 and 365."

        if days_value is not None:
            payload["default_payment_days"] = days_value

    if "guest_system_database_path" in payload:
        raw_path = payload.get("guest_system_database_path")
        if not isinstance(raw_path, str) or raw_path.strip() == "":
            field_errors["guest_system_database_path"] = "Expected a non-empty relative .db path."
        else:
            normalized = raw_path.replace("\\", "/").strip()
            pure_path = PurePath(normalized)
            is_windows_absolute = bool(re.match(r"^[a-zA-Z]:/", normalized))

            if pure_path.is_absolute() or is_windows_absolute:
                field_errors["guest_system_database_path"] = "Absolute paths are not allowed."
            elif any(part in {"..", ""} for part in pure_path.parts):
                field_errors["guest_system_database_path"] = "Path traversal segments are not allowed."
            elif not normalized.lower().endswith(".db"):
                field_errors["guest_system_database_path"] = "Path must point to a .db file."

    return field_errors


async def _validate_business_letter_numbering_state(
    payload: dict[str, Any],
    *,
    current_profile: dict[str, Any],
) -> dict[str, str]:
    field_errors: dict[str, str] = {}
    store = NumberSequenceStore()
    tenant_id = "default"

    for scope in _BUSINESS_LETTER_NUMBERING_SCOPES:
        next_values = _business_letter_effective_numbering_values(payload, scope)
        current_values = _business_letter_effective_numbering_values(current_profile, scope)
        sequence_kind = str(next_values.get("sequence_kind") or "").strip()
        if not sequence_kind:
            continue
        if not store.has_sequence_entries(tenant_id=tenant_id, sequence_kind=sequence_kind):
            continue

        for suffix in _BUSINESS_LETTER_LOCKED_NUMBER_FIELDS:
            if suffix not in next_values:
                continue
            next_value = next_values.get(suffix)
            current_value = current_values.get(suffix)
            if next_value != current_value:
                field_errors[_business_letter_field_key(scope, suffix)] = "Numbering settings cannot be changed after first use."

    return field_errors


def _coerce_select_value(value: Any, expected: Any) -> tuple[bool, Any]:
    if value == expected:
        return True, expected

    if isinstance(expected, bool):
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered == "true":
                return True, True
            if lowered == "false":
                return True, False
        return False, value

    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return (float(value) == float(expected), expected)
        if isinstance(value, str):
            try:
                parsed = float(value)
                return (parsed == float(expected), expected)
            except ValueError:
                return False, value
        return False, value

    if isinstance(expected, str):
        if isinstance(value, str):
            return (value == expected, expected)
        return False, value

    return False, value


def _validate_plugin_profile_value(plugin_id: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_plugin_settings",
                "message": "Plugin settings must be an object.",
                "plugin_id": plugin_id,
                "field_errors": {},
            },
        )

    loaded = _plugin_registry.get_plugin(plugin_id)
    if loaded is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "plugin_not_found",
                "message": f"Unknown plugin: {plugin_id}",
                "plugin_id": plugin_id,
                "field_errors": {},
            },
        )

    settings_fields: list[dict[str, Any]] = loaded.definition.settings_fields
    field_map = {
        str(field.get("key", "")).strip(): field
        for field in settings_fields
        if str(field.get("key", "")).strip()
    }

    payload = cast(dict[str, Any], value)
    field_errors: dict[str, str] = {}
    normalized_payload: dict[str, Any] = {}

    for key in payload.keys():
        if key not in field_map:
            field_errors[key] = "Unknown setting field."

    for field_key, field in field_map.items():
        field_type = str(field.get("type", "string")).strip().lower() or "string"
        required = field.get("required") is True
        raw_value = payload.get(field_key)

        if field_key not in payload:
            if required:
                field_errors[field_key] = "This field is required."
            continue

        if field_type in {"string", "text", "password"}:
            if not isinstance(raw_value, str):
                field_errors[field_key] = "Expected a string value."
                continue
            if required and raw_value.strip() == "":
                field_errors[field_key] = "This field is required."
                continue
            normalized_payload[field_key] = raw_value
            continue

        if field_type == "boolean":
            if not isinstance(raw_value, bool):
                field_errors[field_key] = "Expected a boolean value."
                continue
            normalized_payload[field_key] = raw_value
            continue

        if field_type == "number":
            if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
                field_errors[field_key] = "Expected a numeric value."
                continue
            as_float = float(raw_value)
            if not math.isfinite(as_float):
                field_errors[field_key] = "Expected a finite numeric value."
                continue
            normalized_payload[field_key] = raw_value
            continue

        if field_type == "select":
            options_raw = field.get("options")
            if not isinstance(options_raw, list) or not options_raw:
                normalized_payload[field_key] = raw_value
                continue

            expected_values: list[Any] = []
            for option in cast(list[Any], options_raw):
                if isinstance(option, dict) and "value" in option:
                    option_value = cast(dict[str, Any], option).get("value")
                    expected_values.append(option_value)
                elif isinstance(option, (str, int, float, bool)):
                    expected_values.append(option)

            matched = False
            for expected in expected_values:
                is_match, coerced = _coerce_select_value(raw_value, expected)
                if is_match:
                    matched = True
                    normalized_payload[field_key] = coerced
                    break

            if not matched:
                field_errors[field_key] = "Value is not in allowed options."
            continue

        normalized_payload[field_key] = raw_value

    if plugin_id == "business_letter":
        field_errors.update(_validate_business_letter_profile_fields(normalized_payload))

    if field_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_plugin_settings",
                "message": "Plugin settings validation failed.",
                "plugin_id": plugin_id,
                "field_errors": field_errors,
            },
        )

    return normalized_payload


async def _validate_plugin_profile_update(
    category: str,
    key: str,
    value: Any,
    *,
    user_id: int | None,
    team_id: int | None,
    service: SettingsService,
) -> Any:
    if category != "plugins":
        return value
    if not key.endswith("_profile"):
        return value

    plugin_id = key[: -len("_profile")].strip()
    if not plugin_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_plugin_settings_key",
                "message": "Invalid plugin settings key.",
                "plugin_id": "",
                "field_errors": {},
            },
        )

    normalized_value = _validate_plugin_profile_value(plugin_id, value)
    if plugin_id == "business_letter":
        current_value = await service.get(category=category, key=key, user_id=user_id, team_id=team_id)
        current_profile = cast(dict[str, Any], current_value) if isinstance(current_value, dict) else {}
        numbering_errors = await _validate_business_letter_numbering_state(normalized_value, current_profile=current_profile)
        if numbering_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "invalid_plugin_settings",
                    "message": "Plugin settings validation failed.",
                    "plugin_id": plugin_id,
                    "field_errors": numbering_errors,
                },
            )

    return normalized_value


@router.post("")
async def update_setting(
    payload: SettingUpdateRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    requester_user_id, requester = await _require_authenticated_user(session, authorization)
    _enforce_settings_scope_access(
        requester_user_id=requester_user_id,
        requester=requester,
        user_id=payload.user_id,
        team_id=payload.team_id,
    )
    service = SettingsService(session)
    validated_value = await _validate_plugin_profile_update(
        payload.category,
        payload.key,
        payload.value,
        user_id=payload.user_id,
        team_id=payload.team_id,
        service=service,
    )
    effect = await service.update(
        category=payload.category,
        key=payload.key,
        value=validated_value,
        user_id=payload.user_id,
        team_id=payload.team_id,
    )
    await session.commit()
    return {"updated": True, "effect": effect}


@router.get("/{category}/{key}")
async def get_setting(
    category: str,
    key: str,
    user_id: int | None = None,
    team_id: int | None = None,
    include_secret: bool = False,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    requester_user_id, requester = await _require_authenticated_user(session, authorization)
    _enforce_settings_scope_access(
        requester_user_id=requester_user_id,
        requester=requester,
        user_id=user_id,
        team_id=team_id,
    )
    service = SettingsService(session)
    value = await service.get(category=category, key=key, user_id=user_id, team_id=team_id)
    if is_secret_setting(category, key) and include_secret and not bool(getattr(requester, "is_admin", False)):
        raise HTTPException(status_code=403, detail="Only admins can request unmasked secret settings")
    if is_secret_setting(category, key) and not include_secret:
        value = "********"
    return {"category": category, "key": key, "value": value}


@router.post("/chat/cleanup-obsolete")
async def cleanup_obsolete_chat_settings(
    dry_run: bool = False,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(db_session_dependency),
) -> dict[str, Any]:
    _requester_user_id, requester = await _require_authenticated_user(session, authorization)
    if not bool(getattr(requester, "is_admin", False)):
        raise HTTPException(status_code=403, detail="Only admins can clean up global chat settings")

    if dry_run:
        stats = await get_obsolete_global_chat_cleanup_stats(session)
        return {
            "dry_run": True,
            "category": "chat",
            "keys": [
                "temperature",
                "max_new_tokens",
                "top_p",
                "top_k",
                "repetition_penalty",
                "do_sample",
                "seed",
                "stop_sequences",
            ],
            **stats,
        }

    stats = await cleanup_obsolete_global_chat_settings(session)
    await session.commit()
    return {
        "dry_run": False,
        "category": "chat",
        "keys": [
            "temperature",
            "max_new_tokens",
            "top_p",
            "top_k",
            "repetition_penalty",
            "do_sample",
            "seed",
            "stop_sequences",
        ],
        **stats,
    }
