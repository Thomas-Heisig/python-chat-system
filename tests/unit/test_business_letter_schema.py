from __future__ import annotations

import json

from app.training.evaluation.business_letter_schema import validate_business_letter_json_text


def test_business_letter_schema_accepts_valid_payload() -> None:
    payload = {
        "document": {
            "document_type": "angebot",
            "status": "draft",
            "subject": "Abstimmung zur Kuechenarbeitsplatte",
            "salutation": "Sehr geehrter Herr Mustermann,",
            "body": {
                "paragraphs": [
                    "vielen Dank fuer Ihre Anfrage.",
                    "Bitte bestaetigen Sie die finalen Masse.",
                ],
                "closing": "Mit freundlichen Gruessen",
            },
            "ready_for_sending": False,
        },
        "validation": {
            "status": "needs_review",
            "errors": [],
            "warnings": [],
            "missing_information": ["bestaetigte Masse"],
        },
        "email": {
            "to": ["kunde@example.de"],
            "cc": [],
            "bcc": [],
            "reply_to": "info@example.de",
            "subject": "Angebot 2026-1001",
            "body_text": "Guten Tag,\n\nvielen Dank.",
            "body_html": "<p>Guten Tag,</p><p>vielen Dank.</p>",
        },
    }

    result = validate_business_letter_json_text(json.dumps(payload, ensure_ascii=False))

    assert result.valid is True
    assert result.errors == []


def test_business_letter_schema_rejects_non_json_output() -> None:
    result = validate_business_letter_json_text("### Brief\nNicht als JSON")

    assert result.valid is False
    assert result.errors[0].startswith("invalid_json")


def test_business_letter_schema_rejects_forbidden_markdown_patterns() -> None:
    payload = {
        "document": {
            "document_type": "geschaeftsbrief",
            "status": "draft",
            "subject": "# Ueberschrift",
            "salutation": "Sehr geehrter Herr Mustermann,",
            "body": {
                "paragraphs": ["Ich habe Ihre Anfrage verstanden."],
                "closing": "Mit freundlichen Gruessen",
            },
            "missing_information": ["Datum"],
        }
    }

    result = validate_business_letter_json_text(json.dumps(payload, ensure_ascii=False))

    assert result.valid is False
    assert any(err.startswith("forbidden_pattern") for err in result.errors)


def test_business_letter_schema_accepts_extended_status_values() -> None:
    payload = {
        "document_type": "geschaeftsbrief",
        "status": "queued",
        "subject": "Statuswechsel",
        "salutation": "Sehr geehrte Damen und Herren,",
        "body_paragraphs": ["Die Nachricht wurde zur Zustellung eingereiht."],
        "closing": "Mit freundlichen Gruessen",
        "missing_information": [],
    }

    result = validate_business_letter_json_text(json.dumps(payload, ensure_ascii=False))

    assert result.valid is True
    assert result.errors == []
