# packages/plugins/whatsapp/plugin.py
from __future__ import annotations

import os
import re
from typing import Any

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "whatsapp",
    "name": "WhatsApp",
    "description": "WhatsApp-Nachrichten senden (über Twilio WhatsApp Business API)",
    "category": "📱 Social & Communication",
    "apiKeyRequired": True,
    "intentPattern": r"\b(whatsapp|wa|nachricht|sms|message|send|benachrichtigung)\b",
    "status": "implemented",
    "settingsFields": [],
}


PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


class WhatsAppPlugin:
    name = "whatsapp"
    description = "WhatsApp-Nachrichten senden (über Twilio WhatsApp Business API)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Empfänger-Telefonnummer im internationalen Format (z.B. '+491701234567').",
            },
            "message": {
                "type": "string",
                "description": "Nachrichtentext (max. 1600 Zeichen).",
            },
            "media_url": {
                "type": "string",
                "description": "Optional: URL zu einem Bild, Dokument oder Video.",
            },
            "from": {
                "type": "string",
                "description": "Absender-Telefonnummer (überschreibt die Umgebungsvariable).",
            },
            "communication_channel": {
                "type": "string",
                "enum": ["letter", "email", "both", "whatsapp"],
                "description": "Optionaler fachuebergreifender Ausgabekanal.",
            },
            "validate_only": {
                "type": "boolean",
                "default": False,
                "description": "Nur validieren, nicht senden.",
            },
            "delivery": {
                "type": "object",
                "description": "Kompatible Eingabestruktur fuer Versanddaten.",
            },
            "content": {
                "type": "object",
                "description": "Kompatible Eingabestruktur fuer Nachrichtentexte.",
            },
        },
        "required": [],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message_sid": {"type": "string"},
            "status": {"type": "string"},
            "to": {"type": "string"},
            "validation": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM", "")
        self.base_url = "https://api.twilio.com/2010-04-01"

    def _is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    def _format_phone(self, number: str) -> str:
        """Formatierte Telefonnummer für Twilio."""
        number = number.strip()
        if not number.startswith("+"):
            number = f"+{number}"
        return number

    def _normalize_request(self, input_data: dict[str, Any]) -> dict[str, Any]:
        delivery = input_data.get("delivery") if isinstance(input_data.get("delivery"), dict) else {}
        content = input_data.get("content") if isinstance(input_data.get("content"), dict) else {}

        to = str(input_data.get("to", "")).strip()
        if not to:
            to = str(delivery.get("recipient", "")).strip()

        message = str(input_data.get("message", "")).strip()
        if not message:
            message = str(content.get("message", "")).strip()
        if not message:
            message = str(content.get("email_text", "")).strip()
        if not message:
            message = str(content.get("letter_text", "")).strip()

        media_url = str(input_data.get("media_url", "")).strip() or None
        from_number = str(input_data.get("from", "")).strip() or None

        channel = str(input_data.get("communication_channel", "")).strip().lower()
        if not channel:
            channel = str(delivery.get("channel", "")).strip().lower() or "whatsapp"

        return {
            "to": to,
            "message": message,
            "media_url": media_url,
            "from": from_number,
            "communication_channel": channel,
            "validate_only": bool(input_data.get("validate_only", False)),
        }

    def _validate_request(self, data: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        missing_information: list[str] = []

        channel = str(data.get("communication_channel", "whatsapp")).strip().lower()
        if channel not in {"whatsapp", "both", "letter", "email"}:
            warnings.append(f"Unbekannter communication_channel '{channel}', fallback auf 'whatsapp'.")
            channel = "whatsapp"

        if channel in {"letter", "email"}:
            warnings.append(f"communication_channel={channel}: WhatsApp-Versand wird uebersprungen.")

        to = str(data.get("to", "")).strip()
        if channel in {"whatsapp", "both"}:
            if not to:
                errors.append("Empfaenger (to) ist erforderlich.")
                missing_information.append("to")
            elif not PHONE_RE.match(to):
                errors.append("Empfaenger-Telefonnummer ist ungueltig.")

            message = str(data.get("message", "")).strip()
            if not message:
                errors.append("Nachricht (message) ist erforderlich.")
                missing_information.append("message")

        media_raw = data.get("media_url")
        media_url = str(media_raw).strip() if media_raw is not None else ""
        if media_url and not (media_url.startswith("http://") or media_url.startswith("https://")):
            errors.append("media_url muss eine gueltige URL sein.")

        status = "ready" if not errors else "needs_review"
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "missing_information": missing_information,
        }

    async def _send_message(
        self,
        to: str,
        message: str,
        media_url: str | None,
        from_number: str | None,
    ) -> dict[str, Any]:
        """Sendet eine WhatsApp-Nachricht über die Twilio API."""
        if not self._is_configured():
            return {"error": "Twilio nicht konfiguriert. Setze TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN und TWILIO_WHATSAPP_FROM in der Umgebung."}

        sender = from_number or self.from_number
        sender = self._format_phone(sender)
        recipient = self._format_phone(to)

        url = f"{self.base_url}/Accounts/{self.account_sid}/Messages.json"
        auth = (self.account_sid, self.auth_token)

        payload = {
            "To": f"whatsapp:{recipient}",
            "From": f"whatsapp:{sender}",
            "Body": message[:1600],  # WhatsApp-Limit
        }

        if media_url:
            payload["MediaUrl"] = media_url

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, data=payload, auth=auth)
                response.raise_for_status()
                data = response.json()
                return {
                    "message_sid": data.get("sid"),
                    "status": data.get("status"),
                    "to": data.get("to", "").replace("whatsapp:", ""),
                }
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"error": "Ungültige Twilio-Zugangsdaten. Prüfe TWILIO_ACCOUNT_SID und TWILIO_AUTH_TOKEN."}
                if e.response.status_code == 404:
                    return {"error": "Absender-Nummer nicht gefunden. Prüfe TWILIO_WHATSAPP_FROM."}
                if e.response.status_code == 429:
                    return {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                return {"error": f"HTTP-Fehler: {e.response.status_code} - {e.response.text}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_request(input_data)
        validation = self._validate_request(normalized)

        channel = str(normalized.get("communication_channel", "whatsapp")).strip().lower()
        if channel not in {"whatsapp", "both", "letter", "email"}:
            channel = "whatsapp"
        if channel in {"letter", "email"}:
            return {
                "success": True,
                "status": "skipped",
                "reason": "unsupported_channel",
                "message": f"communication_channel={channel}: WhatsApp-Versand uebersprungen.",
                "validation": validation,
            }

        if validation["errors"]:
            return {
                "success": False,
                "error": validation["errors"][0],
                "validation": validation,
            }

        if normalized["validate_only"]:
            return {
                "success": True,
                "status": "ready",
                "message": "WhatsApp-Payload ist valide (validate_only=true).",
                "validation": validation,
            }

        result = await self._send_message(
            normalized["to"],
            normalized["message"],
            normalized["media_url"],
            normalized["from"],
        )

        if "error" in result:
            return {"success": False, "error": result["error"], "validation": validation}

        return {
            "success": True,
            "message_sid": result.get("message_sid"),
            "status": result.get("status"),
            "to": result.get("to", normalized["to"]),
            "message": f"WhatsApp-Nachricht an {normalized['to']} gesendet. Status: {result.get('status')}",
            "validation": validation,
        }


