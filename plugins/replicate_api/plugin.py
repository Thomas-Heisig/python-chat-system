# packages/plugins/replicate_api/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportUnusedImport=false

import asyncio
import json
import os
import uuid
from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "replicate_api",
    "name": "Replicate API",
    "description": "Replicate Cloud API für KI-Modelle (Bildgenerierung, Text, Audio, etc.)",
    "category": "🔌 Externe APIs",
    "apiKeyRequired": True,
    "intentPattern": r"\b(replicate|sdxl|stable diffusion|bild generieren|image|text-to-image)\b",
    "settingsFields": [
        {
            "key": "default_task",
            "label": "Standardaufgabe",
            "type": "select",
            "group": "Allgemein",
            "options": ["image", "text", "audio", "custom"],
            "default": "image",
            "description": "Voreinstellung für den Task-Typ.",
        },
        {
            "key": "default_model",
            "label": "Standardmodell",
            "type": "string",
            "group": "Modell",
            "default": "stability-ai/sdxl",
            "description": "Modell-Identifier für Standardanfragen.",
        },
        {
            "key": "default_wait_timeout",
            "label": "Wartezeit (Sek.)",
            "type": "number",
            "group": "Laufzeit",
            "default": 120,
            "description": "Maximale Wartezeit bei synchroner Ausführung.",
        },
    ],
    "status": "implemented",
}


