from __future__ import annotations

import asyncio
import base64
import os
from datetime import datetime
from typing import Any, cast

import httpx
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError


PLUGIN_META: dict[str, Any] = {
    "id": "jtl_suite",
    "name": "JTL Suite (Enterprise)",
    "description": "Maximale JTL-Integration: Wawi, Shop, WMS, eazyAuction inkl. Rechnungen, Angebote, Analytics, Bulk-Export und hybridem API/SQL-Routing.",
    "category": "📊 Business & Analytics",
    "apiKeyRequired": True,
    "intentPattern": r"\b(jtl|wawi|jtl-shop|shop|wms|eazyauction|erp|auftrag|bestellung|rechnung|angebot|kunde|produkt|artikel|umsatz|bestand|lager|analytics)\b",
    "status": "implemented",
    "pluginFrontend": {
        "title": "JTL Suite Frontend",
        "description": "Schnelle Einstiege fuer Wawi, Shop, WMS, eazyAuction, Rechnungen, Angebote und SQL-Abfragen.",
        "sections": [
            {
                "id": "wawi",
                "title": "JTL-Wawi",
                "description": "Produkte, Kunden, Auftraege, Rechnungen und Angebote direkt abrufen.",
                "actions": [
                    {
                        "id": "wawi-products",
                        "label": "Produkte anzeigen",
                        "description": "Befuellt den Runner mit einer Produktlisten-Abfrage.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_products", "limit": 20},
                    },
                    {
                        "id": "wawi-customers",
                        "label": "Kunden anzeigen",
                        "description": "Befuellt den Runner mit einer Kundenlisten-Abfrage.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_customers", "limit": 20},
                    },
                    {
                        "id": "wawi-orders",
                        "label": "Auftraege anzeigen",
                        "description": "Befuellt den Runner mit einer Auftragslisten-Abfrage.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_orders", "limit": 20},
                    },
                    {
                        "id": "wawi-invoices",
                        "label": "Rechnungen anzeigen",
                        "description": "Befuellt den Runner mit einer Rechnungslisten-Abfrage.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_invoices", "limit": 20},
                    },
                    {
                        "id": "wawi-quotes",
                        "label": "Angebote anzeigen",
                        "description": "Befuellt den Runner mit einer Angebotslisten-Abfrage.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_quotes", "limit": 20},
                    },
                ],
            },
            {
                "id": "shop-wms",
                "title": "Shop und WMS",
                "description": "Typische Abfragen fuer Shop-Auftraege, WMS-Picklisten und Marketplace-Listings.",
                "actions": [
                    {
                        "id": "shop-orders",
                        "label": "Shop-Auftraege",
                        "description": "Befuellt den Runner mit einer Shop-Auftragsliste.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_shop_orders", "limit": 20},
                    },
                    {
                        "id": "wms-picklists",
                        "label": "WMS-Picklisten",
                        "description": "Befuellt den Runner mit einer Picklisten-Abfrage.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_wms_picklists", "limit": 20},
                    },
                    {
                        "id": "marketplace-listings",
                        "label": "Marketplace-Listings",
                        "description": "Befuellt den Runner mit einer eazyAuction-Listing-Abfrage.",
                        "openTab": "manual",
                        "pluginInput": {"action": "list_marketplace_listings", "limit": 20},
                    },
                ],
            },
            {
                "id": "analytics",
                "title": "Analytics & Reports",
                "description": "Vordefinierte Business-Reports direkt aus der Datenbank.",
                "actions": [
                    {
                        "id": "analytics-sales",
                        "label": "Umsatzübersicht",
                        "description": "Zeigt Umsatz, Anzahl Bestellungen und durchschnittlichen Bestellwert.",
                        "openTab": "manual",
                        "pluginInput": {"action": "analytics", "report_type": "sales_overview", "date_from": "2026-01-01"},
                    },
                    {
                        "id": "analytics-top-products",
                        "label": "Bestseller",
                        "description": "Zeigt die umsatzstärksten Produkte.",
                        "openTab": "manual",
                        "pluginInput": {"action": "analytics", "report_type": "top_selling_products", "limit": 10},
                    },
                    {
                        "id": "analytics-clv",
                        "label": "Kundenwert (CLV)",
                        "description": "Zeigt Kunden mit dem höchsten Lifetime-Value.",
                        "openTab": "manual",
                        "pluginInput": {"action": "analytics", "report_type": "customer_lifetime_value", "limit": 10},
                    },
                ],
            },
            {
                "id": "sql",
                "title": "SQL und Verbindung",
                "description": "Direkter Zugriff auf die JTL-Datenbanken fuer Diagnose und Reporting.",
                "actions": [
                    {
                        "id": "sql-test",
                        "label": "DB-Verbindung testen",
                        "description": "Befuellt den Runner fuer einen schnellen SQL-Verbindungstest.",
                        "openTab": "manual",
                        "pluginInput": {"action": "db_test_connection", "db_service": "wawi"},
                    },
                    {
                        "id": "sql-query",
                        "label": "SQL-Abfrage vorbereiten",
                        "description": "Legt eine sichere SELECT-Abfrage gegen die Wawi-Datenbank vor.",
                        "openTab": "manual",
                        "pluginInput": {
                            "action": "db_query",
                            "db_service": "wawi",
                            "sql": "SELECT TOP 20 * FROM tArtikel ORDER BY kArtikel DESC",
                            "sql_params": {},
                        },
                    },
                    {
                        "id": "sql-tables",
                        "label": "Tabellen auflisten",
                        "description": "Zeigt alle Tabellen der Wawi-Datenbank.",
                        "openTab": "manual",
                        "pluginInput": {"action": "db_tables", "db_service": "wawi"},
                    },
                    {
                        "id": "sql-settings",
                        "label": "SQL-Settings oeffnen",
                        "description": "Springt in die Settings-Ansicht des Plugins fuer Host, Login und Datenbanknamen.",
                        "openTab": "settings",
                    },
                ],
            },
        ],
    },
    "settingsFields": [
        # ---------- JTL-Wawi ----------
        {"key": "jtl_wawi_base_url", "label": "JTL-Wawi API Base URL", "type": "string", "group": "JTL-Wawi", "default": ""},
        {"key": "jtl_wawi_api_key", "label": "JTL-Wawi API Key", "type": "string", "group": "JTL-Wawi", "default": ""},
        # ---------- JTL-Shop ----------
        {"key": "jtl_shop_base_url", "label": "JTL-Shop API Base URL", "type": "string", "group": "JTL-Shop", "default": ""},
        {"key": "jtl_shop_api_key", "label": "JTL-Shop API Key", "type": "string", "group": "JTL-Shop", "default": ""},
        # ---------- JTL-WMS ----------
        {"key": "jtl_wms_base_url", "label": "JTL-WMS API Base URL", "type": "string", "group": "JTL-WMS", "default": ""},
        {"key": "jtl_wms_api_key", "label": "JTL-WMS API Key", "type": "string", "group": "JTL-WMS", "default": ""},
        # ---------- JTL-eazyAuction ----------
        {"key": "jtl_eazyauction_base_url", "label": "JTL-eazyAuction API Base URL", "type": "string", "group": "JTL-eazyAuction", "default": ""},
        {"key": "jtl_eazyauction_api_key", "label": "JTL-eazyAuction API Key", "type": "string", "group": "JTL-eazyAuction", "default": ""},
        # ---------- Laufzeit ----------
        {"key": "request_timeout_seconds", "label": "HTTP Timeout (Sek.)", "type": "number", "group": "Laufzeit", "default": 20},
        {"key": "verify_tls", "label": "TLS Zertifikat prüfen", "type": "boolean", "group": "Laufzeit", "default": True},
        {"key": "max_pagination_pages", "label": "Max. Seiten bei fetch_all", "type": "number", "group": "Laufzeit", "default": 10},
        {"key": "retry_max_attempts", "label": "Wiederholungen bei API-Fehlern", "type": "number", "group": "Laufzeit", "default": 3},
        {"key": "retry_backoff_factor", "label": "Retry-Backoff-Faktor", "type": "number", "group": "Laufzeit", "default": 1.0},
        {"key": "api_read_timeout", "label": "API Lese-Timeout (Sek.)", "type": "number", "group": "Laufzeit", "default": 30},
        {"key": "api_write_timeout", "label": "API Schreib-Timeout (Sek.)", "type": "number", "group": "Laufzeit", "default": 60},
        # ---------- JTL SQL ----------
        {"key": "jtl_db_host", "label": "JTL SQL Host", "type": "string", "group": "JTL SQL", "default": "localhost"},
        {"key": "jtl_db_port", "label": "JTL SQL Port", "type": "number", "group": "JTL SQL", "default": 1433},
        {"key": "jtl_db_user", "label": "JTL SQL Benutzer", "type": "string", "group": "JTL SQL", "default": "sa"},
        {"key": "jtl_db_password", "label": "JTL SQL Passwort", "type": "string", "group": "JTL SQL", "default": "sa"},
        {"key": "jtl_db_driver", "label": "SQL Driver", "type": "string", "group": "JTL SQL", "default": "ODBC Driver 18 for SQL Server"},
        {"key": "jtl_wawi_db_name", "label": "JTL-Wawi DB", "type": "string", "group": "JTL SQL", "default": "eazybusiness"},
        {"key": "jtl_shop_db_name", "label": "JTL-Shop DB", "type": "string", "group": "JTL SQL", "default": ""},
        {"key": "jtl_wms_db_name", "label": "JTL-WMS DB", "type": "string", "group": "JTL SQL", "default": ""},
        {"key": "jtl_eazyauction_db_name", "label": "JTL-eazyAuction DB", "type": "string", "group": "JTL SQL", "default": ""},
        {"key": "jtl_db_encrypt", "label": "SQL Encrypt", "type": "boolean", "group": "JTL SQL", "default": False},
        {"key": "jtl_db_trust_server_certificate", "label": "Trust Server Certificate", "type": "boolean", "group": "JTL SQL", "default": True},
        {"key": "jtl_db_timeout_seconds", "label": "SQL Timeout (Sek.)", "type": "number", "group": "JTL SQL", "default": 20},
        {"key": "sql_query_timeout_seconds", "label": "SQL Query Timeout (Sek.)", "type": "number", "group": "JTL SQL", "default": 60},
        {"key": "db_pool_size", "label": "SQL Connection Pool Size", "type": "number", "group": "JTL SQL", "default": 5},
        {"key": "allow_cross_database_joins", "label": "Cross-DB-Joins erlauben", "type": "boolean", "group": "JTL SQL", "default": False},
        {"key": "jtl_mandant_filter", "label": "Standard-Mandant (kMandant) für Queries", "type": "number", "group": "JTL SQL", "default": 0},
        # ---------- Analytics ----------
        {"key": "analytics_default_limit", "label": "Standard-Limit für Reports", "type": "number", "group": "Analytics", "default": 50},
        {"key": "analytics_use_db", "label": "Analytics immer via DB (sonst hybrid)", "type": "boolean", "group": "Analytics", "default": False},
    ],
}


