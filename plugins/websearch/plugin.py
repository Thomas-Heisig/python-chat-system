from __future__ import annotations

import os
from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "websearch",
    "name": "WebSearch",
    "description": "Websuche mit Provider-Fallback (Exa, Brave, Bing, DuckDuckGo)",
    "category": "🌐 Core / Web",
    "apiKeyRequired": True,
    "intentPattern": r"\b(suche|finde|google)\b",
    "status": "implemented",
    "settingsFields": [
        {
            "key": "provider_mode",
            "label": "Provider-Modus",
            "type": "select",
            "default": "auto",
            "group": "Verbindung",
            "options": [
                {"value": "auto", "label": "Auto (Fallback)"},
                {"value": "exa", "label": "Exa"},
                {"value": "brave", "label": "Brave Search"},
                {"value": "bing", "label": "Bing Search"},
                {"value": "duckduckgo", "label": "DuckDuckGo"},
            ],
        },
        {
            "key": "fallback_providers",
            "label": "Fallback-Provider (CSV)",
            "type": "string",
            "default": "exa,brave,bing,duckduckgo",
            "group": "Verbindung",
        },
        {
            "key": "request_timeout_seconds",
            "label": "HTTP-Timeout (Sekunden)",
            "type": "number",
            "default": 10,
            "group": "Laufzeit",
        },
    ],
}


