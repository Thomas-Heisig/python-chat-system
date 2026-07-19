from __future__ import annotations

import asyncio
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

import pytest

from plugins.business_letter.plugin import BusinessLetterPlugin


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "business_letter"


def _payload() -> dict[str, Any]:
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
        "document_number": "DOC-TEST-1001",
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
    return asyncio.run(BusinessLetterPlugin().execute(payload))


def _require_external_validators() -> bool:
    return str(os.getenv("REQUIRE_EXTERNAL_VALIDATORS", "")).strip() in {"1", "true", "TRUE", "yes", "on"}


def _verapdf_command(pdf_path: Path) -> list[str] | None:
    docker_cmd = str(os.getenv("VERAPDF_CMD", "")).strip()
    if docker_cmd:
        return [*shlex.split(docker_cmd), str(pdf_path)]
    verapdf = shutil.which("verapdf")
    if verapdf:
        return [verapdf, str(pdf_path)]
    return None


def _normalize_pdf_text(pdf_bytes: bytes) -> str:
    pdf_text = pdf_bytes.decode("latin-1", errors="ignore")
    pdf_text = re.sub(r"D:\\d{14}Z", "D:TIMESTAMPZ", pdf_text)
    pdf_text = re.sub(
        r"\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})?",
        "ISO_TIMESTAMP",
        pdf_text,
    )
    return pdf_text


def _load_expected_pdf_tokens() -> list[str]:
    content = (FIXTURE_DIR / "zugferd_expected_pdf_tokens.txt").read_text(encoding="utf-8")
    return [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]


def _official_kosit_fixture_dir() -> Path:
    return FIXTURE_DIR / "official" / "kosit" / "v2026-01-31"


def _official_kosit_cii_fixture_dir() -> Path:
    return FIXTURE_DIR / "official" / "kosit-cii" / "v2026-01-31"


def _official_validator_paths() -> tuple[Path, Path] | None:
    xsd_raw = os.getenv("XRECHNUNG_XSD_PATH", "").strip()
    schematron_raw = os.getenv("XRECHNUNG_SCHEMATRON_PATH", "").strip()
    if not xsd_raw or not schematron_raw:
        return None
    xsd_path = Path(xsd_raw)
    schematron_path = Path(schematron_raw)
    if not xsd_path.is_file() or not schematron_path.is_file():
        return None
    return xsd_path, schematron_path


def _official_cii_validator_paths() -> tuple[Path, Path] | None:
    xsd_raw = os.getenv("XRECHNUNG_CII_XSD_PATH", "").strip()
    schematron_raw = os.getenv("XRECHNUNG_CII_SCHEMATRON_PATH", "").strip()
    if not xsd_raw or not schematron_raw:
        return None
    xsd_path = Path(xsd_raw)
    schematron_path = Path(schematron_raw)
    if not xsd_path.is_file() or not schematron_path.is_file():
        return None
    return xsd_path, schematron_path


def test_zugferd_pdf_embeds_facturx_xml() -> None:
    result = _execute({**_payload(), "einvoice": {"enabled": True, "standard": "zugferd", "profile": "en16931"}})

    assert "error" not in result
    einvoice = result["einvoice"]
    pdf_bytes = bytes(einvoice["pdf"]["bytes"])
    pdf_text = pdf_bytes.decode("latin-1", errors="ignore")

    assert "/EmbeddedFile" in pdf_text
    assert "factur-x.xml" in pdf_text
    assert "/AFRelationship /Alternative" in pdf_text
    assert einvoice["profile"] == "EN 16931"


def test_xrechnung_includes_schema_and_schematron_validation_report() -> None:
    result = _execute({**_payload(), "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"}})

    assert "error" not in result
    einvoice = result["einvoice"]
    assert "schema_validation" in einvoice
    assert "schematron_validation" in einvoice
    assert isinstance(einvoice["schema_validation"].get("rules"), list)
    assert isinstance(einvoice["schematron_validation"].get("rules"), list)
    schema_rule_ids = {rule.get("rule_id") for rule in einvoice["schema_validation"]["rules"]}
    schematron_rule_ids = {rule.get("rule_id") for rule in einvoice["schematron_validation"]["rules"]}
    assert "XR-SCHEMA-006" in schema_rule_ids
    assert "XR-SCHEMA-007" in schema_rule_ids
    assert "XR-SCH-005" in schematron_rule_ids
    assert "XR-SCH-006" in schematron_rule_ids


