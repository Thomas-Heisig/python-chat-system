# packages/plugins/api_tester/plugin.py
from __future__ import annotations

import json
import time
from typing import Any

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "api_tester",
    "name": "API Tester",
    "description": "Führt HTTP-Requests durch und gibt Status, Header und Antwort zurück.",
    "category": "🔧 Developer Tools",
    "apiKeyRequired": False,
    "intentPattern": r"\b(api|teste|request|http|get|post|put|delete)\b",
    "status": "implemented",
    "settingsFields": [],
}


class ApiTesterPlugin:
    name = "api_tester"
    description = "Führt HTTP-Requests durch und gibt Status, Header und Antwort zurück."

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Die Ziel-URL."},
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                "default": "GET",
                "description": "HTTP-Methode.",
            },
            "headers": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "Optional: HTTP-Header als Schlüssel-Wert-Objekt.",
            },
            "body": {
                "type": ["string", "object", "null"],
                "description": "Optional: Request-Body (String oder JSON-Objekt).",
            },
        },
        "required": ["url"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "status_code": {"type": "integer"},
            "headers": {"type": "object"},
            "body": {"type": "string"},
            "elapsed_ms": {"type": "number"},
            "error": {"type": "string"},
        },
    }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        url = str(input_data.get("url", "")).strip()
        if not url:
            return {"error": "URL ist erforderlich."}

        method = str(input_data.get("method", "GET")).upper()
        headers = input_data.get("headers", {})
        if not isinstance(headers, dict):
            headers = {}
        # Header-Werte in Strings umwandeln
        headers = {str(k): str(v) for k, v in headers.items()}

        body = input_data.get("body")
        # Wenn body ein dict ist, als JSON senden
        if isinstance(body, dict):
            body_json = json.dumps(body)
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
        else:
            body_json = str(body) if body is not None else None

        try:
            start = time.perf_counter()
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    content=body_json,
                    follow_redirects=True,
                )
            elapsed_ms = (time.perf_counter() - start) * 1000

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "elapsed_ms": round(elapsed_ms, 2),
            }
        except httpx.TimeoutException:
            return {"error": "Zeitüberschreitung (Timeout) bei der Anfrage."}
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP-Fehler: {e.response.status_code}",
                "status_code": e.response.status_code,
            }
        except Exception as e:
            return {"error": f"Fehler: {str(e)}"}


