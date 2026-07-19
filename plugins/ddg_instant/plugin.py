# packages/plugins/ddg_instant/plugin.py
from __future__ import annotations

from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "ddg_instant",
    "name": "DuckDuckGo Instant Answer",
    "description": "Sofortige Antworten auf Faktenfragen (Wetter, Definitionen, Bedeutungen) über die DuckDuckGo Instant Answer API",
    "category": "🌐 Core / Web",
    "apiKeyRequired": False,
    "intentPattern": r"\b(wetter|definition|bedeutung|instant|antwort|sofort|was ist|wer ist)\b",
    "status": "implemented",
    "settingsFields": [],
}


class DdgInstantPlugin:
    name = "ddg_instant"
    description = "Sofortige Antworten auf Faktenfragen (Wetter, Definitionen, Bedeutungen)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Die Frage oder der Suchbegriff.",
            },
        },
        "required": ["query"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "abstract": {"type": "string"},
            "definition": {"type": "string"},
            "type": {"type": "string"},
            "source": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"error": "Keine Suchanfrage angegeben."}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                    },
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

        if not isinstance(data, dict):
            return {"error": "Ungültige Antwort von der API."}

        payload = cast(dict[str, Any], data)

        # Extrahiere die relevanten Felder
        result: dict[str, Any] = {}

        # AbstractText (zusammenfassende Antwort)
        abstract = payload.get("AbstractText")
        if isinstance(abstract, str) and abstract.strip():
            result["abstract"] = abstract.strip()

        # Definition (für Begriffserklärungen)
        definition = payload.get("Definition")
        if isinstance(definition, str) and definition.strip():
            result["definition"] = definition.strip()

        # Answer (direkte Antwort, z.B. bei Wetter)
        answer = payload.get("Answer")
        if isinstance(answer, str) and answer.strip():
            result["answer"] = answer.strip()

        # Type (z.B. "A" für Artikel, "D" für Definition)
        answer_type = payload.get("Type")
        if isinstance(answer_type, str):
            result["type"] = answer_type

        # Heading (überschrift)
        heading = payload.get("Heading")
        if isinstance(heading, str) and heading.strip():
            result["heading"] = heading.strip()

        # Quelle
        source_url = payload.get("AbstractURL")
        if isinstance(source_url, str) and source_url.strip():
            result["source"] = source_url.strip()

        # Fallback: Wenn nichts gefunden wurde, gib einen Hinweis
        if not any(key in result for key in ["abstract", "definition", "answer"]):
            # Suche in RelatedTopics nach ersten Treffern
            related = payload.get("RelatedTopics")
            if isinstance(related, list) and related:
                for topic in related:
                    if isinstance(topic, dict):
                        text = topic.get("Text")
                        if isinstance(text, str) and text.strip():
                            result["abstract"] = text.strip()
                            break

        if not any(key in result for key in ["abstract", "definition", "answer"]):
            return {"error": f"Keine sofortige Antwort für '{query}' gefunden."}

        return result

