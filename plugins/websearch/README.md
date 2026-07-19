# 📦 WebSearch Plugin – Vollständige Übersicht

Das `websearch` Plugin ist bereits **korrekt implementiert** und folgt dem Standard-Schema aller Plugins. Hier ist eine vollständige Übersicht:

---

## 📄 `packages/plugins/websearch/plugin.py`

```python
from __future__ import annotations

from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "websearch",
    "name": "WebSearch",
    "description": "DuckDuckGo-Websuche",
    "category": "🌐 Core / Web",
    "apiKeyRequired": False,
    "intentPattern": r"\b(suche|finde|google)\b",
    "status": "implemented",
}


class WebSearchPlugin:
    """Simple external websearch plugin using DuckDuckGo Instant Answer API."""

    name = "websearch"
    description = "DuckDuckGo-Websuche"
    input_schema: dict[str, Any] = {"type": "object", "properties": {"query": {"type": "string"}}}
    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "results": {"type": "array"},
        },
    }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"results": []}

        async with httpx.AsyncClient(timeout=10.0) as client:
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

        # AbstractText (Hauptantwort)
        abstract_text_value = data.get("AbstractText")
        abstract_text = abstract_text_value.strip() if isinstance(abstract_text_value, str) else ""
        if abstract_text:
            heading_value = data.get("Heading")
            heading = heading_value.strip() if isinstance(heading_value, str) and heading_value.strip() else query
            results.append(
                {
                    "title": heading,
                    "snippet": abstract_text,
                }
            )

        # RelatedTopics (weitere Ergebnisse)
        related_raw = data.get("RelatedTopics")
        related_topics: list[Any] = cast(list[Any], related_raw) if isinstance(related_raw, list) else []

        for topic in related_topics:
            if not isinstance(topic, dict):
                continue
            topic_map = cast(dict[str, Any], topic)
            topic_text = topic_map.get("Text")
            if isinstance(topic_text, str) and topic_text.strip():
                text = topic_text.strip()
                results.append({"title": text, "snippet": text})
            nested_raw = topic_map.get("Topics")
            nested_topics: list[Any] = cast(list[Any], nested_raw) if isinstance(nested_raw, list) else []
            for nested in nested_topics:
                if not isinstance(nested, dict):
                    continue
                nested_map = cast(dict[str, Any], nested)
                nested_text = nested_map.get("Text")
                if isinstance(nested_text, str) and nested_text.strip():
                    text = nested_text.strip()
                    results.append({"title": text, "snippet": text})
            if len(results) >= 5:
                break

        return {"results": results[:5]}
```

---

## 📄 `packages/plugins/websearch/README.md`

````markdown
# WebSearch Plugin

**ID:** `websearch`  
**Kategorie:** 🌐 Core / Web  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das WebSearch Plugin führt eine **Websuche** über die **DuckDuckGo Instant Answer API** durch. Es liefert:

- Eine Zusammenfassung (Abstract) der Ergebnisseite
- Verwandte Themen (Related Topics)
- Maximal 5 Ergebnisse

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(suche|finde|google)\b
```text
````

**Beispiele:**

- _"Suche nach Granit-Angeboten."_
- _"Finde Informationen zu Nero Assoluto."_
- _"Google mal nach Naturstein."_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit** – es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "query": "Granit Angebote"
}
```

| Feld    | Typ    | Beschreibung               |
| ------- | ------ | -------------------------- |
| `query` | string | Suchbegriff (erforderlich) |

---

## 📤 Output-Schema

```json
{
  "results": [
    {
      "title": "Granit Angebote – Heishg Naturstein",
      "snippet": "Entdecken Sie unsere aktuellen Granit Angebote..."
    },
    {
      "title": "Granit – Wikipedia",
      "snippet": "Granit ist ein magmatisches Gestein..."
    }
  ]
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/websearch/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Keine Ergebnisse"

**Lösung:** Prüfe den Suchbegriff. Bei sehr spezifischen oder ungewöhnlichen Begriffen liefert DuckDuckGo möglicherweise keine Ergebnisse.

### Fehler: "Timeout"

**Lösung:** Die DuckDuckGo API kann bei hoher Last langsamer sein. Wiederhole die Anfrage später.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Suche nach Granit-Angeboten."_
>
> **Elisa:** _"Ich habe 5 Ergebnisse gefunden:_
>
> 1. _Granit Angebote – Heishg Naturstein_
> 2. _Granit – Wikipedia_
> 3. _..._"

---

## 📚 Siehe auch

- [DuckDuckGo API](https://duckduckgo.com/api)
- [Plugins Übersicht](../PLUGINS.md)

```text

---

## ✅ Fazit

Das **WebSearch Plugin** ist vollständig implementiert und funktionsfähig. Es folgt dem **Standard-Plugin-Schema** und kann bei Bedarf erweitert werden (z. B. durch zusätzliche Suchquellen wie Google oder Bing).

**Möchtest du, dass ich das Plugin erweitere (z. B. mit Google Custom Search oder Bing Search als Fallback) oder ein neues Plugin für eine andere API erstelle?**
```
