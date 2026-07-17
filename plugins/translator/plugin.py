# packages/plugins/translator/plugin.py
from __future__ import annotations

import os
from typing import Any

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "translator",
    "name": "Translator",
    "description": "Übersetzt Texte in verschiedene Sprachen (DeepL, Google, LibreTranslate)",
    "category": "🧠 NLP & Content",
    "apiKeyRequired": True,  # Für DeepL/Google; LibreTranslate ist kostenlos
    "intentPattern": r"\b(übersetze|translate|translation|Übersetzung)\b",
    "status": "implemented",
    "settingsFields": [
        {
            "key": "service",
            "label": "Standard-Dienst",
            "type": "select",
            "default": "libretranslate",
            "group": "Verbindung",
            "options": [
                {"value": "libretranslate", "label": "LibreTranslate"},
                {"value": "deepl", "label": "DeepL"},
                {"value": "google", "label": "Google"},
            ],
        },
        {
            "key": "target_lang",
            "label": "Standard-Zielsprache",
            "type": "string",
            "default": "en",
            "group": "Modell",
        },
        {
            "key": "source_lang",
            "label": "Standard-Quellsprache",
            "type": "string",
            "default": "auto",
            "group": "Modell",
        },
        {
            "key": "preserve_formatting",
            "label": "Formatierung erhalten",
            "type": "boolean",
            "default": True,
            "group": "Laufzeit",
        },
    ],
}