class ReplicateAPIPlugin:
    name = "replicate_api"
    description = "Replicate Cloud API für KI-Modelle (Bildgenerierung, Text, Audio, etc.)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "enum": ["image", "text", "audio", "custom"],
                "default": "image",
                "description": "Aufgabentyp: image (Bilder), text (Textgenerierung), audio (Audio), custom (eigenes Modell).",
            },
            "prompt": {
                "type": "string",
                "description": "Prompt für die Modellgenerierung.",
            },
            "model": {
                "type": "string",
                "description": "Modell-Identifier (z.B. 'stability-ai/sdxl', 'meta/llama-2-70b-chat').",
                "default": "stability-ai/sdxl",
            },
            "version": {
                "type": "string",
                "description": "Modell-Version (optional, verwendet neueste Version wenn nicht angegeben).",
            },
            "parameters": {
                "type": "object",
                "description": "Modell-spezifische Parameter (z.B. width, height, num_outputs, etc.).",
                "additionalProperties": True,
            },
            "wait": {
                "type": "boolean",
                "default": True,
                "description": "Auf Ergebnis warten (true) oder nur Prediction-ID zurückgeben (false).",
            },
            "timeout": {
                "type": "integer",
                "default": 120,
                "description": "Maximale Wartezeit in Sekunden (nur wenn wait=true).",
            },
            "webhook": {
                "type": "string",
                "description": "Webhook-URL für asynchrone Benachrichtigung (optional).",
            },
            "webhook_events_filter": {
                "type": "array",
                "items": {"type": "string", "enum": ["start", "output", "logs", "completed"]},
                "description": "Webhook-Event-Filter (optional).",
            },
        },
        "required": ["prompt"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "prediction_id": {"type": "string"},
            "model": {"type": "string"},
            "version": {"type": "string"},
            "status": {"type": "string"},
            "output": {"type": ["array", "string", "null"]},
            "urls": {"type": "object"},
            "error": {"type": "string"},
            "message": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = os.getenv("REPLICATE_API_KEY", "")
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def _request(self, method: str, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Führt einen Request an die Replicate API durch."""
        if not self._is_configured():
            return {"error": "Replicate API-Key nicht konfiguriert. Setze REPLICATE_API_KEY in der Umgebung."}

        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                else:
                    return {"error": f"Unsupported method: {method}"}
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"error": "Ungültiger API-Key. Prüfe REPLICATE_API_KEY."}
                if e.response.status_code == 429:
                    return {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                if e.response.status_code == 503:
                    return {"error": "Replicate API ist derzeit nicht verfügbar."}
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def _create_prediction(
        self,
        model: str,
        version: str | None,
        prompt: str,
        parameters: dict[str, Any] | None,
        webhook: str | None,
        webhook_events_filter: list[str] | None,
    ) -> dict[str, Any]:
        """Erstellt eine neue Prediction."""
        data: dict[str, Any] = {
            "version": version if version else model,
            "input": {"prompt": prompt},
        }
        if parameters:
            data["input"].update(parameters)
        if webhook:
            data["webhook"] = webhook
        if webhook_events_filter:
            data["webhook_events_filter"] = webhook_events_filter

        # Für SDXL-Modelle: Standardparameter setzen
        if "sdxl" in model.lower() or "stable-diffusion" in model.lower():
            if "width" not in data["input"]:
                data["input"]["width"] = 768
            if "height" not in data["input"]:
                data["input"]["height"] = 768
            if "num_outputs" not in data["input"]:
                data["input"]["num_outputs"] = 1

        return await self._request("POST", "/predictions", data)

    async def _get_prediction(self, prediction_id: str) -> dict[str, Any]:
        """Ruft den Status einer Prediction ab."""
        return await self._request("GET", f"/predictions/{prediction_id}")

    async def _poll_prediction(self, prediction_id: str, timeout: int) -> dict[str, Any]:
        """Pollt eine Prediction bis zur Fertigstellung."""
        start_time = asyncio.get_event_loop().time()
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                return {"error": f"Zeitüberschreitung ({timeout} Sekunden) bei der Wartezeit für die Prediction."}

            result = await self._get_prediction(prediction_id)
            if "error" in result:
                return result

            status = result.get("status")
            if status == "succeeded":
                return {"success": True, "prediction": result}
            elif status == "failed":
                error_msg = result.get("error", "Unbekannter Fehler")
                return {"error": f"Prediction fehlgeschlagen: {error_msg}"}
            elif status in ["starting", "processing"]:
                await asyncio.sleep(2)
                continue
            else:
                return {"error": f"Unerwarteter Status: {status}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task = str(input_data.get("task", "image")).lower()
        prompt = str(input_data.get("prompt", "")).strip()
        if not prompt:
            return {"success": False, "error": "prompt ist erforderlich."}

        model = str(input_data.get("model", "stability-ai/sdxl")).strip()
        version = str(input_data.get("version", "")).strip() or None
        parameters = input_data.get("parameters")
        if not isinstance(parameters, dict):
            parameters = {}
        wait = bool(input_data.get("wait", True))
        timeout = max(10, int(input_data.get("timeout", 120)))
        webhook = str(input_data.get("webhook", "")).strip() or None
        webhook_events_filter = input_data.get("webhook_events_filter")
        if not isinstance(webhook_events_filter, list):
            webhook_events_filter = None

        # Modell für verschiedene Tasks
        if task == "image":
            if not model or model == "stability-ai/sdxl":
                model = "stability-ai/sdxl"
                if not version:
                    version = "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        elif task == "text":
            if not model or model == "meta/llama-2-70b-chat":
                model = "meta/llama-2-70b-chat"
                if not version:
                    version = "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"
        elif task == "audio":
            if not model:
                model = "suno-ai/bark"
                if not version:
                    version = "b3221de1d8aa8a42539b0df05c1382b5bfce0aa6b7271dd69d4081843e5622f3"
        else:  # custom
            if version:
                model = version
            elif "/" not in model:
                return {"error": "Für custom-Task wird ein vollständiger Modell-Identifier (owner/model) benötigt."}

        # Prompt anpassen
        if task == "image":
            # Bei Bildgenerierung den Prompt als Text übergeben
            pass
        elif task == "text":
            # Bei Textgenerierung: Prompt als Nachricht formatieren
            if "messages" not in parameters:
                parameters["messages"] = [{"role": "user", "content": prompt}]
        elif task == "audio":
            # Bei Audio: Prompt für Sprachgenerierung
            if "text" not in parameters:
                parameters["text"] = prompt

        # Prediction erstellen
        result = await self._create_prediction(
            model=model,
            version=version,
            prompt=prompt,
            parameters=parameters,
            webhook=webhook,
            webhook_events_filter=webhook_events_filter,
        )

        if "error" in result:
            return {"success": False, "error": result["error"]}

        prediction_id = result.get("id", "")
        urls = result.get("urls", {})

        if not wait:
            return {
                "success": True,
                "prediction_id": prediction_id,
                "model": result.get("model", model),
                "version": result.get("version", version),
                "status": result.get("status", "starting"),
                "urls": urls,
                "message": f"Prediction {prediction_id} gestartet. Überwache mit GET /predictions/{prediction_id}.",
            }

        # Auf Ergebnis warten
        poll_result = await self._poll_prediction(prediction_id, timeout)
        if "error" in poll_result:
            return {"success": False, "error": poll_result["error"]}

        prediction = poll_result.get("prediction", {})
        output = prediction.get("output")
        status = prediction.get("status", "unknown")

        return {
            "success": True,
            "prediction_id": prediction_id,
            "model": prediction.get("model", model),
            "version": prediction.get("version", version),
            "status": status,
            "output": output,
            "urls": urls,
            "message": f"Prediction {prediction_id} erfolgreich abgeschlossen.",
        }