def test_xrechnung_xml_contains_document_currency_and_invoice_lines() -> None:
    result = _execute(
        {
            **_payload(),
            "payment_method_code": "58",
            "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"},
        }
    )

    assert "error" not in result
    xml = str(result["einvoice"]["xml"])
    assert "<cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>" in xml
    assert "<cbc:PaymentMeansCode>58</cbc:PaymentMeansCode>" in xml
    assert "<cac:InvoiceLine>" in xml
    assert "<cbc:InvoicedQuantity unitCode=\"C62\">" in xml
    assert "<cbc:LineExtensionAmount currencyID=\"EUR\">199.90</cbc:LineExtensionAmount>" in xml


def test_xrechnung_validation_rejects_invalid_currency_code() -> None:
    result = _execute(
        {
            **_payload(),
            "currency": "FOO",
            "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"},
        }
    )

    validation = result["einvoice"]["validation"]
    assert validation["valid"] is False
    assert any(entry["code"] == "BR-CL-001" for entry in validation["errors"])


def test_xrechnung_validation_rejects_invalid_payment_means_code() -> None:
    result = _execute(
        {
            **_payload(),
            "payment_method_code": "999",
            "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"},
        }
    )

    validation = result["einvoice"]["validation"]
    assert validation["valid"] is False
    assert any(entry["code"] == "BR-CL-002" for entry in validation["errors"])


def test_xrechnung_validation_rejects_invalid_unit_code() -> None:
    payload = _payload()
    payload["positions"][0]["unit_code"] = "XXX"
    result = _execute({**payload, "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"}})

    validation = result["einvoice"]["validation"]
    assert validation["valid"] is False
    assert any(entry["code"] == "BR-CL-004" for entry in validation["errors"])


def test_xrechnung_validation_rejects_invalid_tax_category() -> None:
    payload = _payload()
    payload["positions"][0]["vat_category"] = "BAD"
    result = _execute({**payload, "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"}})

    validation = result["einvoice"]["validation"]
    assert validation["valid"] is False
    assert any(entry["code"] == "BR-CL-003" for entry in validation["errors"])


def test_golden_file_xml_matches_expected_output() -> None:
    result = _execute({**_payload(), "einvoice": {"enabled": True, "standard": "zugferd", "profile": "en16931"}})

    expected_xml = (FIXTURE_DIR / "zugferd_expected_invoice.xml").read_text(encoding="utf-8")
    actual_xml = str(result["einvoice"]["xml"])
    assert actual_xml.rstrip() == expected_xml.rstrip()


def test_golden_file_pdf_matches_expected_tokens() -> None:
    result = _execute({**_payload(), "einvoice": {"enabled": True, "standard": "zugferd", "profile": "en16931"}})

    normalized = _normalize_pdf_text(bytes(result["einvoice"]["pdf"]["bytes"]))
    expected_tokens = _load_expected_pdf_tokens()
    for token in expected_tokens:
        assert token in normalized


