# packages/plugins/openai_api/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false

import json
import os
from typing import Any, AsyncGenerator, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "openai_api",
    "name": "OpenAI API",
    "description": "OpenAI API (GPT-4, GPT-3.5, Embeddings, etc.)",
    "category": "🔌 Externe APIs",
    "apiKeyRequired": True,
    "intentPattern": r"\b(openai|gpt|chatgpt|gpt-4|gpt-3.5|embedding|whisper|dall-e)\b",
    "settingsFields": [
        {
            "key": "default_model",
            "label": "Standardmodell",
            "type": "select",
            "group": "Modell",
            "options": ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "default": "gpt-4o-mini",
            "description": "Wird genutzt, wenn kein Modell explizit übergeben wird.",
        },
        {
            "key": "default_temperature",
            "label": "Standard-Temperatur",
            "type": "number",
            "group": "Modell",
            "default": 0.7,
            "description": "Kreativität bei Chat-Antworten.",
        },
        {
            "key": "default_max_tokens",
            "label": "Standard Max Tokens",
            "type": "number",
            "group": "Modell",
            "default": 512,
            "description": "Maximale Antwortlänge für Standardaufrufe.",
        },
        {
            "key": "enable_streaming",
            "label": "Streaming standardmäßig aktiv",
            "type": "boolean",
            "group": "Laufzeit",
            "default": True,
            "description": "Wenn aktiv, werden Antworten chunkweise geliefert.",
        },
    ],
    "status": "implemented",
}