class WebSearchPlugin:
    """Simple external websearch plugin using DuckDuckGo Instant Answer API."""

    name = "websearch"
    description = "Websuche mit Exa/Brave/Bing/DuckDuckGo-Fallback"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "count": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
            "provider": {
                "type": "string",
                "enum": ["auto", "exa", "brave", "bing", "duckduckgo"],
                "default": "auto",
            },
        },
        "required": ["query"],
    }
    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "results": {"type": "array"},
            "provider": {"type": "string"},
            "provider_errors": {"type": "array"},
        },
    }

    def __init__(self, settings: dict[str, Any] | None = None):
        self._settings = settings if isinstance(settings, dict) else {}
        self.timeout_seconds = 10.0
        self.provider_mode = "auto"
        self.fallback_providers = ["exa", "brave", "bing", "duckduckgo"]

        self.exa_api_key = os.getenv("EXA_API_KEY", "").strip()
        self.brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
        self.bing_api_key = os.getenv("BING_SEARCH_API_KEY", "").strip()

        self._apply_settings_overrides()

    def set_settings(self, settings: dict[str, Any]) -> None:
        self._settings = settings if isinstance(settings, dict) else {}
        self._apply_settings_overrides()

    def _integration_settings(self) -> dict[str, Any]:
        raw = self._settings.get("integrations", {})
        if isinstance(raw, dict):
            return raw
        return {}

    def _resolve_key(self, settings_key: str, env_name: str, current: str) -> str:
        value = self._settings.get(settings_key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        integration_value = self._integration_settings().get(settings_key)
        if isinstance(integration_value, str) and integration_value.strip():
            return integration_value.strip()
        env_value = os.getenv(env_name, "").strip()
        if env_value:
            return env_value
        return current

    def _apply_settings_overrides(self) -> None:
        timeout_value = self._settings.get("request_timeout_seconds")
        if isinstance(timeout_value, (int, float)):
            self.timeout_seconds = max(3.0, float(timeout_value))

        provider_mode_value = self._settings.get("provider_mode")
        if isinstance(provider_mode_value, str) and provider_mode_value.strip():
            self.provider_mode = provider_mode_value.strip().lower()

        fallback_value = self._settings.get("fallback_providers")
        if isinstance(fallback_value, str) and fallback_value.strip():
            self.fallback_providers = [item.strip().lower() for item in fallback_value.split(",") if item.strip()]

        self.exa_api_key = self._resolve_key("exa_api_key", "EXA_API_KEY", self.exa_api_key)
        self.brave_api_key = self._resolve_key("brave_search_api_key", "BRAVE_SEARCH_API_KEY", self.brave_api_key)
        self.bing_api_key = self._resolve_key("bing_search_api_key", "BING_SEARCH_API_KEY", self.bing_api_key)

    def _provider_order(self, requested_provider: str) -> list[str]:
        if requested_provider and requested_provider != "auto":
            return [requested_provider]
        if self.provider_mode and self.provider_mode != "auto":
            return [self.provider_mode]
        return self.fallback_providers

    def _provider_enabled(self, provider: str) -> bool:
        if provider == "exa":
            return bool(self.exa_api_key)
        if provider == "brave":
            return bool(self.brave_api_key)
        if provider == "bing":
            return bool(self.bing_api_key)
        if provider == "duckduckgo":
            return True
        return False

    async def _search_exa(self, query: str, count: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": self.exa_api_key, "Content-Type": "application/json"},
                json={"query": query, "numResults": count},
            )
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            return {"results": []}
        results_raw = payload.get("results", [])
        results: list[dict[str, str]] = []
        if isinstance(results_raw, list):
            for row in cast(list[Any], results_raw)[:count]:
                if not isinstance(row, dict):
                    continue
                row_map = cast(dict[str, Any], row)
                title = str(row_map.get("title", "")).strip() or str(row_map.get("url", "")).strip()
                snippet = str(row_map.get("text", "")).strip()
                if len(snippet) > 320:
                    snippet = snippet[:317] + "..."
                results.append({"title": title, "snippet": snippet, "url": str(row_map.get("url", "")).strip()})
        return {"results": results}

    async def _search_brave(self, query: str, count: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": count},
                headers={"Accept": "application/json", "X-Subscription-Token": self.brave_api_key},
            )
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            return {"results": []}
        web = payload.get("web", {})
        web_map = cast(dict[str, Any], web) if isinstance(web, dict) else {}
        results_raw = web_map.get("results", [])
        results: list[dict[str, str]] = []
        if isinstance(results_raw, list):
            for row in cast(list[Any], results_raw)[:count]:
                if not isinstance(row, dict):
                    continue
                row_map = cast(dict[str, Any], row)
                results.append(
                    {
                        "title": str(row_map.get("title", "")).strip(),
                        "snippet": str(row_map.get("description", "")).strip(),
                        "url": str(row_map.get("url", "")).strip(),
                    }
                )
        return {"results": results}

    async def _search_bing(self, query: str, count: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                "https://api.bing.microsoft.com/v7.0/search",
                params={"q": query, "count": count, "responseFilter": "Webpages", "safeSearch": "Moderate"},
                headers={"Ocp-Apim-Subscription-Key": self.bing_api_key},
            )
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            return {"results": []}
        web_pages = payload.get("webPages", {})
        web_map = cast(dict[str, Any], web_pages) if isinstance(web_pages, dict) else {}
        value = web_map.get("value", [])
        results: list[dict[str, str]] = []
        if isinstance(value, list):
            for item in cast(list[Any], value)[:count]:
                if not isinstance(item, dict):
                    continue
                item_map = cast(dict[str, Any], item)
                results.append(
                    {
                        "title": str(item_map.get("name", "")).strip(),
                        "snippet": str(item_map.get("snippet", "")).strip(),
                        "url": str(item_map.get("url", "")).strip(),
                    }
                )
        return {"results": results}

    async def _search_duckduckgo(self, query: str, count: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )
            resp.raise_for_status()
            payload = resp.json()

        if not isinstance(payload, dict):
            return {"results": []}
        data = cast(dict[str, Any], payload)

        results: list[dict[str, str]] = []

        abstract_text_value = data.get("AbstractText")
        abstract_text = abstract_text_value.strip() if isinstance(abstract_text_value, str) else ""
        if abstract_text:
            heading_value = data.get("Heading")
            heading = heading_value.strip() if isinstance(heading_value, str) and heading_value.strip() else query
            results.append({"title": heading, "snippet": abstract_text, "url": ""})

        related_raw = data.get("RelatedTopics")
        related_topics: list[Any] = cast(list[Any], related_raw) if isinstance(related_raw, list) else []

        for topic in related_topics:
            if not isinstance(topic, dict):
                continue
            topic_map = cast(dict[str, Any], topic)
            topic_text = topic_map.get("Text")
            topic_url = str(topic_map.get("FirstURL", "")).strip()
            if isinstance(topic_text, str) and topic_text.strip():
                text = topic_text.strip()
                results.append({"title": text, "snippet": text, "url": topic_url})
            nested_raw = topic_map.get("Topics")
            nested_topics: list[Any] = cast(list[Any], nested_raw) if isinstance(nested_raw, list) else []
            for nested in nested_topics:
                if not isinstance(nested, dict):
                    continue
                nested_map = cast(dict[str, Any], nested)
                nested_text = nested_map.get("Text")
                nested_url = str(nested_map.get("FirstURL", "")).strip()
                if isinstance(nested_text, str) and nested_text.strip():
                    text = nested_text.strip()
                    results.append({"title": text, "snippet": text, "url": nested_url})
            if len(results) >= count:
                break

        return {"results": results[:count]}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"results": []}
        count = max(1, min(10, int(input_data.get("count", 5))))
        requested_provider = str(input_data.get("provider", "")).strip().lower()
        provider_order = self._provider_order(requested_provider)
        provider_errors: list[str] = []

        for provider in provider_order:
            if not self._provider_enabled(provider):
                provider_errors.append(f"{provider}: nicht konfiguriert")
                continue
            try:
                if provider == "exa":
                    response = await self._search_exa(query, count)
                elif provider == "brave":
                    response = await self._search_brave(query, count)
                elif provider == "bing":
                    response = await self._search_bing(query, count)
                else:
                    response = await self._search_duckduckgo(query, count)

                results = response.get("results", [])
                if isinstance(results, list) and results:
                    return {
                        "provider": provider,
                        "results": results,
                        "provider_errors": provider_errors,
                    }
                provider_errors.append(f"{provider}: keine Ergebnisse")
            except httpx.HTTPStatusError as exc:
                provider_errors.append(f"{provider}: HTTP {exc.response.status_code}")
            except Exception as exc:
                provider_errors.append(f"{provider}: {exc}")

        return {"provider": "none", "results": [], "provider_errors": provider_errors}

