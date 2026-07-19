from __future__ import annotations

import asyncio
from typing import Any

from plugins.business_letter import plugin as business_letter_module
from plugins.business_letter.plugin import BusinessLetterPlugin
from plugins.business_letter.services.persistence import BusinessLetterPersistence


def _execute(payload: dict[str, Any]) -> dict[str, Any]:
    plugin = BusinessLetterPlugin(
        {
            "company_name": "Steinbau Real GmbH",
            "company_street": "Industriestrasse 99",
            "company_city": "Hannover",
            "company_zip": "30159",
            "company_manager": "Maria Real",
            "company_vat_id": "DE998877665",
        }
    )
    return asyncio.run(plugin.execute(payload))


def _base_payload(letter_type: str) -> dict[str, Any]:
    return {
        "letter_type": letter_type,
        "document_kind": letter_type,
        "subject": f"Dokument {letter_type}",
        "communication_channel": "email",
        "recipient_email": "kunde@example.de",
        "customer_company": "Kunde GmbH",
        "customer_street": "Hauptweg 12",
        "customer_zip": "10115",
        "customer_city": "Berlin",
    }


def _source_document(kind: str, number: str = "SRC-1001") -> dict[str, Any]:
    return {
        "document_id": f"doc-{number.lower()}",
        "document_number": number,
        "document_kind": kind,
        "document": {
            "subject": f"Quelle {kind}",
            "recipient": {
                "name": "Kunde GmbH",
                "street": "Hauptweg 12",
                "postal_code": "10115",
                "city": "Berlin",
                "email": "kunde@example.de",
            },
            "relationships": {
                "project_id": "project-77",
                "customer_id": "customer-44",
            },
        },
        "commercial_document": {
            "document_kind": kind,
            "customer_visible": {
                "issue_date": "2026-07-12",
                "payment_due_date": "2026-07-26",
                "totals": {
                    "payable_amount": "999.50",
                },
                "project_reference": "Projekt Nord",
            },
            "positions": [
                {
                    "line_id": "1",
                    "name": "Fensterbank Granit",
                    "description": "Fensterbank Granit",
                    "quantity": "2",
                    "unit_code": "C62",
                    "price_net": "120.00",
                    "vat_category": "S",
                    "vat_rate": "19",
                    "stone_details": {
                        "material_type": "Granit",
                        "trade_name": "Nero Assoluto",
                    },
                },
                {
                    "line_id": "2",
                    "name": "Montage",
                    "description": "Montage vor Ort",
                    "quantity": "1",
                    "unit_code": "C62",
                    "price_net": "80.00",
                    "vat_category": "S",
                    "vat_rate": "19",
                },
            ],
        },
    }


def test_conversion_offer_to_order_confirmation_is_allowed() -> None:
    payload = _base_payload("auftragsbestaetigung")
    payload["conversion_action"] = "angebot_to_auftragsbestaetigung"
    payload["source_document"] = _source_document("angebot", number="ANG-2026-17")

    result = _execute(payload)

    assert "error" not in result
    assert result["conversion"]["applied"] is True
    assert result["conversion"]["source_kind"] == "angebot"
    assert result["document"]["relationships"]["source_document_number"] == "ANG-2026-17"
    assert len(result["commercial_document"]["positions"]) == 2


def test_conversion_rejects_wrong_source_kind() -> None:
    payload = _base_payload("gutschrift")
    payload["conversion_action"] = "rechnung_to_gutschrift"
    payload["source_document"] = _source_document("angebot", number="ANG-2026-20")

    result = _execute(payload)

    assert "error" in result
    assert "erwartet Quelldokument-Typ 'rechnung'" in str(result["error"])


