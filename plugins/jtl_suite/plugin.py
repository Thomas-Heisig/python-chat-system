from __future__ import annotations

import asyncio
from typing import Any, Mapping

import httpx
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from .settings import JTL_DEFAULT_SETTINGS, public_settings, resolve_settings

PLUGIN_ID = "jtl_suite"

PLUGIN_META: dict[str, Any] = {
    "id": PLUGIN_ID,
    "name": "JTL Suite",
    "description": "Zentraler Zugriff auf JTL-Wawi, Shop, WMS, eazyAuction und Business-Analytics.",
    "category": "Business & Analytics",
    "icon": "/api/plugins/jtl_suite/assets/logo.svg",
    "apiKeyRequired": False,
    "status": "implemented",
    "intentPattern": r"\b(jtl|wawi|jtl-shop|shop|wms|eazyauction|erp|auftrag|bestellung|rechnung|angebot|kunde|produkt|artikel|umsatz|bestand|lager|analytics)\b",
    "pluginFrontend": {
        "component": "JTLSuitePage",
        "title": "JTL Suite",
        "description": "Wawi, Shop, WMS, eazyAuction, Analytics und SQL in einer Oberfläche.",
        "sections": [
            {
                "id": "wawi",
                "title": "JTL-Wawi",
                "description": "Produkte, Kunden, Aufträge, Rechnungen und Angebote.",
                "actions": [
                    {"id": "wawi-products", "label": "Produkte", "description": "Produktliste abrufen", "pluginInput": {"action": "list_products", "limit": 20}},
                    {"id": "wawi-customers", "label": "Kunden", "description": "Kundenliste abrufen", "pluginInput": {"action": "list_customers", "limit": 20}},
                    {"id": "wawi-orders", "label": "Aufträge", "description": "Auftragsliste abrufen", "pluginInput": {"action": "list_orders", "limit": 20}},
                    {"id": "wawi-invoices", "label": "Rechnungen", "description": "Rechnungsliste abrufen", "pluginInput": {"action": "list_invoices", "limit": 20}},
                    {"id": "wawi-quotes", "label": "Angebote", "description": "Angebotsliste abrufen", "pluginInput": {"action": "list_quotes", "limit": 20}},
                ],
            },
            {
                "id": "channels",
                "title": "Shop, WMS & Marktplätze",
                "description": "Operative Daten aus den angebundenen JTL-Diensten.",
                "actions": [
                    {"id": "shop-orders", "label": "Shop-Aufträge", "pluginInput": {"action": "list_shop_orders", "limit": 20}},
                    {"id": "wms-picklists", "label": "WMS-Picklisten", "pluginInput": {"action": "list_wms_picklists", "limit": 20}},
                    {"id": "marketplace-listings", "label": "Marketplace-Listings", "pluginInput": {"action": "list_marketplace_listings", "limit": 20}},
                ],
            },
            {
                "id": "analytics",
                "title": "Analytics",
                "description": "Vordefinierte Auswertungen auf Basis der JTL-Datenbank.",
                "actions": [
                    {"id": "sales-overview", "label": "Umsatzübersicht", "pluginInput": {"action": "analytics", "report_type": "sales_overview", "limit": 50}},
                    {"id": "top-products", "label": "Bestseller", "pluginInput": {"action": "analytics", "report_type": "top_selling_products", "limit": 10}},
                    {"id": "customer-value", "label": "Kundenwert", "pluginInput": {"action": "analytics", "report_type": "customer_lifetime_value", "limit": 10}},
                ],
            },
            {
                "id": "database",
                "title": "SQL & Diagnose",
                "description": "Verbindung prüfen, Tabellen untersuchen und sichere SELECT-Abfragen ausführen.",
                "actions": [
                    {"id": "db-test", "label": "Verbindung testen", "pluginInput": {"action": "db_test_connection", "db_service": "wawi"}},
                    {"id": "db-tables", "label": "Tabellen auflisten", "pluginInput": {"action": "db_tables", "db_service": "wawi"}},
                    {"id": "db-query", "label": "SQL-Abfrage", "pluginInput": {"action": "db_query", "db_service": "wawi", "sql": "SELECT TOP 20 * FROM tArtikel ORDER BY kArtikel DESC", "sql_params": {}}},
                    {"id": "open-settings", "label": "Settings öffnen", "openTab": "settings", "pluginInput": {}},
                ],
            },
        ],
    },
    "settingsFields": [
        {"key": "jtl_wawi_base_url", "label": "JTL-Wawi API Base URL", "type": "string", "group": "JTL-Wawi", "default": ""},
        {"key": "jtl_wawi_api_key", "label": "JTL-Wawi API Key", "type": "password", "group": "JTL-Wawi", "default": ""},
        {"key": "jtl_shop_base_url", "label": "JTL-Shop API Base URL", "type": "string", "group": "JTL-Shop", "default": ""},
        {"key": "jtl_shop_api_key", "label": "JTL-Shop API Key", "type": "password", "group": "JTL-Shop", "default": ""},
        {"key": "jtl_wms_base_url", "label": "JTL-WMS API Base URL", "type": "string", "group": "JTL-WMS", "default": ""},
        {"key": "jtl_wms_api_key", "label": "JTL-WMS API Key", "type": "password", "group": "JTL-WMS", "default": ""},
        {"key": "jtl_eazyauction_base_url", "label": "JTL-eazyAuction API Base URL", "type": "string", "group": "JTL-eazyAuction", "default": ""},
        {"key": "jtl_eazyauction_api_key", "label": "JTL-eazyAuction API Key", "type": "password", "group": "JTL-eazyAuction", "default": ""},
        {"key": "request_timeout_seconds", "label": "HTTP-Timeout (Sek.)", "type": "number", "group": "Laufzeit", "default": 20},
        {"key": "verify_tls", "label": "TLS-Zertifikate prüfen", "type": "boolean", "group": "Laufzeit", "default": True},
        {"key": "max_pagination_pages", "label": "Maximale Seiten", "type": "number", "group": "Laufzeit", "default": 10},
        {"key": "jtl_db_host", "label": "SQL Host", "type": "string", "group": "JTL SQL", "default": "localhost"},
        {"key": "jtl_db_port", "label": "SQL Port", "type": "number", "group": "JTL SQL", "default": 1433},
        {"key": "jtl_db_user", "label": "SQL Benutzer", "type": "string", "group": "JTL SQL", "default": "sa"},
        {"key": "jtl_db_password", "label": "SQL Passwort", "type": "password", "group": "JTL SQL", "default": ""},
        {"key": "jtl_db_driver", "label": "ODBC Driver", "type": "string", "group": "JTL SQL", "default": "ODBC Driver 18 for SQL Server"},
        {"key": "jtl_wawi_db_name", "label": "Wawi-Datenbank", "type": "string", "group": "JTL SQL", "default": "eazybusiness"},
        {"key": "jtl_shop_db_name", "label": "Shop-Datenbank", "type": "string", "group": "JTL SQL", "default": ""},
        {"key": "jtl_wms_db_name", "label": "WMS-Datenbank", "type": "string", "group": "JTL SQL", "default": ""},
        {"key": "jtl_eazyauction_db_name", "label": "eazyAuction-Datenbank", "type": "string", "group": "JTL SQL", "default": ""},
        {"key": "jtl_db_encrypt", "label": "SQL Encrypt", "type": "boolean", "group": "JTL SQL", "default": True},
        {"key": "jtl_db_trust_server_certificate", "label": "Server-Zertifikat vertrauen", "type": "boolean", "group": "JTL SQL", "default": False},
        {"key": "sql_query_timeout_seconds", "label": "Query-Timeout (Sek.)", "type": "number", "group": "JTL SQL", "default": 60},
        {"key": "analytics_default_limit", "label": "Standardlimit", "type": "number", "group": "Analytics", "default": 50},
        {"key": "analytics_use_db", "label": "Analytics über SQL", "type": "boolean", "group": "Analytics", "default": False},
    ],
}

