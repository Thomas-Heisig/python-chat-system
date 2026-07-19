# DeepSeek API Plugin

```python
# packages/plugins/deepseek_api/plugin.py
from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "deepseek_api",
    "name": "DeepSeek API",
    "description": "DeepSeek Cloud API (Chat, Code, Reasoner)",
    "category": "🔌 Externe APIs",
    "apiKeyRequired": True,
    "intentPattern": r"\b(deepseek|cloud|reasoner|deepseek-chat|deepseek-coder)\b",
    "status": "implemented",
}


class DeepSeekAPIPlugin:
    name = "deepseek_api"
    description = "DeepSeek Cloud API (Chat, Code, Reasoner)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Der Prompt für das DeepSeek-Modell.",
            },
            "model": {
                "type": "string",
                "enum": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
                "default": "deepseek-chat",
                "description": "DeepSeek-Modell: chat, coder oder reasoner.",
            },
            "temperature": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 2.0,
                "default": 0.7,
                "description": "Kreativität der Antwort (0=deterministisch, 1=kreativ).",
            },
            "max_tokens": {
                "type": "integer",
                "minimum": 1,
                "maximum": 4096,
                "default": 512,
                "description": "Maximale Anzahl von Tokens in der Antwort.",
            },
            "stream": {
                "type": "boolean",
                "default": True,
                "description": "Ob die Antwort gestreamt werden soll.",
            },
            "system_prompt": {
                "type": "string",
                "description": "Optionaler System-Prompt für die Kontextsteuerung.",
            },
        },
        "required": ["prompt"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "model": {"type": "string"},
            "tokens_input": {"type": "integer"},
            "tokens_output": {"type": "integer"},
            "tokens_total": {"type": "integer"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def _request(
        self,
        prompt: str,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 512,
        stream: bool = True,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Führt einen Request an die DeepSeek API durch (mit Streaming-Unterstützung)."""
        if not self._is_configured():
            yield {"error": "DeepSeek API-Key nicht konfiguriert. Setze DEEPSEEK_API_KEY in der Umgebung."}
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                if stream:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    delta = data.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield {
                                            "type": "chunk",
                                            "content": content,
                                            "model": model,
                                            "provider": "deepseek",
                                        }
                                except json.JSONDecodeError:
                                    continue
                else:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    yield {
                        "type": "done",
                        "content": content,
                        "model": model,
                        "tokens_input": usage.get("prompt_tokens", 0),
                        "tokens_output": usage.get("completion_tokens", 0),
                        "tokens_total": usage.get("total_tokens", 0),
                        "provider": "deepseek",
                    }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    yield {"error": "Ungültiger API-Key. Prüfe DEEPSEEK_API_KEY."}
                elif e.response.status_code == 429:
                    yield {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                elif e.response.status_code == 503:
                    yield {"error": "DeepSeek API ist derzeit nicht verfügbar."}
                else:
                    yield {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                yield {"error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        prompt = str(input_data.get("prompt", "")).strip()
        if not prompt:
            return {"error": "Prompt ist erforderlich."}

        model = str(input_data.get("model", "deepseek-chat"))
        temperature = float(input_data.get("temperature", 0.7))
        max_tokens = int(input_data.get("max_tokens", 512))
        stream = bool(input_data.get("stream", True))
        system_prompt = str(input_data.get("system_prompt", "")).strip() or None

        # Sammle alle Chunks (für nicht-streaming oder einfache Rückgabe)
        chunks = []
        error = None
        async for item in self._request(prompt, model, temperature, max_tokens, stream, system_prompt):
            if item.get("error"):
                error = item["error"]
                break
            if item.get("type") == "chunk":
                chunks.append(item.get("content", ""))
            elif item.get("type") == "done":
                return {
                    "content": item.get("content", ""),
                    "model": item.get("model", model),
                    "tokens_input": item.get("tokens_input", 0),
                    "tokens_output": item.get("tokens_output", 0),
                    "tokens_total": item.get("tokens_total", 0),
                }

        if error:
            return {"error": error}

        if chunks:
            return {
                "content": "".join(chunks).strip(),
                "model": model,
                "tokens_input": 0,
                "tokens_output": 0,
                "tokens_total": 0,
            }

        return {"error": "Keine Antwort von DeepSeek erhalten."}
```

## 📄 DeepSeek API Plugin

**ID:** `deepseek_api`  
**Kategorie:** 🔌 Externe APIs  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das DeepSeek API Plugin ermöglicht die **Nutzung der DeepSeek Cloud API** für:

