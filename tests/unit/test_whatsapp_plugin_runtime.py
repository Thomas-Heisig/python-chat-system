from __future__ import annotations

import asyncio
from typing import Any

from plugins.whatsapp.plugin import WhatsAppPlugin


def _run(plugin: WhatsAppPlugin, payload: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(plugin.execute(payload))


def test_whatsapp_plugin_skips_for_letter_channel() -> None:
    plugin = WhatsAppPlugin()

    result = _run(
        plugin,
        {
            "communication_channel": "letter",
            "to": "+491701234567",
            "message": "Test",
        },
    )

    assert result["success"] is True
    assert result["status"] == "skipped"
    assert result["reason"] == "unsupported_channel"
    assert "uebersprungen" in result["message"]


def test_whatsapp_plugin_accepts_delivery_content_envelope_validate_only() -> None:
    plugin = WhatsAppPlugin()

    result = _run(
        plugin,
        {
            "delivery": {"channel": "both", "recipient": "+491701234567"},
            "content": {"email_text": "Anbei der Status zum Auftrag."},
            "validate_only": True,
        },
    )

    assert result["success"] is True
    assert result["status"] == "ready"
    assert result["validation"]["errors"] == []


def test_whatsapp_plugin_rejects_invalid_phone() -> None:
    plugin = WhatsAppPlugin()

    result = _run(
        plugin,
        {
            "to": "abc",
            "message": "Hallo",
            "validate_only": True,
        },
    )

    assert result["success"] is False
    assert "Telefonnummer" in result["error"]


def test_whatsapp_plugin_uses_normalized_send_path() -> None:
    plugin = WhatsAppPlugin()
    captured: dict[str, Any] = {}

    async def _fake_send_message(
        to: str,
        message: str,
        media_url: str | None,
        from_number: str | None,
    ) -> dict[str, Any]:
        captured["to"] = to
        captured["message"] = message
        captured["media_url"] = media_url
        captured["from"] = from_number
        return {"message_sid": "SM123", "status": "queued", "to": to}

    plugin._send_message = _fake_send_message  # type: ignore[method-assign]

    result = _run(
        plugin,
        {
            "to": "+491701234567",
            "message": "Statusupdate",
            "media_url": "https://example.org/file.pdf",
        },
    )

    assert result["success"] is True
    assert captured["to"] == "+491701234567"
    assert captured["message"] == "Statusupdate"
    assert captured["media_url"] == "https://example.org/file.pdf"
