from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any

import pytest

from plugins.business_letter import plugin as business_letter_module
from plugins.business_letter.plugin import BusinessLetterPlugin
from plugins.business_letter.services.numbering import NumberSequenceStore
from plugins.business_letter.services.persistence import BusinessLetterPersistence


def _base_payload() -> dict[str, Any]:
    return {
        "letter_type": "angebot",
        "subject": "Angebot fuer Steinplatte",
        "communication_channel": "email",
        "customer_company": "Kunde GmbH",
        "customer_first_name": "Anna",
        "customer_last_name": "Beispiel",
        "customer_salutation": "Frau",
        "customer_street": "Hauptweg 12",
        "customer_zip": "10115",
        "customer_city": "Berlin",
        "customer_country": "Deutschland",
        "recipient_email": "kunde@example.de",
        "buyer_reference": "BR-2026-01",
        "issue_date": "2026-07-18",
        "positions": [
            {
                "name": "Steinplatte",
                "description": "Natursteinplatte",
                "quantity": "1",
                "unit_code": "C62",
                "price_net": "199.90",
                "vat_rate": "19",
            }
        ],
        "plugin_settings": {
            "company_name": "Steinbau Real GmbH",
            "company_street": "Industriestrasse 99",
            "company_city": "Hannover",
            "company_zip": "30159",
            "company_manager": "Maria Real",
            "company_vat_id": "DE998877665",
        },
    }


def _execute(payload: dict[str, Any]) -> dict[str, Any]:
    plugin = BusinessLetterPlugin()
    return asyncio.run(plugin.execute(payload))


def test_number_sequences_are_separate_per_document_kind(tmp_path: Path) -> None:
    store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    offer_first = store.next_number(prefix="ANG", sequence_kind="angebot", tenant_id="tenant-a", year=2026, width=5)
    invoice_first = store.next_number(prefix="RECH", sequence_kind="rechnung", tenant_id="tenant-a", year=2026, width=5)
    offer_second = store.next_number(prefix="ANG", sequence_kind="angebot", tenant_id="tenant-a", year=2026, width=5)

    assert offer_first == "ANG-2026-00001"
    assert invoice_first == "RECH-2026-00001"
    assert offer_second == "ANG-2026-00002"


def test_number_sequences_reset_per_year(tmp_path: Path) -> None:
    store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    last_year = store.next_number(prefix="ANG", sequence_kind="angebot", tenant_id="tenant-a", year=2025, width=4)
    next_year = store.next_number(prefix="ANG", sequence_kind="angebot", tenant_id="tenant-a", year=2026, width=4)

    assert last_year == "ANG-2025-0001"
    assert next_year == "ANG-2026-0001"


def test_number_sequences_support_custom_pattern(tmp_path: Path) -> None:
    store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    number = store.next_number(
        prefix="ANG",
        sequence_kind="angebot",
        tenant_id="tenant-a",
        year=2026,
        width=3,
        pattern="{prefix}/{year}/{sequence_text}",
    )

    assert number == "ANG/2026/001"


def test_number_sequences_respect_start_value(tmp_path: Path) -> None:
    store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    number = store.next_number(
        prefix="RE",
        sequence_kind="rechnung",
        tenant_id="tenant-a",
        year=2026,
        width=4,
        start_value=150,
    )

    assert number == "RE-2026-0150"


def test_number_sequences_can_skip_year_reset(tmp_path: Path) -> None:
    store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    first = store.next_number(
        prefix="RE",
        sequence_kind="rechnung",
        tenant_id="tenant-a",
        year=2025,
        width=4,
        year_reset=False,
    )
    second = store.next_number(
        prefix="RE",
        sequence_kind="rechnung",
        tenant_id="tenant-a",
        year=2026,
        width=4,
        year_reset=False,
    )

    assert first == "RE-2025-0001"
    assert second == "RE-2026-0002"


def test_number_sequence_preview_uses_start_value_without_reserving(tmp_path: Path) -> None:
    store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    preview = store.peek_next_number(
        prefix="GS",
        sequence_kind="gutschrift",
        tenant_id="tenant-a",
        year=2026,
        width=3,
        start_value=8,
    )

    assert preview["preview"] == "GS-2026-008"
    assert preview["next_value"] == 8
    assert preview["current_value"] == 7


