# packages/plugins/google_search/plugin.py
from __future__ import annotations

import os
from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "google_search",
    "name": "Google Search",
    "description": "Google Custom Search API (Websuche mit Google)",
    "category": "🌐 Core / Web",
    "apiKeyRequired": True,
    "intentPattern": r"\b(google|suche|finde|search|googlen)\b",
    "status": "implemented",
    "settingsFields": [],
}


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key_raw, item_raw in cast(dict[object, Any], value).items():
        normalized[str(key_raw)] = item_raw
    return normalized


class GoogleSearchPlugin:
    name = "google_search"
    description = "Google Custom Search API (Websuche mit Google)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Suchbegriff für Google.",
            },
            "num": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "default": 5,
                "description": "Anzahl der Ergebnisse (1-10).",
            },
            "start": {
                "type": "integer",
                "minimum": 1,
                "default": 1,
                "description": "Startindex für Paginierung.",
            },
            "language": {
                "type": "string",
                "description": "Sprachcode für Ergebnisse (z.B. 'de', 'en').",
                "default": "de",
            },
            "site": {
                "type": "string",
                "description": "Website-Filter (z.B. 'wikipedia.org').",
            },
            "safe": {
                "type": "string",
                "enum": ["off", "medium", "high"],
                "default": "medium",
                "description": "SafeSearch-Einstellung.",
            },
            "date_restrict": {
                "type": "string",
                "enum": ["d1", "w1", "m1", "y1"],
                "description": "Zeitraum-Beschränkung (d1=letzter Tag, w1=letzte Woche, m1=letzter Monat, y1=letztes Jahr).",
            },
        },
        "required": ["query"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "total_results": {"type": "integer"},
            "results": {"type": "array"},
            "query": {"type": "string"},
            "search_terms": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "")
        self.cx = os.getenv("GOOGLE_SEARCH_CX", "")  # Search Engine ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def _is_configured(self) -> bool:
        return bool(self.api_key and self.cx)

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"error": "Suchbegriff (query) ist erforderlich."}

        if not self._is_configured():
            return {
                "success": False,
                "error": "Google Search nicht konfiguriert. Setze GOOGLE_SEARCH_API_KEY und GOOGLE_SEARCH_CX in der Umgebung.",
            }

        num = max(1, min(10, int(input_data.get("num", 5))))
        start = max(1, int(input_data.get("start", 1)))
        language = str(input_data.get("language", "de")).strip()
        site = str(input_data.get("site", "")).strip()
        safe = str(input_data.get("safe", "medium"))
        date_restrict = str(input_data.get("date_restrict", "")).strip()

        params: dict[str, Any] = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": num,
            "start": start,
            "safe": safe,
        }

        if language:
            params["lr"] = f"lang_{language}"
        if site:
            params["siteSearch"] = site
        if date_restrict:
            params["dateRestrict"] = date_restrict

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    return {
                        "success": False,
                        "error": "Ungültiger API-Key oder CX-ID. Prüfe GOOGLE_SEARCH_API_KEY und GOOGLE_SEARCH_CX.",
                    }
                if e.response.status_code == 429:
                    return {"success": False, "error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                return {"success": False, "error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"success": False, "error": f"Fehler: {str(e)}"}

        if not isinstance(payload, dict):
            return {"success": False, "error": "Ungültige Antwort von der Google Search API."}

        data = _as_dict(payload)

        # Prüfe auf API-Fehler
        if "error" in data:
            error_info = _as_dict(data.get("error"))
            message = str(error_info.get("message", "Unbekannter Fehler"))
            return {
                "success": False,
                "error": f"Google Search API-Fehler: {message}",
            }

        # Ergebnisse extrahieren
        items_raw = data.get("items", [])
        items: list[dict[str, Any]] = []
        if isinstance(items_raw, list):
            for raw_item in cast(list[Any], items_raw):
                item = _as_dict(raw_item)
                if item:
                    items.append(item)

        search_information_raw = data.get("searchInformation", {})
        search_information = _as_dict(search_information_raw)
        total_raw = search_information.get("totalResults", 0)
        try:
            total_results = int(str(total_raw))
        except (TypeError, ValueError):
            total_results = 0

        formatted_results: list[dict[str, str]] = []
        for item in items:
            formatted_results.append({
                "title": str(item.get("title", "")),
                "snippet": str(item.get("snippet", "")),
                "url": str(item.get("link", "")),
                "display_url": str(item.get("displayLink", "")),
                "cache_url": str(item.get("cacheId", "")),
            })

        search_terms = query
        queries_raw = _as_dict(data.get("queries", {}))
        request_raw = queries_raw.get("request", [])
        if isinstance(request_raw, list) and request_raw:
            first_request = _as_dict(request_raw[0])
            if first_request:
                search_terms = str(first_request.get("searchTerms", query))

        return {
            "success": True,
            "total_results": total_results,
            "results": formatted_results,
            "query": query,
            "search_terms": search_terms,
        }

