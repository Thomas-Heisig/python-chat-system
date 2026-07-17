from __future__ import annotations

import asyncio
from typing import Any

from plugins.business_letter.plugin import BusinessLetterPlugin


def _execute(payload: dict[str, Any]) -> dict[str, Any]:
    plugin = BusinessLetterPlugin()
    return asyncio.run(plugin.execute(payload))


def _base_payload() -> dict[str, Any]:
    return {
        "letter_type": "angebot",
        "subject": "Angebot fuer Fensterbank",
        "customer_company": "Kunde GmbH",
        "customer_first_name": "Anna",
        "customer_last_name": "Beispiel",
        "customer_salutation": "Frau",
        "customer_street": "Hauptweg 12",
        "customer_zip": "10115",
        "customer_city": "Berlin",
        "customer_country": "Deutschland",
        "recipient_email": "kunde@example.de",
        "document_number": "DOC-2026-9001",
        "offer_valid_until": "13.08.2026",
        "due_date": "31.07.2026",
        "plugin_settings": {
            "company_name": "Steinbau Real GmbH",
            "company_street": "Industriestrasse 99",
            "company_city": "Hannover",
            "company_zip": "30159",
            "company_manager": "Maria Real",
            "company_vat_id": "DE998877665",
        },
    }


def test_runtime_complete_email_delivery_ready() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "email"

    result = _execute(payload)

    assert "error" not in result
    assert result["validation"]["errors"] == []
    assert result["validation"]["status"] == "ready"
    assert result["email"]["to"] == ["kunde@example.de"]


def test_runtime_incomplete_letter_draft_has_address_errors() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "letter"
    payload["customer_street"] = ""
    payload["customer_zip"] = ""
    payload["customer_city"] = ""

    result = _execute(payload)

    assert "error" not in result
    assert any("Vollständige Empfängeradresse fehlt" in item for item in result["validation"]["errors"])
    assert result["document"]["status"] == "needs_review"


def test_runtime_missing_required_attachment_raises_validation_error() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "email"
    payload["attachments"] = [
        {
            "name": "Angebot",
            "file_name": "angebot.pdf",
            "required": True,
            "included": False,
        }
    ]

    result = _execute(payload)

    assert "error" not in result
    assert any("Erforderliche Anlage fehlt" in item for item in result["validation"]["errors"])


def test_runtime_placeholder_company_data_blocks_ready_for_sending() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "email"
    payload["ready_for_sending"] = True
    payload.pop("plugin_settings", None)

    result = _execute(payload)

    assert "error" not in result
    assert any("Platzhalterdaten blockieren den Versandstatus ready" in item for item in result["validation"]["errors"])


def test_runtime_combined_output_both_contains_letter_and_email() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "both"
    payload["email_subject"] = "Angebot DOC-2026-9001"

    result = _execute(payload)

    assert "error" not in result
    assert result["delivery"]["channel"] == "both"
    assert isinstance(result["letter"], str) and len(result["letter"]) > 0
    assert isinstance(result["email"]["body_text"], str) and len(result["email"]["body_text"]) > 0
    assert isinstance(result["content"]["email_html"], str) and len(result["content"]["email_html"]) > 0


def test_runtime_mahnung_requires_invoice_and_due_fields() -> None:
    payload = _base_payload()
    payload["letter_type"] = "mahnung_1"
    payload["communication_channel"] = "email"
    payload.pop("invoice_number", None)
    payload.pop("invoice_date", None)
    payload.pop("invoice_amount", None)
    payload.pop("due_date", None)

    result = _execute(payload)

    assert "error" not in result
    errors = result["validation"]["errors"]
    assert any("Für Mahnungen ist Rechnungsnummer erforderlich" in item for item in errors)
    assert any("Für Mahnungen ist Fälligkeit erforderlich" in item for item in errors)