def test_explicit_document_number_is_preserved(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plugin = BusinessLetterPlugin()
    plugin._number_sequences = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    def fail_if_called(**_: Any) -> str:
        raise AssertionError("sequence reservation should not run for explicit document numbers")

    monkeypatch.setattr(plugin._number_sequences, "next_number", fail_if_called)

    result = asyncio.run(plugin.execute({**_base_payload(), "document_number": "DOC-EXPLICIT-4711"}))

    assert "error" not in result
    assert result["document"]["reference"]["document_number"] == "DOC-EXPLICIT-4711"


def test_parallel_numbering_allocates_unique_numbers(tmp_path: Path) -> None:
    store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    def reserve() -> str:
        return store.next_number(prefix="ANG", sequence_kind="angebot", tenant_id="tenant-a", year=2026, width=4)

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(lambda _: reserve(), range(12)))

    assert len(results) == len(set(results))
    assert sorted(results) == [f"ANG-2026-{index:04d}" for index in range(1, 13)]


def test_persistence_failure_before_atomic_write_does_not_advance_sequence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sequence_store = NumberSequenceStore(tmp_path / "business_letter.sqlite3")

    plugin = BusinessLetterPlugin()
    plugin._number_sequences = sequence_store
    captured_number: dict[str, str] = {}

    def fail_persist_document(**kwargs: Any) -> dict[str, Any]:
        captured_number["document_number"] = str(kwargs["reference"]["document_number"])
        raise RuntimeError("persistence unavailable")

    monkeypatch.setattr(plugin, "_persist_document", fail_persist_document)

    first_result = asyncio.run(plugin.execute({**_base_payload(), "persist_to_database": True}))

    assert "error" in first_result
    assert "persistence unavailable" in str(first_result["error"])
    assert captured_number["document_number"]

    next_number = sequence_store.next_number(
        prefix="ANG",
        sequence_kind="angebot",
        tenant_id="default",
        year=datetime.now().year,
        width=5,
    )
    assert next_number.endswith("00001")


def test_dual_save_warn_strategy_returns_warning_after_retries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    attempts = {"count": 0}

    def fail_guest_mirror(**_: Any) -> dict[str, Any]:
        attempts["count"] += 1
        raise RuntimeError("guest mirror unavailable")

    monkeypatch.setattr(persistence, "mirror_to_guest_database", fail_guest_mirror)

    payload = {
        **_base_payload(),
        "document_number": "",
        "persist_to_database": True,
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "dual_save_enabled": True,
            "dual_save_failure_mode": "warn",
            "dual_save_retry_attempts": 2,
        },
    }

    result = _execute(payload)

    assert "error" not in result
    persisted = result["database"]["persisted"]
    assert persisted["guest_system_storage"]["status"] == "warning"
    assert persisted["guest_system_storage"]["attempts"] == 3
    assert attempts["count"] == 3


def test_dual_save_fail_strategy_aborts_after_retries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    def fail_guest_mirror(**_: Any) -> dict[str, Any]:
        raise RuntimeError("guest mirror unavailable")

    monkeypatch.setattr(persistence, "mirror_to_guest_database", fail_guest_mirror)

    payload = {
        **_base_payload(),
        "document_number": "",
        "persist_to_database": True,
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "dual_save_enabled": True,
            "dual_save_failure_mode": "fail",
            "dual_save_retry_attempts": 1,
        },
    }

    result = _execute(payload)

    assert "error" in result
    assert "Dual-save failed after 2 attempts" in str(result["error"])


def test_dual_save_queue_strategy_marks_guest_persist_for_follow_up(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    def fail_guest_mirror(**_: Any) -> dict[str, Any]:
        raise RuntimeError("guest mirror unavailable")

    monkeypatch.setattr(persistence, "mirror_to_guest_database", fail_guest_mirror)

    payload = {
        **_base_payload(),
        "document_number": "",
        "persist_to_database": True,
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "dual_save_enabled": True,
            "dual_save_failure_mode": "queue",
            "dual_save_retry_attempts": 0,
        },
    }

    result = _execute(payload)

    assert "error" not in result
    assert result["database"]["persisted"]["guest_system_storage"]["status"] == "queued"


