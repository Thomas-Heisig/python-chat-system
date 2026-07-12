from pathlib import PurePath
from zoneinfo import ZoneInfo

from app.core.exceptions import InvalidSettingError
from app.models.path_security import normalize_base_directories
from app.settings.defaults import SYSTEM_HARD_LIMITS
from typing import cast


def _strip_model_key_prefix(key: str) -> str:
    if not key.startswith("model_"):
        return key

    rest = key[len("model_"):]
    model_id_raw, separator, suffix = rest.partition("_")
    if separator != "_" or not model_id_raw.isdigit() or not suffix:
        return key
    return suffix


def validate_setting(category: str, key: str, value: object) -> object:
    normalized_key = _strip_model_key_prefix(key)

    if category == "model" and key == "base_directories":
        if not isinstance(value, list):
            raise InvalidSettingError("base_directories must be a list")

        raw_directories = cast(list[object], value)
        for entry in raw_directories:
            if not isinstance(entry, (str, int, float)):
                raise InvalidSettingError("base_directories entries must be strings")
            path_text = str(entry).strip()
            if not path_text:
                raise InvalidSettingError("base_directories entries must not be empty")
            if any(part == ".." for part in PurePath(path_text).parts):
                raise InvalidSettingError("base_directories entries must not contain path traversal")

        normalized_directories = normalize_base_directories(raw_directories)
        if not normalized_directories:
            raise InvalidSettingError("base_directories must contain at least one valid directory")
        return normalized_directories

    if category == "model" and key == "relevance_flags":
        if not isinstance(value, dict):
            raise InvalidSettingError("relevance_flags must be object")
        relevance_map: dict[str, str] = {}
        value_map = cast(dict[object, object], value)
        for raw_model_id, raw_relevance in value_map.items():
            model_id = str(raw_model_id).strip()
            if not model_id.isdigit():
                raise InvalidSettingError("relevance_flags keys must be numeric model ids")
            relevance = str(raw_relevance).strip().lower()
            if relevance not in {"favorite", "irrelevant"}:
                raise InvalidSettingError("relevance_flags values must be favorite or irrelevant")
            relevance_map[model_id] = relevance
        return relevance_map

    if category == "chat" and normalized_key == "temperature":
        if not isinstance(value, (int, float)):
            raise InvalidSettingError("temperature must be numeric")
        if value < 0 or value > 2:
            raise InvalidSettingError("temperature must be in range 0..2")

    if category == "chat" and normalized_key == "max_new_tokens":
        if not isinstance(value, int):
            raise InvalidSettingError("max_new_tokens must be integer")
        if value <= 0:
            raise InvalidSettingError("max_new_tokens must be greater than 0")

    if category == "chat" and normalized_key == "top_p":
        if not isinstance(value, (int, float)):
            raise InvalidSettingError("top_p must be numeric")
        if value <= 0 or value > 1:
            raise InvalidSettingError("top_p must be in range (0, 1]")

    if category == "chat" and normalized_key == "top_k":
        if not isinstance(value, int):
            raise InvalidSettingError("top_k must be integer")
        if value < 0:
            raise InvalidSettingError("top_k must be non-negative")

    if category == "chat" and normalized_key == "repetition_penalty":
        if not isinstance(value, (int, float)):
            raise InvalidSettingError("repetition_penalty must be numeric")
        if value < 0.5 or value > 2:
            raise InvalidSettingError("repetition_penalty must be in range 0.5..2")

    if category == "chat" and normalized_key == "seed":
        if not isinstance(value, int):
            raise InvalidSettingError("seed must be integer")
        if value < 0:
            raise InvalidSettingError("seed must be non-negative")

    if category == "chat" and normalized_key == "do_sample":
        if not isinstance(value, bool):
            raise InvalidSettingError("do_sample must be boolean")

    if category == "chat" and normalized_key == "auto_specialist_enabled":
        if not isinstance(value, bool):
            raise InvalidSettingError("auto_specialist_enabled must be boolean")

    if category == "chat" and normalized_key == "stop_sequences":
        if not isinstance(value, list):
            raise InvalidSettingError("stop_sequences must be a list of strings")
        normalized_sequences: list[str] = []
        for item in cast(list[object], value):
            if not isinstance(item, str):
                raise InvalidSettingError("stop_sequences entries must be strings")
            normalized = item.strip()
            if normalized:
                normalized_sequences.append(normalized)
        return normalized_sequences

    if category == "chat" and normalized_key == "context_limit_tokens":
        if not isinstance(value, int):
            raise InvalidSettingError("context_limit_tokens must be integer")
        if value < 512:
            raise InvalidSettingError("context_limit_tokens must be at least 512")

    if category == "chat" and normalized_key == "context_safety_margin_tokens":
        if not isinstance(value, int):
            raise InvalidSettingError("context_safety_margin_tokens must be integer")
        if value < 0:
            raise InvalidSettingError("context_safety_margin_tokens must be non-negative")

    if category == "chat" and normalized_key == "conversation_context_limit_map":
        if not isinstance(value, dict):
            raise InvalidSettingError("conversation_context_limit_map must be object")
        normalized_map: dict[str, int] = {}
        value_map = cast(dict[object, object], value)
        for raw_conversation_id, raw_limit in value_map.items():
            conversation_id = str(raw_conversation_id)
            if not conversation_id.isdigit():
                raise InvalidSettingError("conversation_context_limit_map keys must be numeric conversation ids")
            if not isinstance(raw_limit, int):
                raise InvalidSettingError("conversation_context_limit_map values must be integers")
            if raw_limit < 512:
                raise InvalidSettingError("conversation_context_limit_map values must be at least 512")
            normalized_map[conversation_id] = raw_limit
        return normalized_map

    if category == "chat" and normalized_key == "conversation_generation_profiles_map":
        if not isinstance(value, dict):
            raise InvalidSettingError("conversation_generation_profiles_map must be object")

    if category == "chat" and normalized_key == "conversation_project_map":
        if not isinstance(value, dict):
            raise InvalidSettingError("conversation_project_map must be object")
        normalized_map: dict[str, int] = {}
        value_map = cast(dict[object, object], value)
        for raw_conversation_id, raw_project_id in value_map.items():
            conversation_id = str(raw_conversation_id)
            if not conversation_id.isdigit():
                raise InvalidSettingError("conversation_project_map keys must be numeric conversation ids")
            if not isinstance(raw_project_id, int):
                raise InvalidSettingError("conversation_project_map values must be integer project ids")
            if raw_project_id <= 0:
                raise InvalidSettingError("conversation_project_map values must be positive")
            normalized_map[conversation_id] = raw_project_id
        return normalized_map

    if category == "knowledge" and normalized_key == "top_k":
        if not isinstance(value, int):
            raise InvalidSettingError("top_k must be integer")
        if value < 1:
            raise InvalidSettingError("top_k must be greater than 0")

    if category == "knowledge" and normalized_key == "min_score_ratio":
        if not isinstance(value, (int, float)):
            raise InvalidSettingError("min_score_ratio must be numeric")
        if value < 0 or value > 1:
            raise InvalidSettingError("min_score_ratio must be in range 0..1")

    if category == "knowledge" and normalized_key == "min_absolute_score":
        if not isinstance(value, int):
            raise InvalidSettingError("min_absolute_score must be integer")
        if value < 0:
            raise InvalidSettingError("min_absolute_score must be non-negative")

    if category == "knowledge" and normalized_key == "min_score_gap":
        if not isinstance(value, int):
            raise InvalidSettingError("min_score_gap must be integer")
        if value < 0:
            raise InvalidSettingError("min_score_gap must be non-negative")

    if category == "prompt" and normalized_key == "system_prompt":
        if not isinstance(value, str):
            raise InvalidSettingError("system_prompt must be string")
        return value.strip()

    if category == "system" and normalized_key == "language":
        if not isinstance(value, str):
            raise InvalidSettingError("language must be string")
        normalized = value.strip().lower()
        if normalized not in {"de", "en"}:
            raise InvalidSettingError("language must be one of: de, en")
        return normalized

    if category == "system" and normalized_key == "theme":
        if not isinstance(value, str):
            raise InvalidSettingError("theme must be string")
        normalized = value.strip().lower()
        if normalized not in {"system", "light", "dark"}:
            raise InvalidSettingError("theme must be one of: system, light, dark")
        return normalized

    if category == "system" and normalized_key == "timezone":
        if not isinstance(value, str):
            raise InvalidSettingError("timezone must be string")
        normalized = value.strip()
        if not normalized:
            raise InvalidSettingError("timezone must not be empty")
        try:
            ZoneInfo(normalized)
        except Exception as exc:
            raise InvalidSettingError("timezone must be a valid IANA timezone") from exc
        return normalized

    if category == "training" and normalized_key == "enabled":
        if not isinstance(value, bool):
            raise InvalidSettingError("enabled must be boolean")

    if category == "training" and normalized_key == "default_trainer":
        if not isinstance(value, str):
            raise InvalidSettingError("default_trainer must be string")
        normalized = value.strip().lower()
        if not normalized:
            raise InvalidSettingError("default_trainer must not be empty")
        return normalized

    if category == "training" and normalized_key == "base_model":
        if not isinstance(value, str):
            raise InvalidSettingError("base_model must be string")
        normalized = value.strip()
        # Empty string means "not configured yet".
        if not normalized:
            return ""
        return normalized

    if category == "training" and normalized_key in {"artifacts_directory", "datasets_directory"}:
        if not isinstance(value, str):
            raise InvalidSettingError(f"{normalized_key} must be string")
        normalized = value.strip()
        if not normalized:
            raise InvalidSettingError(f"{normalized_key} must not be empty")
        if any(part == ".." for part in PurePath(normalized).parts):
            raise InvalidSettingError(f"{normalized_key} must not contain path traversal")
        return normalized

    if category == "training" and normalized_key == "max_concurrent_jobs":
        if not isinstance(value, int):
            raise InvalidSettingError("max_concurrent_jobs must be integer")
        if value < 1:
            raise InvalidSettingError("max_concurrent_jobs must be at least 1")

    if category == "training" and normalized_key in {"auto_start_queue", "auto_evaluate", "auto_register_model"}:
        if not isinstance(value, bool):
            raise InvalidSettingError(f"{normalized_key} must be boolean")

    hard_limit = SYSTEM_HARD_LIMITS.get((category, normalized_key))
    if isinstance(hard_limit, int) and isinstance(value, int):
        return min(value, hard_limit)

    return cast(object, value)
