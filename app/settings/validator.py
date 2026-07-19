from pathlib import PurePath
from zoneinfo import ZoneInfo

from app.core.exceptions import InvalidSettingError
from app.models.path_security import normalize_base_directories
from app.settings.defaults import SYSTEM_HARD_LIMITS
from typing import cast


INTEGRATION_SECRET_KEYS = {
    "chatgpt_api_key",
    "deepl_api_key",
    "anthropic_api_key",
    "google_ai_api_key",
    "mistral_api_key",
    "cohere_api_key",
    "perplexity_api_key",
    "groq_api_key",
    "together_api_key",
    "openrouter_api_key",
    "huggingface_api_key",
    "replicate_api_key",
    "deepseek_api_key",
    "xai_api_key",
    "elevenlabs_api_key",
    "assemblyai_api_key",
    "tavily_api_key",
    "serpapi_api_key",
    "google_maps_api_key",
    "mapbox_api_key",
    "openweather_api_key",
    "weatherapi_api_key",
    "tomorrowio_api_key",
    "newsapi_api_key",
    "twilio_api_key",
    "sendgrid_api_key",
    "slack_bot_token",
    "discord_bot_token",
    "github_token",
    "notion_api_key",
    "airtable_api_key",
    "stripe_secret_key",
    "azure_openai_api_key",
    "aws_bedrock_api_key",
    "deepinfra_api_key",
    "nvidia_nim_api_key",
    "octoai_api_key",
    "fireworks_api_key",
    "github_copilot_api_key",
    "stability_api_key",
    "runway_api_key",
    "pika_api_key",
    "heygen_api_key",
    "fal_api_key",
    "unstructured_api_key",
    "llamaparse_api_key",
    "firecrawl_api_key",
    "pinecone_api_key",
    "weaviate_api_key",
    "qdrant_api_key",
    "cloudconvert_api_key",
    "exa_api_key",
    "brave_search_api_key",
    "bing_search_api_key",
    "gnews_api_key",
    "scrapingbee_api_key",
    "apify_api_key",
    "alpha_vantage_api_key",
    "yahoo_finance_api_key",
    "openexchangerates_api_key",
    "whatsapp_business_api_key",
    "telegram_bot_token",
    "microsoft_teams_api_key",
    "calendly_api_key",
    "virustotal_api_key",
    "hibp_api_key",
}