def test_persistence_applies_retention_hash_and_archive_group(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    payload = {
        **_base_payload(),
        "document_number": "DOC-ARCHIVE-1",
        "persist_to_database": True,
        "einvoice": {"enabled": True, "standard": "xrechnung"},
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "dual_save_enabled": False,
            "retention_days": 30,
            "enable_hash_verification": True,
            "archive_pdf_xml_together": True,
            "store_xml_artifact": True,
            "artifact_directory": "archive/business-letter",
        },
    }

    result = _execute(payload)

    assert "error" not in result
    persisted = result["database"]["persisted"]
    assert persisted["plugin_storage"]["document"]["retention_until"]
    pdf_and_xml = [
        item for item in persisted["plugin_storage"]["artifacts"]
        if item["artifact_kind"] in {"pdf", "xrechnung_xml"}
    ]
    assert len(pdf_and_xml) == 2
    assert all(item["hash_verified"] is True for item in pdf_and_xml)
    assert all(item["storage_key"].startswith("archive/business-letter/") for item in pdf_and_xml)
    assert len({item["archive_group"] for item in pdf_and_xml}) == 1


def test_persistence_archives_validation_reports_when_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    report_dir = tmp_path / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "doc_official_schema.txt").write_text("schema ok", encoding="utf-8")
    (report_dir / "doc_official_schematron.txt").write_text("schematron ok", encoding="utf-8")
    (report_dir / "doc_official_summary.json").write_text('{"ok":true}', encoding="utf-8")
    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(report_dir))

    plugin = BusinessLetterPlugin()
    monkeypatch.setattr(plugin, "_build_einvoice_payload", lambda *args, **kwargs: {
        "standard": "XRechnung",
        "valid": True,
        "xml": "<Invoice/>",
        "official_validation": {
            "schema": {"report_file": "doc_official_schema.txt"},
            "schematron": {"report_file": "doc_official_schematron.txt"},
        },
    })

    result = asyncio.run(
        plugin.execute(
            {
                **_base_payload(),
                "persist_to_database": True,
                "einvoice": {"enabled": True, "standard": "xrechnung"},
                "plugin_settings": {
                    **_base_payload()["plugin_settings"],
                    "dual_save_enabled": False,
                    "store_validation_reports": True,
                    "artifact_directory": "archive/reports",
                },
            }
        )
    )

    assert "error" not in result
    validation_artifacts = [
        item for item in result["database"]["persisted"]["plugin_storage"]["artifacts"]
        if item["artifact_kind"] == "validation_report"
    ]
    assert len(validation_artifacts) == 3
    assert all(item["storage_key"].startswith("archive/reports/") for item in validation_artifacts)


def test_released_documents_become_immutable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    base = {
        **_base_payload(),
        "document_id": "doc-immutable-1",
        "document_number": "DOC-IMMUTABLE-1",
        "persist_to_database": True,
        "ready_for_sending": True,
        "payment_terms": "Zahlbar innerhalb von 14 Tagen.",
        "payment_due_date": "2026-08-01",
        "due_date": "2026-08-01",
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "dual_save_enabled": False,
            "lock_released_documents": True,
        },
    }

    first = _execute(base)
    assert "error" not in first
    assert first["status"] == "ready"
    assert first["database"]["persisted"]["plugin_storage"]["document"]["is_immutable"] is True

    second = _execute({**base, "subject": "Geändertes Angebot fuer Steinplatte"})
    assert "error" in second
    assert "immutable" in str(second["error"]).lower()


def test_xrechnung_output_includes_xml_and_validation() -> None:
    result = _execute({**_base_payload(), "einvoice": {"enabled": True, "standard": "xrechnung"}})

    assert "error" not in result
    assert result["einvoice"]["standard"] == "XRechnung"
    assert result["einvoice"]["validation"]["valid"] is True
    assert "<cac:LegalMonetaryTotal>" in result["einvoice"]["xml"]
    assert "<cbc:PayableAmount currencyID=\"EUR\">" in result["einvoice"]["xml"]


def test_zugferd_output_requires_pdfa3_and_wraps_xrechnung() -> None:
    result = _execute({**_base_payload(), "einvoice": {"enabled": True, "standard": "zugferd"}})

    assert "error" not in result
    assert result["einvoice"]["standard"] == "ZUGFeRD"
    assert result["einvoice"]["pdfa3_required"] is True
    assert result["einvoice"]["validation"]["valid"] is True


