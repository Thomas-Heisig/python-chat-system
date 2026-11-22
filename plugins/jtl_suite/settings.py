from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

SETTING_SOURCE_ORDER = (
    "system_defaults",
    "environment",
    "tenant",
    "team",
    "user",
    "location",
    "plugin",
    "request_override",
)

JTL_DEFAULT_SETTINGS: dict[str, Any] = {
    "jtl_wawi_base_url": "",
    "jtl_wawi_api_key": "",
    "jtl_shop_base_url": "",
    "jtl_shop_api_key": "",
    "jtl_wms_base_url": "",
    "jtl_wms_api_key": "",
    "jtl_eazyauction_base_url": "",
    "jtl_eazyauction_api_key": "",
    "jtl_db_host": "localhost",
    "jtl_db_port": 1433,
    "jtl_db_user": "sa",
    "jtl_db_password": "",
    "jtl_db_driver": "ODBC Driver 18 for SQL Server",
    "jtl_wawi_db_name": "eazybusiness",
    "jtl_shop_db_name": "",
    "jtl_wms_db_name": "",
    "jtl_eazyauction_db_name": "",
    "jtl_db_encrypt": True,
    "jtl_db_trust_server_certificate": False,
    "jtl_db_timeout_seconds": 20,
    "request_timeout_seconds": 20,
    "verify_tls": True,
    "max_pagination_pages": 10,
    "retry_max_attempts": 3,
    "retry_backoff_factor": 1.0,
    "api_read_timeout": 30,
    "api_write_timeout": 60,
    "sql_query_timeout_seconds": 60,
    "db_pool_size": 5,
    "allow_cross_database_joins": False,
    "jtl_mandant_filter": 0,
    "analytics_default_limit": 50,
    "analytics_use_db": False,
}

ENVIRONMENT_KEYS = {
    "jtl_wawi_base_url": "JTL_WAWI_BASE_URL",
    "jtl_wawi_api_key": "JTL_WAWI_API_KEY",
    "jtl_shop_base_url": "JTL_SHOP_BASE_URL",
    "jtl_shop_api_key": "JTL_SHOP_API_KEY",
    "jtl_wms_base_url": "JTL_WMS_BASE_URL",
    "jtl_wms_api_key": "JTL_WMS_API_KEY",
    "jtl_eazyauction_base_url": "JTL_EAZYAUCTION_BASE_URL",
    "jtl_eazyauction_api_key": "JTL_EAZYAUCTION_API_KEY",
    "jtl_db_host": "JTL_DB_HOST",
    "jtl_db_port": "JTL_DB_PORT",
    "jtl_db_user": "JTL_DB_USER",
    "jtl_db_password": "JTL_DB_PASSWORD",
    "jtl_db_driver": "JTL_DB_DRIVER",
    "jtl_wawi_db_name": "JTL_WAWI_DB_NAME",
    "jtl_shop_db_name": "JTL_SHOP_DB_NAME",
    "jtl_wms_db_name": "JTL_WMS_DB_NAME",
    "jtl_eazyauction_db_name": "JTL_EAZYAUCTION_DB_NAME",
    "jtl_db_encrypt": "JTL_DB_ENCRYPT",
    "jtl_db_trust_server_certificate": "JTL_DB_TRUST_SERVER_CERTIFICATE",
    "jtl_db_timeout_seconds": "JTL_DB_TIMEOUT_SECONDS",
}

SECRET_KEYS = {
    "jtl_wawi_api_key",
    "jtl_shop_api_key",
    "jtl_wms_api_key",
    "jtl_eazyauction_api_key",
    "jtl_db_password",
}

@dataclass(slots=True)
class ResolvedSettings:
    resolved_settings: dict[str, Any]
    setting_sources: dict[str, str]
    unknown_settings: list[str]


def _coerce(key: str, value: Any) -> Any:
    default = JTL_DEFAULT_SETTINGS.get(key)
    if isinstance(default, bool):
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
    if isinstance(default, int) and not isinstance(default, bool):
        return int(value)
    if isinstance(default, float):
        return float(value)
    return value


def environment_settings() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, env_name in ENVIRONMENT_KEYS.items():
        raw = os.getenv(env_name)
        if raw not in (None, ""):
            values[key] = _coerce(key, raw)
    return values


def resolve_settings(
    *scopes: tuple[str, Mapping[str, Any] | None],
    strict: bool = False,
    known_keys: Iterable[str] | None = None,
) -> ResolvedSettings:
    resolved = dict(JTL_DEFAULT_SETTINGS)
    sources = {key: "system_defaults" for key in resolved}
    unknown: list[str] = []
    allowed = set(known_keys or JTL_DEFAULT_SETTINGS)

    all_scopes = (("environment", environment_settings()), *scopes)
    for scope_name, raw_values in all_scopes:
        if not isinstance(raw_values, Mapping):
            continue
        for raw_key, raw_value in raw_values.items():
            key = str(raw_key)
            if key not in allowed:
                if key not in unknown:
                    unknown.append(key)
                continue
            resolved[key] = _coerce(key, raw_value)
            sources[key] = scope_name

    if strict and unknown:
        raise ValueError("Unbekannte JTL-Settings: " + ", ".join(sorted(unknown)))

    return ResolvedSettings(resolved, sources, unknown)


def public_settings(settings: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in settings.items() if key not in SECRET_KEYS}