def test_external_xml_validator_if_available(tmp_path: Path) -> None:
    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    result = _execute({**_payload(), "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"}})
    xml_path = tmp_path / "invoice.xml"
    xml_path.write_text(str(result["einvoice"]["xml"]), encoding="utf-8")

    completed = subprocess.run([xmllint, "--noout", str(xml_path)], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr


def test_official_xrechnung_validation_executes_with_xsd_and_schematron(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    xsd_path = FIXTURE_DIR / "official" / "official-minimal-invoice.xsd"
    schematron_path = FIXTURE_DIR / "official" / "official-minimal-invoice.sch"
    monkeypatch.setenv("XRECHNUNG_XSD_PATH", str(xsd_path))
    monkeypatch.setenv("XRECHNUNG_SCHEMATRON_PATH", str(schematron_path))
    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(tmp_path))

    result = _execute({**_payload(), "einvoice": {"enabled": True, "standard": "xrechnung", "profile": "en16931"}})

    assert "error" not in result
    official = result["einvoice"]["official_validation"]
    assert official["executed"] is True
    assert official["valid"] is True
    assert official["schema"]["status"] == "passed"
    assert official["schematron"]["status"] == "passed"

    report_files = {path.name for path in tmp_path.iterdir() if path.is_file()}
    schema_report_file = str(official["schema"].get("report_file") or "")
    schematron_report_file = str(official["schematron"].get("report_file") or "")
    assert schema_report_file
    assert schematron_report_file
    assert schema_report_file in report_files
    assert schematron_report_file in report_files
    summary_report_file = schema_report_file.replace("_official_schema.txt", "_official_summary.json")
    assert summary_report_file in report_files


def test_external_pdfa_validator_if_available(tmp_path: Path) -> None:
    result = _execute({**_payload(), "einvoice": {"enabled": True, "standard": "zugferd", "profile": "en16931"}})
    pdf_path = tmp_path / "invoice.pdf"
    pdf_path.write_bytes(bytes(result["einvoice"]["pdf"]["bytes"]))

    verapdf_cmd = _verapdf_command(pdf_path)
    if not verapdf_cmd:
        if _require_external_validators():
            pytest.fail("veraPDF command is required but not available")
        pytest.skip("veraPDF not available in environment")

    completed = subprocess.run(verapdf_cmd, capture_output=True, text=True)
    report_dir = os.getenv("VERAPDF_REPORT_DIR", "").strip()
    if report_dir:
        report_path = Path(report_dir)
        report_path.mkdir(parents=True, exist_ok=True)
        (report_path / "verapdf-report.txt").write_text(
            (completed.stdout or "") + "\n" + (completed.stderr or ""),
            encoding="utf-8",
        )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_official_reference_valid_example_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from plugins.business_letter.einvoice.official_validation import validate_xrechnung_official_conformance

    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    xsd_path = FIXTURE_DIR / "official" / "official-minimal-invoice.xsd"
    schematron_path = FIXTURE_DIR / "official" / "official-minimal-invoice.sch"
    xml_payload = (FIXTURE_DIR / "official" / "reference-valid-invoice.xml").read_text(encoding="utf-8")
    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(tmp_path))

    result = validate_xrechnung_official_conformance(
        xml_payload,
        xsd_path=str(xsd_path),
        schematron_path=str(schematron_path),
        report_prefix="official_reference_valid",
    )

    assert result["executed"] is True
    assert result["valid"] is True
    assert result["status"] == "passed"
    assert result.get("rule_ids") == []
    classification = result.get("classification", {})
    assert isinstance(classification, dict)
    assert classification.get("schematron") is False


def test_official_reference_invalid_example_reports_rule_ids_and_classes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from plugins.business_letter.einvoice.official_validation import validate_xrechnung_official_conformance

    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    xsd_path = FIXTURE_DIR / "official" / "official-minimal-invoice.xsd"
    schematron_path = FIXTURE_DIR / "official" / "official-minimal-invoice.sch"
    xml_payload = (FIXTURE_DIR / "official" / "reference-invalid-invoice.xml").read_text(encoding="utf-8")
    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(tmp_path))

    result = validate_xrechnung_official_conformance(
        xml_payload,
        xsd_path=str(xsd_path),
        schematron_path=str(schematron_path),
        report_prefix="official_reference_invalid",
    )

    assert result["executed"] is True
    assert result["valid"] is False
    assert result["status"] == "failed"
    rule_ids = [str(item) for item in result.get("rule_ids", [])]
    assert any(item.startswith("BR-DE-") for item in rule_ids)
    assert any("EN16931" in item for item in rule_ids)
    classification = result.get("classification", {})
    assert classification.get("schematron") is True
    assert classification.get("en16931") is True
    assert classification.get("xrechnung_specific") is True