def test_xrechnung_validation_reports_missing_buyer_reference() -> None:
    result = _execute({**_base_payload(), "buyer_reference": "", "einvoice": {"enabled": True, "standard": "xrechnung"}})

    errors = result["einvoice"]["validation"]["errors"]
    assert any(entry["code"] == "BR-DE-001" for entry in errors)


def test_plugin_settings_are_exposed_in_resolved_settings() -> None:
    payload = {
        **_base_payload(),
        "plugin_settings": {
            "default_currency": "CHF",
            "default_payment_terms": "Zahlbar innerhalb von 10 Tagen ohne Abzug.",
            "default_payment_method_code": "30",
            "document_number_prefix": "RECH",
            "document_number_width": 6,
            "guest_system_database_path": "data/database/custom_guest.db",
        },
    }
    result = _execute(payload)

    assert "error" not in result
    resolved = result["settings"]["resolved"]
    assert resolved["default_currency"] == "CHF"
    assert resolved["default_payment_terms"] == "Zahlbar innerhalb von 10 Tagen ohne Abzug."
    assert resolved["default_payment_method_code"] == "30"
    assert resolved["document_number_prefix"] == "RECH"
    assert resolved["document_number_width"] == 6
    assert resolved["guest_system_database_path"] == "data/database/custom_guest.db"


def test_sensitive_plugin_settings_are_masked_in_resolved_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    extra_field = {
        "key": "smtp_password",
        "label": "SMTP Passwort",
        "type": "password",
        "default": "",
        "group": "Kommunikation",
    }
    original_fields = list(business_letter_module.PLUGIN_META["settingsFields"])
    monkeypatch.setitem(business_letter_module.PLUGIN_META, "settingsFields", [*original_fields, extra_field])

    payload = {
        **_base_payload(),
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "smtp_password": "topsecret",
        },
    }

    result = _execute(payload)

    assert "error" not in result
    assert result["settings"]["resolved"]["smtp_password"] == "********"


def test_runtime_defaults_from_settings_are_applied_to_commercial_document() -> None:
    payload = {
        **_base_payload(),
        "currency": "",
        "payment_terms": "",
        "payment_method_code": "",
        "issue_date": "2026-07-18",
        "plugin_settings": {
            "default_currency": "CHF",
            "default_payment_terms": "Zahlbar innerhalb von 14 Tagen.",
            "default_payment_method_code": "58",
            "default_payment_days": 21,
        },
    }
    result = _execute(payload)

    assert "error" not in result
    customer_visible = result["commercial_document"]["customer_visible"]
    assert customer_visible["currency"] == "CHF"
    assert customer_visible["payment_terms"] == "Zahlbar innerhalb von 14 Tagen."
    assert customer_visible["payment_method_code"] == "58"
    assert customer_visible["payment_due_date"] == "2026-08-08"


def test_priority3_mapping_matrix_reverse_charge_and_tax_exemption() -> None:
    payload = {
        **_base_payload(),
        "buyer_electronic_address": "leitweg-4711",
        "buyer_electronic_address_scheme": "0204",
        "seller_electronic_address": "rechnung@steinbau-real.de",
        "seller_electronic_address_scheme": "EM",
        "positions": [
            {
                "name": "Montageleistung Reverse Charge",
                "quantity": "1",
                "unit_code": "HUR",
                "price_net": "100.00",
                "vat_category": "AE",
                "vat_rate": "0",
                "tax_exemption_reason": "Reverse charge",
            },
            {
                "name": "Steuerbefreite Nebenleistung",
                "quantity": "1",
                "unit_code": "C62",
                "price_net": "50.00",
                "vat_category": "E",
                "vat_rate": "0",
                "tax_exemption_reason": "Steuerfreie Ausfuhrlieferung",
                "tax_exemption_reason_code": "VATEX-EU-132",
            },
        ],
        "einvoice": {"enabled": True, "standard": "xrechnung"},
    }

    result = _execute(payload)

    assert "error" not in result
    validation = result["einvoice"]["validation"]
    assert validation["valid"] is True
    categories = {item["category"] for item in validation["tax_breakdown"]}
    assert {"AE", "E"}.issubset(categories)
    xml = result["einvoice"]["xml"]
    assert "<cbc:EndpointID schemeID=\"0204\">leitweg-4711</cbc:EndpointID>" in xml
    assert "<cbc:EndpointID schemeID=\"EM\">rechnung@steinbau-real.de</cbc:EndpointID>" in xml
    assert "<cbc:TaxExemptionReason>Reverse charge</cbc:TaxExemptionReason>" in xml
    assert "<cbc:TaxExemptionReasonCode>VATEX-EU-132</cbc:TaxExemptionReasonCode>" in xml


