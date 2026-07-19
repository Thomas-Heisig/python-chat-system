from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path
from typing import Any

from plugins.business_letter.constants import PLACEHOLDER_PATTERNS


def _clean(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        return default
    return "" if any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS) else text


@lru_cache(maxsize=1)
def _system_logo_data_url() -> str:
    candidate = Path(__file__).resolve().parents[3] / "frontend" / "public" / "kernschmiede-logo.svg"
    try:
        svg_text = candidate.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not svg_text:
        return ""
    encoded = base64.b64encode(svg_text.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_company_settings(runtime_settings: dict[str, Any]) -> dict[str, str]:
    registry_legacy = str(runtime_settings.get("company_registry") or "").strip()
    bank_legacy = str(runtime_settings.get("company_bank") or "").strip()

    registry_number = str(runtime_settings.get("company_registry_number") or "").strip()
    registry_court = str(runtime_settings.get("company_registry_court") or "").strip()
    if not registry_number and registry_legacy:
        registry_number = registry_legacy
    if not registry_court and "·" in registry_legacy:
        registry_court = registry_legacy.split("·", maxsplit=1)[1].strip()

    bank_name = str(runtime_settings.get("company_bank_name") or "").strip()
    iban = str(runtime_settings.get("company_iban") or "").strip()
    bic = str(runtime_settings.get("company_bic") or "").strip()
    account_holder = str(runtime_settings.get("company_account_holder") or "").strip()
    if not bank_name and bank_legacy:
        bank_name = bank_legacy

    configured_logo_url = _clean(runtime_settings.get("company_logo_url"))
    system_logo_data_url = _system_logo_data_url()
    logo_url = configured_logo_url or system_logo_data_url
    logo_origin = "custom" if configured_logo_url else ("system" if system_logo_data_url else "unset")

    return {
        "logo_url": logo_url,
        "logo_origin": logo_origin,
        "logo_fallback_text": "Kernschmiede" if logo_origin == "system" else "",
        "name": _clean(runtime_settings.get("company_name")),
        "street": _clean(runtime_settings.get("company_street")),
        "zip": _clean(runtime_settings.get("company_zip")),
        "city": _clean(runtime_settings.get("company_city")),
        "country": _clean(runtime_settings.get("company_country")),
        "postbox": _clean(runtime_settings.get("company_postbox")),
        "phone": _clean(runtime_settings.get("company_phone")),
        "mobile": _clean(runtime_settings.get("company_mobile")),
        "fax": _clean(runtime_settings.get("company_fax")),
        "email": _clean(runtime_settings.get("company_email")),
        "electronic_address": _clean(runtime_settings.get("company_electronic_address")),
        "electronic_address_scheme": _clean(runtime_settings.get("company_electronic_address_scheme")),
        "email_reply_to": _clean(runtime_settings.get("company_email_reply_to") or runtime_settings.get("company_email")),
        "email_bcc": _clean(runtime_settings.get("company_email_bcc")),
        "website": _clean(runtime_settings.get("company_website")),
        "tax_id": _clean(runtime_settings.get("company_tax_id")),
        "vat_id": _clean(runtime_settings.get("company_vat_id")),
        "legal_form": _clean(runtime_settings.get("company_legal_form")),
        "registry_number": _clean(registry_number),
        "registry_court": _clean(registry_court),
        "responsible_content": _clean(runtime_settings.get("company_responsible_content")),
        "manager": _clean(runtime_settings.get("company_manager")),
        "chamber": _clean(runtime_settings.get("company_chamber")),
        "profession": _clean(runtime_settings.get("company_profession")),
        "bank_name": _clean(bank_name),
        "iban": _clean(iban),
        "bic": _clean(bic),
        "account_holder": _clean(account_holder or runtime_settings.get("company_name")),
        "agb": _clean(runtime_settings.get("company_agb")),
        "privacy": _clean(runtime_settings.get("company_privacy")),
        "base_intro_text": _clean(runtime_settings.get("base_intro_text")) or "vielen Dank für Ihre Anfrage.",
        "base_closing_text": _clean(runtime_settings.get("base_closing_text")) or "Mit freundlichen Grüßen",
        "base_missing_info_text": _clean(runtime_settings.get("base_missing_info_text")) or "Bitte reichen Sie fehlende Angaben nach, damit wir die Bearbeitung abschließen können.",
        "default_signatory_name": _clean(runtime_settings.get("default_signatory_name")) or _clean(runtime_settings.get("company_manager")),
        "default_signatory_position": _clean(runtime_settings.get("default_signatory_position")) or _clean(runtime_settings.get("company_profession")),
        "default_language": _clean(runtime_settings.get("default_language")) or "de",
        "default_tone": _clean(runtime_settings.get("default_tone")) or "professionell_freundlich",
        "default_cc": _clean(runtime_settings.get("default_cc")),
        "default_email_subject_template": _clean(runtime_settings.get("default_email_subject_template")) or "{document_kind} {document_number}",
        "default_reply_to_address": _clean(runtime_settings.get("default_reply_to_address") or runtime_settings.get("company_email_reply_to") or runtime_settings.get("company_email")),
        "default_email_html_enabled": _clean(runtime_settings.get("default_email_html_enabled")) or "true",
        "default_attach_pdf": _clean(runtime_settings.get("default_attach_pdf")) or "true",
        "default_attach_xml": _clean(runtime_settings.get("default_attach_xml")) or "false",
        "default_salutation": _clean(runtime_settings.get("default_salutation")) or "Sehr geehrte Damen und Herren,",
        "default_email_greeting": _clean(runtime_settings.get("default_email_greeting")) or "Guten Tag,",
        "default_email_signature": _clean(runtime_settings.get("default_email_signature")) or "Mit freundlichen Grüßen\nMax Mustermann\nSteinmetz- und Steinbildhauermeister",
        "default_email_disclaimer": _clean(runtime_settings.get("default_email_disclaimer")),
        "default_confidentiality_notice": _clean(runtime_settings.get("default_confidentiality_notice")),
        "text_natural_material_notice": _clean(runtime_settings.get("text_natural_material_notice")),
        "text_external_trades_notice": _clean(runtime_settings.get("text_external_trades_notice")),
        "text_measurement_notice": _clean(runtime_settings.get("text_measurement_notice")),
        "default_currency": _clean(runtime_settings.get("default_currency")) or "EUR",
        "default_payment_terms": _clean(runtime_settings.get("default_payment_terms")),
        "default_payment_method_code": _clean(runtime_settings.get("default_payment_method_code")) or "58",
        "default_payment_days": _clean(runtime_settings.get("default_payment_days")) or "14",
        "default_buyer_reference": _clean(runtime_settings.get("default_buyer_reference")),
        "default_payment_reference": _clean(runtime_settings.get("default_payment_reference")),
        "default_country_code": _clean(runtime_settings.get("default_country_code")) or "DE",
        "default_unit_code": _clean(runtime_settings.get("default_unit_code")) or "C62",
        "default_tax_rate": _clean(runtime_settings.get("default_tax_rate")) or "19",
        "default_tax_category": _clean(runtime_settings.get("default_tax_category")) or "S",
        "default_tax_exemption_enabled": _clean(runtime_settings.get("default_tax_exemption_enabled")) or "false",
        "default_tax_exemption_reason": _clean(runtime_settings.get("default_tax_exemption_reason")),
        "default_tax_exemption_reason_code": _clean(runtime_settings.get("default_tax_exemption_reason_code")),
        "default_reverse_charge_enabled": _clean(runtime_settings.get("default_reverse_charge_enabled")) or "false",
        "default_reverse_charge_note": _clean(runtime_settings.get("default_reverse_charge_note")) or "Reverse charge",
        "default_cash_discount_percent": _clean(runtime_settings.get("default_cash_discount_percent")),
        "default_cash_discount_days": _clean(runtime_settings.get("default_cash_discount_days")),
        "default_dunning_fee": _clean(runtime_settings.get("default_dunning_fee")),
        "default_late_interest_rate": _clean(runtime_settings.get("default_late_interest_rate")),
        "dual_save_enabled": _clean(runtime_settings.get("dual_save_enabled")) or "false",
        "dual_save_failure_mode": _clean(runtime_settings.get("dual_save_failure_mode")) or "warn",
        "dual_save_retry_attempts": _clean(runtime_settings.get("dual_save_retry_attempts")) or "3",
        "guest_system_database_mode": _clean(runtime_settings.get("guest_system_database_mode")) or "sqlite",
        "artifact_directory": _clean(runtime_settings.get("artifact_directory")),
        "retention_days": _clean(runtime_settings.get("retention_days")) or "3650",
        "enable_document_versioning": _clean(runtime_settings.get("enable_document_versioning")) or "true",
        "enable_hash_verification": _clean(runtime_settings.get("enable_hash_verification")) or "true",
        "lock_released_documents": _clean(runtime_settings.get("lock_released_documents")) or "true",
        "store_validation_reports": _clean(runtime_settings.get("store_validation_reports")) or "true",
        "archive_pdf_xml_together": _clean(runtime_settings.get("archive_pdf_xml_together")) or "true",
        "default_filename_pattern": _clean(runtime_settings.get("default_filename_pattern")) or "{document_number}",
        "layout_template": _clean(runtime_settings.get("layout_template")) or "classic",
        "logo_strict_mode": _clean(runtime_settings.get("logo_strict_mode")) or "false",
        "logo_max_bytes": _clean(runtime_settings.get("logo_max_bytes")) or "1048576",
        "logo_width_mm": _clean(runtime_settings.get("logo_width_mm")) or "32",
        "logo_position": _clean(runtime_settings.get("logo_position")) or "left",
        "page_margin_mm": _clean(runtime_settings.get("page_margin_mm")) or "20",
        "default_font_family": _clean(runtime_settings.get("default_font_family")) or "Source Sans 3",
        "default_font_size_pt": _clean(runtime_settings.get("default_font_size_pt")) or "11",
        "accent_color": _clean(runtime_settings.get("accent_color")) or "#234662",
        "footer_text": _clean(runtime_settings.get("footer_text")),
        "show_page_numbers": _clean(runtime_settings.get("show_page_numbers")) or "true",
        "show_bank_details_in_footer": _clean(runtime_settings.get("show_bank_details_in_footer")) or "true",
        "show_legal_details_in_footer": _clean(runtime_settings.get("show_legal_details_in_footer")) or "true",
        "draft_watermark_text": _clean(runtime_settings.get("draft_watermark_text")) or "ENTWURF",
        "default_pdf_filename_pattern": _clean(runtime_settings.get("default_pdf_filename_pattern")) or "{document_number}.pdf",
        "default_einvoice_enabled": _clean(runtime_settings.get("default_einvoice_enabled")) or "false",
        "default_einvoice_standard": _clean(runtime_settings.get("default_einvoice_standard")) or "xrechnung",
        "default_einvoice_profile": _clean(runtime_settings.get("default_einvoice_profile")) or "en16931",
        "default_einvoice_syntax": _clean(runtime_settings.get("default_einvoice_syntax")) or "UBL",
        "validate_before_send": _clean(runtime_settings.get("validate_before_send")) or "true",
        "block_send_on_validation_error": _clean(runtime_settings.get("block_send_on_validation_error")) or "true",
    }


def build_recipient(data: dict[str, Any]) -> dict[str, str]:
    company = str(data.get("customer_company") or "").strip()
    fallback_name = str(data.get("customer_name") or "").strip()
    contact = str(data.get("customer_contact") or "").strip()
    first_name = str(data.get("customer_first_name") or "").strip()
    last_name = str(data.get("customer_last_name") or "").strip()
    title = str(data.get("customer_title") or "").strip()
    if not contact:
        contact = " ".join(item for item in [first_name, last_name] if item).strip()

    return {
        "company": company or fallback_name,
        "name": fallback_name or contact,
        "contact": contact,
        "title": title,
        "salutation": str(data.get("customer_salutation") or "").strip(),
        "street": str(data.get("customer_street") or "").strip(),
        "postal_code": str(data.get("customer_zip") or "").strip(),
        "city": str(data.get("customer_city") or "").strip(),
        "country": str(data.get("customer_country") or "").strip(),
        "email": str(data.get("recipient_email") or "").strip(),
        "electronic_address": str(data.get("buyer_electronic_address") or "").strip(),
        "electronic_address_scheme": str(data.get("buyer_electronic_address_scheme") or "").strip(),
    }


def build_salutation(data: dict[str, Any], company: dict[str, str]) -> str:
    salutation_type = str(data.get("customer_salutation") or "").strip()
    title = str(data.get("customer_title") or "").strip()
    last_name = str(data.get("customer_last_name") or "").strip()
    contact = str(data.get("customer_contact") or "").strip()

    if not last_name and contact:
        last_name = contact

    name = " ".join(part for part in [title, last_name] if part)

    if salutation_type == "Herr" and name:
        return f"Sehr geehrter Herr {name},"
    if salutation_type == "Frau" and name:
        return f"Sehr geehrte Frau {name},"
    if salutation_type == "Firma":
        return "Sehr geehrte Damen und Herren,"
    if salutation_type == "Divers" and name:
        return f"Guten Tag {name},"
    if salutation_type == "Neutral" and contact:
        return f"Guten Tag {contact},"
    if contact:
        return f"Guten Tag {contact},"
    return company["default_salutation"] or "Sehr geehrte Damen und Herren,"
