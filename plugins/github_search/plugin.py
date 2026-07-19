# packages/plugins/github_search/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false

import os
from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "github_search",
    "name": "GitHub Search",
    "description": "GitHub Code-, Repository- und Issue-Suche über die GitHub API",
    "category": "🔧 Developer Tools",
    "apiKeyRequired": True,
    "intentPattern": r"\b(github|code|repository|repo|issue|pull request|pr|star|fork|commit)\b",
    "status": "implemented",
    "settingsFields": [],
}


class GitHubSearchPlugin:
    name = "github_search"
    description = "GitHub Code-, Repository- und Issue-Suche über die GitHub API"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Suchbegriff für GitHub.",
            },
            "type": {
                "type": "string",
                "enum": ["repositories", "code", "issues", "users"],
                "default": "repositories",
                "description": "Typ der Suche: repositories, code, issues, users.",
            },
            "language": {
                "type": "string",
                "description": "Programmiersprache für Code-Suche (z.B. python, javascript).",
            },
            "repo": {
                "type": "string",
                "description": "Repository für Code-Suche (z.B. owner/repo).",
            },
            "owner": {
                "type": "string",
                "description": "Besitzer für Repository-Suche (z.B. owner).",
            },
            "sort": {
                "type": "string",
                "enum": ["stars", "forks", "updated", "relevance"],
                "default": "relevance",
                "description": "Sortierkriterium für Repository-Suche.",
            },
            "order": {
                "type": "string",
                "enum": ["asc", "desc"],
                "default": "desc",
                "description": "Sortierreihenfolge.",
            },
            "per_page": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 10,
                "description": "Anzahl der Ergebnisse pro Seite.",
            },
            "page": {
                "type": "integer",
                "minimum": 1,
                "default": 1,
                "description": "Seitennummer.",
            },
        },
        "required": ["query"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "total_count": {"type": "integer"},
            "items": {"type": "array"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = os.getenv("GITHUB_API_KEY", os.getenv("GITHUB_TOKEN", ""))
        self.base_url = "https://api.github.com"
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"token {self.api_key}"
        self.headers["Accept"] = "application/vnd.github.v3+json"

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Führt einen Request an die GitHub API durch."""
        if not self._is_configured():
            return {"error": "GitHub Token nicht konfiguriert. Setze GITHUB_TOKEN in der Umgebung."}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"error": "Ungültiger GitHub Token. Prüfe GITHUB_TOKEN."}
                if e.response.status_code == 403:
                    return {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                if e.response.status_code == 404:
                    return {"error": "Nicht gefunden."}
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"error": "query ist erforderlich."}

        search_type = str(input_data.get("type", "repositories")).lower()
        per_page = max(1, min(100, int(input_data.get("per_page", 10))))
        page = max(1, int(input_data.get("page", 1)))
        sort = str(input_data.get("sort", "relevance"))
        order = str(input_data.get("order", "desc"))
        language = str(input_data.get("language", "")).strip()
        repo = str(input_data.get("repo", "")).strip()
        owner = str(input_data.get("owner", "")).strip()

        # Suchanfrage aufbauen
        search_query = query
        if language:
            search_query += f" language:{language}"
        if repo:
            search_query += f" repo:{repo}"
        if owner:
            search_query += f" user:{owner}"

        params = {
            "q": search_query,
            "per_page": per_page,
            "page": page,
        }

        if search_type == "repositories":
            params["sort"] = sort
            params["order"] = order
            endpoint = "/search/repositories"
        elif search_type == "code":
            endpoint = "/search/code"
        elif search_type == "issues":
            endpoint = "/search/issues"
        elif search_type == "users":
            endpoint = "/search/users"
        else:
            return {"error": f"Unbekannter Suchtyp: {search_type}"}

        result = await self._request(endpoint, params)

        if "error" in result:
            return {"success": False, "error": result["error"]}

        # Ergebnisse formatieren
        items = result.get("items", [])
        formatted_items = []

        for item in items:
            if search_type == "repositories":
                formatted_items.append({
                    "id": item.get("id"),
                    "name": item.get("full_name"),
                    "description": item.get("description"),
                    "url": item.get("html_url"),
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "language": item.get("language"),
                    "owner": item.get("owner", {}).get("login"),
                    "updated_at": item.get("updated_at"),
                })
            elif search_type == "code":
                formatted_items.append({
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "repository": item.get("repository", {}).get("full_name"),
                    "url": item.get("html_url"),
                })
            elif search_type == "issues":
                formatted_items.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "url": item.get("html_url"),
                    "repository": item.get("repository_url", "").replace("https://api.github.com/repos/", ""),
                    "user": item.get("user", {}).get("login"),
                    "created_at": item.get("created_at"),
                })
            elif search_type == "users":
                formatted_items.append({
                    "id": item.get("id"),
                    "login": item.get("login"),
                    "name": item.get("name"),
                    "url": item.get("html_url"),
                    "avatar_url": item.get("avatar_url"),
                    "repos": item.get("public_repos"),
                    "followers": item.get("followers"),
                })

        return {
            "success": True,
            "total_count": result.get("total_count", 0),
            "items": formatted_items,
        }