def test_priority3_mapping_matrix_base_quantity_shipping_rounding_and_multiple_tax_rates() -> None:
    payload = {
        **_base_payload(),
        "purchase_order_reference": "PO-2026-77",
        "contract_reference": "CTR-2026-12",
        "project_reference": "PRJ-ALPHA",
        "delivery_note_reference": "LS-2026-33",
        "payment_terms": "Zahlbar innerhalb von 10 Tagen ohne Abzug.",
        "payment_reference": "PAY-REF-10",
        "positions": [
            {
                "name": "Naturstein nach Preisbasismenge",
                "quantity": "250",
                "unit_code": "KGM",
                "price_net": "40.00",
                "price_base_quantity": "100",
                "price_base_quantity_unit_code": "KGM",
                "vat_rate": "19",
            },
            {
                "name": "Planungsleistung",
                "quantity": "1",
                "unit_code": "H87",
                "price_net": "50.00",
                "vat_rate": "7",
            },
        ],
        "document_allowances": [{"reason": "Projektbonus", "amount": "10.00", "vat_category": "S", "vat_rate": "19"}],
        "document_charges": [{"reason": "Mindermengenzuschlag", "amount": "5.00", "vat_category": "S", "vat_rate": "19"}],
        "shipping_costs": {"reason": "Versand", "amount": "15.00", "vat_category": "S", "vat_rate": "19", "reason_code": "FC"},
        "rounding_amount": "0.01",
        "einvoice": {"enabled": True, "standard": "xrechnung"},
    }

    result = _execute(payload)

    assert "error" not in result
    totals = result["commercial_document"]["totals"]
    assert totals["line_net_total"] == "150.00"
    assert totals["allowance_total"] == "10.00"
    assert totals["charge_total"] == "20.00"
    assert totals["payable_rounding_amount"] == "0.01"
    assert totals["tax_exclusive_amount"] == "160.00"
    xml = result["einvoice"]["xml"]
    assert "<cbc:BaseQuantity unitCode=\"KGM\">100.000</cbc:BaseQuantity>" in xml
    assert "<cac:OrderReference>" in xml
    assert "<cac:ContractDocumentReference>" in xml
    assert "<cac:ProjectReference>" in xml
    assert "<cac:DespatchDocumentReference>" in xml
    assert "<cbc:PaymentID>PAY-REF-10</cbc:PaymentID>" in xml
    assert "<cbc:PayableRoundingAmount currencyID=\"EUR\">0.01</cbc:PayableRoundingAmount>" in xml
    assert xml.count("<cac:TaxSubtotal>") >= 2
    assert "<cbc:AllowanceChargeReason>Versand</cbc:AllowanceChargeReason>" in xml


@pytest.mark.parametrize(
    ("document_kind", "expected_type_code"),
    [
        ("abschlagsrechnung", "326"),
        ("gutschrift", "381"),
        ("stornorechnung", "381"),
    ],
)
def test_priority3_mapping_matrix_document_type_codes(document_kind: str, expected_type_code: str) -> None:
    payload = {
        **_base_payload(),
        "letter_type": document_kind,
        "document_kind": document_kind,
        "original_invoice_number": "INV-2026-0007",
        "einvoice": {"enabled": True, "standard": "xrechnung"},
    }

    result = _execute(payload)

    assert "error" not in result
    xml = result["einvoice"]["xml"]
    assert f"<cbc:InvoiceTypeCode>{expected_type_code}</cbc:InvoiceTypeCode>" in xml
    if document_kind in {"gutschrift", "stornorechnung"}:
        assert "<cac:BillingReference>" in xml
        assert "<cbc:ID>INV-2026-0007</cbc:ID>" in xml


