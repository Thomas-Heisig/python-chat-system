from __future__ import annotations

import asyncio
import json
import logging

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidSettingError
from app.db_models.setting import Setting
from app.settings.service import SettingsService
from app.settings.validator import validate_setting


logger = logging.getLogger(__name__)


_repair_lock = asyncio.Lock()


OBSOLETE_GLOBAL_CHAT_KEYS: tuple[str, ...] = (
    "temperature",
    "max_new_tokens",
    "top_p",
    "top_k",
    "repetition_penalty",
    "do_sample",
    "seed",
    "stop_sequences",
)


def _safe_parse_json(value_json: str) -> object | None:
    try:
        return json.loads(value_json)
    except Exception:
        return None


def _redact_setting_value(category: str, key: str, value: object | None) -> object:
    key_text = key.lower()
    if category in {"auth", "security"}:
        return "***redacted***"
    if any(token in key_text for token in ("password", "secret", "token", "api_key", "credential")):
        return "***redacted***"
    return value


async def repair_invalid_settings(session: AsyncSession) -> dict[str, int]:
    repaired = 0
    checked = 0

    async with _repair_lock:
        rows = (await session.execute(select(Setting).order_by(Setting.id.asc()))).scalars().all()
        service = SettingsService(session)

        for row in rows:
            checked += 1
            try:
                parsed = json.loads(row.value_json)
                validate_setting(row.category, row.key, parsed)
                continue
            except (json.JSONDecodeError, InvalidSettingError) as exc:
                invalid_reason = str(exc)
                invalid_value = _safe_parse_json(row.value_json)
            except Exception:
                # Unknown errors are not treated as repairable settings problems.
                continue

            try:
                replacement = await service.get(
                    row.category,
                    row.key,
                    user_id=row.user_id,
                    team_id=row.team_id,
                )
            except Exception:
                logger.warning(
                    "Startup repair could not resolve replacement value",
                    extra={
                        "category": row.category,
                        "key": row.key,
                        "scope_user_id": row.user_id,
                        "scope_team_id": row.team_id,
                        "invalid_value": _redact_setting_value(row.category, row.key, invalid_value),
                        "invalid_reason": invalid_reason,
                    },
                )
                continue

            try:
                replacement_json = json.dumps(replacement, ensure_ascii=False)
                if replacement_json == row.value_json:
                    continue

                row.value_json = replacement_json
                repaired += 1
                logger.info(
                    "Startup repaired invalid persisted setting",
                    extra={
                        "category": row.category,
                        "key": row.key,
                        "scope_user_id": row.user_id,
                        "scope_team_id": row.team_id,
                        "invalid_value": _redact_setting_value(row.category, row.key, invalid_value),
                        "replacement_value": _redact_setting_value(row.category, row.key, replacement),
                        "invalid_reason": invalid_reason,
                    },
                )
            except Exception:
                logger.warning(
                    "Startup repair failed while writing replacement",
                    extra={
                        "category": row.category,
                        "key": row.key,
                        "scope_user_id": row.user_id,
                        "scope_team_id": row.team_id,
                        "invalid_value": _redact_setting_value(row.category, row.key, invalid_value),
                        "replacement_value": _redact_setting_value(row.category, row.key, replacement),
                        "invalid_reason": invalid_reason,
                    },
                )
                continue

        return {"checked": checked, "repaired": repaired}


async def cleanup_obsolete_global_chat_settings(session: AsyncSession) -> dict[str, int]:
    stats = await get_obsolete_global_chat_cleanup_stats(session)
    async with _repair_lock:
        matched_count = stats["matched_count"]
        if matched_count <= 0:
            return {"matched_count": 0, "deleted": 0, "remaining_count": 0}

        result = await session.execute(
            delete(Setting)
            .where(Setting.category == "chat")
            .where(Setting.key.in_(OBSOLETE_GLOBAL_CHAT_KEYS))
            .where(Setting.user_id.is_(None))
            .where(Setting.team_id.is_(None))
        )
        deleted = int(result.rowcount or 0)
        remaining_count = max(0, matched_count - deleted)
        if deleted > 0:
            logger.info(
                "Startup cleanup removed obsolete global chat settings",
                extra={
                    "category": "chat",
                    "deleted": deleted,
                    "matched_count": matched_count,
                    "remaining_count": remaining_count,
                    "keys": list(OBSOLETE_GLOBAL_CHAT_KEYS),
                    "scope_user_id": None,
                    "scope_team_id": None,
                },
            )
        return {
            "matched_count": matched_count,
            "deleted": deleted,
            "remaining_count": remaining_count,
        }


async def get_obsolete_global_chat_cleanup_stats(session: AsyncSession) -> dict[str, int]:
    async with _repair_lock:
        count_stmt = (
            select(func.count())
            .select_from(Setting)
            .where(Setting.category == "chat")
            .where(Setting.key.in_(OBSOLETE_GLOBAL_CHAT_KEYS))
            .where(Setting.user_id.is_(None))
            .where(Setting.team_id.is_(None))
        )
        matched_count = int((await session.execute(count_stmt)).scalar_one() or 0)
        return {
            "matched_count": matched_count,
            "remaining_count": matched_count,
        }
