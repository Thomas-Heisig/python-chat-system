from __future__ import annotations

import asyncio
import base64
from typing import Any

import pytest

from plugins.business_letter.plugin import BusinessLetterPlugin
from plugins.business_letter.services.artifacts import build_pdf_payload


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
    assert result["validation"]["status"] == "needs_review"
    assert any("Unterzeichner" in item for item in result["validation"]["errors"])


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


def test_runtime_uses_document_kind_specific_numbering_settings(tmp_path) -> None:
    plugin = BusinessLetterPlugin(
        {
            "rechnung_document_number_prefix": "RE",
            "rechnung_document_number_sequence_kind": "business_letter:rechnung",
            "rechnung_document_number_pattern": "{prefix}/{year}/{sequence_text}",
            "rechnung_document_number_width": 4,
        }
    )
    plugin._number_sequences = plugin._number_sequences.__class__(tmp_path / "business_letter.sqlite3")

    payload = _base_payload()
    payload.pop("document_number", None)
    payload["letter_type"] = "rechnung"
    payload["document_kind"] = "rechnung"
    payload["positions"] = [
        {
            "name": "Fensterbank",
            "quantity": "2",
            "unit_code": "C62",
            "price_net": "149.00",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]

    result = asyncio.run(plugin.execute(payload))

    assert "error" not in result
    assert result["document"]["reference"]["document_number"].startswith("RE/")


def test_runtime_applies_position_and_tax_defaults_only_when_enabled() -> None:
    payload = _base_payload()
    payload["positions"] = [
        {
            "name": "Granitplatte",
            "quantity": "1",
            "price_net": "250.00",
        }
    ]
    payload["buyer_reference"] = ""
    payload["payment_reference"] = ""
    payload["plugin_settings"] = {
        "default_unit_code": "MTK",
        "default_tax_category": "E",
        "default_tax_rate": 0,
        "default_tax_exemption_enabled": True,
        "default_tax_exemption_reason": "Steuerfreie Leistung",
        "default_tax_exemption_reason_code": "VATEX-EU-132",
        "default_buyer_reference": "04011000-12345-35",
        "default_payment_reference": "RE-{document_number}",
    }

    result = _execute(payload)

    assert "error" not in result
    position = result["commercial_document"]["customer_visible"]["positions"][0]
    assert position["unit_code"] == "MTK"
    assert position["vat_category"] == "E"
    assert position["vat_rate"] == "0.00"
    assert result["commercial_document"]["customer_visible"]["buyer_reference"] == "04011000-12345-35"
    assert result["commercial_document"]["customer_visible"]["payment_reference"] == "RE-{document_number}"
    tax_breakdown = result["commercial_document"]["customer_visible"]["vat_breakdown"][0]
    assert tax_breakdown["tax_exemption_reason"] == "Steuerfreie Leistung"
    assert tax_breakdown["tax_exemption_reason_code"] == "VATEX-EU-132"


def test_runtime_applies_layout_settings_to_html_pdf_and_artifact_names() -> None:
    payload = _base_payload()
    payload["plugin_settings"] = {
        **payload["plugin_settings"],
        "company_bank_name": "Steinbank",
        "company_iban": "DE02120300000000202051",
        "company_bic": "BYLADEM1001",
        "company_legal_form": "GmbH",
        "company_registry_number": "HRB 55555",
        "company_registry_court": "Amtsgericht Hannover",
        "company_logo_url": "https://example.com/logo.png",
        "logo_width_mm": 44,
        "logo_position": "right",
        "page_margin_mm": 18,
        "default_font_family": "IBM Plex Sans",
        "default_font_size_pt": 13,
        "accent_color": "#005a36",
        "footer_text": "Steinbau Real GmbH · Werkstraße 8 · 30159 Hannover",
        "show_page_numbers": True,
        "show_bank_details_in_footer": True,
        "show_legal_details_in_footer": True,
        "draft_watermark_text": "ENTWURF INTERN",
        "default_pdf_filename_pattern": "pdf-{document_number}",
    }

    result = _execute(payload)

    assert "error" not in result
    html = result["content"]["document_html"]
    assert "font-family:IBM Plex Sans" in html
    assert "font-size:13pt" in html
    assert "margin:18mm" in html
    assert "justify-content:flex-end" in html
    assert "width:44mm" in html
    assert "#005a36" in html
    assert "Steinbau Real GmbH · Werkstraße 8 · 30159 Hannover" in html
    assert "Steinbank · DE02120300000000202051 · BYLADEM1001" in html
    assert "GmbH · HRB 55555 · Amtsgericht Hannover" in html
    assert "ENTWURF INTERN" in html
    assert any(artifact["file_name"] == "pdf-DOC-2026-9001.pdf" for artifact in result["artifacts"] if artifact["kind"] == "pdf")

    pdf_payload = build_pdf_payload(result["template"], result["document"]["reference"], result["document"])
    pdf_bytes = base64.b64decode(pdf_payload)
    assert b"Steinbau Real GmbH" in pdf_bytes
    assert b"Steinbank" in pdf_bytes
    assert b"Seite 1/1" in pdf_bytes
    assert b"LAYOUT font=IBM Plex Sans size_pt=13 margin_mm=18 accent=#005a36" in pdf_bytes
    assert b"LAYOUT logo_present=yes logo_width_mm=44 logo_position=right" in pdf_bytes
    assert "ENTWURF INTERN".encode("latin-1", errors="ignore") in pdf_bytes


def test_runtime_uses_kernschmiede_system_logo_when_company_logo_missing() -> None:
    payload = _base_payload()
    payload["plugin_settings"] = {
        "company_name": "Steinbau Real GmbH",
        "company_street": "Industriestrasse 99",
        "company_city": "Hannover",
        "company_zip": "30159",
        "company_manager": "Maria Real",
        "company_vat_id": "DE998877665",
    }

    result = _execute(payload)

    assert "error" not in result
    html = result["content"]["document_html"]
    assert "data:image/svg+xml;base64," in html
    assert "Steinbau Real GmbH" in html

    pdf_payload = build_pdf_payload(result["template"], result["document"]["reference"], result["document"])
    pdf_bytes = base64.b64decode(pdf_payload)
    assert b"Kernschmiede" in pdf_bytes


def test_runtime_applies_shipping_defaults_and_auto_attachments() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "email"
    payload["document_kind"] = "rechnung"
    payload["positions"] = [
        {
            "name": "Fensterbank",
            "quantity": "1",
            "unit_code": "C62",
            "price_net": "149.00",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]
    payload["buyer_reference"] = "04011000-12345-35"
    payload["einvoice"] = {"enabled": True, "standard": "xrechnung"}
    payload["plugin_settings"] = {
        **payload["plugin_settings"],
        "default_email_subject_template": "{document_kind} {document_number} für {customer_company}",
        "default_cc": "vertrieb@example.de; kalkulation@example.de",
        "company_email_bcc": "archiv@example.de",
        "default_reply_to_address": "reply@example.de",
        "default_email_html_enabled": False,
        "default_attach_pdf": True,
        "default_attach_xml": True,
    }

    result = _execute(payload)

    assert "error" not in result
    assert result["email"]["subject"] == "rechnung DOC-2026-9001 für Kunde GmbH"
    assert result["delivery"]["subject"] == result["email"]["subject"]
    assert result["email"]["cc"] == ["vertrieb@example.de", "kalkulation@example.de"]
    assert result["email"]["bcc"] == ["archiv@example.de"]
    assert result["email"]["reply_to"] == "reply@example.de"
    assert result["email"]["html_enabled"] is False
    assert result["email"]["body_html"] == ""
    attachments = result["email"]["attachments"]
    assert [item["kind"] for item in attachments] == ["pdf", "xrechnung_xml"]
    assert attachments[0]["file_name"].endswith(".pdf")
    assert attachments[0]["content_base64"]
    assert attachments[1]["file_name"] == "xrechnung.xml"
    assert base64.b64decode(attachments[1]["content_base64"]).startswith(b"<?xml")


def test_runtime_blocks_email_delivery_on_validator_errors_when_configured() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "email"
    payload["letter_type"] = "rechnung"
    payload["document_kind"] = "rechnung"
    payload["positions"] = [
        {
            "name": "Fensterbank",
            "quantity": "1",
            "unit_code": "C62",
            "price_net": "149.00",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]
    payload["buyer_reference"] = ""
    payload["einvoice"] = {"enabled": True, "standard": "xrechnung"}
    payload["plugin_settings"] = {
        **payload["plugin_settings"],
        "validate_before_send": True,
        "block_send_on_validation_error": True,
    }

    result = _execute(payload)

    assert "error" not in result
    assert result["status"] == "needs_review"
    assert result["ready_for_sending"] is False
    assert result["delivery"]["blocked"] is True
    assert "E-Rechnungsvalidierung fehlgeschlagen" in result["delivery"]["block_reason"]
    assert any("E-Rechnungsvalidierung fehlgeschlagen" in item for item in result["validation"]["errors"])


def test_runtime_strict_logo_validation_returns_clear_error() -> None:
    payload = _base_payload()
    payload["communication_channel"] = "email"
    payload["company_logo_file"] = {"data_url": "data:image/png;base64,%%not-base64%%", "file_name": "logo.png"}
    payload["plugin_settings"] = {
        **payload["plugin_settings"],
        "logo_strict_mode": True,
    }

    result = _execute(payload)

    assert "error" not in result
    layout = result["template"]["layout"]
    assert layout["logo_strict_mode"] in {True, "True", "true"}
    with pytest.raises(ValueError, match="logo_base64_invalid"):
        build_pdf_payload(result["template"], result["document"]["reference"], result["document"])