def test_dispatch_queue_persists_attempt_and_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    plugin = BusinessLetterPlugin()

    async def fake_send(_: dict[str, Any]) -> dict[str, Any]:
        return {"success": False, "error": "smtp unavailable"}

    monkeypatch.setattr(plugin, "_send_via_email_plugin_interface", fake_send)

    payload = {
        **_base_payload(),
        "document_id": "doc-dispatch-1",
        "document_number": "DOC-DISPATCH-1",
        "persist_to_database": True,
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "dispatch_queue_enabled": True,
            "dispatch_execute_immediately": True,
            "dispatch_retry_attempts": 3,
            "dispatch_provider": "smtp",
            "dual_save_enabled": False,
        },
        "ready_for_sending": True,
        "payment_terms": "Zahlbar innerhalb von 14 Tagen.",
        "payment_due_date": "2026-08-01",
        "due_date": "2026-08-01",
    }

    result = asyncio.run(plugin.execute(payload))

    assert "error" not in result
    dispatch = result["delivery"]["dispatch"]
    assert dispatch["enabled"] is True
    assert dispatch["status"] == "queued"
    assert dispatch["queue"]["attempt_count"] == 1
    assert dispatch["queue"]["max_attempts"] == 3
    assert dispatch["queue"]["next_retry_at"]

    connection = sqlite3.connect(tmp_path / "business_letter.sqlite3")
    connection.row_factory = sqlite3.Row
    try:
        queue_row = connection.execute("SELECT * FROM dispatch_queue WHERE document_id = ?", ("doc-dispatch-1",)).fetchone()
        assert queue_row is not None
        assert str(queue_row["status"]) == "queued"
        history_rows = connection.execute("SELECT event_type FROM dispatch_history WHERE dispatch_id = ?", (queue_row["dispatch_id"],)).fetchall()
        assert len(history_rows) >= 2
        assert {str(row["event_type"]) for row in history_rows}.issuperset({"enqueued", "retry_scheduled"})
    finally:
        connection.close()