- **Chat** – `deepseek-chat` (Allzweck-Chat)
- **Code** – `deepseek-coder` (Optimiert für Code-Generierung)
- **Reasoner** – `deepseek-reasoner` (Logisches Denken, Schritt-für-Schritt)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(deepseek|cloud|reasoner|deepseek-chat|deepseek-coder)\b
```

**Beispiele:**

- _"Nutze DeepSeek für diese komplexe Frage."_
- _"DeepSeek Coder, bitte generiere Python-Code."_
- _"Lass DeepSeek Reasoner das Problem lösen."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable           | Beschreibung     | Erforderlich |
| ------------------ | ---------------- | ------------ |
| `DEEPSEEK_API_KEY` | DeepSeek API-Key | ✅           |

### DeepSeek API-Key erhalten

1. Besuche [DeepSeek Platform](https://platform.deepseek.com/)
2. Registriere dich und erstelle einen API-Key
3. Setze den Key als `DEEPSEEK_API_KEY` in der Umgebung

---

## 📦 Input-Schema

```json
{
  "prompt": "Erkläre den Unterschied zwischen Granit und Marmor.",
  "model": "deepseek-chat",
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": true,
  "system_prompt": "Du bist ein Naturstein-Experte."
}
```

| Feld            | Typ     | Standard        | Beschreibung                                           |
| --------------- | ------- | --------------- | ------------------------------------------------------ |
| `prompt`        | string  | –               | Der Prompt (erforderlich)                              |
| `model`         | string  | `deepseek-chat` | `deepseek-chat`, `deepseek-coder`, `deepseek-reasoner` |
| `temperature`   | number  | `0.7`           | Kreativität (0.0–2.0)                                  |
| `max_tokens`    | integer | `512`           | Maximale Antwort-Tokens                                |
| `stream`        | boolean | `true`          | Streaming aktivieren                                   |
| `system_prompt` | string  | –               | Optionaler System-Prompt                               |

---

## 📤 Output-Schema

```json
{
  "content": "Granit ist ein magmatisches Gestein...",
  "model": "deepseek-chat",
  "tokens_input": 15,
  "tokens_output": 120,
  "tokens_total": 135
}
```

**Bei Fehlern:**

```json
{
  "error": "DeepSeek API-Key nicht konfiguriert."
}
```

---

## 🧪 Beispiele

### 1. Chat (Streaming)

**Input:**

```json
{
  "prompt": "Erkläre den Unterschied zwischen Granit und Marmor.",
  "model": "deepseek-chat",
  "stream": true
}
```

**Output:** (Streaming) Chunks werden nacheinander geliefert.

### 2. Coder

**Input:**

```json
{
  "prompt": "Schreibe eine Python-Funktion, die die Fibonacci-Zahlen berechnet.",
  "model": "deepseek-coder"
}
```

### 3. Reasoner

**Input:**

```json
{
  "prompt": "Ein Raum hat 5m x 4m. Wie viele 60cm x 60cm Fliesen werden benötigt?",
  "model": "deepseek-reasoner"
}
```

### 4. Mit System-Prompt

**Input:**

```json
{
  "prompt": "Was ist die beste Arbeitsplatte für eine Küche?",
  "system_prompt": "Du bist ein Naturstein-Experte und antwortest auf Deutsch.",
  "temperature": 0.3
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/deepseek_api/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── plugin copy.py     # Backup (optional)
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key"

**Lösung:** Prüfe `DEEPSEEK_API_KEY` in der Umgebung. Stelle sicher, dass der Key gültig und aktiv ist.

### Fehler: "Rate-Limit überschritten"

**Lösung:** DeepSeek hat ein Rate-Limit. Warte einige Sekunden und versuche es erneut.

### Fehler: "DeepSeek API ist derzeit nicht verfügbar"

**Lösung:** Die DeepSeek API hat möglicherweise Wartungsarbeiten. Versuche es später erneut oder verwende ein lokales Modell.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Nutze DeepSeek für diese komplexe Frage: Was ist der Unterschied zwischen Granit, Marmor und Quarzit?"_
>
> **Elisa:** _(nutzt DeepSeek-Chat für eine ausführliche, strukturierte Antwort)_

> **Nutzer:** _"Generiere mir einen Python-Code für eine Steinpreis-Berechnung."_
>
> **Elisa:** _(nutzt DeepSeek-Coder)_

---

## 📚 Siehe auch

- [DeepSeek Platform](https://platform.deepseek.com/)
- [DeepSeek API Dokumentation](https://api-docs.deepseek.com/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
