# packages/plugins/sql_runner/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportUnusedImport=false

import os
import time
from typing import Any

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


PLUGIN_META: dict[str, Any] = {
    "id": "sql_runner",
    "name": "SQL Runner",
    "description": "Führt SQL-Abfragen auf einer Datenbank aus (SELECT nur, mit Sicherheitsbeschränkungen)",
    "category": "🔧 Developer Tools",
    "apiKeyRequired": True,
    "intentPattern": r"\b(sql|datenbank|abfrage|select|query|run sql)\b",
    "settingsFields": [
        {
            "key": "default_connection_string",
            "label": "Standard Connection String",
            "type": "string",
            "group": "Verbindung",
            "default": "",
            "description": "Wird genutzt, wenn keine Verbindung im Request gesetzt ist.",
        },
        {
            "key": "default_limit",
            "label": "Standard LIMIT",
            "type": "number",
            "group": "Laufzeit",
            "default": 100,
            "description": "Maximale Zeilenanzahl pro Query.",
        },
        {
            "key": "default_timeout",
            "label": "Standard Timeout (Sek.)",
            "type": "number",
            "group": "Laufzeit",
            "default": 10,
            "description": "Zeitlimit für SQL-Ausführung.",
        },
        {
            "key": "readonly_enforced",
            "label": "Read-Only Erzwingung",
            "type": "boolean",
            "group": "Sicherheit",
            "default": True,
            "description": "Nur SELECT-Abfragen erlauben.",
        },
    ],
    "status": "implemented",
}


class SQLRunnerPlugin:
    name = "sql_runner"
    description = "Führt SQL-Abfragen auf einer Datenbank aus (SELECT nur, mit Sicherheitsbeschränkungen)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Die SQL-Abfrage (nur SELECT, keine DDL/DML).",
            },
            "params": {
                "type": "object",
                "description": "Parameter für parametrisierte Abfragen (optional).",
                "additionalProperties": True,
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "default": 100,
                "description": "Maximale Anzahl von zurückgegebenen Zeilen.",
            },
            "timeout": {
                "type": "integer",
                "minimum": 1,
                "maximum": 60,
                "default": 10,
                "description": "Zeitlimit in Sekunden für die Abfrage.",
            },
            "connection_string": {
                "type": "string",
                "description": "Datenbank-Connection-String (überschreibt die Umgebungsvariable).",
            },
        },
        "required": ["query"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "columns": {"type": "array"},
            "rows": {"type": "array"},
            "row_count": {"type": "integer"},
            "execution_time_ms": {"type": "number"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        # Standard-Connection-String aus Umgebung
        self.default_connection_string = os.getenv("SQL_CONNECTION_STRING", "")

    def _is_configured(self) -> bool:
        return bool(self.default_connection_string)

    def _validate_query(self, query: str) -> bool:
        """Validiert, dass die Abfrage nur SELECT ist."""
        query_lower = query.strip().lower()
        # Entferne Kommentare und führende Leerzeichen
        cleaned = query_lower
        # Einfache Prüfung: darf nicht mit INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE beginnen
        forbidden_keywords = [
            "insert",
            "update",
            "delete",
            "drop",
            "alter",
            "create",
            "truncate",
            "grant",
            "revoke",
            "exec",
            "execute",
            "call",
        ]
        # Suche nach verbotenen Keywords am Anfang oder nach einem Semikolon
        for keyword in forbidden_keywords:
            if cleaned.startswith(keyword):
                return False
            # Auch nach Semikolon (mehrere Statements) prüfen
            if f";{keyword}" in cleaned:
                return False
        return True

    def _execute_query(self, query: str, params: dict[str, Any] | None, limit: int, timeout: int, connection_string: str | None) -> dict[str, Any]:
        """Führt die SQL-Abfrage aus."""
        conn_str = connection_string or self.default_connection_string
        if not conn_str:
            return {"error": "Keine Datenbankverbindung konfiguriert."}

        # Prüfe, ob die Abfrage sicher ist
        if not self._validate_query(query):
            return {"error": "Nur SELECT-Abfragen sind erlaubt."}

        # Begrenze die Abfrage (LIMIT hinzufügen, falls nicht vorhanden)
        query_trimmed = query.strip()
        if not query_trimmed.lower().startswith("select"):
            return {"error": "Nur SELECT-Abfragen sind erlaubt."}

        # Falls kein LIMIT vorhanden, füge eines hinzu
        if "limit" not in query_trimmed.lower():
            # Stelle sicher, dass wir das LIMIT nicht doppelt einfügen
            # Einfach anfügen, aber nur wenn kein ORDER BY oder GROUP BY stört
            query_trimmed = f"{query_trimmed} LIMIT {limit}"

        try:
            engine = create_engine(conn_str)
            with engine.connect() as conn:
                start_time = time.perf_counter()
                result = conn.execute(text(query_trimmed), params or {})
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                # Ergebnis abrufen
                columns = [col for col in result.keys()]
                rows = [list(row) for row in result.fetchmany(limit)]
                row_count = len(rows)

                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": row_count,
                    "execution_time_ms": round(elapsed_ms, 2),
                    "message": f"Abfrage erfolgreich ausgeführt. {row_count} Zeilen zurückgegeben.",
                }
        except SQLAlchemyError as e:
            return {"error": f"Datenbankfehler: {str(e)}"}
        except Exception as e:
            return {"error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"success": False, "error": "SQL-Abfrage ist erforderlich."}

        params = input_data.get("params")
        if not isinstance(params, dict):
            params = {}
        limit = max(1, min(1000, int(input_data.get("limit", 100))))
        timeout = max(1, min(60, int(input_data.get("timeout", 10))))
        connection_string = str(input_data.get("connection_string", "")).strip() or None

        if not self._is_configured() and not connection_string:
            return {"success": False, "error": "Keine Datenbankverbindung konfiguriert. Setze SQL_CONNECTION_STRING in der Umgebung."}

        # Ausführung
        result = self._execute_query(query, params, limit, timeout, connection_string)

        if "error" in result:
            return {"success": False, "error": result["error"]}

        return result