def test_dispatch_idempotency_prevents_duplicate_send(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persistence = BusinessLetterPersistence(tmp_path / "business_letter.sqlite3")
    monkeypatch.setattr(business_letter_module, "DEFAULT_PERSISTENCE", persistence)

    plugin = BusinessLetterPlugin()
    send_calls = {"count": 0}

    async def fake_send(_: dict[str, Any]) -> dict[str, Any]:
        send_calls["count"] += 1
        return {"success": True, "message": "ok"}

    monkeypatch.setattr(plugin, "_send_via_email_plugin_interface", fake_send)

    payload = {
        **_base_payload(),
        "document_id": "doc-dispatch-idempotent",
        "document_number": "DOC-IDEMPOTENT-1",
        "persist_to_database": True,
        "plugin_settings": {
            **_base_payload()["plugin_settings"],
            "dispatch_queue_enabled": True,
            "dispatch_execute_immediately": True,
            "dispatch_retry_attempts": 2,
            "dispatch_provider": "smtp",
            "dual_save_enabled": False,
        },
        "ready_for_sending": True,
        "payment_terms": "Zahlbar innerhalb von 14 Tagen.",
        "payment_due_date": "2026-08-01",
        "due_date": "2026-08-01",
    }

    first = asyncio.run(plugin.execute(payload))
    second = asyncio.run(plugin.execute({**payload, "revision_number": 2}))

    assert "error" not in first
    assert "error" not in second
    assert send_calls["count"] == 1
    assert first["delivery"]["dispatch"]["status"] == "sent"
    assert second["delivery"]["dispatch"]["status"] == "duplicate_suppressed"


def test_priority3_mapping_matrix_final_invoice_uses_prepayment() -> None:
    payload = {
        **_base_payload(),
        "letter_type": "schlussrechnung",
        "document_kind": "schlussrechnung",
        "prepaid_amount": "50.00",
        "original_invoice_number": "ABS-2026-0010",
        "einvoice": {"enabled": True, "standard": "xrechnung"},
    }

    result = _execute(payload)

    assert "error" not in result
    totals = result["commercial_document"]["totals"]
    assert totals["prepaid_amount"] == "50.00"
    assert totals["payable_amount"] == "187.88"
    xml = result["einvoice"]["xml"]
    assert "<cbc:PrepaidAmount currencyID=\"EUR\">50.00</cbc:PrepaidAmount>" in xml
    assert "<cac:BillingReference>" in xml


def test_cii_output_includes_root_and_validation() -> None:
    result = _execute({**_base_payload(), "einvoice": {"enabled": True, "standard": "xrechnung", "syntax": "CII"}})

    assert "error" not in result
    assert result["einvoice"]["syntax"] == "CII"
    assert result["einvoice"]["validation"]["valid"] is True
    assert "<rsm:CrossIndustryInvoice" in result["einvoice"]["xml"]
    assert "<ram:DuePayableAmount>" in result["einvoice"]["xml"]


def test_priority3_mapping_matrix_cii_parity_for_references_and_base_quantity() -> None:
    payload = {
        **_base_payload(),
        "buyer_electronic_address": "leitweg-4711",
        "buyer_electronic_address_scheme": "0204",
        "seller_electronic_address": "rechnung@steinbau-real.de",
        "seller_electronic_address_scheme": "EM",
        "purchase_order_reference": "PO-2026-77",
        "contract_reference": "CTR-2026-12",
        "project_reference": "PRJ-ALPHA",
        "original_invoice_number": "INV-ALT-100",
        "payment_terms": "Zahlbar innerhalb von 10 Tagen ohne Abzug.",
        "prepaid_amount": "50.00",
        "rounding_amount": "0.01",
        "positions": [
            {
                "name": "Naturstein nach Preisbasismenge",
                "quantity": "250",
                "unit_code": "KGM",
                "price_net": "40.00",
                "price_base_quantity": "100",
                "price_base_quantity_unit_code": "KGM",
                "vat_rate": "19",
            }
        ],
        "einvoice": {"enabled": True, "standard": "xrechnung", "syntax": "CII"},
    }

    result = _execute(payload)

    assert "error" not in result
    xml = result["einvoice"]["xml"]
    assert '<ram:URIID schemeID="EM">rechnung@steinbau-real.de</ram:URIID>' in xml
    assert '<ram:URIID schemeID="0204">leitweg-4711</ram:URIID>' in xml
    assert '<ram:BuyerOrderReferencedDocument>' in xml
    assert '<ram:ContractReferencedDocument>' in xml
    assert '<ram:SpecifiedProcuringProject>' in xml
    assert '<ram:InvoiceReferencedDocument>' in xml
    assert '<ram:BasisQuantity unitCode="KGM">100</ram:BasisQuantity>' in xml or '<ram:BasisQuantity unitCode="KGM">100.000</ram:BasisQuantity>' in xml
    assert '<ram:RoundingAmount>0.01</ram:RoundingAmount>' in xml
    assert '<ram:TotalPrepaidAmount>50.00</ram:TotalPrepaidAmount>' in xml


def test_priority3_mapping_matrix_cii_reverse_charge_and_exemption() -> None:
    payload = {
        **_base_payload(),
        "buyer_electronic_address": "leitweg-4711",
        "buyer_electronic_address_scheme": "0204",
        "seller_electronic_address": "rechnung@steinbau-real.de",
        "seller_electronic_address_scheme": "EM",
        "positions": [
            {
                "name": "Montageleistung Reverse Charge",
                "quantity": "1",
                "unit_code": "HUR",
                "price_net": "100.00",
                "vat_category": "AE",
                "vat_rate": "0",
                "tax_exemption_reason": "Reverse charge",
            },
            {
                "name": "Steuerbefreite Nebenleistung",
                "quantity": "1",
                "unit_code": "C62",
                "price_net": "50.00",
                "vat_category": "E",
                "vat_rate": "0",
                "tax_exemption_reason": "Steuerfreie Ausfuhrlieferung",
                "tax_exemption_reason_code": "VATEX-EU-132",
            },
        ],
        "einvoice": {"enabled": True, "standard": "xrechnung", "syntax": "CII"},
    }

    result = _execute(payload)

    assert "error" not in result
    xml = result["einvoice"]["xml"]
    assert '<ram:CategoryCode>AE</ram:CategoryCode>' in xml
    assert '<ram:ExemptionReason>Reverse charge</ram:ExemptionReason>' in xml
    assert '<ram:CategoryCode>E</ram:CategoryCode>' in xml
    assert '<ram:ExemptionReasonCode>VATEX-EU-132</ram:ExemptionReasonCode>' in xml