def test_conversion_supports_position_subset_and_partial_quantity() -> None:
    payload = _base_payload("rechnung")
    payload["conversion_action"] = "lieferschein_to_rechnung"
    payload["source_document"] = _source_document("lieferschein", number="LS-2026-12")
    payload["source_position_line_ids"] = ["1"]
    payload["source_position_quantities"] = {"1": "0.5"}

    result = _execute(payload)

    assert "error" not in result
    positions = result["commercial_document"]["positions"]
    assert len(positions) == 1
    assert positions[0]["line_id"] == "1"
    assert positions[0]["quantity"] == "0.500"


def test_storno_requires_source_reference() -> None:
    payload = _base_payload("stornorechnung")
    payload["positions"] = [
        {
            "name": "Storno-Position",
            "quantity": "1",
            "unit_code": "C62",
            "price_net": "50",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]
    payload["due_date"] = "2026-08-01"

    result = _execute(payload)

    assert "error" not in result
    assert any("Stornorechnung benötigt eine Ursprungsrechnung" in item for item in result["validation"]["errors"])


def test_credit_note_requires_reference() -> None:
    payload = _base_payload("gutschrift")
    payload["positions"] = [
        {
            "name": "Gutschrift Position",
            "quantity": "1",
            "unit_code": "C62",
            "price_net": "50",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]
    payload["due_date"] = "2026-08-01"

    result = _execute(payload)

    assert "error" not in result
    assert any("Gutschrift benötigt ein Bezugsdokument" in item for item in result["validation"]["errors"])


def test_dunning_requires_open_invoice_reference() -> None:
    payload = _base_payload("mahnung_1")
    payload["invoice_number"] = "RE-2026-009"
    payload["invoice_date"] = "2026-07-01"
    payload["invoice_amount"] = "120.00"
    payload["due_date"] = "2026-07-15"

    result = _execute(payload)

    assert "error" not in result
    assert any("Mahnung benötigt eine offene Rechnung" in item for item in result["validation"]["errors"])


def test_return_note_requires_invoice_or_delivery_note_reference_kind() -> None:
    payload = _base_payload("retourenschein")
    payload["delivery_date"] = "2026-08-01"
    payload["source_document_number"] = "ANG-2026-99"
    payload["source_document_kind"] = "angebot"

    result = _execute(payload)

    assert "error" not in result
    assert any("Retourenschein darf nur auf Lieferschein oder Rechnung referenzieren" in item for item in result["validation"]["errors"])


def test_storno_conversion_sets_original_invoice_number_from_source() -> None:
    payload = _base_payload("stornorechnung")
    payload["conversion_action"] = "rechnung_to_stornorechnung"
    payload["source_document"] = _source_document("rechnung", number="RE-2026-88")

    result = _execute(payload)

    assert "error" not in result
    customer_visible = result["commercial_document"]["customer_visible"]
    assert customer_visible["original_invoice_number"] == "RE-2026-88"
    assert result["document"]["relationships"]["source_document_kind"] == "rechnung"


def test_delivery_to_invoice_uses_remaining_quantity_from_followups() -> None:
    payload = _base_payload("rechnung")
    payload["conversion_action"] = "lieferschein_to_rechnung"
    payload["source_document"] = _source_document("lieferschein", number="LS-2026-77")
    payload["source_document_followups"] = [
        {
            "document_kind": "rechnung",
            "commercial_document": {
                "positions": [
                    {
                        "line_id": "1",
                        "quantity": "1",
                    }
                ]
            },
        }
    ]

    result = _execute(payload)

    assert "error" not in result
    positions = result["commercial_document"]["positions"]
    first_line = next(item for item in positions if item["line_id"] == "1")
    assert first_line["quantity"] == "1.000"


def test_invoice_to_credit_sets_negative_line_values() -> None:
    payload = _base_payload("gutschrift")
    payload["conversion_action"] = "rechnung_to_gutschrift"
    payload["source_document"] = _source_document("rechnung", number="RE-2026-33")

    result = _execute(payload)

    assert "error" not in result
    positions = result["commercial_document"]["positions"]
    assert positions
    assert all(str(item["line_net_amount"]).startswith("-") for item in positions)


def test_invoice_to_reminder_uses_open_balance_after_payments_and_credits() -> None:
    payload = _base_payload("zahlungserinnerung")
    payload["conversion_action"] = "rechnung_to_zahlungserinnerung"
    payload["source_document"] = _source_document("rechnung", number="RE-2026-56")
    payload["source_document"]["commercial_document"]["customer_visible"]["totals"]["payable_amount"] = "1000.00"
    payload["source_document_followups"] = [
        {"document_kind": "zahlung", "payment_amount": "200.00"},
        {"document_kind": "gutschrift", "amount": "50.00"},
    ]

    result = _execute(payload)

    assert "error" not in result
    assert result["conversion"]["open_amount"] == "750.00"


def test_conversion_uses_persistent_followup_chain_for_remaining_quantities(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    plugin = BusinessLetterPlugin(
        {
            "company_name": "Steinbau Real GmbH",
            "company_street": "Industriestrasse 99",
            "company_city": "Hannover",
            "company_zip": "30159",
            "company_manager": "Maria Real",
            "company_vat_id": "DE998877665",
        }
    )

    source_payload = _base_payload("lieferschein")
    source_payload["persist_to_database"] = True
    source_payload["project_id"] = "project-chain-77"
    source_payload["customer_id"] = "customer-chain-44"
    source_payload["positions"] = [
        {
            "line_id": "1",
            "name": "Fensterbank Granit",
            "description": "Fensterbank Granit",
            "quantity": "2",
            "unit_code": "C62",
            "price_net": "120.00",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]
    source_result = asyncio.run(plugin.execute(source_payload))
    assert "error" not in source_result
    source_document_id = str(source_result["document_id"])

    first_invoice_payload = _base_payload("rechnung")
    first_invoice_payload["persist_to_database"] = True
    first_invoice_payload["conversion_action"] = "lieferschein_to_rechnung"
    first_invoice_payload["source_document_id"] = source_document_id
    first_invoice_payload["source_position_line_ids"] = ["1"]
    first_invoice_payload["source_position_quantities"] = {"1": "1"}
    first_invoice_payload["due_date"] = "2026-08-15"
    first_invoice_result = asyncio.run(plugin.execute(first_invoice_payload))
    assert "error" not in first_invoice_result

    second_invoice_payload = _base_payload("rechnung")
    second_invoice_payload["persist_to_database"] = True
    second_invoice_payload["conversion_action"] = "lieferschein_to_rechnung"
    second_invoice_payload["source_document_id"] = source_document_id
    second_invoice_payload["source_position_line_ids"] = ["1"]
    second_invoice_payload["due_date"] = "2026-08-20"
    second_invoice_result = asyncio.run(plugin.execute(second_invoice_payload))

    assert "error" not in second_invoice_result
    positions = second_invoice_result["commercial_document"]["positions"]
    assert positions[0]["quantity"] == "1.000"
    assert second_invoice_result["conversion"]["follow_up_documents"] >= 1


def test_project_case_overview_returns_timeline_and_quantity_chain(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    plugin = BusinessLetterPlugin(
        {
            "company_name": "Steinbau Real GmbH",
            "company_street": "Industriestrasse 99",
            "company_city": "Hannover",
            "company_zip": "30159",
            "company_manager": "Maria Real",
            "company_vat_id": "DE998877665",
        }
    )

    source_payload = _base_payload("lieferschein")
    source_payload["persist_to_database"] = True
    source_payload["project_id"] = "project-timeline-11"
    source_payload["customer_id"] = "customer-timeline-12"
    source_payload["positions"] = [
        {
            "line_id": "1",
            "name": "Montage",
            "description": "Montage vor Ort",
            "quantity": "2",
            "unit_code": "C62",
            "price_net": "80.00",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]
    source_result = asyncio.run(plugin.execute(source_payload))
    assert "error" not in source_result
    source_document_id = str(source_result["document_id"])

    for due_date in ["2026-08-10", "2026-08-11"]:
        invoice_payload = _base_payload("rechnung")
        invoice_payload["persist_to_database"] = True
        invoice_payload["conversion_action"] = "lieferschein_to_rechnung"
        invoice_payload["source_document_id"] = source_document_id
        invoice_payload["source_position_line_ids"] = ["1"]
        invoice_payload["source_position_quantities"] = {"1": "1"}
        invoice_payload["due_date"] = due_date
        invoice_result = asyncio.run(plugin.execute(invoice_payload))
        assert "error" not in invoice_result

    overview_result = asyncio.run(
        plugin.execute(
            {
                "action": "project_case_overview",
                "letter_type": "angebot",
                "subject": "Projektakte",
                "project_id": "project-timeline-11",
                "source_document_id": source_document_id,
            }
        )
    )

    assert "error" not in overview_result
    assert overview_result["success"] is True
    project_case = overview_result["project_case"]
    assert project_case["status_view"]["document_count"] >= 3
    assert project_case["quantity_chain"]["totals"]["open_quantity"] == "0.000"


def test_conversion_resolves_source_document_from_persistent_project_context(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    plugin = BusinessLetterPlugin(
        {
            "company_name": "Steinbau Real GmbH",
            "company_street": "Industriestrasse 99",
            "company_city": "Hannover",
            "company_zip": "30159",
            "company_manager": "Maria Real",
            "company_vat_id": "DE998877665",
        }
    )

    source_payload = _base_payload("angebot")
    source_payload["persist_to_database"] = True
    source_payload["project_id"] = "project-context-22"
    source_payload["customer_id"] = "customer-context-23"
    source_payload["offer_valid_until"] = "2026-08-30"
    source_payload["positions"] = [
        {
            "line_id": "1",
            "name": "Kuechenplatte Granit",
            "description": "Kuechenplatte Granit",
            "quantity": "1",
            "unit_code": "C62",
            "price_net": "300.00",
            "vat_category": "S",
            "vat_rate": "19",
        }
    ]
    source_result = asyncio.run(plugin.execute(source_payload))
    assert "error" not in source_result

    conversion_payload = _base_payload("auftragsbestaetigung")
    conversion_payload["persist_to_database"] = True
    conversion_payload["conversion_action"] = "angebot_to_auftragsbestaetigung"
    conversion_payload["project_id"] = "project-context-22"
    conversion_payload["customer_id"] = "customer-context-23"
    # no explicit source_document_id/number on purpose
    conversion_result = asyncio.run(plugin.execute(conversion_payload))

    assert "error" not in conversion_result
    assert conversion_result["conversion"]["applied"] is True
    assert conversion_result["conversion"]["source_kind"] == "angebot"
    assert str(conversion_result["document"]["relationships"]["source_document_id"]).strip() != ""


def test_delivery_to_invoice_blocks_when_source_status_not_allowed() -> None:
    payload = _base_payload("rechnung")
    payload["conversion_action"] = "lieferschein_to_rechnung"
    source = _source_document("lieferschein", number="LS-STATUS-01")
    source["status"] = "draft"
    payload["source_document"] = source

    result = _execute(payload)

    assert "error" in result
    assert "nicht erlaubt" in str(result["error"])


def test_invoice_to_reminder_blocks_when_open_amount_is_zero() -> None:
    payload = _base_payload("zahlungserinnerung")
    payload["conversion_action"] = "rechnung_to_zahlungserinnerung"
    payload["source_document"] = _source_document("rechnung", number="RE-PAID-01")
    payload["source_document"]["status"] = "sent"
    payload["source_document"]["commercial_document"]["customer_visible"]["totals"]["payable_amount"] = "1000.00"
    payload["source_document_followups"] = [
        {"document_kind": "zahlung", "payment_amount": "1000.00"},
    ]

    result = _execute(payload)

    assert "error" in result
    assert "kein offener Betrag" in str(result["error"])
