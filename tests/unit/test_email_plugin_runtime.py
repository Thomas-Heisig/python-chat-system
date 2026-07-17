from __future__ import annotations

import asyncio
from typing import Any

from plugins.email.plugin import EmailPlugin


def _run(plugin: EmailPlugin, payload: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(plugin.execute(payload))


def test_email_plugin_skips_on_letter_channel() -> None:
    plugin = EmailPlugin()

    result = _run(
        plugin,
        {
            "communication_channel": "letter",
            "subject": "Test",
            "body": "Nur Briefkanal.",
        },
    )

    assert result["success"] is True
    assert "uebersprungen" in result["message"]
    assert result["validation"]["status"] == "ready"


def test_email_plugin_accepts_business_letter_envelope_validate_only() -> None:
    plugin = EmailPlugin()

    result = _run(
        plugin,
        {
            "communication_channel": "both",
            "email": {
                "to": ["kunde@example.de"],
                "cc": ["team@example.de"],
                "bcc": [],
                "reply_to": "reply@example.de",
                "subject": "Angebot 2026-1000",
                "body_text": "Guten Tag,\n\nAnbei das Angebot.",
                "body_html": "<p>Guten Tag,</p><p>Anbei das Angebot.</p>",
            },
            "delivery": {
                "subject": "Angebot 2026-1000",
                "recipient": "kunde@example.de",
                "reply_to": "reply@example.de",
                "channel": "both",
            },
            "content": {
                "email_text": "Fallback body",
                "email_html": "<p>Fallback html</p>",
            },
            "validate_only": True,
        },
    )

    assert result["success"] is True
    assert result["validation"]["errors"] == []
    assert result["validation"]["status"] == "ready"


def test_email_plugin_rejects_invalid_recipient_mail() -> None:
    plugin = EmailPlugin()

    result = _run(
        plugin,
        {
            "to": ["ungueltig"],
            "subject": "Test",
            "body": "Text",
            "validate_only": True,
        },
    )

    assert result["success"] is False
    assert "Ungueltige E-Mail-Adresse" in result["error"]


def test_email_plugin_uses_normalized_payload_for_smtp_send() -> None:
    plugin = EmailPlugin()
    captured: dict[str, Any] = {}

    async def _fake_send_via_smtp(
        to: list[str],
        subject: str,
        body: str,
        html_body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        captured["to"] = to
        captured["subject"] = subject
        captured["body"] = body
        captured["reply_to"] = reply_to
        return {"success": True, "message": "ok"}

    plugin._send_via_smtp = _fake_send_via_smtp  # type: ignore[method-assign]

    result = _run(
        plugin,
        {
            "provider": "smtp",
            "to": "kunde@example.de, team@example.de",
            "subject": "Betreff",
            "body": "Nachricht",
            "reply_to": "reply@example.de",
        },
    )

    assert result["success"] is True
    assert captured["to"] == ["kunde@example.de", "team@example.de"]
    assert captured["subject"] == "Betreff"
    assert captured["reply_to"] == "reply@example.de"