def is_secret_setting(category: str, key: str) -> bool:
    normalized_key = _strip_model_key_prefix(key)
    return category == "integrations" and normalized_key in INTEGRATION_SECRET_KEYS


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

    if category == "chat" and normalized_key == "plugin_orchestration_enabled":
        if not isinstance(value, bool):
            raise InvalidSettingError("plugin_orchestration_enabled must be boolean")

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
        context_limit_map: dict[str, int] = {}
        value_map = cast(dict[object, object], value)
        for raw_conversation_id, raw_limit in value_map.items():
            conversation_id = str(raw_conversation_id)
            if not conversation_id.isdigit():
                raise InvalidSettingError("conversation_context_limit_map keys must be numeric conversation ids")
            if not isinstance(raw_limit, int):
                raise InvalidSettingError("conversation_context_limit_map values must be integers")
            if raw_limit < 512:
                raise InvalidSettingError("conversation_context_limit_map values must be at least 512")
            context_limit_map[conversation_id] = raw_limit
        return context_limit_map

    if category == "chat" and normalized_key == "conversation_generation_profiles_map":
        if not isinstance(value, dict):
            raise InvalidSettingError("conversation_generation_profiles_map must be object")

    if category == "chat" and normalized_key == "conversation_project_map":
        if not isinstance(value, dict):
            raise InvalidSettingError("conversation_project_map must be object")
        conversation_project_map: dict[str, int] = {}
        value_map = cast(dict[object, object], value)
        for raw_conversation_id, raw_project_id in value_map.items():
            conversation_id = str(raw_conversation_id)
            if not conversation_id.isdigit():
                raise InvalidSettingError("conversation_project_map keys must be numeric conversation ids")
            if not isinstance(raw_project_id, int):
                raise InvalidSettingError("conversation_project_map values must be integer project ids")
            if raw_project_id <= 0:
                raise InvalidSettingError("conversation_project_map values must be positive")
            conversation_project_map[conversation_id] = raw_project_id
        return conversation_project_map

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

    if category == "integrations" and normalized_key in INTEGRATION_SECRET_KEYS:
        if not isinstance(value, str):
            raise InvalidSettingError(f"{normalized_key} must be string")
        normalized = value.strip()
        if len(normalized) > 1024:
            raise InvalidSettingError(f"{normalized_key} is too long")
        return normalized

    if category == "integrations" and normalized_key == "ollama_local_enabled":
        if not isinstance(value, bool):
            raise InvalidSettingError("ollama_local_enabled must be boolean")

    if category == "integrations" and normalized_key == "custom_provider_keys":
        if not isinstance(value, dict):
            raise InvalidSettingError("custom_provider_keys must be object")
        provider_map: dict[str, str] = {}
        value_map = cast(dict[object, object], value)
        for raw_key, raw_value in value_map.items():
            key_text = str(raw_key).strip().lower()
            if not key_text:
                raise InvalidSettingError("custom_provider_keys keys must not be empty")
            if len(key_text) > 120:
                raise InvalidSettingError("custom_provider_keys key is too long")
            if not isinstance(raw_value, str):
                raise InvalidSettingError("custom_provider_keys values must be strings")
            value_text = raw_value.strip()
            if len(value_text) > 1024:
                raise InvalidSettingError("custom_provider_keys value is too long")
            provider_map[key_text] = value_text
        return provider_map

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

    if category == "training" and normalized_key in {"auto_start_queue", "auto_evaluate", "auto_register_model", "auto_activate_model", "continual_training", "archive_on_success", "deduplicate_jobs", "load_in_4bit", "logging_first_step", "load_best_model_at_end", "greater_is_better"}:
        if not isinstance(value, bool):
            raise InvalidSettingError(f"{normalized_key} must be boolean")

    if category == "training" and normalized_key == "continual_model_id":
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
            raise InvalidSettingError("continual_model_id must be a positive integer or null")

    if category == "training" and normalized_key == "project_id":
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
            raise InvalidSettingError("project_id must be a positive integer or null")

    if category == "training" and normalized_key == "training_cycle_id":
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 120:
            raise InvalidSettingError("training_cycle_id must be a non-empty string up to 120 characters")
        return value.strip()

    if category == "training" and normalized_key == "training_preset":
        if not isinstance(value, str) or value not in {"safe", "balanced", "intensive", "custom"}:
            raise InvalidSettingError("training_preset must be safe, balanced, intensive or custom")

    if category == "training" and normalized_key in {"num_train_epochs", "learning_rate", "lora_dropout", "validation_split", "warmup_ratio", "weight_decay"}:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidSettingError(f"{normalized_key} must be numeric")
        numeric_value = float(value)
        limits = {
            "num_train_epochs": (0.1, 20.0),
            "learning_rate": (0.0000001, 1.0),
            "lora_dropout": (0.0, 0.8),
            "validation_split": (0.02, 0.3),
            "warmup_ratio": (0.0, 0.5),
            "weight_decay": (0.0, 1.0),
        }
        minimum, maximum = limits[normalized_key]
        if numeric_value < minimum or numeric_value > maximum:
            raise InvalidSettingError(f"{normalized_key} must be in range {minimum}..{maximum}")
        return numeric_value

    if category == "training" and normalized_key in {
        "per_device_train_batch_size", "gradient_accumulation_steps", "max_sequence_length",
        "lora_r", "lora_alpha", "eval_steps", "save_steps", "logging_steps", "max_steps", "seed",
    }:
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidSettingError(f"{normalized_key} must be integer")
        limits = {
            "per_device_train_batch_size": (1, 64),
            "gradient_accumulation_steps": (1, 256),
            "max_sequence_length": (128, 32768),
            "lora_r": (1, 1024),
            "lora_alpha": (1, 4096),
            "eval_steps": (1, 1000000),
            "save_steps": (10, 1000000),
            "logging_steps": (1, 1000000),
            "max_steps": (0, 10000000),
            "seed": (0, 2147483647),
        }
        minimum, maximum = limits[normalized_key]
        if value < minimum or value > maximum:
            raise InvalidSettingError(f"{normalized_key} must be in range {minimum}..{maximum}")

    if category == "training" and normalized_key == "target_modules":
        if not isinstance(value, list) or not value:
            raise InvalidSettingError("target_modules must be a non-empty list")
        normalized_modules: list[str] = []
        for item in cast(list[object], value):
            if not isinstance(item, str) or not item.strip():
                raise InvalidSettingError("target_modules entries must be non-empty strings")
            normalized_modules.append(item.strip())
        return normalized_modules

    if category == "training" and normalized_key == "metric_for_best_model":
        if not isinstance(value, str):
            raise InvalidSettingError("metric_for_best_model must be string")
        normalized_metric = value.strip()
        if not normalized_metric:
            raise InvalidSettingError("metric_for_best_model must not be empty")
        if len(normalized_metric) > 120:
            raise InvalidSettingError("metric_for_best_model is too long")
        return normalized_metric

    if category == "workspace" and normalized_key == "seed_demo_data":
        if not isinstance(value, bool):
            raise InvalidSettingError("seed_demo_data must be boolean")

    if category == "workspace" and normalized_key == "project_meta_map":
        if not isinstance(value, dict):
            raise InvalidSettingError("project_meta_map must be object")

        normalized_map: dict[str, dict[str, object]] = {}
        value_map = cast(dict[object, object], value)
        for raw_project_id, raw_meta in value_map.items():
            project_id = str(raw_project_id)
            if not project_id.isdigit() or int(project_id) <= 0:
                raise InvalidSettingError("project_meta_map keys must be positive numeric project ids")

            if not isinstance(raw_meta, dict):
                raise InvalidSettingError("project_meta_map values must be objects")

            typed_meta = cast(dict[object, object], raw_meta)
            raw_parent = typed_meta.get("parent_project_id")
            parent_project_id: int | None = None
            if raw_parent is not None:
                if not isinstance(raw_parent, int) or raw_parent <= 0:
                    raise InvalidSettingError("parent_project_id must be positive integer or null")
                if raw_parent == int(project_id):
                    raise InvalidSettingError("project cannot be its own parent")
                parent_project_id = raw_parent

            raw_scope = typed_meta.get("scope_kind", "project")
            if not isinstance(raw_scope, str):
                raise InvalidSettingError("scope_kind must be string")
            scope_kind = raw_scope.strip().lower()
            if scope_kind not in {"tenant", "user", "area", "project"}:
                raise InvalidSettingError("scope_kind must be tenant, user, area or project")

            raw_area = typed_meta.get("area_key")
            area_key: str | None = None
            if raw_area is not None:
                if not isinstance(raw_area, str):
                    raise InvalidSettingError("area_key must be string or null")
                area_key = raw_area.strip()[:120] or None

            raw_tenant = typed_meta.get("tenant_key")
            tenant_key: str | None = None
            if raw_tenant is not None:
                if not isinstance(raw_tenant, str):
                    raise InvalidSettingError("tenant_key must be string or null")
                tenant_key = raw_tenant.strip()[:120] or None

            raw_owner = typed_meta.get("owner_user_id")
            owner_user_id: int | None = None
            if raw_owner is not None:
                if not isinstance(raw_owner, int) or raw_owner <= 0:
                    raise InvalidSettingError("owner_user_id must be positive integer or null")
                owner_user_id = raw_owner

            normalized_map[project_id] = {
                "project_id": int(project_id),
                "parent_project_id": parent_project_id,
                "scope_kind": scope_kind,
                "area_key": area_key,
                "tenant_key": tenant_key,
                "owner_user_id": owner_user_id,
            }

        return normalized_map

    hard_limit = SYSTEM_HARD_LIMITS.get((category, normalized_key))
    if isinstance(hard_limit, int) and isinstance(value, int):
        return min(value, hard_limit)

    return cast(object, value)