@pytest.mark.parametrize(
    ("fixture_name", "required_markers"),
    [
        (
            "01.05_minimal_test_ubl.xml",
            [
                '<cbc:BuyerReference>',
                '<cbc:EndpointID schemeID="EM">rechnungsausgang@test.com</cbc:EndpointID>',
            ],
        ),
        (
            "01.01_comprehensive_test_ubl.xml",
            [
                '<cac:OrderReference>',
                '<cac:BillingReference>',
                '<cac:ProjectReference>',
            ],
        ),
        (
            "03.07a-INVOICE_ubl.xml",
            [
                '<cbc:CustomizationID>',
                '<cac:AccountingSupplierParty>',
                '<cac:AccountingCustomerParty>',
            ],
        ),
    ],
)
def test_official_kosit_valid_reference_cases_pass_with_pinned_assets(
    fixture_name: str,
    required_markers: list[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from plugins.business_letter.einvoice.official_validation import validate_xrechnung_official_conformance

    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    validator_paths = _official_validator_paths()
    if validator_paths is None:
        if _require_external_validators():
            pytest.fail("Official XRechnung validator assets are required but not configured")
        pytest.skip("Official validator assets not configured")

    xml_payload = (_official_kosit_fixture_dir() / fixture_name).read_text(encoding="utf-8")
    for marker in required_markers:
        assert marker in xml_payload

    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(tmp_path))
    xsd_path, schematron_path = validator_paths
    result = validate_xrechnung_official_conformance(
        xml_payload,
        xsd_path=str(xsd_path),
        schematron_path=str(schematron_path),
        report_prefix=f"kosit_valid_{fixture_name.replace('.', '_')}",
    )

    assert result["executed"] is True
    assert result["valid"] is True
    assert result["status"] == "passed"
    assert result["schema"]["valid"] is True
    assert result["schematron"]["valid"] is True
    assert result.get("errors") == []


def test_official_kosit_invalid_derived_case_reports_expected_rule_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from plugins.business_letter.einvoice.official_validation import validate_xrechnung_official_conformance

    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    validator_paths = _official_validator_paths()
    if validator_paths is None:
        if _require_external_validators():
            pytest.fail("Official XRechnung validator assets are required but not configured")
        pytest.skip("Official validator assets not configured")

    xml_payload = (_official_kosit_fixture_dir() / "01.05_minimal_test_ubl.xml").read_text(encoding="utf-8")
    xml_payload = xml_payload.replace("<cbc:BuyerReference>90000000-03083-72</cbc:BuyerReference>", "<cbc:BuyerReference></cbc:BuyerReference>")
    xml_payload = xml_payload.replace('<cbc:EndpointID schemeID="EM">rechnungseingang@test.de</cbc:EndpointID>', "")
    xml_payload = xml_payload.replace('<cbc:EndpointID schemeID="EM">rechnungsausgang@test.com</cbc:EndpointID>', "")
    xml_payload = xml_payload.replace('<cbc:PayableAmount currencyID="EUR">4743.75</cbc:PayableAmount>', '<cbc:PayableAmount currencyID="EUR">4744.75</cbc:PayableAmount>')

    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(tmp_path))
    xsd_path, schematron_path = validator_paths
    result = validate_xrechnung_official_conformance(
        xml_payload,
        xsd_path=str(xsd_path),
        schematron_path=str(schematron_path),
        report_prefix="kosit_invalid_derived_01_05",
    )

    assert result["executed"] is True
    assert result["valid"] is False
    assert result["status"] == "failed"
    assert result["schema"]["valid"] is True
    assert result["schematron"]["valid"] is False

    rule_ids = set(str(item) for item in result.get("rule_ids", []))
    assert "BR-DE-15" in rule_ids
    assert "PEPPOL-EN16931-R010" in rule_ids
    assert "PEPPOL-EN16931-R020" in rule_ids
    assert "BR-DEX-09" in rule_ids

    classification = result.get("classification", {})
    assert classification.get("xsd") is False
    assert classification.get("schematron") is True
    assert classification.get("en16931") is True
    assert classification.get("xrechnung_specific") is True