class OpenAIAPIPlugin:
    name = "openai_api"
    description = "OpenAI API (GPT-4, GPT-3.5, Embeddings, etc.)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Der Prompt für das OpenAI-Modell.",
            },
            "model": {
                "type": "string",
                "enum": [
                    "gpt-4",
                    "gpt-4-turbo",
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-3.5-turbo",
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                    "text-embedding-ada-002",
                    "whisper-1",
                    "dall-e-3",
                    "dall-e-2",
                ],
                "default": "gpt-4o-mini",
                "description": "OpenAI-Modell.",
            },
            "task": {
                "type": "string",
                "enum": ["chat", "completion", "embedding", "transcription", "image"],
                "default": "chat",
                "description": "Aufgabentyp.",
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
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                        "content": {"type": "string"},
                    },
                },
                "description": "Alternativ zu prompt: Liste von Nachrichten für Chat.",
            },
            "image_prompt": {
                "type": "string",
                "description": "Prompt für Bildgenerierung (für DALL-E).",
            },
            "image_size": {
                "type": "string",
                "enum": ["1024x1024", "1792x1024", "1024x1792"],
                "default": "1024x1024",
                "description": "Bildgröße für DALL-E.",
            },
            "image_quality": {
                "type": "string",
                "enum": ["standard", "hd"],
                "default": "standard",
                "description": "Bildqualität für DALL-E.",
            },
            "embedding_model": {
                "type": "string",
                "enum": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
                "default": "text-embedding-3-small",
                "description": "Embedding-Modell.",
            },
            "audio_file": {
                "type": "string",
                "description": "Pfad oder Base64-kodierte Audiodatei für Transkription.",
            },
        },
        "required": ["prompt"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "model": {"type": "string"},
            "content": {"type": "string"},
            "tokens_input": {"type": "integer"},
            "tokens_output": {"type": "integer"},
            "tokens_total": {"type": "integer"},
            "cost": {"type": "number"},
            "image_url": {"type": "string"},
            "embedding": {"type": "array"},
            "transcription": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    # Kosten pro 1000 Tokens (Stand Juni 2026)
    _COST_MAP: dict[str, dict[str, float]] = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "text-embedding-3-small": {"input": 0.00002, "output": 0.00002},
        "text-embedding-3-large": {"input": 0.00013, "output": 0.00013},
        "text-embedding-ada-002": {"input": 0.0001, "output": 0.0001},
    }

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    def _estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        """Schätzt die Kosten für die Nutzung."""
        if model not in self._COST_MAP:
            return 0.0
        costs = self._COST_MAP[model]
        input_cost = (tokens_input / 1000) * costs.get("input", 0)
        output_cost = (tokens_output / 1000) * costs.get("output", 0)
        return input_cost + output_cost

    async def _request(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Führt einen Request an die OpenAI API durch."""
        if not self._is_configured():
            return {"error": "OpenAI API-Key nicht konfiguriert. Setze OPENAI_API_KEY in der Umgebung."}

        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=self.headers, json=data)
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"error": "Ungültiger API-Key. Prüfe OPENAI_API_KEY."}
                if e.response.status_code == 429:
                    return {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                if e.response.status_code == 503:
                    return {"error": "OpenAI API ist derzeit nicht verfügbar."}
                return {"error": f"HTTP-Fehler: {e.response.status_code} - {e.response.text}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def _stream_request(self, endpoint: str, data: dict[str, Any]) -> AsyncGenerator[dict[str, Any], None]:
        """Führt einen Streaming-Request an die OpenAI API durch."""
        if not self._is_configured():
            yield {"type": "error", "error": "OpenAI API-Key nicht konfiguriert."}
            return

        data["stream"] = True
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream("POST", url, headers=self.headers, json=data) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                yield {"type": "chunk", "data": chunk}
                            except json.JSONDecodeError:
                                continue
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    yield {"type": "error", "error": "Ungültiger API-Key."}
                elif e.response.status_code == 429:
                    yield {"type": "error", "error": "Rate-Limit überschritten."}
                else:
                    yield {"type": "error", "error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                yield {"type": "error", "error": f"Fehler: {str(e)}"}

    async def _chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> dict[str, Any]:
        """Führt eine Chat-Completion durch."""
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if stream:
            chunks = []
            full_content = ""
            usage = None
            async for chunk in self._stream_request("/chat/completions", data):
                if chunk.get("type") == "error":
                    return {"success": False, "error": chunk["error"]}
                if chunk.get("type") == "chunk":
                    delta = chunk["data"].get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        full_content += content
                        chunks.append(content)
            return {
                "success": True,
                "content": full_content,
                "model": model,
                "usage": usage,
            }
        else:
            result = await self._request("/chat/completions", data)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = result.get("usage", {})
            return {
                "success": True,
                "content": message.get("content", ""),
                "model": result.get("model", model),
                "usage": usage,
            }

    async def _embedding(self, text: str, model: str) -> dict[str, Any]:
        """Erstellt ein Embedding für einen Text."""
        data = {
            "model": model,
            "input": text,
        }
        result = await self._request("/embeddings", data)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        embedding_data = result.get("data", [])
        embedding = embedding_data[0].get("embedding", []) if embedding_data else []
        usage = result.get("usage", {})
        return {
            "success": True,
            "embedding": embedding,
            "model": result.get("model", model),
            "usage": usage,
        }

    async def _image_generation(self, prompt: str, size: str, quality: str) -> dict[str, Any]:
        """Generiert ein Bild mit DALL-E."""
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
        }
        result = await self._request("/images/generations", data)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        image_data = result.get("data", [])
        image_url = image_data[0].get("url") if image_data else None
        return {
            "success": True,
            "image_url": image_url,
            "model": "dall-e-3",
            "usage": {},
        }

    async def _transcription(self, audio_file: str) -> dict[str, Any]:
        """Transkribiert eine Audiodatei."""
        # Hinweis: Für Audio-Transkription ist eine Datei-Upload erforderlich.
        # Diese Implementierung ist ein Platzhalter für die Integration.
        return {"success": False, "error": "Transkription benötigt eine Datei-Upload."}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task = str(input_data.get("task", "chat")).lower()

        if task == "chat":
            prompt = str(input_data.get("prompt", "")).strip()
            model = str(input_data.get("model", "gpt-4o-mini")).strip()
            temperature = float(input_data.get("temperature", 0.7))
            max_tokens = int(input_data.get("max_tokens", 512))
            stream = bool(input_data.get("stream", True))
            system_prompt = str(input_data.get("system_prompt", "")).strip() or None
            messages = input_data.get("messages")

            if not prompt and not messages:
                return {"success": False, "error": "prompt oder messages ist erforderlich."}

            if messages:
                if not isinstance(messages, list):
                    return {"success": False, "error": "messages muss ein Array sein."}
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

            result = await self._chat_completion(messages, model, temperature, max_tokens, stream)
            if not result.get("success"):
                return result

            usage = result.get("usage", {})
            tokens_input = usage.get("prompt_tokens", 0)
            tokens_output = usage.get("completion_tokens", 0)
            cost = self._estimate_cost(model, tokens_input, tokens_output)

            return {
                "success": True,
                "content": result.get("content", ""),
                "model": result.get("model", model),
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "tokens_total": usage.get("total_tokens", 0),
                "cost": round(cost, 6),
            }

        elif task == "embedding":
            text = str(input_data.get("prompt", "")).strip()
            model = str(input_data.get("embedding_model", "text-embedding-3-small")).strip()
            if not text:
                return {"success": False, "error": "prompt für Embedding ist erforderlich."}
            result = await self._embedding(text, model)
            if not result.get("success"):
                return result
            usage = result.get("usage", {})
            tokens_input = usage.get("prompt_tokens", 0)
            cost = self._estimate_cost(model, tokens_input, 0)
            return {
                "success": True,
                "embedding": result.get("embedding", []),
                "model": result.get("model", model),
                "tokens_input": tokens_input,
                "tokens_total": usage.get("total_tokens", 0),
                "cost": round(cost, 6),
            }

        elif task == "image":
            prompt = str(input_data.get("image_prompt", input_data.get("prompt", ""))).strip()
            if not prompt:
                return {"success": False, "error": "image_prompt ist erforderlich."}
            size = str(input_data.get("image_size", "1024x1024")).strip()
            quality = str(input_data.get("image_quality", "standard")).strip()
            result = await self._image_generation(prompt, size, quality)
            if not result.get("success"):
                return result
            # Kosten für DALL-E 3: ca. $0.04-$0.08 pro Bild (abhängig von Größe)
            cost = 0.04 if size == "1024x1024" else 0.08
            return {
                "success": True,
                "image_url": result.get("image_url"),
                "model": "dall-e-3",
                "cost": cost,
            }

        elif task == "transcription":
            audio_file = str(input_data.get("audio_file", "")).strip()
            if not audio_file:
                return {"success": False, "error": "audio_file ist erforderlich."}
            return await self._transcription(audio_file)

        else:
            return {"success": False, "error": f"Unbekannte Aufgabe: {task}"}