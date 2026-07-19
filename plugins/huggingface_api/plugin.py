# packages/plugins/huggingface_api/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportUnusedImport=false

import os
from typing import Any, AsyncGenerator, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "huggingface_api",
    "name": "Hugging Face API",
    "description": "Hugging Face Inference API (Text, Embeddings, Bilder, etc.)",
    "category": "🔌 Externe APIs",
    "apiKeyRequired": True,
    "intentPattern": r"\b(huggingface|hf|inference|embedding|generation)\b",
    "status": "implemented",
    "settingsFields": [],
}


class HuggingFaceAPIPlugin:
    name = "huggingface_api"
    description = "Hugging Face Inference API (Text, Embeddings, Bilder, etc.)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Modell-ID auf Hugging Face (z.B. 'meta-llama/Llama-2-7b-chat-hf').",
                "default": "microsoft/phi-2",
            },
            "prompt": {
                "type": "string",
                "description": "Eingabetext für Textgenerierung.",
            },
            "task": {
                "type": "string",
                "enum": [
                    "text-generation",
                    "text2text-generation",
                    "summarization",
                    "translation",
                    "fill-mask",
                    "feature-extraction",
                    "sentence-similarity",
                    "image-generation",
                    "image-to-text",
                    "text-to-image",
                    "object-detection",
                ],
                "default": "text-generation",
                "description": "Aufgabentyp.",
            },
            "parameters": {
                "type": "object",
                "description": "Zusätzliche Parameter für das Modell (z.B. {'temperature': 0.7, 'max_new_tokens': 200}).",
                "additionalProperties": True,
            },
            "input": {
                "type": ["string", "array"],
                "description": "Alternativer Input (für Embeddings oder ähnliche Tasks).",
            },
            "source_lang": {
                "type": "string",
                "description": "Quellsprache für Übersetzung (z.B. 'en', 'de').",
                "default": "en",
            },
            "target_lang": {
                "type": "string",
                "description": "Zielsprache für Übersetzung (z.B. 'en', 'de').",
                "default": "de",
            },
        },
        "oneOf": [
            {"required": ["prompt"]},
            {"required": ["input"]},
        ],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "task": {"type": "string"},
            "model": {"type": "string"},
            "result": {"type": "array"},
            "generated_text": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        self.base_url = "https://api-inference.huggingface.co/models"

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def _request(
        self,
        model: str,
        payload: dict[str, Any],
        task: str = "text-generation",
    ) -> dict[str, Any]:
        """Führt einen Request an die Hugging Face Inference API durch."""
        if not self._is_configured():
            return {"error": "Hugging Face API-Key nicht konfiguriert. Setze HUGGINGFACE_API_KEY in der Umgebung."}

        url = f"{self.base_url}/{model}"

        # Bei bestimmten Tasks müssen wir die Parameter anpassen
        if task == "text-generation":
            # Sicherstellen, dass die Parameter korrekt sind
            if "parameters" not in payload and "parameters" in self.input_schema["properties"]:
                payload["parameters"] = payload.get("parameters", {})
            # Textgenerierung erwartet "inputs" statt "prompt"
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
        elif task == "text2text-generation":
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
        elif task == "summarization":
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
        elif task == "translation":
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
        elif task == "fill-mask":
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
        elif task == "feature-extraction":
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
        elif task == "sentence-similarity":
            # Für Similarity brauchen wir ein Array
            if "input" in payload and isinstance(payload["input"], (list, tuple)):
                payload["inputs"] = {
                    "source_sentence": payload["input"][0],
                    "sentences": payload["input"][1:],
                }
                if "prompt" in payload:
                    del payload["prompt"]
        elif task == "image-generation":
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
            # Bildgenerierung: wir müssen die Antwort als Bytes abfangen
        elif task == "image-to-text":
            # Für Bild-zu-Text brauchen wir Datei-Upload – hier nicht implementiert
            return {"error": "Image-to-Text wird nur mit Datei-Upload unterstützt."}
        elif task == "text-to-image":
            if "prompt" in payload:
                payload["inputs"] = payload.pop("prompt")
        elif task == "object-detection":
            # Objekterkennung ebenfalls Datei-Upload – hier nicht implementiert
            return {"error": "Object Detection wird nur mit Datei-Upload unterstützt."}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return {"success": True, "data": data}
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"error": "Ungültiger API-Key. Prüfe HUGGINGFACE_API_KEY."}
                if e.response.status_code == 503:
                    return {"error": "Modell wird gerade geladen. Bitte später erneut versuchen."}
                if e.response.status_code == 429:
                    return {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                return {"error": f"HTTP-Fehler: {e.response.status_code} - {e.response.text}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        model = str(input_data.get("model", "microsoft/phi-2")).strip()
        task = str(input_data.get("task", "text-generation")).strip()
        parameters = input_data.get("parameters", {})

        # Eingabe vorbereiten
        if "prompt" in input_data:
            prompt = str(input_data["prompt"]).strip()
            if not prompt:
                return {"error": "Prompt ist erforderlich."}
        elif "input" in input_data:
            prompt = input_data["input"]
        else:
            return {"error": "Eingabe (prompt oder input) ist erforderlich."}

        # Spezielle Parameter für Übersetzung
        if task == "translation":
            source_lang = str(input_data.get("source_lang", "en")).strip()
            target_lang = str(input_data.get("target_lang", "de")).strip()
            if not source_lang or not target_lang:
                return {"error": "source_lang und target_lang sind für Übersetzung erforderlich."}
            # Bei Hugging Face: Format "translate_{source}_to_{target}"
            model = f"{source_lang}to{target_lang}" if not model else model

        # Payload bauen
        if task in ["sentence-similarity"]:
            if isinstance(prompt, list):
                if len(prompt) < 2:
                    return {"error": "Für sentence-similarity wird mindestens 1 Quellsatz und 1 Zielsatz benötigt."}
                payload = {"inputs": {"source_sentence": prompt[0], "sentences": prompt[1:]}}
            else:
                return {"error": "Für sentence-similarity wird ein Array benötigt."}
        else:
            payload = {"inputs": prompt, "parameters": parameters}

        # API-Aufruf
        result = await self._request(model, payload, task)

        if "error" in result:
            return {"success": False, "error": result["error"]}

        # Ergebnis formatieren
        data = result.get("data", [])

        # Textgenerierung gibt oft ein Array mit "generated_text" zurück
        generated_text = None
        if task in ["text-generation", "text2text-generation", "summarization"]:
            if isinstance(data, list) and data and isinstance(data[0], dict):
                generated_text = data[0].get("generated_text") or data[0].get("summary_text") or str(data[0])
            elif isinstance(data, list) and data and isinstance(data[0], str):
                generated_text = data[0]
            elif isinstance(data, dict):
                generated_text = str(data)

        return {
            "success": True,
            "task": task,
            "model": model,
            "result": data,
            "generated_text": generated_text,
        }