@pytest.mark.parametrize(
    ("fixture_name", "required_markers"),
    [
        (
            "01.05_minimal_test_uncefact.xml",
            [
                '<rsm:CrossIndustryInvoice',
                '<ram:BuyerReference>90000000-03083-72</ram:BuyerReference>',
                '<ram:URIID schemeID="EM">rechnungsausgang@test.com</ram:URIID>',
            ],
        ),
        (
            "01.06_minimal_test_uncefact.xml",
            [
                '<rsm:CrossIndustryInvoice',
                '<ram:DuePayableAmount>4743.75</ram:DuePayableAmount>',
                '<ram:URIID schemeID="EM">rechnungseingang@test.de</ram:URIID>',
            ],
        ),
    ],
)
def test_official_kosit_cii_valid_reference_cases_pass_with_pinned_assets(
    fixture_name: str,
    required_markers: list[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from plugins.business_letter.einvoice.official_validation import validate_xrechnung_official_conformance

    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    validator_paths = _official_cii_validator_paths()
    if validator_paths is None:
        if _require_external_validators():
            pytest.fail("Official CII validator assets are required but not configured")
        pytest.skip("Official CII validator assets not configured")

    xml_payload = (_official_kosit_cii_fixture_dir() / fixture_name).read_text(encoding="utf-8")
    for marker in required_markers:
        assert marker in xml_payload

    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(tmp_path))
    xsd_path, schematron_path = validator_paths
    result = validate_xrechnung_official_conformance(
        xml_payload,
        xsd_path=str(xsd_path),
        schematron_path=str(schematron_path),
        report_prefix=f"kosit_cii_valid_{fixture_name.replace('.', '_')}",
        syntax="CII",
    )

    assert result["executed"] is True
    assert result["valid"] is True
    assert result["status"] == "passed"
    assert result["schema"]["valid"] is True
    assert result["schematron"]["valid"] is True
    assert result.get("errors") == []


def test_official_kosit_cii_invalid_derived_case_reports_expected_rule_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from plugins.business_letter.einvoice.official_validation import validate_xrechnung_official_conformance

    xmllint = shutil.which("xmllint")
    if not xmllint:
        if _require_external_validators():
            pytest.fail("xmllint is required but not available")
        pytest.skip("xmllint not available in environment")

    validator_paths = _official_cii_validator_paths()
    if validator_paths is None:
        if _require_external_validators():
            pytest.fail("Official CII validator assets are required but not configured")
        pytest.skip("Official CII validator assets not configured")

    xml_payload = (_official_kosit_cii_fixture_dir() / "01.05_minimal_test_uncefact.xml").read_text(encoding="utf-8")
    xml_payload = xml_payload.replace("<ram:BuyerReference>90000000-03083-72</ram:BuyerReference>", "<ram:BuyerReference></ram:BuyerReference>")
    xml_payload = xml_payload.replace('<ram:URIID schemeID="EM">rechnungeingang@test.de</ram:URIID>', '<ram:URIID schemeID="EM">rechnungeingang@test.de</ram:URIID>')
    xml_payload = xml_payload.replace('<ram:URIID schemeID="EM">rechnungseingang@test.de</ram:URIID>', "")
    xml_payload = xml_payload.replace('<ram:URIID schemeID="EM">rechnungsausgang@test.com</ram:URIID>', "")
    xml_payload = xml_payload.replace('<ram:DuePayableAmount>4743.75</ram:DuePayableAmount>', '<ram:DuePayableAmount>4744.75</ram:DuePayableAmount>')

    monkeypatch.setenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", str(tmp_path))
    xsd_path, schematron_path = validator_paths
    result = validate_xrechnung_official_conformance(
        xml_payload,
        xsd_path=str(xsd_path),
        schematron_path=str(schematron_path),
        report_prefix="kosit_cii_invalid_derived_01_05",
        syntax="CII",
    )

    assert result["executed"] is True
    assert result["valid"] is False
    assert result["status"] == "failed"
    assert result["schema"]["valid"] is True
    assert result["schematron"]["valid"] is False

    rule_ids = set(str(item) for item in result.get("rule_ids", []))
    assert "BR-DE-15" in rule_ids
    assert "PEPPOL-EN16931-R010" in rule_ids
    assert "PEPPOL-EN16931-R020" in rule_ids
    assert "BR-DEX-09" in rule_ids


def test_persist_to_plugin_and_guest_system_sqlite(tmp_path: Path) -> None:
    guest_db = tmp_path / "guest_system.db"
    payload = {
        **_payload(),
        "document_number": "",
        "persist_to_database": True,
        "guest_system_database_path": str(guest_db),
        "plugin_settings": {
            **_payload()["plugin_settings"],
            "dual_save_enabled": True,
        },
        "einvoice": {"enabled": True, "standard": "zugferd", "profile": "en16931"},
    }
    result = _execute(payload)

    assert "error" not in result
    persisted = result["database"]["persisted"]
    assert "plugin_storage" in persisted
    assert "guest_system_storage" in persisted
    assert guest_db.exists()

    with sqlite3.connect(guest_db) as connection:
        doc_count = connection.execute("SELECT COUNT(*) FROM guest_business_letter_documents").fetchone()[0]
        artifact_count = connection.execute("SELECT COUNT(*) FROM guest_business_letter_artifacts").fetchone()[0]

    assert doc_count >= 1
    assert artifact_count >= 1
