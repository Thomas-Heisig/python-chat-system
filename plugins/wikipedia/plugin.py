from __future__ import annotations

from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
	"id": "wikipedia",
	"name": "Wikipedia",
	"description": "Wikipedia-Artikelabruf",
	"category": "🌐 Core / Web",
	"apiKeyRequired": False,
	"intentPattern": r"\b(wikipedia|wiki|lexikon)\b",
	"status": "implemented",
    "settingsFields": [],
}


class WikipediaPlugin:
	name = "wikipedia"
	description = "Wikipedia-Artikelabruf"
	input_schema: dict[str, Any] = {"type": "object", "properties": {"title": {"type": "string"}}}
	output_schema: dict[str, Any] = {
		"type": "object",
		"properties": {
			"extract": {"type": "string"},
		},
	}

	async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
		title = str(input_data.get("title", "")).strip()
		if not title:
			return {"extract": "Seite nicht gefunden."}

		try:
			async with httpx.AsyncClient(timeout=10.0) as client:
				resp = await client.get(
					"https://de.wikipedia.org/w/api.php",
					params={
						"action": "query",
						"prop": "extracts",
						"exintro": True,
						"explaintext": True,
						"titles": title,
						"format": "json",
						"redirects": 1,
					},
				)
				resp.raise_for_status()
				payload = resp.json()
		except (httpx.HTTPError, ValueError):
			return {"extract": "Wikipedia derzeit nicht erreichbar."}

		if not isinstance(payload, dict):
			return {"extract": "Seite nicht gefunden."}
		data = cast(dict[str, Any], payload)
		query = data.get("query")
		if not isinstance(query, dict):
			return {"extract": "Seite nicht gefunden."}
		pages = query.get("pages")
		if not isinstance(pages, dict):
			return {"extract": "Seite nicht gefunden."}

		for page_id, page in pages.items():
			if str(page_id) == "-1" or not isinstance(page, dict):
				continue
			extract = page.get("extract")
			if isinstance(extract, str) and extract.strip():
				return {"extract": extract.strip()}

		return {"extract": "Seite nicht gefunden."}


