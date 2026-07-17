from __future__ import annotations

import asyncio
from typing import Any

from plugins.translator.plugin import TranslatorPlugin


def _run(plugin: TranslatorPlugin, payload: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(plugin.execute(payload))


def test_translator_validate_only_with_content_envelope() -> None:
    plugin = TranslatorPlugin()

    result = _run(
        plugin,
        {
            "content": {
                "email_text": "Guten Tag, hier ist Ihr Angebot.",
                "target_lang": "en",
            },
            "validate_only": True,
        },
    )

    assert result["success"] is True
    assert "validation" in result
    assert result["validation"]["errors"] == []


def test_translator_rejects_missing_target_lang() -> None:
    plugin = TranslatorPlugin()

    result = _run(
        plugin,
        {
            "text": "Hallo",
            "validate_only": True,
        },
    )

    assert result["success"] is False
    assert "target_lang" in result["error"]


def test_translator_rejects_invalid_service() -> None:
    plugin = TranslatorPlugin()

    result = _run(
        plugin,
        {
            "text": "Hallo",
            "target_lang": "en",
            "service": "foobar",
            "validate_only": True,
        },
    )

    assert result["success"] is False
    assert "Uebersetzungsdienst" in result["error"]


def test_translator_uses_provider_path_with_normalized_values() -> None:
    plugin = TranslatorPlugin()
    captured: dict[str, Any] = {}

    async def _fake_translate_libretranslate(
        text: str,
        target_lang: str,
        source_lang: str = "auto",
    ) -> dict[str, Any]:
        captured["text"] = text
        captured["target_lang"] = target_lang
        captured["source_lang"] = source_lang
        return {
            "translated_text": "Hello",
            "detected_source_lang": "de",
            "service": "libretranslate",
            "success": True,
        }

    plugin._translate_libretranslate = _fake_translate_libretranslate  # type: ignore[method-assign]

    result = _run(
        plugin,
        {
            "text": "Hallo",
            "target_lang": "en",
            "service": "libretranslate",
        },
    )

    assert result["success"] is True
    assert result["translated_text"] == "Hello"
    assert captured["text"] == "Hallo"
    assert captured["target_lang"] == "en"