API_ACTIONS: dict[str, tuple[str, str, str]] = {
    "list_products": ("wawi", "GET", "/api/v1/products"),
    "get_product": ("wawi", "GET", "/api/v1/products/{item_id}"),
    "list_customers": ("wawi", "GET", "/api/v1/customers"),
    "create_customer": ("wawi", "POST", "/api/v1/customers"),
    "list_orders": ("wawi", "GET", "/api/v1/orders"),
    "create_order": ("wawi", "POST", "/api/v1/orders"),
    "list_invoices": ("wawi", "GET", "/api/v1/invoices"),
    "get_invoice": ("wawi", "GET", "/api/v1/invoices/{item_id}"),
    "list_quotes": ("wawi", "GET", "/api/v1/quotes"),
    "get_quote": ("wawi", "GET", "/api/v1/quotes/{item_id}"),
    "list_shop_orders": ("shop", "GET", "/api/v1/orders"),
    "list_wms_picklists": ("wms", "GET", "/api/v1/picklists"),
    "list_marketplace_listings": ("eazyauction", "GET", "/api/v1/listings"),
}

SERVICE_SETTING_KEYS = {
    "wawi": ("jtl_wawi_base_url", "jtl_wawi_api_key"),
    "shop": ("jtl_shop_base_url", "jtl_shop_api_key"),
    "wms": ("jtl_wms_base_url", "jtl_wms_api_key"),
    "eazyauction": ("jtl_eazyauction_base_url", "jtl_eazyauction_api_key"),
}

