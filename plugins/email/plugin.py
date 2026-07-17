# packages/plugins/email/plugin.py
from __future__ import annotations

import asyncio
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Any

import httpx


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


PLUGIN_META: dict[str, Any] = {
    "id": "email",
    "name": "E-Mail",
    "description": "Senden von E-Mails über SMTP oder SendGrid",
    "category": "📱 Social & Communication",
    "apiKeyRequired": True,
    "intentPattern": r"\b(email|mail|schreiben|anfrage|versenden|nachricht)\b",
    "status": "implemented",
    "settingsFields": [],
}


class EmailPlugin:
    name = "email"
    description = "Senden von E-Mails über SMTP oder SendGrid"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "to": {
                "type": ["string", "array"],
                "description": "Empfänger-E-Mail-Adresse oder Liste von Adressen.",
            },
            "subject": {
                "type": "string",
                "description": "Betreff der E-Mail.",
            },
            "body": {
                "type": "string",
                "description": "Text-Inhalt der E-Mail.",
            },
            "html_body": {
                "type": "string",
                "description": "Optional: HTML-Inhalt der E-Mail.",
            },
            "cc": {
                "type": ["string", "array"],
                "description": "Optional: CC-Empfänger (kommagetrennt oder Liste).",
            },
            "bcc": {
                "type": ["string", "array"],
                "description": "Optional: BCC-Empfänger (kommagetrennt oder Liste).",
            },
            "reply_to": {
                "type": "string",
                "description": "Optionale Reply-To-Adresse.",
            },
            "attachments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "content": {"type": "string", "description": "Base64-kodierter Inhalt"},
                        "mime_type": {"type": "string", "default": "application/octet-stream"},
                    },
                },
                "description": "Optional: Anhänge (Base64-kodiert).",
            },
            "provider": {
                "type": "string",
                "enum": ["smtp", "sendgrid"],
                "default": "smtp",
                "description": "E-Mail-Provider: smtp oder sendgrid.",
            },
            "communication_channel": {
                "type": "string",
                "enum": ["letter", "email", "both"],
                "description": "Optionaler Kanal aus fachuebergreifenden Payloads.",
            },
            "validate_only": {
                "type": "boolean",
                "default": False,
                "description": "Nur validieren, nicht senden.",
            },
            "email": {
                "type": "object",
                "description": "Kompatibilitaet zu business_letter.email-Struktur.",
            },
            "delivery": {
                "type": "object",
                "description": "Kompatibilitaet zu business_letter.delivery-Struktur.",
            },
            "content": {
                "type": "object",
                "description": "Kompatibilitaet zu business_letter.content-Struktur.",
            },
        },
        "required": [],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "validation": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        # SMTP-Konfiguration
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "")

        # SendGrid-Konfiguration
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")

        self.max_retries = int(os.getenv("EMAIL_MAX_RETRIES", 3))
        self.retry_delay = int(os.getenv("EMAIL_RETRY_DELAY", 2))

    def _is_smtp_configured(self) -> bool:
        return all([self.smtp_host, self.smtp_user, self.smtp_pass, self.sender_email])

    def _is_sendgrid_configured(self) -> bool:
        return bool(self.sendgrid_api_key)

    def _coerce_email_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            parsed = [str(item).strip() for item in value if str(item).strip()]
            return parsed
        if isinstance(value, str):
            parsed = [item.strip() for item in value.split(",") if item.strip()]
            return parsed
        return []

    def _normalize_request(self, input_data: dict[str, Any]) -> dict[str, Any]:
        email_payload = input_data.get("email") if isinstance(input_data.get("email"), dict) else {}
        delivery_payload = input_data.get("delivery") if isinstance(input_data.get("delivery"), dict) else {}
        content_payload = input_data.get("content") if isinstance(input_data.get("content"), dict) else {}

        to_values = self._coerce_email_list(input_data.get("to"))
        if not to_values:
            to_values = self._coerce_email_list(email_payload.get("to"))
        if not to_values:
            recipient = str(delivery_payload.get("recipient", "")).strip()
            if recipient:
                to_values = [recipient]

        cc_values = self._coerce_email_list(input_data.get("cc"))
        if not cc_values:
            cc_values = self._coerce_email_list(email_payload.get("cc"))

        bcc_values = self._coerce_email_list(input_data.get("bcc"))
        if not bcc_values:
            bcc_values = self._coerce_email_list(email_payload.get("bcc"))

        subject = str(input_data.get("subject", "")).strip()
        if not subject:
            subject = str(email_payload.get("subject", "")).strip()
        if not subject:
            subject = str(delivery_payload.get("subject", "")).strip()

        body = str(input_data.get("body", "")).strip()
        if not body:
            body = str(email_payload.get("body_text", "")).strip()
        if not body:
            body = str(content_payload.get("email_text", "")).strip()

        html_body = str(input_data.get("html_body", "")).strip()
        if not html_body:
            html_body = str(email_payload.get("body_html", "")).strip()
        if not html_body:
            html_body = str(content_payload.get("email_html", "")).strip()

        reply_to = str(input_data.get("reply_to", "")).strip()
        if not reply_to:
            reply_to = str(email_payload.get("reply_to", "")).strip()
        if not reply_to:
            reply_to = str(delivery_payload.get("reply_to", "")).strip()

        attachments = input_data.get("attachments")
        if not isinstance(attachments, list):
            attachments = []

        provider = str(input_data.get("provider", "smtp")).strip().lower() or "smtp"
        channel = str(input_data.get("communication_channel", "")).strip().lower()
        if not channel:
            channel = str(delivery_payload.get("channel", "")).strip().lower() or "email"

        return {
            "to": to_values,
            "subject": subject,
            "body": body,
            "html_body": html_body or None,
            "cc": cc_values,
            "bcc": bcc_values,
            "reply_to": reply_to or None,
            "attachments": attachments,
            "provider": provider,
            "communication_channel": channel,
            "validate_only": bool(input_data.get("validate_only", False)),
        }

    def _validate_request(self, data: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        missing_information: list[str] = []

        channel = str(data.get("communication_channel", "email")).strip().lower()
        if channel not in {"letter", "email", "both"}:
            warnings.append(f"Unbekannter communication_channel '{channel}', fallback auf 'email'.")
            channel = "email"

        if channel == "letter":
            warnings.append("communication_channel=letter: Versand wird vom email-Plugin bewusst uebersprungen.")

        to_values = data.get("to") if isinstance(data.get("to"), list) else []
        cc_values = data.get("cc") if isinstance(data.get("cc"), list) else []
        bcc_values = data.get("bcc") if isinstance(data.get("bcc"), list) else []
        reply_to_value = data.get("reply_to")
        reply_to = str(reply_to_value).strip() if isinstance(reply_to_value, str) else ""
        subject = str(data.get("subject", "")).strip()
        body = str(data.get("body", "")).strip()
        html_body = str(data.get("html_body", "")).strip()

        if channel in {"email", "both"}:
            if not to_values:
                errors.append("Empfaenger (to) ist erforderlich.")
                missing_information.append("to")

            if not subject:
                errors.append("Betreff (subject) ist erforderlich.")
                missing_information.append("subject")

            if not body and not html_body:
                errors.append("Inhalt ist erforderlich (body oder html_body).")
                missing_information.append("body/html_body")

        for label, values in (("to", to_values), ("cc", cc_values), ("bcc", bcc_values)):
            for item in values:
                if not EMAIL_RE.match(str(item)):
                    errors.append(f"Ungueltige E-Mail-Adresse in {label}: {item}")

        if reply_to and not EMAIL_RE.match(reply_to):
            errors.append(f"Ungueltige Reply-To-Adresse: {reply_to}")

        attachments = data.get("attachments") if isinstance(data.get("attachments"), list) else []
        for index, attachment in enumerate(attachments):
            if not isinstance(attachment, dict):
                warnings.append(f"Attachment an Position {index} ist kein Objekt und wird ignoriert.")
                continue
            filename = str(attachment.get("filename", "")).strip()
            content = str(attachment.get("content", "")).strip()
            if not filename:
                warnings.append(f"Attachment an Position {index} ohne filename wird ignoriert.")
            if not content:
                warnings.append(f"Attachment '{filename or index}' ohne content wird ignoriert.")

        status = "ready" if not errors else "needs_review"
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "missing_information": missing_information,
        }

    async def _send_via_smtp(
        self,
        to: list[str],
        subject: str,
        body: str,
        html_body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Sendet E-Mail über SMTP mit Retry-Logik."""
        if not self._is_smtp_configured():
            return {"success": False, "error": "SMTP nicht konfiguriert. Prüfe SMTP_HOST, SMTP_USER, SMTP_PASS, SENDER_EMAIL."}

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)
        if reply_to:
            msg["Reply-To"] = reply_to

        part1 = MIMEText(body, "plain")
        msg.attach(part1)
        if html_body:
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)

        # Anhänge hinzufügen
        if attachments:
            for attachment in attachments:
                import base64
                part = MIMEBase("application", "octet-stream")
                try:
                    content = base64.b64decode(attachment.get("content", ""))
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{attachment.get("filename", "attachment")}"',
                    )
                    msg.attach(part)
                except Exception:
                    continue

        recipients = list(to)
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)

        retries = 0
        last_error = None

        while retries < self.max_retries:
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg, to_addrs=recipients)
                    return {
                        "success": True,
                        "message": f"E-Mail erfolgreich an {', '.join(to)} gesendet.",
                    }
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries < self.max_retries:
                    await asyncio.sleep(self.retry_delay ** retries)

        return {"success": False, "error": f"E-Mail konnte nicht gesendet werden: {last_error}"}

    async def _send_via_sendgrid(
        self,
        to: list[str],
        subject: str,
        body: str,
        html_body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Sendet E-Mail über SendGrid API."""
        if not self._is_sendgrid_configured():
            return {"success": False, "error": "SendGrid API-Key nicht konfiguriert. Prüfe SENDGRID_API_KEY."}

        if not self.sender_email:
            return {"success": False, "error": "SENDER_EMAIL ist nicht konfiguriert."}

        # SendGrid Payload erstellen
        payload: dict[str, Any] = {
            "personalizations": [
                {
                    "to": [{"email": addr} for addr in to],
                }
            ],
            "from": {"email": self.sender_email},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": body},
            ],
        }

        if cc:
            payload["personalizations"][0]["cc"] = [{"email": addr} for addr in cc]
        if bcc:
            payload["personalizations"][0]["bcc"] = [{"email": addr} for addr in bcc]
        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        if html_body:
            payload["content"].append({"type": "text/html", "value": html_body})

        if attachments:
            # SendGrid unterstützt Anhänge über den 'attachments' Key
            payload["attachments"] = []
            for attachment in attachments:
                import base64
                payload["attachments"].append({
                    "content": attachment.get("content", ""),
                    "filename": attachment.get("filename", "attachment"),
                    "type": attachment.get("mime_type", "application/octet-stream"),
                    "disposition": "attachment",
                })

        retries = 0
        last_error = None

        while retries < self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.sendgrid.com/v3/mail/send",
                        headers={
                            "Authorization": f"Bearer {self.sendgrid_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    if response.status_code == 202:
                        return {
                            "success": True,
                            "message": f"E-Mail erfolgreich an {', '.join(to)} gesendet (via SendGrid).",
                        }
                    else:
                        last_error = f"SendGrid-Fehler: {response.status_code} - {response.text}"
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries < self.max_retries:
                    await asyncio.sleep(self.retry_delay ** retries)

        return {"success": False, "error": f"E-Mail konnte nicht gesendet werden: {last_error}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_request(input_data)
        validation = self._validate_request(normalized)

        if normalized["communication_channel"] == "letter":
            return {
                "success": True,
                "message": "communication_channel=letter: E-Mail-Versand uebersprungen.",
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
                "message": "E-Mail-Payload ist valide (validate_only=true).",
                "validation": validation,
            }

        provider = normalized["provider"]
        if provider == "sendgrid":
            result = await self._send_via_sendgrid(
                normalized["to"],
                normalized["subject"],
                normalized["body"],
                normalized["html_body"],
                normalized["cc"],
                normalized["bcc"],
                normalized["reply_to"],
                normalized["attachments"],
            )
        else:
            result = await self._send_via_smtp(
                normalized["to"],
                normalized["subject"],
                normalized["body"],
                normalized["html_body"],
                normalized["cc"],
                normalized["bcc"],
                normalized["reply_to"],
                normalized["attachments"],
            )

        result["validation"] = validation
        return result