class TranslatorPlugin:
    name = "translator"
    description = "Übersetzt Texte in verschiedene Sprachen (DeepL, Google, LibreTranslate)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der zu übersetzende Text.",
            },
            "target_lang": {
                "type": "string",
                "description": "Zielsprache (z.B. 'en', 'de', 'fr', 'es', 'it', 'ja', 'zh'). Für DeepL auch 'EN-US', 'EN-GB' etc.",
            },
            "source_lang": {
                "type": "string",
                "description": "Quellsprache (optional, 'auto' für automatische Erkennung).",
                "default": "auto",
            },
            "service": {
                "type": "string",
                "enum": ["libretranslate", "deepl", "google"],
                "default": "libretranslate",
                "description": "Übersetzungsdienst: libretranslate (kostenlos), deepl (API-Key), google (API-Key).",
            },
            "api_key": {
                "type": "string",
                "description": "API-Key für den gewählten Dienst (DeepL oder Google). Für LibreTranslate nicht benötigt.",
            },
            "preserve_formatting": {
                "type": "boolean",
                "default": True,
                "description": "HTML-Formatierung beibehalten (für DeepL).",
            },
            "communication_channel": {
                "type": "string",
                "enum": ["letter", "email", "both", "whatsapp", "translator"],
                "description": "Optionaler fachuebergreifender Kontextkanal.",
            },
            "validate_only": {
                "type": "boolean",
                "default": False,
                "description": "Nur validieren, keine Uebersetzung ausfuehren.",
            },
            "content": {
                "type": "object",
                "description": "Kompatible Eingabestruktur fuer fachuebergreifende Textfelder.",
            },
        },
        "required": [],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "translated_text": {"type": "string"},
            "detected_source_lang": {"type": "string"},
            "service_used": {"type": "string"},
            "message": {"type": "string"},
            "validation": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.deepl_api_key = os.getenv("DEEPL_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")

    def _is_configured(self, service: str) -> bool:
        if service == "deepl":
            return bool(self.deepl_api_key)
        if service == "google":
            return bool(self.google_api_key)
        return True  # LibreTranslate immer verfügbar

    def _get_service_name(self, service: str) -> str:
        return service

    def _normalize_request(self, input_data: dict[str, Any]) -> dict[str, Any]:
        content = input_data.get("content") if isinstance(input_data.get("content"), dict) else {}

        text = str(input_data.get("text", "")).strip()
        if not text:
            text = str(content.get("message", "")).strip()
        if not text:
            text = str(content.get("email_text", "")).strip()
        if not text:
            text = str(content.get("letter_text", "")).strip()

        target_lang = str(input_data.get("target_lang", "")).strip()
        if not target_lang:
            target_lang = str(content.get("target_lang", "")).strip()

        return {
            "text": text,
            "target_lang": target_lang,
            "source_lang": str(input_data.get("source_lang", "auto")).strip() or "auto",
            "service": str(input_data.get("service", "libretranslate")).strip().lower() or "libretranslate",
            "api_key": str(input_data.get("api_key", "")).strip() or None,
            "preserve_formatting": bool(input_data.get("preserve_formatting", True)),
            "communication_channel": str(input_data.get("communication_channel", "translator")).strip().lower()
            or "translator",
            "validate_only": bool(input_data.get("validate_only", False)),
        }

    def _validate_request(self, normalized: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        missing_information: list[str] = []

        if normalized["service"] not in {"libretranslate", "deepl", "google"}:
            errors.append("Ungueltiger Uebersetzungsdienst. Erlaubt: libretranslate, deepl, google")
            missing_information.append("service")

        if not normalized["text"]:
            errors.append("text ist erforderlich.")
            missing_information.append("text")

        if not normalized["target_lang"]:
            errors.append("target_lang ist erforderlich.")
            missing_information.append("target_lang")

        channel = normalized["communication_channel"]
        if channel not in {"translator", "letter", "email", "both", "whatsapp"}:
            warnings.append(f"Unbekannter communication_channel '{channel}', fallback auf 'translator'.")
            channel = "translator"

        status = "ready" if not errors else "needs_review"
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "missing_information": missing_information,
        }

    async def _translate_libretranslate(
        self, text: str, target_lang: str, source_lang: str = "auto"
    ) -> dict[str, Any]:
        """Übersetzung mit LibreTranslate (kostenlos, öffentliche API)."""
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }
        endpoints = [
            "https://libretranslate.com/translate",
            "https://translate.argosopentech.com/translate",
        ]

        async with httpx.AsyncClient(timeout=15.0) as client:
            last_error = "Unbekannter Fehler"
            for url in endpoints:
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return {
                        "translated_text": data.get("translatedText", ""),
                        "detected_source_lang": data.get("detectedLanguage", {}).get("language", source_lang),
                        "service": "libretranslate",
                        "success": True,
                    }
                except httpx.HTTPStatusError as e_json:
                    try:
                        response = await client.post(url, data=payload)
                        response.raise_for_status()
                        data = response.json()
                        return {
                            "translated_text": data.get("translatedText", ""),
                            "detected_source_lang": data.get("detectedLanguage", {}).get("language", source_lang),
                            "service": "libretranslate",
                            "success": True,
                        }
                    except httpx.HTTPStatusError as e_form:
                        last_error = f"HTTP-Fehler: {e_form.response.status_code}"
                    except Exception as e_form_exc:
                        last_error = f"Fehler: {str(e_form_exc)}"
                    else:
                        break
                    _ = e_json
                except Exception as e:
                    last_error = f"Fehler: {str(e)}"

            return {"error": last_error}

    async def _translate_deepl(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
        preserve_formatting: bool = True,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Übersetzung mit DeepL API (benötigt API-Key)."""
        key = api_key or self.deepl_api_key
        if not key:
            return {"error": "DeepL API-Key fehlt. Setze DEEPL_API_KEY oder übergebe api_key."}

        url = "https://api.deepl.com/v2/translate"
        if source_lang == "auto":
            params = {
                "auth_key": key,
                "text": text,
                "target_lang": target_lang,
                "preserve_formatting": "1" if preserve_formatting else "0",
            }
        else:
            params = {
                "auth_key": key,
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "preserve_formatting": "1" if preserve_formatting else "0",
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, params=params)
                response.raise_for_status()
                data = response.json()
                translation = data.get("translations", [{}])[0]
                return {
                    "translated_text": translation.get("text", ""),
                    "detected_source_lang": translation.get("detected_source_language", source_lang),
                    "service": "deepl",
                    "success": True,
                }
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    return {"error": "Ungültiger DeepL API-Key."}
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def _translate_google(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Übersetzung mit Google Translate API (benötigt API-Key und Projekt)."""
        key = api_key or self.google_api_key
        if not key:
            return {"error": "Google Translate API-Key fehlt. Setze GOOGLE_TRANSLATE_API_KEY oder übergebe api_key."}

        # Google Translate API v2: POST https://translation.googleapis.com/language/translate/v2
        url = "https://translation.googleapis.com/language/translate/v2"
        params = {
            "key": key,
            "q": text,
            "target": target_lang,
            "format": "text",
        }
        if source_lang != "auto":
            params["source"] = source_lang

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, params=params)
                response.raise_for_status()
                data = response.json()
                translation = data.get("data", {}).get("translations", [{}])[0]
                return {
                    "translated_text": translation.get("translatedText", ""),
                    "detected_source_lang": translation.get("detectedSourceLanguage", source_lang),
                    "service": "google",
                    "success": True,
                }
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    return {"error": "Ungültiger Google Translate API-Key."}
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_request(input_data)
        validation = self._validate_request(normalized)

        if validation["errors"]:
            return {"success": False, "error": validation["errors"][0], "validation": validation}

        if normalized["validate_only"]:
            return {
                "success": True,
                "message": "Translator-Payload ist valide (validate_only=true).",
                "validation": validation,
            }

        # Service auswählen
        if normalized["service"] == "deepl":
            result = await self._translate_deepl(
                normalized["text"],
                normalized["target_lang"],
                normalized["source_lang"],
                normalized["preserve_formatting"],
                normalized["api_key"],
            )
        elif normalized["service"] == "google":
            result = await self._translate_google(
                normalized["text"],
                normalized["target_lang"],
                normalized["source_lang"],
                normalized["api_key"],
            )
        else:  # libretranslate
            result = await self._translate_libretranslate(
                normalized["text"],
                normalized["target_lang"],
                normalized["source_lang"],
            )

        if "error" in result:
            return {"success": False, "error": result["error"], "validation": validation}

        return {
            "success": True,
            "translated_text": result.get("translated_text", ""),
            "detected_source_lang": result.get("detected_source_lang", normalized["source_lang"]),
            "service_used": result.get("service", normalized["service"]),
            "message": (
                f"Text erfolgreich von {normalized['source_lang']} nach {normalized['target_lang']} "
                f"uebersetzt (via {result.get('service', normalized['service'])})."
            ),
            "validation": validation,
        }