class JTLSuitePlugin:
    name = "jtl_suite"
    description = "Maximale JTL-Integration"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    # Bestehende Aktionen (kompatibel)
                    "list_products",
                    "get_product",
                    "list_customers",
                    "create_customer",
                    "list_orders",
                    "create_order",
                    "update_order_status",
                    "sync_stock_to_shop",
                    "list_shop_orders",
                    "list_wms_picklists",
                    "list_marketplace_listings",
                    "db_test_connection",
                    "db_query",
                    "custom_request",
                    # Neue Aktionen
                    "list_invoices",
                    "get_invoice",
                    "create_invoice_from_order",
                    "download_invoice_pdf",
                    "list_quotes",
                    "get_quote",
                    "update_quote",
                    "convert_quote_to_order",
                    "list_warehouses",
                    "get_stock",
                    "adjust_stock",
                    "list_stock_movements",
                    "list_shipments",
                    "get_shipment",
                    "create_shipment",
                    "list_payments",
                    "get_payment",
                    "create_payment",
                    "analytics",
                    "db_tables",
                    "db_describe_table",
                    # Bulk-Fetch (optional)
                    "fetch_all_products",
                    "fetch_all_customers",
                    "fetch_all_orders",
                    "fetch_all_invoices",
                    "fetch_all_quotes",
                ],
                "default": "list_products",
                "description": "Aktion fuer die JTL-Produkte.",
            },
            "item_id": {
                "type": "string",
                "description": "Ressourcen-ID fuer get_*, update_*, download_* etc.",
            },
            "status": {
                "type": "string",
                "description": "Neuer Auftragsstatus fuer update_order_status.",
            },
            "comment": {
                "type": "string",
                "description": "Kommentar für add_order_comment.",
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "minimum": 1,
                "maximum": 1000,
            },
            "fetch_all": {
                "type": "boolean",
                "default": False,
                "description": "Alle Seiten über Paginierung abrufen (nur bei list_*).",
            },
            "query": {
                "type": "string",
                "description": "Optionaler Suchbegriff fuer Listen-Endpunkte.",
            },
            "date_from": {
                "type": "string",
                "format": "date",
                "description": "Startdatum (YYYY-MM-DD) für Analytics oder gefilterte Listen.",
            },
            "date_to": {
                "type": "string",
                "format": "date",
                "description": "Enddatum (YYYY-MM-DD).",
            },
            "group_by": {
                "type": "string",
                "enum": ["day", "week", "month", "quarter", "year", "product", "customer"],
                "description": "Für Analytics: Gruppierung.",
            },
            "report_type": {
                "type": "string",
                "enum": [
                    "sales_overview",
                    "top_selling_products",
                    "customer_lifetime_value",
                    "slow_moving_inventory",
                    "order_fulfillment_kpi",
                    "invoice_payment_behavior"
                ],
                "description": "Vordefinierter Report für Analytics.",
            },
            "aggregate": {
                "type": "string",
                "enum": ["sum", "avg", "count", "min", "max"],
                "description": "Aggregatfunktion für Analytics.",
            },
            "customer": {
                "type": "object",
                "description": "Kundendaten fuer create_customer.",
            },
            "order": {
                "type": "object",
                "description": "Auftragsdaten fuer create_order.",
            },
            "invoice": {
                "type": "object",
                "description": "Rechnungsdaten für create_invoice (falls unterstützt).",
            },
            "quote": {
                "type": "object",
                "description": "Angebotsdaten für update_quote.",
            },
            "product": {
                "type": "object",
                "description": "Produktdaten für create_product / update_product.",
            },
            "stock_updates": {
                "type": "array",
                "description": "Bestandsdaten fuer sync_stock_to_shop.",
                "items": {
                    "type": "object",
                    "properties": {
                        "sku": {"type": "string"},
                        "quantity": {"type": "number"},
                    },
                    "required": ["sku", "quantity"],
                },
            },
            "quantity": {
                "type": "number",
                "description": "Menge für adjust_stock.",
            },
            "service": {
                "type": "string",
                "enum": ["wawi", "shop", "wms", "eazyauction"],
                "description": "Nur fuer custom_request: JTL-Service.",
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                "description": "Nur fuer custom_request: HTTP-Methode.",
            },
            "endpoint": {
                "type": "string",
                "description": "Nur fuer custom_request: relativer Endpunkt, z. B. /api/v1/orders.",
            },
            "payload": {
                "type": "object",
                "description": "Nur fuer custom_request: JSON-Payload.",
            },
            "params": {
                "type": "object",
                "description": "Nur fuer custom_request: Query-Parameter.",
            },
            "db_service": {
                "type": "string",
                "enum": ["wawi", "shop", "wms", "eazyauction"],
                "description": "JTL-Dienst fuer direkten DB-Zugriff.",
            },
            "db_name": {
                "type": "string",
                "description": "Optionaler Datenbankname. Ueberschreibt den konfigurierten Namen.",
            },
            "sql": {
                "type": "string",
                "description": "SQL-Select-Statement fuer db_query.",
            },
            "sql_params": {
                "type": "object",
                "description": "Named SQL-Parameter, z. B. {\"limit\": 20}.",
            },
            "table_name": {
                "type": "string",
                "description": "Für db_describe_table: Tabellenname.",
            },
        },
        "required": ["action"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "service": {"type": "string"},
            "action": {"type": "string"},
            "status_code": {"type": "integer"},
            "data": {"type": "object"},
            "message": {"type": "string"},
            "pagination": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    # ------------------------------------------------------------
    #  ENTITÄTSKONFIGURATION (für generischen Dispatcher)
    #  Sowohl Plural als auch Singular, damit alte und neue Aktionen funktionieren.
    # ------------------------------------------------------------
    ENTITY_CONFIG: dict[str, dict[str, str]] = {
        # Plural (für list_*)
        "products": {"api_path": "/api/v1/products", "db_table": "tArtikel", "pk": "kArtikel"},
        "customers": {"api_path": "/api/v1/customers", "db_table": "tKunde", "pk": "kKunde"},
        "orders": {"api_path": "/api/v1/orders", "db_table": "tBestellung", "pk": "kBestellung"},
        "invoices": {"api_path": "/api/v1/invoices", "db_table": "tRechnung", "pk": "kRechnung"},
        "quotes": {"api_path": "/api/v1/quotes", "db_table": "tAngebot", "pk": "kAngebot"},
        "warehouses": {"api_path": "/api/v1/warehouses", "db_table": "tLager", "pk": "kLager"},
        "shipments": {"api_path": "/api/v1/shipments", "db_table": "tVersand", "pk": "kVersand"},
        "payments": {"api_path": "/api/v1/payments", "db_table": "tZahlung", "pk": "kZahlung"},
        # Singular (für get_*, create_*, update_*, delete_*)
        "product": {"api_path": "/api/v1/products", "db_table": "tArtikel", "pk": "kArtikel"},
        "customer": {"api_path": "/api/v1/customers", "db_table": "tKunde", "pk": "kKunde"},
        "order": {"api_path": "/api/v1/orders", "db_table": "tBestellung", "pk": "kBestellung"},
        "invoice": {"api_path": "/api/v1/invoices", "db_table": "tRechnung", "pk": "kRechnung"},
        "quote": {"api_path": "/api/v1/quotes", "db_table": "tAngebot", "pk": "kAngebot"},
        "warehouse": {"api_path": "/api/v1/warehouses", "db_table": "tLager", "pk": "kLager"},
        "shipment": {"api_path": "/api/v1/shipments", "db_table": "tVersand", "pk": "kVersand"},
        "payment": {"api_path": "/api/v1/payments", "db_table": "tZahlung", "pk": "kZahlung"},
    }

    # Vorgefertigte Analytics-SQL-Templates
    ANALYTICS_TEMPLATES: dict[str, str] = {
        "sales_overview": """
            SELECT 
                {group_by_sql} AS period,
                COUNT(DISTINCT kBestellung) AS order_count,
                SUM(fGesamtsumme) AS total_revenue,
                AVG(fGesamtsumme) AS avg_order_value
            FROM tBestellung
            WHERE dErstellt BETWEEN :date_from AND :date_to
              AND nStatus >= 2
            GROUP BY {group_by_sql}
            ORDER BY period
        """,
        "top_selling_products": """
            SELECT TOP (:limit)
                p.cName AS product_name,
                p.cArtNr AS sku,
                SUM(bp.fAnzahl) AS quantity_sold,
                SUM(bp.fPreis * bp.fAnzahl) AS revenue
            FROM tBestellposition bp
            JOIN tArtikel p ON bp.kArtikel = p.kArtikel
            JOIN tBestellung b ON bp.kBestellung = b.kBestellung
            WHERE b.dErstellt BETWEEN :date_from AND :date_to
              AND b.nStatus >= 2
            GROUP BY p.cName, p.cArtNr
            ORDER BY revenue DESC
        """,
        "customer_lifetime_value": """
            SELECT TOP (:limit)
                k.cVorname + ' ' + k.cNachname AS customer,
                k.kKunde AS customer_id,
                COUNT(b.kBestellung) AS order_count,
                SUM(b.fGesamtsumme) AS lifetime_value
            FROM tKunde k
            JOIN tBestellung b ON k.kKunde = b.kKunde
            WHERE b.nStatus >= 2
            GROUP BY k.cVorname, k.cNachname, k.kKunde
            ORDER BY lifetime_value DESC
        """,
        "slow_moving_inventory": """
            SELECT TOP (:limit)
                p.cName AS product_name,
                p.cArtNr AS sku,
                ISNULL(SUM(bp.fAnzahl), 0) AS sold_last_90_days,
                l.fBestand AS current_stock,
                CASE WHEN ISNULL(SUM(bp.fAnzahl), 0) > 0 
                     THEN l.fBestand / SUM(bp.fAnzahl) 
                     ELSE 9999 END AS days_of_stock
            FROM tArtikel p
            LEFT JOIN tLagerbestand l ON p.kArtikel = l.kArtikel
            LEFT JOIN tBestellposition bp ON p.kArtikel = bp.kArtikel
            LEFT JOIN tBestellung b ON bp.kBestellung = b.kBestellung 
                AND b.dErstellt >= DATEADD(day, -90, GETDATE())
            GROUP BY p.cName, p.cArtNr, l.fBestand
            HAVING ISNULL(l.fBestand, 0) > 0
            ORDER BY days_of_stock DESC
        """,
        "order_fulfillment_kpi": """
            SELECT 
                AVG(DATEDIFF(hour, dErstellt, dVersendet)) AS avg_hours_to_ship,
                AVG(DATEDIFF(day, dErstellt, dBezahlt)) AS avg_days_to_pay,
                COUNT(CASE WHEN dVersendet IS NOT NULL THEN 1 END) * 1.0 / COUNT(*) AS fulfillment_rate
            FROM tBestellung
            WHERE dErstellt BETWEEN :date_from AND :date_to
        """,
        "invoice_payment_behavior": """
            SELECT 
                DATEDIFF(day, r.dErstellt, z.dZahlungseingang) AS days_to_pay,
                COUNT(*) AS frequency
            FROM tRechnung r
            JOIN tZahlung z ON r.kRechnung = z.kRechnung
            WHERE r.dErstellt BETWEEN :date_from AND :date_to
            GROUP BY DATEDIFF(day, r.dErstellt, z.dZahlungseingang)
            ORDER BY days_to_pay
        """
    }

    # ------------------------------------------------------------
    #  KONSTRUKTOR & SETTINGS (kompatibel zur Basisversion)
    # ------------------------------------------------------------
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self._settings: dict[str, Any] = settings if isinstance(settings, dict) else {}

        self.timeout_seconds: float = 20.0
        self.verify_tls: bool = True

        self.wawi_base_url: str = os.getenv("JTL_WAWI_BASE_URL", "")
        self.wawi_api_key: str = os.getenv("JTL_WAWI_API_KEY", "")

        self.shop_base_url: str = os.getenv("JTL_SHOP_BASE_URL", "")
        self.shop_api_key: str = os.getenv("JTL_SHOP_API_KEY", "")

        self.wms_base_url: str = os.getenv("JTL_WMS_BASE_URL", "")
        self.wms_api_key: str = os.getenv("JTL_WMS_API_KEY", "")

        self.eazyauction_base_url: str = os.getenv("JTL_EAZYAUCTION_BASE_URL", "")
        self.eazyauction_api_key: str = os.getenv("JTL_EAZYAUCTION_API_KEY", "")

        self.db_host: str = os.getenv("JTL_DB_HOST", "localhost")
        self.db_port: int = self._int_value(os.getenv("JTL_DB_PORT", 1433), default=1433, min_value=1, max_value=65535)
        self.db_user: str = os.getenv("JTL_DB_USER", "sa")
        self.db_password: str = os.getenv("JTL_DB_PASSWORD", "sa")
        self.db_driver: str = os.getenv("JTL_DB_DRIVER", "ODBC Driver 18 for SQL Server")
        self.wawi_db_name: str = os.getenv("JTL_WAWI_DB_NAME", "eazybusiness")
        self.shop_db_name: str = os.getenv("JTL_SHOP_DB_NAME", "")
        self.wms_db_name: str = os.getenv("JTL_WMS_DB_NAME", "")
        self.eazyauction_db_name: str = os.getenv("JTL_EAZYAUCTION_DB_NAME", "")
        self.db_encrypt: bool = self._env_bool("JTL_DB_ENCRYPT", False)
        self.db_trust_server_certificate: bool = self._env_bool("JTL_DB_TRUST_SERVER_CERTIFICATE", True)
        self.db_timeout_seconds: float = float(
            self._int_value(os.getenv("JTL_DB_TIMEOUT_SECONDS", 20), default=20, min_value=5, max_value=120)
        )

        # Neue Laufzeitparameter (mit Defaults)
        self.max_pagination_pages: int = 10
        self.retry_max_attempts: int = 3
        self.retry_backoff_factor: float = 1.0
        self.api_read_timeout: float = 30.0
        self.api_write_timeout: float = 60.0
        self.sql_query_timeout: int = 60
        self.db_pool_size: int = 5
        self.allow_cross_db_joins: bool = False
        self.mandant_filter: int = 0
        self.analytics_default_limit: int = 50
        self.analytics_use_db: bool = False

        self._apply_settings_overrides()
        self._db_engines: dict[str, Any] = {}

    def set_settings(self, settings: dict[str, Any]) -> None:
        self._settings = settings
        self._apply_settings_overrides()

    def _integration_settings(self) -> dict[str, Any]:
        raw = self._settings.get("integrations", {})
        if isinstance(raw, dict):
            return cast(dict[str, Any], raw)
        return {}

    def _resolve_setting_str(self, key: str, current: str) -> str:
        direct = self._settings.get(key)
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        integration_value = self._integration_settings().get(key)
        if isinstance(integration_value, str) and integration_value.strip():
            return integration_value.strip()
        return current.strip()

    def _normalize_base_url(self, value: str) -> str:
        return value.strip().rstrip("/")

    def _apply_settings_overrides(self) -> None:
        s = self._settings

        def get_int(k: str, default: int, mn: int | None = None, mx: int | None = None) -> int:
            val = s.get(k)
            if val is not None:
                try:
                    parsed = int(val)
                    if mn is not None:
                        parsed = max(mn, parsed)
                    if mx is not None:
                        parsed = min(mx, parsed)
                    return parsed
                except (ValueError, TypeError):
                    pass
            return default

        def get_bool(k: str, default: bool) -> bool:
            val = s.get(k)
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in {"1", "true", "yes", "on"}
            return default

        def get_float(k: str, default: float) -> float:
            val = s.get(k)
            if isinstance(val, (int, float)):
                return float(val)
            return default

        # Alte Werte (kompatibel)
        timeout_value = s.get("request_timeout_seconds")
        if isinstance(timeout_value, (int, float)):
            self.timeout_seconds = max(5.0, float(timeout_value))

        tls_value = s.get("verify_tls")
        if isinstance(tls_value, bool):
            self.verify_tls = tls_value

        self.wawi_base_url = self._normalize_base_url(self._resolve_setting_str("jtl_wawi_base_url", self.wawi_base_url))
        self.wawi_api_key = self._resolve_setting_str("jtl_wawi_api_key", self.wawi_api_key)
        self.shop_base_url = self._normalize_base_url(self._resolve_setting_str("jtl_shop_base_url", self.shop_base_url))
        self.shop_api_key = self._resolve_setting_str("jtl_shop_api_key", self.shop_api_key)
        self.wms_base_url = self._normalize_base_url(self._resolve_setting_str("jtl_wms_base_url", self.wms_base_url))
        self.wms_api_key = self._resolve_setting_str("jtl_wms_api_key", self.wms_api_key)
        self.eazyauction_base_url = self._normalize_base_url(
            self._resolve_setting_str("jtl_eazyauction_base_url", self.eazyauction_base_url)
        )
        self.eazyauction_api_key = self._resolve_setting_str("jtl_eazyauction_api_key", self.eazyauction_api_key)

        self.db_host = self._resolve_setting_str("jtl_db_host", self.db_host)
        self.db_user = self._resolve_setting_str("jtl_db_user", self.db_user)
        self.db_password = self._resolve_setting_str("jtl_db_password", self.db_password)
        self.db_driver = self._resolve_setting_str("jtl_db_driver", self.db_driver)
        self.wawi_db_name = self._resolve_setting_str("jtl_wawi_db_name", self.wawi_db_name)
        self.shop_db_name = self._resolve_setting_str("jtl_shop_db_name", self.shop_db_name)
        self.wms_db_name = self._resolve_setting_str("jtl_wms_db_name", self.wms_db_name)
        self.eazyauction_db_name = self._resolve_setting_str("jtl_eazyauction_db_name", self.eazyauction_db_name)

        db_port_value = s.get("jtl_db_port")
        if db_port_value is not None:
            self.db_port = self._int_value(db_port_value, default=self.db_port, min_value=1, max_value=65535)

        db_timeout_value = s.get("jtl_db_timeout_seconds")
        if isinstance(db_timeout_value, (int, float)):
            self.db_timeout_seconds = float(max(5.0, min(120.0, float(db_timeout_value))))

        db_encrypt_value = s.get("jtl_db_encrypt")
        if isinstance(db_encrypt_value, bool):
            self.db_encrypt = db_encrypt_value

        db_tsc_value = s.get("jtl_db_trust_server_certificate")
        if isinstance(db_tsc_value, bool):
            self.db_trust_server_certificate = db_tsc_value

        # Neue Werte
        self.max_pagination_pages = get_int("max_pagination_pages", self.max_pagination_pages, mn=1)
        self.retry_max_attempts = get_int("retry_max_attempts", self.retry_max_attempts, mn=1)
        self.retry_backoff_factor = get_float("retry_backoff_factor", self.retry_backoff_factor)
        self.api_read_timeout = get_float("api_read_timeout", self.api_read_timeout)
        self.api_write_timeout = get_float("api_write_timeout", self.api_write_timeout)
        self.sql_query_timeout = get_int("sql_query_timeout_seconds", self.sql_query_timeout, mn=5)
        self.db_pool_size = get_int("db_pool_size", self.db_pool_size, mn=1, mx=20)
        self.allow_cross_db_joins = get_bool("allow_cross_database_joins", self.allow_cross_db_joins)
        self.mandant_filter = get_int("jtl_mandant_filter", self.mandant_filter)
        self.analytics_default_limit = get_int("analytics_default_limit", self.analytics_default_limit, mn=1)
        self.analytics_use_db = get_bool("analytics_use_db", self.analytics_use_db)

    # ------------------------------------------------------------
    #  HILFSFUNKTIONEN (kompatibel)
    # ------------------------------------------------------------
    def _env_bool(self, key: str, default: bool) -> bool:
        raw = str(os.getenv(key, str(default))).strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True
        if raw in {"0", "false", "no", "off"}:
            return False
        return default

    def _int_value(self, raw: Any, default: int, min_value: int, max_value: int) -> int:
        try:
            parsed = int(raw)
        except Exception:
            return default
        return max(min_value, min(max_value, parsed))

    def _dict_value(self, raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return cast(dict[str, Any], raw)
        return {}

    def _service_config(self, service: str) -> tuple[str, str]:
        service_key = service.lower().strip()
        if service_key == "wawi":
            return self.wawi_base_url, self.wawi_api_key
        if service_key == "shop":
            return self.shop_base_url, self.shop_api_key
        if service_key == "wms":
            return self.wms_base_url, self.wms_api_key
        if service_key == "eazyauction":
            return self.eazyauction_base_url, self.eazyauction_api_key
        return "", ""

    def _database_name_for_service(self, service: str) -> str:
        service_key = service.lower().strip()
        if service_key == "wawi":
            return self.wawi_db_name
        if service_key == "shop":
            return self.shop_db_name
        if service_key == "wms":
            return self.wms_db_name
        if service_key == "eazyauction":
            return self.eazyauction_db_name
        return ""

    def _sqlalchemy_url(self, database_name: str) -> URL:
        return URL.create(
            "mssql+pyodbc",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=database_name,
            query={
                "driver": self.db_driver,
                "Encrypt": "yes" if self.db_encrypt else "no",
                "TrustServerCertificate": "yes" if self.db_trust_server_certificate else "no",
            },
        )

    def _get_engine(self, db_name: str) -> Any:
        if db_name not in self._db_engines:
            self._db_engines[db_name] = create_engine(
                self._sqlalchemy_url(db_name),
                pool_size=self.db_pool_size,
                max_overflow=5,
                pool_pre_ping=True,
            )
        return self._db_engines[db_name]

    # ------------------------------------------------------------
    #  DB-ABFRAGEN (kompatibel erweitert)
    # ------------------------------------------------------------
    def _execute_db_query_sync(
        self,
        *,
        database_name: str,
        sql: str,
        sql_params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        engine = self._get_engine(database_name)
        try:
            with engine.connect() as connection:
                result = connection.execute(text(sql), sql_params or {})
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return {
                    "success": True,
                    "service": "database",
                    "status_code": 200,
                    "data": {
                        "database": database_name,
                        "row_count": len(rows),
                        "rows": rows,
                    },
                }
        except SQLAlchemyError as exc:
            return {"success": False, "service": "database", "error": f"SQL-Fehler: {str(exc)}"}
        except Exception as exc:
            return {"success": False, "service": "database", "error": f"DB-Fehler: {str(exc)}"}

    async def _query_database(
        self,
        *,
        service: str,
        db_name: str,
        sql: str,
        sql_params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        database_name = db_name.strip() if db_name else self._database_name_for_service(service)
        if not database_name:
            return {
                "success": False,
                "service": service,
                "error": "Kein Datenbankname konfiguriert.",
            }

        if not self.db_host or not self.db_user:
            return {
                "success": False,
                "service": service,
                "error": "Datenbank-Host oder Benutzer fehlt.",
            }

        statement = sql.strip()
        if not statement:
            return {"success": False, "service": service, "error": "sql ist erforderlich."}

        allowed_prefixes = ("select", "with")
        if not statement.lower().startswith(allowed_prefixes):
            return {
                "success": False,
                "service": service,
                "error": "Nur lesende SQL-Statements (SELECT/WITH) sind erlaubt.",
            }

        # Mandanten-Filter (optional)
        if self.mandant_filter > 0 and "kMandant" in statement.lower():
            if "kMandant" not in statement.lower().split("where")[-1]:
                statement = statement.rstrip(";") + f" WHERE kMandant = {self.mandant_filter}"

        try:
            return await asyncio.to_thread(
                self._execute_db_query_sync,
                database_name=database_name,
                sql=statement,
                sql_params=sql_params,
            )
        except SQLAlchemyError as exc:
            return {
                "success": False,
                "service": service,
                "error": f"SQL-Fehler: {str(exc)}",
            }
        except ModuleNotFoundError:
            return {
                "success": False,
                "service": service,
                "error": "Treiber fehlt: bitte pyodbc und SQL Server ODBC Driver installieren.",
            }
        except Exception as exc:
            return {
                "success": False,
                "service": service,
                "error": f"Unbekannter SQL-Fehler: {str(exc)}",
            }

    # ------------------------------------------------------------
    #  HTTP-REQUESTS (alte _request bleibt unverändert)
    # ------------------------------------------------------------
    async def _request(
        self,
        *,
        service: str,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        base_url, api_key = self._service_config(service)

        if not base_url:
            return {
                "success": False,
                "service": service,
                "error": f"Base URL fuer Service '{service}' fehlt.",
            }
        if not api_key:
            return {
                "success": False,
                "service": service,
                "error": f"API-Key fuer Service '{service}' fehlt.",
            }

        endpoint_path = endpoint.strip()
        if not endpoint_path.startswith("/"):
            endpoint_path = f"/{endpoint_path}"

        method_normalized = method.strip().upper()
        if method_normalized not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            return {
                "success": False,
                "service": service,
                "error": f"HTTP-Methode nicht unterstuetzt: {method_normalized}",
            }

        url = f"{base_url}{endpoint_path}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds, verify=self.verify_tls) as client:
            try:
                response = await client.request(
                    method=method_normalized,
                    url=url,
                    headers=headers,
                    params=params,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.TimeoutException:
                return {
                    "success": False,
                    "service": service,
                    "error": "Zeitueberschreitung beim Aufruf der JTL-API.",
                }
            except httpx.HTTPStatusError as exc:
                details = exc.response.text.strip()
                if len(details) > 600:
                    details = f"{details[:597]}..."
                return {
                    "success": False,
                    "service": service,
                    "status_code": exc.response.status_code,
                    "error": f"HTTP-Fehler {exc.response.status_code}",
                    "message": details,
                }
            except Exception as exc:
                return {
                    "success": False,
                    "service": service,
                    "error": f"Unbekannter Fehler: {str(exc)}",
                }

        parsed: dict[str, Any]
        try:
            raw_payload = response.json()
            parsed = cast(dict[str, Any], raw_payload) if isinstance(raw_payload, dict) else {"items": raw_payload}
        except Exception:
            parsed = {"raw": response.text}

        return {
            "success": True,
            "service": service,
            "status_code": response.status_code,
            "data": parsed,
        }

    # ------------------------------------------------------------
    #  NEUE REQUEST-METHODE MIT RETRY (für neue Aktionen)
    # ------------------------------------------------------------
    async def _request_with_retry(
        self,
        service: str,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        base_url, api_key = self._service_config(service)
        if not base_url:
            return {"success": False, "service": service, "error": f"Base URL für {service} fehlt."}
        if not api_key:
            return {"success": False, "service": service, "error": f"API-Key für {service} fehlt."}

        endpoint_path = endpoint.strip()
        if not endpoint_path.startswith("/"):
            endpoint_path = f"/{endpoint_path}"
        url = f"{base_url}{endpoint_path}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        method_norm = method.strip().upper()

        timeout = self.api_write_timeout if method_norm in {"POST", "PUT", "PATCH", "DELETE"} else self.api_read_timeout
        timeout = max(timeout, self.timeout_seconds)

        last_exception: Exception | None = None
        for attempt in range(self.retry_max_attempts):
            try:
                async with httpx.AsyncClient(timeout=timeout, verify=self.verify_tls) as client:
                    resp = await client.request(method=method_norm, url=url, headers=headers, params=params, json=payload)
                    resp.raise_for_status()
                    parsed = cast(dict[str, Any], resp.json()) if isinstance(resp.json(), dict) else {"items": resp.json()}
                    return {"success": True, "service": service, "status_code": resp.status_code, "data": parsed}
            except httpx.TimeoutException as e:
                last_exception = e
                if attempt == self.retry_max_attempts - 1:
                    return {"success": False, "service": service, "error": f"Timeout nach {self.retry_max_attempts} Versuchen."}
            except httpx.HTTPStatusError as e:
                details = e.response.text[:500]
                if e.response.status_code in {429, 500, 502, 503, 504} and attempt < self.retry_max_attempts - 1:
                    last_exception = e
                    await asyncio.sleep(self.retry_backoff_factor * (2 ** attempt))
                    continue
                return {
                    "success": False,
                    "service": service,
                    "status_code": e.response.status_code,
                    "error": f"HTTP {e.response.status_code}",
                    "message": details,
                }
            except Exception as e:
                last_exception = e
                if attempt == self.retry_max_attempts - 1:
                    return {"success": False, "service": service, "error": f"Fehler: {str(e)}"}
            await asyncio.sleep(self.retry_backoff_factor * (2 ** attempt))

        return {"success": False, "service": service, "error": f"Unbekannter Fehler: {last_exception}" if last_exception else "Retry fehlgeschlagen."}

    # ------------------------------------------------------------
    #  BULK-FETCH (für fetch_all)
    # ------------------------------------------------------------
    async def _fetch_all_pages(
        self,
        service: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        page_param: str = "page",
        limit_param: str = "limit",
        page_size: int = 100,
    ) -> dict[str, Any]:
        all_items: list[dict[str, Any]] = []
        params = params or {}
        params[limit_param] = page_size
        fetched_pages: int = 0

        for page in range(1, self.max_pagination_pages + 1):
            params[page_param] = page
            resp = await self._request_with_retry(service, "GET", endpoint, params=params, payload=payload)
            if not resp.get("success"):
                return resp
            data: dict[str, Any] = resp.get("data", {})
            raw_items = data.get("items")
            if isinstance(raw_items, list):
                items: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_items)
            else:
                items = [cast(dict[str, Any], raw_items)] if raw_items is not None else []
            if not items:
                break
            all_items.extend(items)
            fetched_pages = page

            total_pages: int = 1
            if isinstance(data.get("total_pages"), int):
                total_pages = data.get("total_pages", 1)
            elif isinstance(data.get("pagination"), dict):
                pag = data.get("pagination", {})
                if isinstance(pag.get("total_pages"), int):
                    total_pages = pag.get("total_pages", 1)
            else:
                total_pages = page  # Annahme: es gibt keine weitere Seite
            if page >= total_pages:
                break

        return {
            "success": True,
            "service": service,
            "status_code": 200,
            "data": {"items": all_items, "total_count": len(all_items), "fetched_pages": fetched_pages},
            "pagination": {"fetched_pages": fetched_pages, "max_pages": self.max_pagination_pages},
        }

    # ------------------------------------------------------------
    #  ANALYTICS-ENGINE
    # ------------------------------------------------------------
    async def _handle_analytics(self, params: dict[str, Any]) -> dict[str, Any]:
        report_type = params.get("report_type")
        if not report_type:
            return {"success": False, "action": "analytics", "error": "report_type ist erforderlich."}

        template = self.ANALYTICS_TEMPLATES.get(report_type)
        if not template:
            return {"success": False, "action": "analytics", "error": f"Unbekannter Report: {report_type}"}

        date_from = params.get("date_from") or "1970-01-01"
        date_to = params.get("date_to") or datetime.now().strftime("%Y-%m-%d")
        limit = params.get("limit") or self.analytics_default_limit

        group_by = params.get("group_by", "day")
        group_sql_map = {
            "day": "CAST(dErstellt AS DATE)",
            "week": "DATEPART(year, dErstellt) * 100 + DATEPART(week, dErstellt)",
            "month": "DATEPART(year, dErstellt) * 100 + DATEPART(month, dErstellt)",
            "quarter": "DATEPART(year, dErstellt) * 10 + DATEPART(quarter, dErstellt)",
            "year": "DATEPART(year, dErstellt)",
        }
        group_sql = group_sql_map.get(group_by, "CAST(dErstellt AS DATE)")

        sql = template.format(group_by_sql=group_sql)
        sql_params: dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
        }
        if params.get("sql_params"):
            extra = params.get("sql_params")
            if isinstance(extra, dict):
                sql_params.update(cast(dict[str, Any], extra))

        result = await self._query_database(
            service="wawi",
            db_name=params.get("db_name", ""),
            sql=sql,
            sql_params=sql_params,
        )
        result["action"] = "analytics"
        result["report_type"] = report_type
        return result

    # ------------------------------------------------------------
    #  SPEZIALAKTIONEN (für alte und neue Spezialfälle)
    # ------------------------------------------------------------
    async def _handle_special_actions(self, action: str, input_data: dict[str, Any]) -> dict[str, Any]:
        # ---------- Alte Spezialaktionen (kompatibel) ----------
        if action == "update_order_status":
            item_id = str(input_data.get("item_id", "")).strip()
            status = str(input_data.get("status", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id ist erforderlich."}
            if not status:
                return {"success": False, "action": action, "error": "status ist erforderlich."}
            result = await self._request(
                service="wawi",
                method="PATCH",
                endpoint=f"/api/v1/orders/{item_id}/status",
                payload={"status": status},
            )
            result["action"] = action
            return result

        if action == "sync_stock_to_shop":
            stock_updates = input_data.get("stock_updates")
            if not isinstance(stock_updates, list) or not stock_updates:
                return {"success": False, "action": action, "error": "stock_updates muss eine nicht-leere Liste sein."}
            result = await self._request(
                service="shop",
                method="POST",
                endpoint="/api/v1/inventory/sync",
                payload={"items": stock_updates},
            )
            result["action"] = action
            return result

        # ---------- Neue Spezialaktionen ----------
        if action == "add_order_comment":
            item_id = str(input_data.get("item_id", "")).strip()
            comment = str(input_data.get("comment", "")).strip()
            if not item_id or not comment:
                return {"success": False, "action": action, "error": "item_id und comment erforderlich."}
            result = await self._request_with_retry("wawi", "POST", f"/api/v1/orders/{item_id}/comments", payload={"text": comment})
            result["action"] = action
            return result

        if action == "cancel_order":
            item_id = str(input_data.get("item_id", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id fehlt."}
            result = await self._request_with_retry("wawi", "POST", f"/api/v1/orders/{item_id}/cancel")
            result["action"] = action
            return result

        if action == "create_invoice_from_order":
            item_id = str(input_data.get("item_id", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id (Auftrags-ID) fehlt."}
            result = await self._request_with_retry("wawi", "POST", f"/api/v1/orders/{item_id}/create_invoice")
            result["action"] = action
            return result

        if action == "download_invoice_pdf":
            item_id = str(input_data.get("item_id", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id (Rechnungs-ID) fehlt."}
            base_url, _ = self._service_config("wawi")
            if not base_url:
                return {"success": False, "action": action, "error": "Wawi Base URL fehlt."}
            url = f"{base_url}/api/v1/invoices/{item_id}/pdf"
            headers = {"Authorization": f"Bearer {self.wawi_api_key}", "Accept": "application/pdf"}
            try:
                async with httpx.AsyncClient(timeout=self.api_write_timeout, verify=self.verify_tls) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    b64 = base64.b64encode(resp.content).decode("utf-8")
                    return {"success": True, "action": action, "data": {"invoice_id": item_id, "pdf_base64": b64}}
            except Exception as e:
                return {"success": False, "action": action, "error": f"PDF-Download fehlgeschlagen: {str(e)}"}

        if action == "convert_quote_to_order":
            item_id = str(input_data.get("item_id", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id (Angebots-ID) fehlt."}
            result = await self._request_with_retry("wawi", "POST", f"/api/v1/quotes/{item_id}/convert")
            result["action"] = action
            return result

        if action == "adjust_stock":
            item_id = str(input_data.get("item_id", "")).strip()
            quantity = input_data.get("quantity")
            if not item_id or quantity is None:
                return {"success": False, "action": action, "error": "item_id und quantity erforderlich."}
            result = await self._request_with_retry("wawi", "POST", f"/api/v1/products/{item_id}/adjust-stock", payload={"quantity": quantity})
            result["action"] = action
            return result

        if action == "list_stock_movements":
            item_id = str(input_data.get("item_id", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id (Produkt-ID) fehlt."}
            limit = self._int_value(input_data.get("limit", 20), default=20, min_value=1, max_value=1000)
            result = await self._request_with_retry("wawi", "GET", f"/api/v1/products/{item_id}/stock-movements", params={"limit": limit})
            result["action"] = action
            return result

        if action == "create_shipment":
            item_id = str(input_data.get("item_id", "")).strip()
            payload = self._dict_value(input_data.get("payload"))
            if not item_id or not payload:
                return {"success": False, "action": action, "error": "item_id und payload erforderlich."}
            result = await self._request_with_retry("wawi", "POST", f"/api/v1/orders/{item_id}/shipments", payload=payload)
            result["action"] = action
            return result

        if action == "create_payment":
            payload = self._dict_value(input_data.get("payload"))
            if not payload:
                return {"success": False, "action": action, "error": "payload erforderlich."}
            result = await self._request_with_retry("wawi", "POST", "/api/v1/payments", payload=payload)
            result["action"] = action
            return result

        # Fallback
        return {"success": False, "action": action, "error": f"Aktion {action} nicht unterstützt oder falsche Parameter."}

    # ------------------------------------------------------------
    #  GENERISCHER ENTITY-DISPATCHER (für list_*, get_*, create_*, update_*, delete_*)
    # ------------------------------------------------------------
    async def _handle_entity_action(self, action: str, input_data: dict[str, Any]) -> dict[str, Any]:
        parts = action.split("_", 1)
        if len(parts) != 2:
            return {"success": False, "action": action, "error": "Ungültiges Aktionsformat."}
        verb, entity_key = parts[0], parts[1]

        entity_config = self.ENTITY_CONFIG.get(entity_key)
        if not entity_config:
            return {"success": False, "action": action, "error": f"Unbekannte Entität: {entity_key}"}

        api_path = entity_config["api_path"]
        service = "wawi"  # Alle Hauptentitäten sind in Wawi
        limit = self._int_value(input_data.get("limit", 20), default=20, min_value=1, max_value=1000)
        query = str(input_data.get("query", "")).strip()
        item_id = str(input_data.get("item_id", "")).strip()
        fetch_all = bool(input_data.get("fetch_all", False))

        # ---------- LIST ----------
        if verb == "list":
            params: dict[str, Any] = {"limit": limit}
            if query:
                params["q"] = query

            # Hybrider Router: Wenn Datumsfilter oder group_by oder analytics_use_db, dann SQL
            if input_data.get("date_from") or input_data.get("date_to") or input_data.get("group_by") or self.analytics_use_db:
                db_table = entity_config["db_table"]
                pk = entity_config["pk"]
                where_clauses: list[str] = []
                sql_params: dict[str, Any] = {"limit": limit}
                if query:
                    where_clauses.append("cName LIKE :query")
                    sql_params["query"] = f"%{query}%"
                if input_data.get("date_from"):
                    where_clauses.append("dErstellt >= :date_from")
                    sql_params["date_from"] = input_data.get("date_from")
                if input_data.get("date_to"):
                    where_clauses.append("dErstellt <= :date_to")
                    sql_params["date_to"] = input_data.get("date_to")
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                sql = f"SELECT TOP (:limit) * FROM {db_table} WHERE {where_sql} ORDER BY {pk} DESC"
                result = await self._query_database(
                    service="wawi",
                    db_name=input_data.get("db_name", ""),
                    sql=sql,
                    sql_params=sql_params,
                )
                result["action"] = action
                return result
            else:
                if fetch_all:
                    return await self._fetch_all_pages(service, api_path, params=params)
                else:
                    return await self._request(service, "GET", api_path, params=params) # type: ignore


        # ---------- GET ----------
        if verb == "get":
            if not item_id:
                return {"success": False, "action": action, "error": "item_id fehlt."}
            return await self._request(service, "GET", f"{api_path}/{item_id}") # type: ignore

        # ---------- CREATE ----------
        if verb == "create":
            payload = self._dict_value(input_data.get(entity_key)) or self._dict_value(input_data.get("payload"))
            if not payload:
                return {"success": False, "action": action, "error": f"{entity_key} Daten fehlen."}
            return await self._request_with_retry(service, "POST", api_path, payload=payload)

        # ---------- UPDATE ----------
        if verb == "update":
            if not item_id:
                return {"success": False, "action": action, "error": "item_id fehlt."}
            payload = self._dict_value(input_data.get(entity_key)) or self._dict_value(input_data.get("payload"))
            if not payload:
                return {"success": False, "action": action, "error": "Update-Daten fehlen."}
            return await self._request_with_retry(service, "PUT", f"{api_path}/{item_id}", payload=payload)

        # ---------- DELETE ----------
        if verb == "delete":
            if not item_id:
                return {"success": False, "action": action, "error": "item_id fehlt."}
            return await self._request_with_retry(service, "DELETE", f"{api_path}/{item_id}")

        # Fallback
        return {"success": False, "action": action, "error": f"Verb {verb} nicht unterstützt für {entity_key}"}

    # ------------------------------------------------------------
    #  HAUPT-EXECUTE (kompatibel zur alten Version, erweitert)
    # ------------------------------------------------------------
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = str(input_data.get("action", "list_products")).strip().lower()

        limit = self._int_value(input_data.get("limit", 20), default=20, min_value=1, max_value=250)
        query = str(input_data.get("query", "")).strip()

        # --------------------------------------------------------
        # 1. Alte Aktionen exakt so wie in der Basisversion (1:1 kompatibel)
        # --------------------------------------------------------
        if action == "list_products":
            params: dict[str, Any] = {"limit": limit}
            if query:
                params["q"] = query
            result = await self._request(
                service="wawi",
                method="GET",
                endpoint="/api/v1/products",
                params=params,
            )
            result["action"] = action
            return result

        if action == "get_product":
            item_id = str(input_data.get("item_id", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id ist erforderlich."}
            result = await self._request(
                service="wawi",
                method="GET",
                endpoint=f"/api/v1/products/{item_id}",
            )
            result["action"] = action
            return result

        if action == "list_customers":
            params = {"limit": limit}
            if query:
                params["q"] = query
            result = await self._request(service="wawi", method="GET", endpoint="/api/v1/customers", params=params)
            result["action"] = action
            return result

        if action == "create_customer":
            customer = self._dict_value(input_data.get("customer"))
            if not customer:
                return {"success": False, "action": action, "error": "customer-Objekt ist erforderlich."}
            result = await self._request(
                service="wawi",
                method="POST",
                endpoint="/api/v1/customers",
                payload=customer,
            )
            result["action"] = action
            return result

        if action == "list_orders":
            params = {"limit": limit}
            if query:
                params["q"] = query
            result = await self._request(service="wawi", method="GET", endpoint="/api/v1/orders", params=params)
            result["action"] = action
            return result

        if action == "create_order":
            order = self._dict_value(input_data.get("order"))
            if not order:
                return {"success": False, "action": action, "error": "order-Objekt ist erforderlich."}
            result = await self._request(
                service="wawi",
                method="POST",
                endpoint="/api/v1/orders",
                payload=order,
            )
            result["action"] = action
            return result

        if action == "update_order_status":
            item_id = str(input_data.get("item_id", "")).strip()
            status = str(input_data.get("status", "")).strip()
            if not item_id:
                return {"success": False, "action": action, "error": "item_id ist erforderlich."}
            if not status:
                return {"success": False, "action": action, "error": "status ist erforderlich."}
            result = await self._request(
                service="wawi",
                method="PATCH",
                endpoint=f"/api/v1/orders/{item_id}/status",
                payload={"status": status},
            )
            result["action"] = action
            return result

        if action == "sync_stock_to_shop":
            stock_updates = input_data.get("stock_updates")
            if not isinstance(stock_updates, list) or not stock_updates:
                return {"success": False, "action": action, "error": "stock_updates muss eine nicht-leere Liste sein."}
            result = await self._request(
                service="shop",
                method="POST",
                endpoint="/api/v1/inventory/sync",
                payload={"items": stock_updates},
            )
            result["action"] = action
            return result

        if action == "list_shop_orders":
            params = {"limit": limit}
            result = await self._request(service="shop", method="GET", endpoint="/api/v1/orders", params=params)
            result["action"] = action
            return result

        if action == "list_wms_picklists":
            params = {"limit": limit}
            result = await self._request(service="wms", method="GET", endpoint="/api/v1/picklists", params=params)
            result["action"] = action
            return result

        if action == "list_marketplace_listings":
            params = {"limit": limit}
            result = await self._request(
                service="eazyauction",
                method="GET",
                endpoint="/api/v1/listings",
                params=params,
            )
            result["action"] = action
            return result

        if action == "db_test_connection":
            service = str(input_data.get("db_service", "wawi")).strip().lower()
            if service not in {"wawi", "shop", "wms", "eazyauction"}:
                return {
                    "success": False,
                    "action": action,
                    "error": "db_service muss einer von wawi, shop, wms, eazyauction sein.",
                }
            db_name = str(input_data.get("db_name", "")).strip()
            result = await self._query_database(
                service=service,
                db_name=db_name,
                sql="SELECT 1 AS ok",
                sql_params=None,
            )
            result["action"] = action
            return result

        if action == "db_query":
            service = str(input_data.get("db_service", "wawi")).strip().lower()
            if service not in {"wawi", "shop", "wms", "eazyauction"}:
                return {
                    "success": False,
                    "action": action,
                    "error": "db_service muss einer von wawi, shop, wms, eazyauction sein.",
                }
            sql = str(input_data.get("sql", "")).strip()
            sql_params = self._dict_value(input_data.get("sql_params"))
            db_name = str(input_data.get("db_name", "")).strip()
            result = await self._query_database(
                service=service,
                db_name=db_name,
                sql=sql,
                sql_params=sql_params,
            )
            result["action"] = action
            return result

        if action == "custom_request":
            service = str(input_data.get("service", "")).strip().lower()
            method = str(input_data.get("method", "GET")).strip().upper()
            endpoint = str(input_data.get("endpoint", "")).strip()
            custom_payload = (
                self._dict_value(input_data.get("payload")) if isinstance(input_data.get("payload"), dict) else None
            )
            custom_params = self._dict_value(input_data.get("params")) if isinstance(input_data.get("params"), dict) else None
            if service not in {"wawi", "shop", "wms", "eazyauction"}:
                return {
                    "success": False,
                    "action": action,
                    "error": "service muss einer von wawi, shop, wms, eazyauction sein.",
                }
            if not endpoint:
                return {"success": False, "action": action, "error": "endpoint ist erforderlich."}
            result = await self._request(
                service=service,
                method=method,
                endpoint=endpoint,
                payload=custom_payload,
                params=custom_params,
            )
            result["action"] = action
            return result

        # --------------------------------------------------------
        # 2. Neue Aktionen – Analytics
        # --------------------------------------------------------
        if action == "analytics":
            return await self._handle_analytics(input_data)

        # --------------------------------------------------------
        # 3. Neue Aktionen – DB-Helfer
        # --------------------------------------------------------
        if action == "db_tables":
            db_service = str(input_data.get("db_service", "wawi")).strip().lower()
            db_name = str(input_data.get("db_name", "")).strip()
            db_name = db_name or self._database_name_for_service(db_service)
            if not db_name:
                return {"success": False, "action": action, "error": "Datenbankname fehlt."}
            try:
                engine = self._get_engine(db_name)
                with engine.connect() as conn:
                    tables = inspect(conn).get_table_names()
                return {"success": True, "action": action, "data": {"database": db_name, "tables": tables}}
            except Exception as e:
                return {"success": False, "action": action, "error": str(e)}

        if action == "db_describe_table":
            table_name = str(input_data.get("table_name", "")).strip()
            if not table_name:
                return {"success": False, "action": action, "error": "table_name erforderlich."}
            db_service = str(input_data.get("db_service", "wawi")).strip().lower()
            db_name = str(input_data.get("db_name", "")).strip()
            db_name = db_name or self._database_name_for_service(db_service)
            if not db_name:
                return {"success": False, "action": action, "error": "Datenbankname fehlt."}
            try:
                engine = self._get_engine(db_name)
                with engine.connect() as conn:
                    inspector = inspect(conn)
                    cols = inspector.get_columns(table_name)
                return {"success": True, "action": action, "data": {"table": table_name, "columns": cols}}
            except Exception as e:
                return {"success": False, "action": action, "error": str(e)}

        # --------------------------------------------------------
        # 4. Bulk-Fetch alias (fetch_all_*)
        # --------------------------------------------------------
        if action.startswith("fetch_all_"):
            # Extrahiere Entität: fetch_all_products -> products
            entity = action.replace("fetch_all_", "")
            if entity not in self.ENTITY_CONFIG:
                return {"success": False, "action": action, "error": f"Unbekannte Entität: {entity}"}
            # Rufe list_ mit fetch_all=True auf
            input_data["action"] = f"list_{entity}"
            input_data["fetch_all"] = True
            return await self.execute(input_data)

        # --------------------------------------------------------
        # 5. Generischer Dispatcher für alle anderen list_*, get_*, create_*, update_*, delete_*
        # --------------------------------------------------------
        if action.startswith(("list_", "get_", "create_", "update_", "delete_")):
            return await self._handle_entity_action(action, input_data)

        # --------------------------------------------------------
        # 6. Spezialaktionen (alte und neue)
        # --------------------------------------------------------
        return await self._handle_special_actions(action, input_data)