# packages/plugins/bing_search/plugin.py
from __future__ import annotations

import os
from typing import Any

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "bing_search",
    "name": "Bing Search",
    "description": "Bing Web Search API",
    "category": "🌐 Core / Web",
    "apiKeyRequired": True,
    "intentPattern": r"\b(bing|suche|finde|google|search)\b",
    "status": "implemented",
    "settingsFields": [],
}


class BingSearchPlugin:
    name = "bing_search"
    description = "Bing Web Search API"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "count": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
            "mkt": {"type": "string", "default": "de-DE", "description": "Markt (z.B. de-DE, en-US)"},
        },
        "required": ["query"],
    }
    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "total_count": {"type": "integer"},
            "error": {"type": "string"},
        },
    }

    def __init__(self, settings: dict[str, Any] | None = None):
        self._settings = settings if isinstance(settings, dict) else {}
        self.api_key = os.getenv("BING_SEARCH_API_KEY", "")
        self._apply_settings_overrides()

    def set_settings(self, settings: dict[str, Any]) -> None:
        self._settings = settings if isinstance(settings, dict) else {}
        self._apply_settings_overrides()

    def _apply_settings_overrides(self) -> None:
        explicit_value = self._settings.get("bing_search_api_key")
        if isinstance(explicit_value, str) and explicit_value.strip():
            self.api_key = explicit_value.strip()
            return

        integration_settings = self._settings.get("integrations", {})
        if isinstance(integration_settings, dict):
            integration_value = integration_settings.get("bing_search_api_key")
            if isinstance(integration_value, str) and integration_value.strip():
                self.api_key = integration_value.strip()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"error": "Keine Suchanfrage angegeben."}

        count = int(input_data.get("count", 5))
        mkt = str(input_data.get("mkt", "de-DE"))

        api_key = self.api_key
        # Fallback: Plugin-eigener API-Key (wenn über Settings bereitgestellt)
        if not api_key:
            # Hier könnte die Plugin-Registry den API-Key aus den Settings liefern
            # Für dieses Beispiel nehmen wir an, dass der Key in den Plugin-Einstellungen gespeichert ist
            # und über eine Methode (z. B. `self.get_api_key()`) verfügbar ist.
            # Da wir hier keine Registry haben, gehen wir von der Umgebungsvariable aus.
            return {"error": "Bing Search API-Key fehlt. Setze BING_SEARCH_API_KEY in der Umgebung."}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    params={
                        "q": query,
                        "count": count,
                        "mkt": mkt,
                        "responseFilter": "Webpages",
                        "safeSearch": "Moderate",
                    },
                    headers={"Ocp-Apim-Subscription-Key": api_key},
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

        web_pages = data.get("webPages", {})
        total_count = web_pages.get("totalEstimatedMatches", 0)
        value = web_pages.get("value", [])

        results = []
        for item in value[:count]:
            results.append({
                "title": item.get("name", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("url", ""),
                "display_url": item.get("displayUrl", ""),
            })

        return {
            "results": results,
            "total_count": total_count,
        }


