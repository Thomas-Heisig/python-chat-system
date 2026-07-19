# packages/plugins/news/plugin.py
from __future__ import annotations

import os
from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "news",
    "name": "News",
    "description": "Aktuelle Nachrichten aus verschiedenen Quellen (NewsAPI)",
    "category": "📊 Business & Analytics",
    "apiKeyRequired": True,
    "intentPattern": r"\b(nachrichten|news|aktuelle|meldungen|headlines|schlagzeilen)\b",
    "status": "implemented",
    "settingsFields": [],
}


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key_raw, value_raw in cast(dict[object, Any], value).items():
        normalized[str(key_raw)] = value_raw
    return normalized


class NewsPlugin:
    name = "news"
    description = "Aktuelle Nachrichten aus verschiedenen Quellen (NewsAPI)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Suchbegriff für Nachrichten (z.B. 'Granit', 'Naturstein').",
            },
            "category": {
                "type": "string",
                "enum": ["business", "entertainment", "general", "health", "science", "sports", "technology"],
                "default": "general",
                "description": "Nachrichtenkategorie.",
            },
            "country": {
                "type": "string",
                "enum": ["ae", "ar", "at", "au", "be", "bg", "br", "ca", "ch", "cn", "co", "cu", "cz", "de", "eg", "fr", "gb", "gr", "hk", "hu", "id", "ie", "il", "in", "it", "jp", "kr", "lt", "lv", "ma", "mx", "my", "ng", "nl", "no", "nz", "ph", "pl", "pt", "ro", "rs", "ru", "sa", "se", "sg", "si", "sk", "th", "tr", "tw", "ua", "us", "ve", "za"],
                "default": "de",
                "description": "Ländercode für Nachrichten (z.B. de, us, gb).",
            },
            "source": {
                "type": "string",
                "description": "Nachrichtenquelle (z.B. 'bbc-news', 'cnn').",
            },
            "page_size": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 5,
                "description": "Anzahl der Artikel pro Seite.",
            },
            "page": {
                "type": "integer",
                "minimum": 1,
                "default": 1,
                "description": "Seitennummer.",
            },
            "sort_by": {
                "type": "string",
                "enum": ["relevancy", "popularity", "publishedAt"],
                "default": "publishedAt",
                "description": "Sortierkriterium.",
            },
            "language": {
                "type": "string",
                "enum": ["ar", "de", "en", "es", "fr", "he", "it", "nl", "no", "pt", "ru", "sv", "ud", "zh"],
                "default": "de",
                "description": "Sprache der Artikel.",
            },
            "from_date": {
                "type": "string",
                "description": "Datum im Format YYYY-MM-DD (ab diesem Datum).",
            },
            "to_date": {
                "type": "string",
                "description": "Datum im Format YYYY-MM-DD (bis zu diesem Datum).",
            },
        },
        "required": ["query"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "total_results": {"type": "integer"},
            "articles": {"type": "array"},
            "query": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = (
            os.getenv("NEWS_API_KEY", "")
            or os.getenv("NEWSAPI_API_KEY", "")
            or os.getenv("NEWS_APIKEY", "")
        )
        self.base_url = "https://newsapi.org/v2"

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Führt einen Request an die NewsAPI durch."""
        if not self._is_configured():
            return {"error": "NewsAPI-Key nicht konfiguriert. Setze NEWS_API_KEY in der Umgebung."}

        url = f"{self.base_url}{endpoint}"
        params["apiKey"] = self.api_key

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"error": "Ungültiger API-Key. Prüfe NEWS_API_KEY."}
                if e.response.status_code == 429:
                    return {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

        if data.get("status") != "ok":
            return {"error": data.get("message", "Unbekannter Fehler")}

        return data

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"error": "Suchbegriff (query) ist erforderlich."}

        category = str(input_data.get("category", "general")).strip()
        country = str(input_data.get("country", "de")).strip()
        source = str(input_data.get("source", "")).strip() or None
        page_size = max(1, min(100, int(input_data.get("page_size", 5))))
        page = max(1, int(input_data.get("page", 1)))
        sort_by = str(input_data.get("sort_by", "publishedAt")).strip()
        language = str(input_data.get("language", "de")).strip()
        from_date = str(input_data.get("from_date", "")).strip() or None
        to_date = str(input_data.get("to_date", "")).strip() or None

        # Endpunkt wählen: /everything oder /top-headlines
        # Wenn nur Kategorie/Land/Quelle, dann top-headlines
        # Sonst everything (für Suche)
        use_headlines = False
        if not query and (category or country or source):
            use_headlines = True

        if use_headlines:
            endpoint = "/top-headlines"
            params: dict[str, Any] = {
                "pageSize": page_size,
                "page": page,
            }
            if category:
                params["category"] = category
            if country:
                params["country"] = country
            if source:
                params["sources"] = source
            if language:
                params["language"] = language
        else:
            endpoint = "/everything"
            params = {
                "q": query,
                "pageSize": page_size,
                "page": page,
                "sortBy": sort_by,
                "language": language,
            }
            if source:
                params["sources"] = source
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date

        result = await self._request(endpoint, params)

        if "error" in result:
            return {"success": False, "error": result["error"]}

        articles_raw = result.get("articles", [])
        articles: list[dict[str, Any]] = []
        if isinstance(articles_raw, list):
            for raw_article in cast(list[Any], articles_raw):
                article = _as_dict(raw_article)
                if article:
                    articles.append(article)
        total_results = result.get("totalResults", len(articles))

        # Artikel formatieren
        formatted_articles: list[dict[str, Any]] = []
        for article in articles:
            formatted_articles.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", ""),
                "author": article.get("author", ""),
                "published_at": article.get("publishedAt", ""),
                "content": article.get("content", ""),
            })

        return {
            "success": True,
            "total_results": total_results,
            "articles": formatted_articles,
            "query": query,
        }