DB_NAME_KEYS = {
    "wawi": "jtl_wawi_db_name",
    "shop": "jtl_shop_db_name",
    "wms": "jtl_wms_db_name",
    "eazyauction": "jtl_eazyauction_db_name",
}

class JTLSuitePlugin:
    name = PLUGIN_ID
    description = PLUGIN_META["description"]
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "item_id": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
            "query": {"type": "string"},
            "service": {"type": "string", "enum": list(SERVICE_SETTING_KEYS)},
            "method": {"type": "string"},
            "endpoint": {"type": "string"},
            "payload": {"type": "object"},
            "params": {"type": "object"},
            "db_service": {"type": "string", "enum": list(DB_NAME_KEYS)},
            "sql": {"type": "string"},
            "sql_params": {"type": "object"},
            "table_name": {"type": "string"},
            "report_type": {"type": "string"},
        },
        "required": ["action"],
    }
    output_schema = {"type": "object"}

    async def execute(
        self,
        plugin_input: Mapping[str, Any] | None = None,
        plugin_settings: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        return await execute(plugin_input, plugin_settings, context)


def _resolve(plugin_input: Mapping[str, Any], plugin_settings: Mapping[str, Any] | None, context: Mapping[str, Any] | None) -> dict[str, Any]:
    ctx = context or {}
    resolved = resolve_settings(
        ("tenant", ctx.get("tenant_settings")),
        ("team", ctx.get("team_settings")),
        ("user", ctx.get("user_settings")),
        ("location", ctx.get("location_settings")),
        ("plugin", plugin_settings),
        ("request_override", plugin_input.get("settings") if isinstance(plugin_input.get("settings"), Mapping) else None),
    )
    return resolved.resolved_settings


def _db_url(settings: Mapping[str, Any], service: str, db_name_override: str | None = None) -> URL:
    db_name = db_name_override or str(settings.get(DB_NAME_KEYS[service], ""))
    if not db_name:
        raise ValueError(f"Keine Datenbank für Service '{service}' konfiguriert.")
    query = {
        "driver": str(settings["jtl_db_driver"]),
        "Encrypt": "yes" if settings["jtl_db_encrypt"] else "no",
        "TrustServerCertificate": "yes" if settings["jtl_db_trust_server_certificate"] else "no",
    }
    return URL.create(
        "mssql+pyodbc",
        username=str(settings["jtl_db_user"]),
        password=str(settings["jtl_db_password"]),
        host=str(settings["jtl_db_host"]),
        port=int(settings["jtl_db_port"]),
        database=db_name,
        query=query,
    )


def _validate_select(sql: str, allow_cross_database: bool) -> None:
    normalized = " ".join(sql.strip().lower().split())
    if not normalized.startswith(("select ", "with ")):
        raise ValueError("Nur SELECT- und WITH-Abfragen sind erlaubt.")
    forbidden = (" insert ", " update ", " delete ", " drop ", " alter ", " truncate ", " merge ", " exec ", " execute ")
    padded = f" {normalized} "
    if any(token in padded for token in forbidden):
        raise ValueError("Die SQL-Abfrage enthält eine nicht erlaubte Anweisung.")
    if not allow_cross_database and ".." in normalized:
        raise ValueError("Cross-Database-Zugriffe sind deaktiviert.")


async def _api_request(settings: Mapping[str, Any], service: str, method: str, endpoint: str, *, params: Mapping[str, Any] | None = None, payload: Any = None) -> dict[str, Any]:
    base_key, api_key_key = SERVICE_SETTING_KEYS[service]
    base_url = str(settings.get(base_key, "")).rstrip("/")
    if not base_url:
        raise ValueError(f"Für '{service}' ist keine API Base URL konfiguriert.")
    headers = {"Accept": "application/json"}
    api_key = str(settings.get(api_key_key, ""))
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-Api-Key"] = api_key
    timeout = float(settings["api_write_timeout"] if method.upper() != "GET" else settings["api_read_timeout"])
    async with httpx.AsyncClient(timeout=timeout, verify=bool(settings["verify_tls"])) as client:
        response = await client.request(method.upper(), f"{base_url}/{endpoint.lstrip('/')}", headers=headers, params=dict(params or {}), json=payload)
    content_type = response.headers.get("content-type", "")
    data: Any = response.json() if "json" in content_type else response.text
    if response.is_error:
        raise RuntimeError(f"JTL API {response.status_code}: {data}")
    return {"success": True, "service": service, "status_code": response.status_code, "data": data}


def _db_execute(settings: Mapping[str, Any], service: str, operation: str, plugin_input: Mapping[str, Any]) -> dict[str, Any]:
    engine = create_engine(
        _db_url(settings, service, str(plugin_input.get("db_name") or "") or None),
        pool_size=int(settings["db_pool_size"]),
        pool_pre_ping=True,
        connect_args={"timeout": int(settings["jtl_db_timeout_seconds"])},
    )
    try:
        if operation == "db_test_connection":
            with engine.connect() as connection:
                row = connection.execute(text("SELECT DB_NAME() AS database_name, @@SERVERNAME AS server_name")).mappings().one()
            return {"success": True, "service": service, "data": dict(row)}
        if operation == "db_tables":
            names = inspect(engine).get_table_names()
            return {"success": True, "service": service, "data": {"tables": names, "count": len(names)}}
        if operation == "db_describe_table":
            table_name = str(plugin_input.get("table_name", "")).strip()
            if not table_name:
                raise ValueError("table_name fehlt.")
            columns = inspect(engine).get_columns(table_name)
            return {"success": True, "service": service, "data": {"table": table_name, "columns": [{"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable")} for c in columns]}}
        sql = str(plugin_input.get("sql", "")).strip()
        _validate_select(sql, bool(settings["allow_cross_database_joins"]))
        with engine.connect() as connection:
            rows = connection.execute(text(sql), dict(plugin_input.get("sql_params") or {})).mappings().fetchmany(int(plugin_input.get("limit") or 1000))
        return {"success": True, "service": service, "data": {"rows": [dict(row) for row in rows], "count": len(rows)}}
    finally:
        engine.dispose()


