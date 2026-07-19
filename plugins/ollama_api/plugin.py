# packages/plugins/ollama_api/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportUnusedImport=false

import json
import os
from typing import Any, AsyncGenerator, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "ollama_api",
    "name": "OLLAMA API",
    "description": "OLLAMA lokale API (Textgenerierung mit verschiedenen Modellen)",
    "category": "🔌 Externe APIs",
    "apiKeyRequired": False,
    "intentPattern": r"\b(ollama|lokal|llama|mistral|code llama)\b",
    "settingsFields": [
        {
            "key": "default_model",
            "label": "Standardmodell",
            "type": "string",
            "group": "Modell",
            "default": "llama2",
            "description": "Wird genutzt, wenn kein Modell im Prompt gesetzt ist.",
        },
        {
            "key": "api_base",
            "label": "API Base URL",
            "type": "string",
            "group": "Verbindung",
            "default": "http://localhost:11434",
            "description": "OLLAMA-Endpunkt für API-Aufrufe.",
        },
        {
            "key": "default_temperature",
            "label": "Standard-Temperatur",
            "type": "number",
            "group": "Modell",
            "default": 0.7,
            "description": "Kreativität bei Textgenerierung.",
        },
        {
            "key": "default_keep_alive",
            "label": "Keep-Alive (Sek.)",
            "type": "number",
            "group": "Laufzeit",
            "default": 300,
            "description": "Wie lange das Modell im Speicher bleibt.",
        },
    ],
    "status": "implemented",
}


class OllamaAPIPlugin:
    name = "ollama_api"
    description = "OLLAMA lokale API (Textgenerierung mit verschiedenen Modellen)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Der Prompt für das OLLAMA-Modell.",
            },
            "model": {
                "type": "string",
                "description": "Name des OLLAMA-Modells (z.B. llama2, mistral, codellama).",
                "default": "llama2",
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
            "keep_alive": {
                "type": "integer",
                "description": "Zeit in Sekunden, die das Modell im Speicher gehalten wird.",
                "default": 300,
            },
            "api_base": {
                "type": "string",
                "description": "OLLAMA API-Basis-URL (überschreibt die Umgebungsvariable).",
            },
        },
        "required": ["prompt"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "model": {"type": "string"},
            "response": {"type": "string"},
            "tokens": {"type": "integer"},
            "total_duration": {"type": "number"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "llama2")

    def _get_api_base(self, input_data: dict[str, Any]) -> str:
        """Ermittelt die API-Basis-URL aus Input oder Umgebung."""
        api_base = str(input_data.get("api_base", "")).strip()
        if api_base:
            return api_base
        return self.api_base

    async def _get_available_models(self, api_base: str) -> list[str]:
        """Ruft die Liste der verfügbaren Modelle von OLLAMA ab."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{api_base}/api/tags")
                response.raise_for_status()
                data = response.json()
                models = data.get("models", [])
                return [model.get("name") for model in models if model.get("name")]
        except Exception:
            return []

    async def _generate_stream(
        self,
        api_base: str,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
        keep_alive: int,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generiert eine Antwort mit Streaming-Unterstützung."""
        url = f"{api_base}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if keep_alive:
            payload["keep_alive"] = keep_alive

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if data.get("done"):
                                yield {
                                    "type": "done",
                                    "model": data.get("model", model),
                                    "tokens": data.get("eval_count", 0),
                                    "total_duration": data.get("total_duration", 0),
                                }
                                break
                            yield {
                                "type": "chunk",
                                "content": data.get("response", ""),
                                "model": data.get("model", model),
                            }
                        except json.JSONDecodeError:
                            continue
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    yield {"type": "error", "message": f"Modell '{model}' nicht gefunden. Verfügbare Modelle: {await self._get_available_models(api_base)}"}
                elif e.response.status_code == 503:
                    yield {"type": "error", "message": "OLLAMA nicht verfügbar. Stelle sicher, dass OLLAMA läuft."}
                else:
                    yield {"type": "error", "message": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                yield {"type": "error", "message": f"Fehler: {str(e)}"}

    async def _generate_sync(
        self,
        api_base: str,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
        keep_alive: int,
    ) -> dict[str, Any]:
        """Generiert eine Antwort ohne Streaming."""
        url = f"{api_base}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if keep_alive:
            payload["keep_alive"] = keep_alive

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "model": data.get("model", model),
                    "tokens": data.get("eval_count", 0),
                    "total_duration": data.get("total_duration", 0),
                }
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    available = await self._get_available_models(api_base)
                    return {"success": False, "error": f"Modell '{model}' nicht gefunden. Verfügbare Modelle: {available}"}
                if e.response.status_code == 503:
                    return {"success": False, "error": "OLLAMA nicht verfügbar. Stelle sicher, dass OLLAMA läuft."}
                return {"success": False, "error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"success": False, "error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        prompt = str(input_data.get("prompt", "")).strip()
        if not prompt:
            return {"success": False, "error": "Prompt ist erforderlich."}

        api_base = self._get_api_base(input_data)
        model = str(input_data.get("model", self.default_model)).strip()
        temperature = float(input_data.get("temperature", 0.7))
        max_tokens = int(input_data.get("max_tokens", 512))
        stream = bool(input_data.get("stream", True))
        system_prompt = str(input_data.get("system_prompt", "")).strip() or None
        keep_alive = int(input_data.get("keep_alive", 300))

        # Bei Streaming: Chunks sammeln und als vollständige Antwort zurückgeben (für einfache Nutzung)
        # In der Praxis könnte man Streaming auch über die Orchestrator-Pipeline abbilden.
        if stream:
            chunks = []
            model_used = model
            tokens = 0
            total_duration = 0
            error = None

            async for chunk in self._generate_stream(
                api_base, prompt, model, temperature, max_tokens, system_prompt, keep_alive
            ):
                if chunk.get("type") == "chunk":
                    chunks.append(chunk.get("content", ""))
                    model_used = chunk.get("model", model_used)
                elif chunk.get("type") == "done":
                    model_used = chunk.get("model", model_used)
                    tokens = chunk.get("tokens", 0)
                    total_duration = chunk.get("total_duration", 0)
                elif chunk.get("type") == "error":
                    error = chunk.get("message", "Unbekannter Fehler")
                    break

            if error:
                return {"success": False, "error": error}

            response_text = "".join(chunks).strip()
            return {
                "success": True,
                "model": model_used,
                "response": response_text,
                "tokens": tokens,
                "total_duration": total_duration,
            }
        else:
            result = await self._generate_sync(
                api_base, prompt, model, temperature, max_tokens, system_prompt, keep_alive
            )
            return result