def _analytics_sql(report_type: str, limit: int) -> str:
    reports = {
        "sales_overview": "SELECT COUNT(*) AS order_count, SUM(fBrutto) AS gross_revenue, AVG(fBrutto) AS average_order_value FROM Verkauf.tAuftrag",
        "top_selling_products": f"SELECT TOP {limit} cArtNr AS sku, cName AS product_name, SUM(fAnzahl) AS quantity FROM Verkauf.tAuftragPosition GROUP BY cArtNr, cName ORDER BY quantity DESC",
        "customer_lifetime_value": f"SELECT TOP {limit} kKunde AS customer_id, SUM(fBrutto) AS lifetime_value FROM Verkauf.tAuftrag GROUP BY kKunde ORDER BY lifetime_value DESC",
    }
    if report_type not in reports:
        raise ValueError(f"Unbekannter Report: {report_type}")
    return reports[report_type]


async def execute(
    plugin_input: Mapping[str, Any] | None = None,
    plugin_settings: Mapping[str, Any] | None = None,
    context: Mapping[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    request = dict(plugin_input or {})
    action = str(request.get("action", "list_products"))
    settings = _resolve(request, plugin_settings, context)
    try:
        if action == "settings.resolved":
            return {"success": True, "action": action, "data": public_settings(settings)}
        if action in API_ACTIONS:
            service, method, endpoint_template = API_ACTIONS[action]
            endpoint = endpoint_template.format(item_id=request.get("item_id", ""))
            params = dict(request.get("params") or {})
            if request.get("limit") is not None:
                params.setdefault("limit", request["limit"])
            if request.get("query"):
                params.setdefault("query", request["query"])
            payload = request.get("payload") or request.get("customer") or request.get("order") or request.get("product")
            result = await _api_request(settings, service, method, endpoint, params=params, payload=payload)
            return {**result, "action": action}
        if action == "custom_request":
            service = str(request.get("service", "wawi"))
            result = await _api_request(settings, service, str(request.get("method", "GET")), str(request.get("endpoint", "")), params=request.get("params"), payload=request.get("payload"))
            return {**result, "action": action}
        if action in {"db_test_connection", "db_query", "db_tables", "db_describe_table"}:
            service = str(request.get("db_service", "wawi"))
            result = await asyncio.to_thread(_db_execute, settings, service, action, request)
            return {**result, "action": action}
        if action == "analytics":
            report_type = str(request.get("report_type", "sales_overview"))
            limit = int(request.get("limit") or settings["analytics_default_limit"])
            analytics_request = {**request, "sql": _analytics_sql(report_type, limit), "limit": limit}
            result = await asyncio.to_thread(_db_execute, settings, "wawi", "db_query", analytics_request)
            return {**result, "action": action, "report_type": report_type}
        raise ValueError(f"Nicht unterstützte Aktion: {action}")
    except (ValueError, RuntimeError, SQLAlchemyError, httpx.HTTPError) as exc:
        return {"success": False, "action": action, "error": str(exc)}


plugin = JTLSuitePlugin()
