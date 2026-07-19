from __future__ import annotations

import base64
import hashlib
import html
import json
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import os
from pathlib import Path
import re
from typing import Any, cast
from uuid import uuid4

from plugins.business_letter.einvoice import build_xrechnung_xml, build_zugferd_package
from plugins.business_letter.models.commercial import build_commercial_document, normalize_document_kind
from plugins.business_letter.models.communication import contains_placeholder, normalize_attachments, normalize_letter_type, resolve_body_paragraphs
from plugins.business_letter.models.parties import build_company_settings, build_recipient, build_salutation
from plugins.business_letter.renderers.html import build_document_html
from plugins.business_letter.renderers.text import render_plain_letter
from plugins.business_letter.services.artifacts import DEFAULT_PERSISTENCE, build_artifacts, build_database_payload, build_pdf_payload, render_artifact_file_name
from plugins.business_letter.services.calculation import normalize_money_adjustments as service_normalize_money_adjustments, normalize_positions as service_normalize_positions
from plugins.business_letter.services.conversion import apply_conversion_action, build_quantity_chain_snapshot
from plugins.business_letter.services.numbering import NumberSequenceStore
from plugins.business_letter.settings import public_settings, resolve_number_sequence_settings, resolve_settings
from plugins.business_letter.services.templates import build_template_payload


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PLACEHOLDER_PATTERNS = [
    re.compile(r"(?i)musterstra(?:s|ß)e"),
    re.compile(r"(?i)max\s+mustermann"),
    re.compile(r"(?i)DE123456789"),
]

MONEY_QUANT = Decimal("0.01")
QUANTITY_QUANT = Decimal("0.001")
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")

COMMUNICATION_DOCUMENT_TYPES = {
    "allgemein",
    "anfrage",
    "angebotsanfrage",
    "angebotserinnerung",
    "angebotsstornierung",
    "bestellbestaetigung",
    "auftragsaenderung",
    "auftragsstornierung",
    "terminbestaetigung",
    "terminverschiebung",
    "lieferankuendigung",
    "versandanzeige",
    "fertigstellungsanzeige",
    "abnahme",
    "abnahmeprotokoll",
    "rechnung_begleitschreiben",
    "zahlungserinnerung",
    "mahnung_1",
    "mahnung_2",
    "mahnung_3",
    "inkassouebergabe",
    "verzugszinsberechnung",
    "reklamation_eingang",
    "reklamation_antwort",
    "reklamation",
    "maengelanzeige",
    "nachbesserung",
    "stornobestaetigung",
    "vertragsaenderung",
    "vertragsbegleitschreiben",
    "fehlende_angaben",
    "dokumentenanforderung",
    "zahlungsavis",
    "kontoauszug",
    "zahlungsbestaetigung",
    "servicebericht",
    "montagebericht",
    "wartungsprotokoll",
    "retourenschein",
    "lieferantenreklamation",
    "anschreiben",
    "serienbrief",
    "kuendigung",
    "empfangsbestaetigung",
}

COMMERCIAL_DOCUMENT_TYPES = {
    "angebot",
    "angebot_treppe",
    "preisangebot",
    "angebotsaenderung",
    "auftragsbestaetigung",
    "kostenvoranschlag",
    "lieferschein",
    "teillieferschein",
    "sammellieferschein",
    "abschlagsrechnung",
    "anzahlungsanforderung",
    "schlussrechnung",
    "rechnung",
    "proformarechnung",
    "gutschrift",
    "stornorechnung",
    "belastungsanzeige",
    "bestellung",
    "bestellaenderung",
    "bestellstornierung",
    "wareneingang",
}

TEMPLATE_MODES = {"auto", "brief", "email", "both", "document"}

STONE_DETAILS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "material_type": {"type": "string"},
        "trade_name": {"type": "string"},
        "origin": {"type": "string"},
        "color": {"type": "string"},
        "surface_finish": {"type": "string"},
        "thickness_mm": {"type": ["string", "number"]},
        "length_mm": {"type": ["string", "number"]},
        "width_mm": {"type": ["string", "number"]},
        "square_meters": {"type": ["string", "number"]},
        "linear_meters": {"type": ["string", "number"]},
        "piece_count": {"type": ["string", "number"]},
        "edge_profile": {"type": "string"},
        "cutouts": {"type": "string"},
        "drillings": {"type": "string"},
        "batch": {"type": "string"},
        "block_number": {"type": "string"},
        "waste_factor": {"type": ["string", "number"]},
        "measurement_number": {"type": "string"},
        "installation_location": {"type": "string"},
    },
}

POSITION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "line_id": {"type": "string"},
        "article_number": {"type": "string"},
        "seller_item_id": {"type": "string"},
        "buyer_item_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "quantity": {"type": ["string", "number"]},
        "unit_code": {"type": "string"},
        "unit_label": {"type": "string"},
        "price_net": {"type": ["string", "number"]},
        "price_base_quantity": {"type": ["string", "number"], "default": "1"},
        "price_base_quantity_unit_code": {"type": "string"},
        "vat_category": {"type": "string"},
        "vat_rate": {"type": ["string", "number"]},
        "tax_exemption_reason": {"type": "string"},
        "tax_exemption_reason_code": {"type": "string"},
        "allowances": {"type": "array", "items": {"type": "object"}},
        "charges": {"type": "array", "items": {"type": "object"}},
        "service_period_start": {"type": "string"},
        "service_period_end": {"type": "string"},
        "project_reference": {"type": "string"},
        "accounting_cost": {"type": "string"},
        "material": {"type": "object"},
        "stone_details": STONE_DETAILS_SCHEMA,
    },
    "required": ["line_id", "name", "quantity", "unit_code", "price_net", "vat_category", "vat_rate"],
}

IMAGE_UPLOAD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "name": {"type": "string"},
        "file_name": {"type": "string"},
        "mime_type": {"type": "string"},
        "content_base64": {"type": "string"},
        "data_url": {"type": "string"},
        "url": {"type": "string"},
    },
    "required": ["name"],
}


def _as_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in cast(dict[object, Any], value).items()}


def _money(value: Any) -> Decimal:
    return Decimal(str(value or "0")).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _escape_html_lines(text: str) -> str:
    blocks = re.split(r"\n\s*\n", text.strip()) if text.strip() else []
    rendered: list[str] = []
    for block in blocks:
        escaped = html.escape(block.strip()).replace("\n", "<br>")
        rendered.append(f"<p>{escaped}</p>")
    return "\n".join(rendered)


EAS_SCHEME_OPTIONS: list[dict[str, str]] = [
    {"label": "EM - E-Mail", "value": "EM"},
    {"label": "0204 - Leitweg-ID", "value": "0204"},
    {"label": "0088 - GLN", "value": "0088"},
    {"label": "0002 - System interne Kennung", "value": "0002"},
]

TAX_CATEGORY_OPTIONS: list[dict[str, str]] = [
    {"label": "S - Standardbesteuert", "value": "S"},
    {"label": "AE - Reverse Charge", "value": "AE"},
    {"label": "E - Steuerbefreit", "value": "E"},
    {"label": "Z - Nullsteuersatz", "value": "Z"},
    {"label": "O - Nicht steuerbar", "value": "O"},
    {"label": "K - Innergemeinschaftliche Lieferung", "value": "K"},
    {"label": "G - Export / Ausfuhr", "value": "G"},
]

TAX_EXEMPTION_CODE_OPTIONS: list[dict[str, str]] = [
    {"label": "Kein Standardcode", "value": ""},
    {"label": "VATEX-EU-AE - Reverse Charge", "value": "VATEX-EU-AE"},
    {"label": "VATEX-EU-132 - Steuerbefreite Lieferung", "value": "VATEX-EU-132"},
    {"label": "VATEX-EU-I - Innergemeinschaftliche Lieferung", "value": "VATEX-EU-I"},
    {"label": "VATEX-EU-O - Nicht steuerbarer Umsatz", "value": "VATEX-EU-O"},
]

COUNTRY_CODE_OPTIONS: list[dict[str, str]] = [
    {"label": "DE - Deutschland", "value": "DE"},
    {"label": "AT - Österreich", "value": "AT"},
    {"label": "CH - Schweiz", "value": "CH"},
    {"label": "BE - Belgien", "value": "BE"},
    {"label": "NL - Niederlande", "value": "NL"},
    {"label": "LU - Luxemburg", "value": "LU"},
]

UNIT_CODE_OPTIONS: list[dict[str, str]] = [
    {"label": "C62 - Stück", "value": "C62"},
    {"label": "MTK - Quadratmeter", "value": "MTK"},
    {"label": "LM - Laufmeter", "value": "LM"},
    {"label": "KGM - Kilogramm", "value": "KGM"},
    {"label": "H87 - Satz", "value": "H87"},
]

INVOICE_TYPE_OPTIONS: list[dict[str, str]] = [
    {"label": "380 - Rechnung", "value": "380"},
    {"label": "326 - Abschlagsrechnung", "value": "326"},
    {"label": "875 - Schlussrechnung", "value": "875"},
    {"label": "381 - Gutschrift / Storno", "value": "381"},
]
_SENSITIVE_SETTING_KEY_PATTERN = re.compile(r"(?i)(password|secret|token|api[_-]?key)")

_DOCUMENT_KIND_SETTING_ALIASES = {
    "angebot_treppe": "angebot",
    "preisangebot": "angebot",
    "angebotsaenderung": "angebot",
    "angebotsstornierung": "angebot",
    "mahnung_1": "mahnung",
    "mahnung_2": "mahnung",
    "mahnung_3": "mahnung",
    "zahlungserinnerung": "mahnung",
    "inkassouebergabe": "mahnung",
    "verzugszinsberechnung": "mahnung",
    "bestellbestaetigung": "auftragsbestaetigung",
    "auftragsaenderung": "auftragsbestaetigung",
    "auftragsstornierung": "auftragsbestaetigung",
    "teillieferschein": "lieferschein",
    "sammellieferschein": "lieferschein",
    "versandanzeige": "lieferschein",
    "proformarechnung": "rechnung",
    "belastungsanzeige": "rechnung",
    "zahlungsavis": "rechnung",
    "kontoauszug": "rechnung",
    "zahlungsbestaetigung": "rechnung",
    "anzahlungsanforderung": "abschlagsrechnung",
}

DOCUMENT_TYPE_RULES: dict[str, dict[str, Any]] = {
    "anfrage": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "angebotsanfrage": {
        "requires_positions": False,
        "requires_offer_valid_until": True,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "angebot": {
        "requires_positions": False,
        "requires_offer_valid_until": True,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "angebot_treppe": {
        "inherits": "angebot",
    },
    "preisangebot": {
        "inherits": "angebot",
    },
    "angebotsaenderung": {
        "inherits": "angebot",
    },
    "angebotsstornierung": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["offer_number"],
    },
    "bestellbestaetigung": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["order_number"],
    },
    "auftragsbestaetigung": {
        "inherits": "bestellbestaetigung",
    },
    "auftragsaenderung": {
        "inherits": "bestellbestaetigung",
    },
    "auftragsstornierung": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["order_number"],
    },
    "lieferschein": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": True,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "teillieferschein": {
        "inherits": "lieferschein",
    },
    "sammellieferschein": {
        "inherits": "lieferschein",
    },
    "versandanzeige": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": True,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "proformarechnung": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "anzahlungsanforderung": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": True,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "rechnung": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": True,
        "requires_delivery_date": False,
        "supports_einvoice": True,
        "required_fields": [],
    },
    "abschlagsrechnung": {
        "inherits": "rechnung",
    },
    "schlussrechnung": {
        "inherits": "rechnung",
    },
    "gutschrift": {
        "inherits": "rechnung",
    },
    "stornorechnung": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": True,
        "requires_delivery_date": False,
        "supports_einvoice": True,
        "required_fields": ["original_invoice_number"],
    },
    "belastungsanzeige": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": True,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "zahlungsavis": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["payment_reference"],
    },
    "kontoauszug": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "zahlungsbestaetigung": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["payment_reference"],
    },
    "zahlungserinnerung": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": True,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["invoice_number", "invoice_date", "invoice_amount", "due_date"],
    },
    "mahnung_1": {
        "inherits": "zahlungserinnerung",
    },
    "mahnung_2": {
        "inherits": "zahlungserinnerung",
    },
    "mahnung_3": {
        "inherits": "zahlungserinnerung",
    },
    "inkassouebergabe": {
        "inherits": "zahlungserinnerung",
    },
    "verzugszinsberechnung": {
        "inherits": "zahlungserinnerung",
    },
    "bestellung": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": True,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "bestellaenderung": {
        "inherits": "bestellung",
    },
    "bestellstornierung": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["order_number"],
    },
    "wareneingang": {
        "requires_positions": True,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": True,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "lieferantenreklamation": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["content"],
    },
    "kostenvoranschlag": {
        "requires_positions": True,
        "requires_offer_valid_until": True,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "servicebericht": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": True,
        "supports_einvoice": False,
        "required_fields": ["content"],
    },
    "montagebericht": {
        "inherits": "servicebericht",
    },
    "abnahmeprotokoll": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": True,
        "supports_einvoice": False,
        "required_fields": ["content"],
    },
    "wartungsprotokoll": {
        "inherits": "servicebericht",
    },
    "reklamation": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": ["content"],
    },
    "retourenschein": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": True,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "anschreiben": {
        "requires_positions": False,
        "requires_offer_valid_until": False,
        "requires_due_date": False,
        "requires_delivery_date": False,
        "supports_einvoice": False,
        "required_fields": [],
    },
    "serienbrief": {
        "inherits": "anschreiben",
    },
    "vertragsbegleitschreiben": {
        "inherits": "anschreiben",
    },
    "kuendigung": {
        "inherits": "anschreiben",
        "required_fields": ["content"],
    },
    "empfangsbestaetigung": {
        "inherits": "anschreiben",
    },
    "reklamation_eingang": {
        "inherits": "reklamation",
    },
    "reklamation_antwort": {
        "inherits": "reklamation",
    },
    "maengelanzeige": {
        "inherits": "reklamation",
    },
    "nachbesserung": {
        "inherits": "servicebericht",
    },
    "stornobestaetigung": {
        "inherits": "anschreiben",
    },
    "vertragsaenderung": {
        "inherits": "anschreiben",
    },
    "fehlende_angaben": {
        "inherits": "anschreiben",
    },
    "dokumentenanforderung": {
        "inherits": "anschreiben",
    },
    "terminbestaetigung": {
        "inherits": "anschreiben",
        "required_fields": ["delivery_date"],
    },
    "terminverschiebung": {
        "inherits": "anschreiben",
        "required_fields": ["delivery_date"],
    },
    "lieferankuendigung": {
        "inherits": "versandanzeige",
    },
    "fertigstellungsanzeige": {
        "inherits": "servicebericht",
    },
    "abnahme": {
        "inherits": "abnahmeprotokoll",
    },
    "rechnung_begleitschreiben": {
        "inherits": "anschreiben",
        "required_fields": ["invoice_number"],
    },
    "allgemein": {
        "inherits": "anschreiben",
    },
}

DOCUMENT_TYPE_FIELD_LABELS: dict[str, str] = {
    "offer_valid_until": "Angebotsgültigkeit",
    "due_date": "Fälligkeit",
    "delivery_date": "Lieferdatum",
    "invoice_number": "Rechnungsnummer",
    "invoice_date": "Rechnungsdatum",
    "invoice_amount": "Rechnungsbetrag",
    "order_number": "Auftragsnummer",
    "payment_reference": "Zahlungsreferenz",
    "original_invoice_number": "Ursprungsrechnung",
    "content": "Beschreibung / Inhalt",
    "response_deadline": "Rückmeldefrist",
}


def _settings_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


class _SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return ""


def _document_kind_setting_scope(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return _DOCUMENT_KIND_SETTING_ALIASES.get(normalized, normalized)


def _int_setting(value: Any, default: int) -> int:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def _document_number_setting_fields() -> list[dict[str, Any]]:
    definitions = [
        ("angebot", "Angebot", "ANG"),
        ("auftragsbestaetigung", "Auftragsbestaetigung", "AB"),
        ("lieferschein", "Lieferschein", "LS"),
        ("rechnung", "Rechnung", "RE"),
        ("abschlagsrechnung", "Abschlagsrechnung", "AR"),
        ("schlussrechnung", "Schlussrechnung", "SR"),
        ("gutschrift", "Gutschrift", "GS"),
        ("stornorechnung", "Stornorechnung", "ST"),
        ("mahnung", "Mahnung", "MAH"),
    ]
    fields: list[dict[str, Any]] = []
    for scope, label, prefix in definitions:
        fields.extend(
            [
                {
                    "key": f"{scope}_document_number_prefix",
                    "label": f"{label} Präfix",
                    "type": "string",
                    "default": prefix,
                    "group": "Nummernkreise je Dokumentart",
                },
                {
                    "key": f"{scope}_document_number_sequence_kind",
                    "label": f"{label} Sequenzkennung",
                    "type": "string",
                    "default": f"business_letter:{scope}",
                    "group": "Nummernkreise je Dokumentart",
                },
                {
                    "key": f"{scope}_document_number_pattern",
                    "label": f"{label} Pattern",
                    "type": "string",
                    "default": "{prefix}-{year}-{sequence_text}",
                    "group": "Nummernkreise je Dokumentart",
                },
                {
                    "key": f"{scope}_document_number_width",
                    "label": f"{label} Laufweite",
                    "type": "number",
                    "default": 5,
                    "group": "Nummernkreise je Dokumentart",
                },
                {
                    "key": f"{scope}_document_number_start_value",
                    "label": f"{label} Startwert",
                    "type": "number",
                    "default": 1,
                    "group": "Nummernkreise je Dokumentart",
                },
                {
                    "key": f"{scope}_document_number_year_reset",
                    "label": f"{label} Jahresreset aktiv",
                    "type": "boolean",
                    "default": True,
                    "group": "Nummernkreise je Dokumentart",
                },
            ]
        )
    return fields


def _extended_settings_fields() -> list[dict[str, Any]]:
    return [
        {
            "key": "default_invoice_type_code",
            "label": "Standard-Rechnungstypcode",
            "type": "select",
            "default": "380",
            "group": "Dokument-Defaults",
            "options": INVOICE_TYPE_OPTIONS,
        },
        {
            "key": "default_country_code",
            "label": "Standard-Landcode",
            "type": "select",
            "default": "DE",
            "group": "Dokument-Defaults",
            "options": COUNTRY_CODE_OPTIONS,
        },
        {
            "key": "default_unit_code",
            "label": "Standard-Einheitencode",
            "type": "select",
            "default": "C62",
            "group": "Dokument-Defaults",
            "options": UNIT_CODE_OPTIONS,
        },
        {
            "key": "default_tax_rate",
            "label": "Standard-Steuersatz (%)",
            "type": "number",
            "default": 19,
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_tax_category",
            "label": "Standard-Steuerkategorie",
            "type": "select",
            "default": "S",
            "group": "Dokument-Defaults",
            "options": TAX_CATEGORY_OPTIONS,
        },
        {
            "key": "default_reverse_charge_enabled",
            "label": "Reverse Charge standardmäßig aktiv",
            "type": "boolean",
            "default": False,
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_tax_exemption_enabled",
            "label": "Steuerbefreiung standardmäßig aktiv",
            "type": "boolean",
            "default": False,
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_buyer_reference",
            "label": "Standard-Leitweg-ID / BuyerReference",
            "type": "string",
            "default": "",
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_payment_reference",
            "label": "Standard-Zahlungsreferenz",
            "type": "string",
            "default": "",
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_delivery_terms",
            "label": "Standard-Lieferbedingungen",
            "type": "string",
            "default": "",
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_place_of_supply",
            "label": "Standard-Leistungsort",
            "type": "string",
            "default": "",
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_jurisdiction",
            "label": "Standard-Gerichtsstand",
            "type": "string",
            "default": "",
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_offer_validity_days",
            "label": "Angebotsgültigkeit in Tagen",
            "type": "number",
            "default": 30,
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_payment_recipient",
            "label": "Standard-Zahlungsempfänger",
            "type": "string",
            "default": "Steinmetzbetrieb Muster GmbH",
            "group": "Bank & Zahlung",
        },
        {
            "key": "default_sepa_creditor_id",
            "label": "SEPA-Gläubiger-ID",
            "type": "string",
            "default": "",
            "group": "Bank & Zahlung",
        },
        {
            "key": "default_sepa_mandate_reference",
            "label": "Mandatsreferenz",
            "type": "string",
            "default": "",
            "group": "Bank & Zahlung",
        },
        {
            "key": "default_payment_purpose_template",
            "label": "Standard-Verwendungszweck-Muster",
            "type": "string",
            "default": "{document_number}",
            "group": "Bank & Zahlung",
        },
        {
            "key": "default_cash_discount_percent",
            "label": "Skonto in Prozent",
            "type": "number",
            "default": 0,
            "group": "Bank & Zahlung",
        },
        {
            "key": "default_cash_discount_days",
            "label": "Skontofrist in Tagen",
            "type": "number",
            "default": 0,
            "group": "Bank & Zahlung",
        },
        {
            "key": "default_dunning_fee",
            "label": "Standard-Mahngebühr",
            "type": "number",
            "default": 0,
            "group": "Bank & Zahlung",
        },
        {
            "key": "default_late_interest_rate",
            "label": "Standard-Verzugszinssatz (%)",
            "type": "number",
            "default": 0,
            "group": "Bank & Zahlung",
        },
        {
            "key": "xrechnung_version",
            "label": "XRechnung-Version",
            "type": "select",
            "default": "3.0.1",
            "group": "E-Rechnung",
            "options": [
                {"label": "3.0.1", "value": "3.0.1"},
                {"label": "2.3.1", "value": "2.3.1"},
            ],
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "zugferd_version",
            "label": "ZUGFeRD-Version",
            "type": "select",
            "default": "2.3.2",
            "group": "E-Rechnung",
            "options": [
                {"label": "2.3.2", "value": "2.3.2"},
                {"label": "2.2", "value": "2.2"},
            ],
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "default_einvoice_profile_invoice",
            "label": "Standard-Profil Rechnung",
            "type": "select",
            "default": "en16931",
            "group": "E-Rechnung",
            "options": [
                {"label": "EN16931", "value": "en16931"},
                {"label": "Basic", "value": "basic"},
                {"label": "Extended", "value": "extended"},
            ],
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "default_einvoice_profile_credit_note",
            "label": "Standard-Profil Gutschrift/Storno",
            "type": "select",
            "default": "en16931",
            "group": "E-Rechnung",
            "options": [
                {"label": "EN16931", "value": "en16931"},
                {"label": "Basic", "value": "basic"},
                {"label": "Extended", "value": "extended"},
            ],
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "validator_profile",
            "label": "Validatorprofil",
            "type": "select",
            "default": "auto",
            "group": "E-Rechnung",
            "options": [
                {"label": "Auto", "value": "auto"},
                {"label": "XRechnung", "value": "xrechnung"},
                {"label": "ZUGFeRD / Factur-X", "value": "zugferd"},
                {"label": "CII / UNCEFACT", "value": "cii"},
            ],
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "validate_on_save",
            "label": "Validierung beim Speichern",
            "type": "boolean",
            "default": True,
            "group": "E-Rechnung",
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "validate_before_send",
            "label": "Validierung vor Versand zwingend",
            "type": "boolean",
            "default": True,
            "group": "E-Rechnung",
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "require_pdfa_check",
            "label": "PDF/A-Prüfung zwingend",
            "type": "boolean",
            "default": True,
            "group": "E-Rechnung",
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "block_send_on_validation_error",
            "label": "Versand bei Validatorfehler blockieren",
            "type": "boolean",
            "default": True,
            "group": "E-Rechnung",
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "store_xml_artifact",
            "label": "XML zusätzlich separat speichern",
            "type": "boolean",
            "default": True,
            "group": "E-Rechnung",
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "archive_validation_report",
            "label": "Validierungsreport archivieren",
            "type": "boolean",
            "default": True,
            "group": "E-Rechnung",
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "dual_save_enabled",
            "label": "Dual-Save aktiv",
            "type": "boolean",
            "default": False,
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "dual_save_failure_mode",
            "label": "Verhalten bei fehlgeschlagenem Dual-Save",
            "type": "select",
            "default": "warn",
            "group": "Persistenz & Archivierung",
            "options": [
                {"label": "Warnen und lokal fortfahren", "value": "warn"},
                {"label": "Abbrechen", "value": "fail"},
                {"label": "Zur Nachbearbeitung markieren", "value": "queue"},
            ],
            "visibleWhen": {"field": "dual_save_enabled", "truthy": True},
        },
        {
            "key": "dual_save_retry_attempts",
            "label": "Wiederholungsversuche",
            "type": "number",
            "default": 3,
            "group": "Persistenz & Archivierung",
            "visibleWhen": {"field": "dual_save_enabled", "truthy": True},
        },
        {
            "key": "guest_system_database_mode",
            "label": "Datenbankmodus",
            "type": "select",
            "default": "sqlite",
            "group": "Persistenz & Archivierung",
            "options": [
                {"label": "SQLite-Datei", "value": "sqlite"},
                {"label": "Externer Adapter", "value": "external"},
            ],
            "visibleWhen": {"field": "dual_save_enabled", "truthy": True},
        },
        {
            "key": "artifact_directory",
            "label": "Artefaktverzeichnis",
            "type": "string",
            "default": "artifacts/jobs",
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "retention_days",
            "label": "Aufbewahrungsdauer (Tage)",
            "type": "number",
            "default": 3650,
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "enable_document_versioning",
            "label": "Versionierung aktiv",
            "type": "boolean",
            "default": True,
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "enable_hash_verification",
            "label": "Hashprüfung aktiv",
            "type": "boolean",
            "default": True,
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "lock_released_documents",
            "label": "Freigegebene Dokumente unveränderlich",
            "type": "boolean",
            "default": True,
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "store_validation_reports",
            "label": "Validierungsreports speichern",
            "type": "boolean",
            "default": True,
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "archive_pdf_xml_together",
            "label": "PDF/XML gemeinsam archivieren",
            "type": "boolean",
            "default": True,
            "group": "Persistenz & Archivierung",
        },
        {
            "key": "dispatch_queue_enabled",
            "label": "Versand-Queue aktiv",
            "type": "boolean",
            "default": True,
            "group": "Mail-/Versand",
        },
        {
            "key": "dispatch_execute_immediately",
            "label": "Queue-Eintrag sofort versenden",
            "type": "boolean",
            "default": True,
            "group": "Mail-/Versand",
        },
        {
            "key": "dispatch_retry_attempts",
            "label": "Max. Versandversuche",
            "type": "number",
            "default": 3,
            "group": "Mail-/Versand",
        },
        {
            "key": "dispatch_provider",
            "label": "Versandadapter",
            "type": "select",
            "default": "smtp",
            "group": "Mail-/Versand",
            "options": [
                {"label": "SMTP", "value": "smtp"},
                {"label": "Microsoft 365", "value": "microsoft365"},
                {"label": "SendGrid", "value": "sendgrid"},
            ],
        },
        {
            "key": "default_cc",
            "label": "Standard-CC",
            "type": "string",
            "default": "",
            "group": "Kommunikation",
        },
        {
            "key": "default_sender_name",
            "label": "Standard-Absendername",
            "type": "string",
            "default": "Steinmetzbetrieb Muster GmbH",
            "group": "Kommunikation",
        },
        {
            "key": "default_email_subject_template",
            "label": "Standard-E-Mail-Betreffmuster",
            "type": "string",
            "default": "{document_kind} {document_number}",
            "group": "Kommunikation",
        },
        {
            "key": "default_reply_to_address",
            "label": "Standard-Antwortadresse",
            "type": "string",
            "default": "info@steinmetz-muster.de",
            "group": "Kommunikation",
        },
        {
            "key": "default_email_html_enabled",
            "label": "HTML-E-Mail aktiv",
            "type": "boolean",
            "default": True,
            "group": "Kommunikation",
        },
        {
            "key": "default_attach_pdf",
            "label": "PDF standardmäßig anhängen",
            "type": "boolean",
            "default": True,
            "group": "Kommunikation",
        },
        {
            "key": "default_attach_xml",
            "label": "XML standardmäßig anhängen",
            "type": "boolean",
            "default": False,
            "group": "Kommunikation",
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "default_filename_pattern",
            "label": "Standard-Dateinamenmuster",
            "type": "string",
            "default": "{document_number}",
            "group": "Kommunikation",
        },
        {
            "key": "default_reminder_text_level_1",
            "label": "Mahntext Stufe 1",
            "type": "text",
            "default": "Bitte begleichen Sie den offenen Betrag innerhalb der nächsten sieben Tage.",
            "group": "Kommunikation",
        },
        {
            "key": "default_reminder_text_level_2",
            "label": "Mahntext Stufe 2",
            "type": "text",
            "default": "Trotz unserer Erinnerung ist der offene Betrag noch nicht eingegangen. Bitte zahlen Sie umgehend.",
            "group": "Kommunikation",
        },
        {
            "key": "layout_template",
            "label": "Briefpapier-Layout",
            "type": "select",
            "default": "classic",
            "group": "Dokumentlayout",
            "options": [
                {"label": "Klassisch", "value": "classic"},
                {"label": "Modern", "value": "modern"},
                {"label": "Werkstatt", "value": "workshop"},
            ],
        },
        {
            "key": "logo_width_mm",
            "label": "Logo-Breite (mm)",
            "type": "number",
            "default": 32,
            "group": "Dokumentlayout",
        },
        {
            "key": "logo_position",
            "label": "Logo-Position",
            "type": "select",
            "default": "left",
            "group": "Dokumentlayout",
            "options": [
                {"label": "Links", "value": "left"},
                {"label": "Zentriert", "value": "center"},
                {"label": "Rechts", "value": "right"},
            ],
        },
        {
            "key": "logo_strict_mode",
            "label": "Logo-Validierung strikt",
            "type": "boolean",
            "default": False,
            "group": "Dokumentlayout",
            "description": "Bei fehlerhaften Logo-Daten wird die PDF-Erzeugung mit einem klaren Fehler abgebrochen.",
        },
        {
            "key": "logo_max_bytes",
            "label": "Maximale Logo-Groesse (Bytes)",
            "type": "number",
            "default": 1048576,
            "group": "Dokumentlayout",
            "description": "Begrenzt die akzeptierte Logo-Groesse fuer das PDF-Embedding.",
        },
        {
            "key": "page_margin_mm",
            "label": "Seitenränder (mm)",
            "type": "number",
            "default": 20,
            "group": "Dokumentlayout",
        },
        {
            "key": "default_font_family",
            "label": "Standardschrift",
            "type": "select",
            "default": "Source Sans 3",
            "group": "Dokumentlayout",
            "options": [
                {"label": "Source Sans 3", "value": "Source Sans 3"},
                {"label": "IBM Plex Sans", "value": "IBM Plex Sans"},
                {"label": "Merriweather", "value": "Merriweather"},
            ],
        },
        {
            "key": "default_font_size_pt",
            "label": "Schriftgröße (pt)",
            "type": "number",
            "default": 11,
            "group": "Dokumentlayout",
        },
        {
            "key": "accent_color",
            "label": "Akzentfarbe",
            "type": "string",
            "default": "#234662",
            "group": "Dokumentlayout",
        },
        {
            "key": "footer_text",
            "label": "Fußzeilentext",
            "type": "text",
            "default": "Steinmetzbetrieb Muster GmbH · Musterstraße 1 · 12345 Musterstadt",
            "group": "Dokumentlayout",
        },
        {
            "key": "show_page_numbers",
            "label": "Seitenzahlen aktiv",
            "type": "boolean",
            "default": True,
            "group": "Dokumentlayout",
        },
        {
            "key": "show_bank_details_in_footer",
            "label": "Bankdaten in Fußzeile anzeigen",
            "type": "boolean",
            "default": True,
            "group": "Dokumentlayout",
        },
        {
            "key": "show_legal_details_in_footer",
            "label": "Rechtliche Angaben in Fußzeile anzeigen",
            "type": "boolean",
            "default": True,
            "group": "Dokumentlayout",
        },
        {
            "key": "draft_watermark_text",
            "label": "Wasserzeichen für Entwürfe",
            "type": "string",
            "default": "ENTWURF",
            "group": "Dokumentlayout",
        },
        {
            "key": "default_pdf_filename_pattern",
            "label": "Standard-PDF-Dateiname",
            "type": "string",
            "default": "{document_number}.pdf",
            "group": "Dokumentlayout",
        },
        {
            "key": "text_installation_notice",
            "label": "Standard-Montagehinweis",
            "type": "text",
            "default": "Montagearbeiten setzen bauseits vorbereitete und zugängliche Einbauorte voraus.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_care_notice",
            "label": "Standard-Pflegehinweis",
            "type": "text",
            "default": "Für die dauerhafte Werterhaltung empfehlen wir eine materialgerechte Pflege gemäß unseren Hinweisen.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_color_variation_notice",
            "label": "Standard-Farbabweichungshinweis",
            "type": "text",
            "default": "Natürliche Farb- und Strukturabweichungen sind materialtypisch und stellen keinen Mangel dar.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_tolerance_notice",
            "label": "Standard-Toleranzhinweis",
            "type": "text",
            "default": "Maß- und Ebenheitstoleranzen richten sich nach den einschlägigen Normen und der handwerklichen Bearbeitung.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_batch_notice",
            "label": "Standard-Lager-/Chargenhinweis",
            "type": "text",
            "default": "Nachlieferungen können chargenbedingt geringfügig von früheren Lieferungen abweichen.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_scaffolding_notice",
            "label": "Standard-Gerüst-/Kranhinweis",
            "type": "text",
            "default": "Erforderliche Gerüst-, Kran- oder Hebetechnikleistungen sind bauseits bereitzustellen, sofern nicht ausdrücklich vereinbart.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_disposal_notice",
            "label": "Standard-Entsorgungshinweis",
            "type": "text",
            "default": "Entsorgungsleistungen sind nur enthalten, wenn sie im Angebot oder Auftrag ausdrücklich ausgewiesen sind.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_warranty_notice",
            "label": "Standard-Gewährleistungstext",
            "type": "text",
            "default": "Es gelten die gesetzlichen Gewährleistungsrechte, soweit keine abweichenden Vereinbarungen getroffen wurden.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_material_availability_notice",
            "label": "Standard-Vorbehalt Materialverfügbarkeit",
            "type": "text",
            "default": "Alle Liefer- und Fertigungstermine stehen unter dem Vorbehalt rechtzeitiger Materialverfügbarkeit.",
            "group": "Fachliche Hinweise",
        },
    ]

PLUGIN_META: dict[str, Any] = {
    "id": "business_letter",
    "name": "Geschäftsbrief",
    "description": "Erstellt strukturierte Brief- und E-Mail-Inhalte für Steinmetzbetriebe",
    "category": "Dokumente",
    "apiKeyRequired": False,
    "intentPattern": r"\b(brief|geschäftsbrief|angebotsschreiben|auftragsbestätigung|reklamation|abnahme|mahnung|rechnung)\b",
    "status": "implemented",
    "summary": "Erstellt und verwaltet Geschaeftsdokumente inklusive E-Rechnung und Folgebeleg-Konvertierungen.",
    "capabilities": [
        "document.quote.create",
        "document.order.confirmation.create",
        "document.invoice.create",
        "document.invoice.convert",
        "document.invoice.cancel",
        "document.reminder.create",
        "document.project_case.overview",
    ],
    "usage_rules": [
        "Keine Betraege oder Positionen erfinden.",
        "Stornorechnung und Konvertierung benoetigen ein gueltiges Ursprungsdokument.",
        "E-Rechnungsdaten muessen bei aktivierter Validierung formal konsistent sein.",
    ],
    "functions": [
        {
            "name": "create_document",
            "description": "Erstellt ein neues Geschaeftsdokument oder Folgebeleg.",
            "read_only": False,
            "side_effect": "creates_document",
            "requires_confirmation": False,
            "required_permissions": ["business_letter.write"],
            "idempotent": True,
            "supports_dry_run": True,
        },
        {
            "name": "project_case_overview",
            "description": "Liest den Status einer Projektakte ohne neue Dokumenterstellung.",
            "read_only": True,
            "side_effect": "none",
            "requires_confirmation": False,
            "required_permissions": ["business_letter.read"],
            "idempotent": True,
            "supports_dry_run": True,
        },
    ],
    "pluginFrontend": {
        "title": "Geschäftsbrief Frontend",
        "description": "Fachliche Einstiege für Angebote, Rechnungen, Mahnungen, E-Mail-Begleitung sowie Layout- und E-Rechnungs-Settings.",
        "page": {
            "eyebrow": "Steinmetz-Workflow",
            "headline": "Geschäftsbrief-Zentrale für Dokumente, Versand und Freigabe",
            "summary": "Diese Frontpage gehört direkt zum Plugin und bündelt die typischen Arbeitswege für kaufmännische Dokumente, Kommunikationsschreiben, E-Rechnung, Layout und revisionsnahe Persistenz.",
            "highlights": [
                "Angebote, Auftragsbestätigungen und Rechnungen",
                "E-Mail-Begleitung und Mahnungen",
                "XRechnung und ZUGFeRD",
                "PDF, Layout und Archivierung",
            ],
            "sections": [
                {
                    "id": "daily-work",
                    "title": "Tägliche Arbeit",
                    "description": "Die häufigsten Einstiege für Verkauf, Ausführung und Abrechnung.",
                    "cards": [
                        {
                            "id": "page-offer",
                            "title": "Angebot erstellen",
                            "description": "Startet mit einem sofort nutzbaren Angebotsentwurf für Natursteinarbeiten.",
                            "bullets": [
                                "Positionen und Projektbezug vorbereitet",
                                "Ideal für Erstangebot oder Nachtrag",
                                "Direkter Einstieg in den Runner",
                            ],
                            "ctaLabel": "Angebot öffnen",
                            "openTab": "manual",
                            "pluginInput": {
                                "letter_type": "angebot",
                                "document_kind": "angebot",
                                "subject": "Angebot für Natursteinarbeiten",
                            },
                        },
                        {
                            "id": "page-invoice",
                            "title": "Rechnung vorbereiten",
                            "description": "Öffnet einen Rechnungsfall mit Zahlungs- und Positionsstruktur.",
                            "bullets": [
                                "Geeignet für Schluss- und Teilrechnungen",
                                "Mit Buyer Reference und Positionen",
                                "Kann direkt auf E-Rechnung erweitert werden",
                            ],
                            "ctaLabel": "Rechnung öffnen",
                            "openTab": "manual",
                            "pluginInput": {
                                "letter_type": "rechnung",
                                "document_kind": "rechnung",
                                "subject": "Rechnung für ausgeführte Natursteinarbeiten",
                            },
                        },
                        {
                            "id": "page-reminder",
                            "title": "Zahlungserinnerung",
                            "description": "Bereitet eine freundliche Zahlungserinnerung oder Mahnung vor.",
                            "bullets": [
                                "Für offene Rechnungen",
                                "Mit Betrags- und Fristbezug",
                                "Kommunikationsschreiben statt Belegdokument",
                            ],
                            "ctaLabel": "Erinnerung öffnen",
                            "openTab": "manual",
                            "pluginInput": {
                                "letter_type": "zahlungserinnerung",
                                "subject": "Erinnerung an offene Rechnung",
                            },
                        },
                    ],
                },
                {
                    "id": "quality-compliance",
                    "title": "Qualität und Compliance",
                    "description": "Einstellungen und Laufwege für valide Dokumente und saubere Ausgabeformate.",
                    "cards": [
                        {
                            "id": "page-einvoice",
                            "title": "E-Rechnung vorbereiten",
                            "description": "Schaltet XRechnung-/ZUGFeRD-Grundstruktur für den nächsten Rechnungsfall vor.",
                            "bullets": [
                                "UBL oder CII",
                                "EN16931-Profil",
                                "Geeignet für Validierung und Versandprüfung",
                            ],
                            "ctaLabel": "E-Rechnung starten",
                            "openTab": "manual",
                            "pluginInput": {
                                "letter_type": "rechnung",
                                "document_kind": "rechnung",
                                "subject": "E-Rechnung für ausgeführte Leistung",
                                "einvoice": {
                                    "enabled": True,
                                    "standard": "xrechnung",
                                    "profile": "en16931",
                                    "syntax": "UBL",
                                },
                            },
                        },
                        {
                            "id": "page-layout",
                            "title": "Layout und PDF",
                            "description": "Öffnet die Settings für Logo, Akzentfarbe, Seitenränder und PDF-Dateinamen.",
                            "bullets": [
                                "Corporate Design pflegen",
                                "PDF-Ausgabe abstimmen",
                                "Footer und Wasserzeichen konfigurieren",
                            ],
                            "ctaLabel": "Layout öffnen",
                            "openTab": "settings",
                        },
                        {
                            "id": "page-archive",
                            "title": "Archivierung und Nummernkreis",
                            "description": "Springt in die Plugin-Settings für Persistenz, Freigabe und Revisionspfad.",
                            "bullets": [
                                "Nummernkreis und Jahresreset",
                                "Dual-Save und Artefakte",
                                "Retention und Sperrlogik",
                            ],
                            "ctaLabel": "Archiv öffnen",
                            "openTab": "settings",
                        },
                    ],
                },
            ],
        },
        "sections": [
            {
                "id": "sales-documents",
                "title": "Vertrieb und Auftragsdokumente",
                "description": "Typische kaufmännische Dokumente für Angebot, Auftrag und Rechnung direkt vorbereiten.",
                "actions": [
                    {
                        "id": "offer-template",
                        "label": "Angebot vorbereiten",
                        "description": "Öffnet den Runner mit einer vorbereiteten Angebotsstruktur inklusive Positionen.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "angebot",
                            "document_kind": "angebot",
                            "subject": "Angebot für Natursteinarbeiten",
                            "recipient_name": "Musterkunde GmbH",
                            "project_reference": "Projekt-Terrasse 2026",
                            "positions": [
                                {
                                    "line_id": "1",
                                    "name": "Fensterbank aus Naturstein",
                                    "quantity": "1",
                                    "unit_code": "C62",
                                    "price_net": "149.00",
                                    "vat_category": "S",
                                    "vat_rate": "19",
                                }
                            ],
                        },
                    },
                    {
                        "id": "order-confirmation-template",
                        "label": "Auftragsbestätigung vorbereiten",
                        "description": "Legt eine Auftragsbestätigung mit Projekt- und Referenzfeldern vor.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "auftragsbestaetigung",
                            "document_kind": "auftragsbestaetigung",
                            "subject": "Auftragsbestätigung für Ihre Steinmetzarbeiten",
                            "recipient_name": "Musterkunde GmbH",
                            "order_reference": "AB-2026-001",
                            "project_reference": "Projekt-Eingangsbereich",
                        },
                    },
                    {
                        "id": "invoice-template",
                        "label": "Rechnung vorbereiten",
                        "description": "Öffnet eine vorbereitete Rechnung mit Zahlungs- und Positionsdaten.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "rechnung",
                            "document_kind": "rechnung",
                            "subject": "Rechnung für ausgeführte Natursteinarbeiten",
                            "recipient_name": "Musterkunde GmbH",
                            "buyer_reference": "PO-7788",
                            "positions": [
                                {
                                    "line_id": "1",
                                    "name": "Arbeitsplatte Granit",
                                    "quantity": "1",
                                    "unit_code": "C62",
                                    "price_net": "890.00",
                                    "vat_category": "S",
                                    "vat_rate": "19",
                                }
                            ],
                        },
                    },
                ],
            },
            {
                "id": "communication",
                "title": "Kommunikation und Versand",
                "description": "Begleitschreiben, Erinnerungen und E-Mail-Flows für den laufenden Kundenkontakt.",
                "actions": [
                    {
                        "id": "invoice-cover-mail",
                        "label": "Rechnungs-Begleitmail vorbereiten",
                        "description": "Füllt den Runner für ein Rechnungsbegleitschreiben per E-Mail vor.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "rechnung_begleitschreiben",
                            "subject": "Ihre Rechnung im Anhang",
                            "communication_channel": "email",
                            "recipient_email": "kunde@example.com",
                            "ready_for_sending": False,
                        },
                    },
                    {
                        "id": "reminder-template",
                        "label": "Zahlungserinnerung vorbereiten",
                        "description": "Startet mit einer vorbereiteten Zahlungserinnerung für offene Rechnungen.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "zahlungserinnerung",
                            "subject": "Erinnerung an offene Rechnung",
                            "invoice_number": "RE-2026-00012",
                            "invoice_amount": "890.00",
                            "due_date": "2026-07-31",
                        },
                    },
                    {
                        "id": "complaint-response-template",
                        "label": "Reklamationsantwort vorbereiten",
                        "description": "Öffnet einen Kommunikationsentwurf für die Antwort auf eine Reklamation.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "reklamation_antwort",
                            "subject": "Antwort auf Ihre Reklamation",
                            "recipient_name": "Musterkunde GmbH",
                        },
                    },
                ],
            },
            {
                "id": "einvoice-layout",
                "title": "E-Rechnung und Layout",
                "description": "Direkte Einstiege zu den wichtigsten Konfigurationsbereichen für E-Rechnung, PDF und Darstellung.",
                "actions": [
                    {
                        "id": "settings-firmendaten",
                        "label": "Firmendaten konfigurieren",
                        "description": "Wechselt in die Settings des Plugins, um Absender- und Firmendaten zu pflegen.",
                        "openTab": "settings",
                    },
                    {
                        "id": "settings-layout",
                        "label": "Layout und PDF öffnen",
                        "description": "Springt in die Settings-Ansicht für Logo, Ränder, Akzentfarbe und PDF-Dateinamen.",
                        "openTab": "settings",
                    },
                    {
                        "id": "einvoice-template",
                        "label": "E-Rechnung vorbereiten",
                        "description": "Öffnet den Runner mit aktivierter XRechnung-/ZUGFeRD-Grundstruktur.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "rechnung",
                            "document_kind": "rechnung",
                            "subject": "E-Rechnung für ausgeführte Leistung",
                            "einvoice": {
                                "enabled": True,
                                "standard": "xrechnung",
                                "profile": "en16931",
                                "syntax": "UBL",
                            },
                            "positions": [
                                {
                                    "line_id": "1",
                                    "name": "Montage und Lieferung",
                                    "quantity": "1",
                                    "unit_code": "C62",
                                    "price_net": "250.00",
                                    "vat_category": "S",
                                    "vat_rate": "19",
                                }
                            ],
                        },
                    },
                ],
            },
            {
                "id": "persistence",
                "title": "Persistenz und Freigabe",
                "description": "Archivierung, Nummernkreis und Versandbereitschaft für operative Abläufe vorbereiten.",
                "actions": [
                    {
                        "id": "persisted-document-template",
                        "label": "Dokument mit Persistenz vorbereiten",
                        "description": "Erstellt einen Entwurf mit aktivierter Datenbankpersistenz und Artefaktablage.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "angebot",
                            "document_kind": "angebot",
                            "subject": "Angebot mit Archivierung",
                            "persist_to_database": True,
                            "generate_templates": True,
                        },
                    },
                    {
                        "id": "send-ready-template",
                        "label": "Versandbereit vorbereiten",
                        "description": "Befuellt den Runner für einen dokumentierten, versandbereiten E-Mail-Fall.",
                        "openTab": "manual",
                        "pluginInput": {
                            "letter_type": "allgemein",
                            "subject": "Dokument zur Freigabe",
                            "communication_channel": "email",
                            "recipient_email": "kunde@example.com",
                            "ready_for_sending": True,
                        },
                    },
                    {
                        "id": "settings-numbering",
                        "label": "Nummernkreis und Archivierung",
                        "description": "Öffnet die Settings für Nummernkreis, Persistenz und Dual-Save.",
                        "openTab": "settings",
                    },
                ],
            },
        ],
    },
    "settingsFields": [
        {"key": "company_logo_url", "label": "Logo-URL", "type": "string", "default": "", "group": "Firmendaten"},
        {
            "key": "company_name",
            "label": "Firmenname",
            "type": "string",
            "default": "Steinmetzbetrieb Muster GmbH",
            "group": "Firmendaten",
        },
        {"key": "company_street", "label": "Straße + Hausnummer", "type": "string", "default": "Musterstraße 1", "group": "Firmendaten"},
        {"key": "company_zip", "label": "PLZ", "type": "string", "default": "12345", "group": "Firmendaten"},
        {"key": "company_city", "label": "Ort", "type": "string", "default": "Musterstadt", "group": "Firmendaten"},
        {"key": "company_country", "label": "Land", "type": "string", "default": "Deutschland", "group": "Firmendaten"},
        {"key": "company_postbox", "label": "Postfach", "type": "string", "default": "", "group": "Firmendaten"},
        {"key": "company_phone", "label": "Telefon", "type": "string", "default": "0123 456789", "group": "Firmendaten"},
        {"key": "company_mobile", "label": "Mobiltelefon", "type": "string", "default": "", "group": "Firmendaten"},
        {"key": "company_fax", "label": "Fax", "type": "string", "default": "", "group": "Firmendaten"},
        {
            "key": "company_email",
            "label": "E-Mail",
            "type": "string",
            "default": "info@steinmetz-muster.de",
            "group": "Firmendaten",
        },
        {
            "key": "company_electronic_address",
            "label": "Elektronische Adresse",
            "type": "string",
            "default": "info@steinmetz-muster.de",
            "group": "Firmendaten",
        },
        {
            "key": "company_electronic_address_scheme",
            "label": "Elektronische Adresse schemeID",
            "type": "select",
            "default": "EM",
            "group": "Firmendaten",
            "options": EAS_SCHEME_OPTIONS,
            "description": "Die schemeID sollte zum Format der elektronischen Adresse passen.",
        },
        {
            "key": "company_email_reply_to",
            "label": "Antwort-E-Mail-Adresse",
            "type": "string",
            "default": "info@steinmetz-muster.de",
            "group": "Firmendaten",
        },
        {"key": "company_email_bcc", "label": "Standard-BCC-Adresse", "type": "string", "default": "", "group": "Firmendaten"},
        {
            "key": "company_website",
            "label": "Webseite",
            "type": "string",
            "default": "www.steinmetz-muster.de",
            "group": "Firmendaten",
        },
        {
            "key": "company_manager",
            "label": "Geschäftsführer",
            "type": "string",
            "default": "Max Mustermann",
            "group": "Firmendaten",
        },
        {
            "key": "company_profession",
            "label": "Berufsbezeichnung",
            "type": "string",
            "default": "Steinmetz- und Steinbildhauermeister",
            "group": "Firmendaten",
        },
        {
            "key": "company_chamber",
            "label": "Aufsichtsbehörde (Handwerkskammer)",
            "type": "string",
            "default": "Handwerkskammer Musterstadt",
            "group": "Firmendaten",
        },
        {"key": "company_agb", "label": "AGB-URL", "type": "string", "default": "www.steinmetz-muster.de/agb", "group": "Firmendaten"},
        {
            "key": "company_privacy",
            "label": "Datenschutz-URL",
            "type": "string",
            "default": "www.steinmetz-muster.de/datenschutz",
            "group": "Firmendaten",
        },
        {"key": "company_tax_id", "label": "Steuernummer", "type": "string", "default": "123/456/7890", "group": "Rechtliche Angaben"},
        {"key": "company_vat_id", "label": "USt-IdNr.", "type": "string", "default": "DE123456789", "group": "Rechtliche Angaben"},
        {"key": "company_legal_form", "label": "Rechtsform", "type": "string", "default": "GmbH", "group": "Rechtliche Angaben"},
        {
            "key": "company_registry_number",
            "label": "Handelsregisternummer",
            "type": "string",
            "default": "HRB 12345",
            "group": "Rechtliche Angaben",
        },
        {
            "key": "company_registry_court",
            "label": "Registergericht",
            "type": "string",
            "default": "Amtsgericht Musterstadt",
            "group": "Rechtliche Angaben",
        },
        {
            "key": "company_responsible_content",
            "label": "Inhaltlich Verantwortlicher",
            "type": "string",
            "default": "Max Mustermann",
            "group": "Rechtliche Angaben",
        },
        {
            "key": "company_bank_name",
            "label": "Bank",
            "type": "string",
            "default": "Musterbank",
            "group": "Bankverbindung",
        },
        {
            "key": "company_iban",
            "label": "IBAN",
            "type": "string",
            "default": "DE12 3456 7890 1234 5678 90",
            "group": "Bankverbindung",
        },
        {
            "key": "company_bic",
            "label": "BIC",
            "type": "string",
            "default": "MUSTDEMMXXX",
            "group": "Bankverbindung",
        },
        {
            "key": "company_account_holder",
            "label": "Kontoinhaber",
            "type": "string",
            "default": "Steinmetzbetrieb Muster GmbH",
            "group": "Bankverbindung",
        },
        {
            "key": "default_language",
            "label": "Standardsprache",
            "type": "select",
            "default": "de",
            "group": "Kommunikation",
            "options": [
                {"label": "Deutsch", "value": "de"},
                {"label": "Englisch", "value": "en"},
            ],
        },
        {
            "key": "default_tone",
            "label": "Standard-Tonalität",
            "type": "select",
            "default": "professionell_freundlich",
            "group": "Kommunikation",
            "options": [
                {"label": "Professionell & freundlich", "value": "professionell_freundlich"},
                {"label": "Formell", "value": "formell"},
                {"label": "Kurz & sachlich", "value": "kurz_sachlich"},
                {"label": "Serviceorientiert", "value": "serviceorientiert"},
                {"label": "Bestimmt", "value": "bestimmt"},
                {"label": "Deeskalierend", "value": "deeskalierend"},
            ],
        },
        {
            "key": "default_currency",
            "label": "Standard-Währung",
            "type": "select",
            "default": "EUR",
            "group": "Dokument-Defaults",
            "options": [
                {"label": "EUR", "value": "EUR"},
                {"label": "USD", "value": "USD"},
                {"label": "CHF", "value": "CHF"},
                {"label": "GBP", "value": "GBP"},
            ],
        },
        {
            "key": "default_payment_terms",
            "label": "Standard-Zahlungsbedingungen",
            "type": "string",
            "default": "Zahlbar innerhalb von 14 Tagen ohne Abzug.",
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_payment_method_code",
            "label": "Standard-Zahlungsmittelcode (UNCL4461)",
            "type": "select",
            "default": "58",
            "group": "Dokument-Defaults",
            "options": [
                {"label": "58 - SEPA-Überweisung", "value": "58"},
                {"label": "59 - SEPA-Lastschrift", "value": "59"},
                {"label": "30 - Überweisung", "value": "30"},
                {"label": "48 - Bankkarte", "value": "48"},
            ],
        },
        {
            "key": "default_payment_days",
            "label": "Standard-Zahlungsziel (Tage)",
            "type": "number",
            "default": 14,
            "group": "Dokument-Defaults",
        },
        {
            "key": "default_tax_exemption_reason",
            "label": "Standard-Steuerbefreiungsgrund",
            "type": "string",
            "default": "",
            "group": "Dokument-Defaults",
            "visibleWhen": {"field": "default_tax_exemption_enabled", "truthy": True},
        },
        {
            "key": "default_tax_exemption_reason_code",
            "label": "Standard-Steuerbefreiungsgrundcode",
            "type": "select",
            "default": "",
            "group": "Dokument-Defaults",
            "options": TAX_EXEMPTION_CODE_OPTIONS,
            "visibleWhen": {"field": "default_tax_exemption_enabled", "truthy": True},
        },
        {
            "key": "default_reverse_charge_note",
            "label": "Standard-Hinweis Reverse Charge",
            "type": "string",
            "default": "Reverse charge",
            "group": "Dokument-Defaults",
            "visibleWhen": {"field": "default_reverse_charge_enabled", "truthy": True},
        },
        {
            "key": "default_einvoice_enabled",
            "label": "E-Rechnung standardmäßig aktiv",
            "type": "boolean",
            "default": False,
            "group": "E-Rechnung",
        },
        {
            "key": "default_einvoice_standard",
            "label": "E-Rechnung-Standard",
            "type": "select",
            "default": "xrechnung",
            "group": "E-Rechnung",
            "options": [
                {"label": "XRechnung", "value": "xrechnung"},
                {"label": "ZUGFeRD", "value": "zugferd"},
            ],
        },
        {
            "key": "default_einvoice_profile",
            "label": "E-Rechnung-Profil",
            "type": "select",
            "default": "en16931",
            "group": "E-Rechnung",
            "options": [
                {"label": "EN16931", "value": "en16931"},
                {"label": "Basic", "value": "basic"},
            ],
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "default_einvoice_syntax",
            "label": "E-Rechnung-Syntax",
            "type": "select",
            "default": "UBL",
            "group": "E-Rechnung",
            "options": [
                {"label": "UBL", "value": "UBL"},
                {"label": "CII", "value": "CII"},
            ],
            "visibleWhen": {"field": "default_einvoice_enabled", "truthy": True},
        },
        {
            "key": "document_number_prefix",
            "label": "Nummernkreis Präfix",
            "type": "string",
            "default": "ANG",
            "group": "Nummernkreis & Persistenz",
        },
        {
            "key": "document_number_sequence_kind",
            "label": "Nummernkreis Kennung",
            "type": "string",
            "default": "business_letter:ANG",
            "group": "Nummernkreis & Persistenz",
        },
        {
            "key": "document_number_pattern",
            "label": "Nummernformat",
            "type": "string",
            "default": "{prefix}-{year}-{sequence_text}",
            "group": "Nummernkreis & Persistenz",
        },
        {
            "key": "document_number_width",
            "label": "Nummern-Laufweite",
            "type": "number",
            "default": 5,
            "group": "Nummernkreis & Persistenz",
        },
        {
            "key": "document_number_start_value",
            "label": "Nummernkreis Startwert",
            "type": "number",
            "default": 1,
            "group": "Nummernkreis & Persistenz",
        },
        {
            "key": "document_number_year_reset",
            "label": "Jahresreset aktiv",
            "type": "boolean",
            "default": True,
            "group": "Nummernkreis & Persistenz",
        },
        {
            "key": "guest_system_database_path",
            "label": "Pfad Gastsystem-Datenbank",
            "type": "string",
            "default": "data/database/chat_system.db",
            "group": "Persistenz & Archivierung",
            "visibleWhen": {"field": "dual_save_enabled", "truthy": True},
        },
        {
            "key": "default_salutation",
            "label": "Standard-Anrede",
            "type": "string",
            "default": "Sehr geehrte Damen und Herren,",
            "group": "Kommunikation",
        },
        {
            "key": "default_email_greeting",
            "label": "Standard-E-Mail-Anrede",
            "type": "string",
            "default": "Guten Tag,",
            "group": "Kommunikation",
        },
        {
            "key": "default_email_signature",
            "label": "E-Mail-Signatur",
            "type": "text",
            "default": "Mit freundlichen Grüßen\nMax Mustermann\nSteinmetz- und Steinbildhauermeister",
            "group": "Kommunikation",
        },
        {
            "key": "default_email_disclaimer",
            "label": "E-Mail-Rechtshinweis",
            "type": "text",
            "default": "",
            "group": "Kommunikation",
        },
        {
            "key": "default_confidentiality_notice",
            "label": "Vertraulichkeitshinweis",
            "type": "text",
            "default": "",
            "group": "Kommunikation",
        },
        {
            "key": "default_signatory_name",
            "label": "Standard Unterzeichner Name",
            "type": "string",
            "default": "Max Mustermann",
            "group": "Kommunikation",
        },
        {
            "key": "default_signatory_position",
            "label": "Standard Unterzeichner Funktion",
            "type": "string",
            "default": "Steinmetz- und Steinbildhauermeister",
            "group": "Kommunikation",
        },
        {
            "key": "base_intro_text",
            "label": "Basis-Einleitung",
            "type": "string",
            "default": "vielen Dank für Ihre Anfrage.",
            "group": "Kommunikation",
        },
        {
            "key": "base_closing_text",
            "label": "Basis-Schlussformel",
            "type": "string",
            "default": "Mit freundlichen Grüßen",
            "group": "Kommunikation",
        },
        {
            "key": "base_missing_info_text",
            "label": "Hinweis bei fehlenden Angaben",
            "type": "string",
            "default": "Bitte reichen Sie fehlende Angaben nach, damit wir die Bearbeitung abschließen können.",
            "group": "Kommunikation",
        },
        {
            "key": "text_natural_material_notice",
            "label": "Hinweis Naturmaterial",
            "type": "text",
            "default": "Naturstein ist ein Naturprodukt. Abweichungen in Farbe, Struktur, Körnung und Maserung stellen keinen Mangel dar.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_external_trades_notice",
            "label": "Hinweis Fremdgewerke",
            "type": "text",
            "default": "Anschlussarbeiten der Gewerke Sanitär und Elektro sind nicht Bestandteil unserer Leistung, sofern sie nicht ausdrücklich angeboten wurden.",
            "group": "Fachliche Hinweise",
        },
        {
            "key": "text_measurement_notice",
            "label": "Hinweis Aufmaß",
            "type": "text",
            "default": "Die Fertigung erfolgt nach abgeschlossenem Aufmaß und schriftlicher Freigabe.",
            "group": "Fachliche Hinweise",
        },
        *_extended_settings_fields(),
        *_document_number_setting_fields(),
    ],
}


class BusinessLetterPlugin:
    name = "business_letter"
    description = "Erstellt strukturierte Brief- und E-Mail-Inhalte für Steinmetzbetriebe"

    TONE_OPTIONS = {
        "professionell_freundlich",
        "formell",
        "kurz_sachlich",
        "serviceorientiert",
        "bestimmt",
        "deeskalierend",
    }

    LETTER_TYPES = {
        "anfrage",
        "angebot",
        "angebotsanfrage",
        "preisangebot",
        "angebotsaenderung",
        "angebotsstornierung",
        "angebot_treppe",
        "abschlagsrechnung",
        "anzahlungsanforderung",
        "bestellbestaetigung",
        "bestellung",
        "bestellaenderung",
        "bestellstornierung",
        "belastungsanzeige",
        "gutschrift",
        "angebotserinnerung",
        "auftragsbestaetigung",
        "auftragsaenderung",
        "auftragsstornierung",
        "anschreiben",
        "empfangsbestaetigung",
        "inkassouebergabe",
        "kontoauszug",
        "kostenvoranschlag",
        "kuendigung",
        "lieferantenreklamation",
        "rechnung",
        "proformarechnung",
        "reklamation",
        "terminbestaetigung",
        "terminverschiebung",
        "lieferankuendigung",
        "lieferschein",
        "teillieferschein",
        "sammellieferschein",
        "montagebericht",
        "fertigstellungsanzeige",
        "abnahme",
        "abnahmeprotokoll",
        "rechnung_begleitschreiben",
        "retourenschein",
        "serienbrief",
        "servicebericht",
        "zahlungserinnerung",
        "zahlungsavis",
        "zahlungsbestaetigung",
        "mahnung_1",
        "mahnung_2",
        "mahnung_3",
        "reklamation_eingang",
        "reklamation_antwort",
        "maengelanzeige",
        "nachbesserung",
        "stornobestaetigung",
        "stornorechnung",
        "vertragsaenderung",
        "vertragsbegleitschreiben",
        "verzugszinsberechnung",
        "versandanzeige",
        "wartungsprotokoll",
        "wareneingang",
        "fehlende_angaben",
        "dokumentenanforderung",
        "allgemein",
        "schlussrechnung",
    }

    POSITION_REQUIRED_DOCUMENT_TYPES = {
        "angebot",
        "angebot_treppe",
        "preisangebot",
        "angebotsaenderung",
        "auftragsbestaetigung",
        "bestellbestaetigung",
        "bestellung",
        "bestellaenderung",
        "kostenvoranschlag",
        "lieferschein",
        "teillieferschein",
        "sammellieferschein",
        "rechnung",
        "abschlagsrechnung",
        "anzahlungsanforderung",
        "schlussrechnung",
        "proformarechnung",
        "gutschrift",
        "stornorechnung",
        "belastungsanzeige",
        "wareneingang",
    }

    EINVOICE_ALLOWED_DOCUMENT_TYPES = {
        "rechnung",
        "abschlagsrechnung",
        "schlussrechnung",
        "gutschrift",
        "stornorechnung",
    }

    DUNNING_REQUIRED_DOCUMENT_TYPES = {
        "zahlungserinnerung",
        "mahnung_1",
        "mahnung_2",
        "mahnung_3",
        "inkassouebergabe",
        "verzugszinsberechnung",
    }

    LETTER_TYPE_ALIASES = {
        "angebotsänderung": "angebotsaenderung",
        "angebotsstornierung": "angebotsstornierung",
        "angebotsanfrage (rfq)": "angebotsanfrage",
        "auftragsbestätigung": "auftragsbestaetigung",
        "auftragsbestaetigung": "auftragsbestaetigung",
        "bestellbestätigung": "bestellbestaetigung",
        "bestelländerung": "bestellaenderung",
        "auftragsänderung": "auftragsaenderung",
        "auftragsstornierung": "auftragsstornierung",
        "lieferankündigung": "lieferankuendigung",
        "proformarechnung": "proformarechnung",
        "anzahlungsanforderung": "anzahlungsanforderung",
        "zahlungsbestätigung": "zahlungsbestaetigung",
        "3. mahnung": "mahnung_3",
        "2. mahnung": "mahnung_2",
        "1. mahnung": "mahnung_1",
        "inkassoübergabe": "inkassouebergabe",
        "kündigung": "kuendigung",
        "stornobestätigung": "stornobestaetigung",
        "vertragsänderung": "vertragsaenderung",
        "vertragsbegleitschreiben": "vertragsbegleitschreiben",
        "mängelanzeige": "maengelanzeige",
        "retourenschein": "retourenschein",
        "lieferantenreklamation": "lieferantenreklamation",
    }

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create_document", "project_case_overview"],
                "description": "Plugin-Aktion: Dokument erzeugen oder Projektakte/Uebersicht laden",
            },
            "letter_type": {"type": "string", "enum": sorted(LETTER_TYPES), "description": "Art des Schreibens"},
            "communication_channel": {"type": "string", "enum": ["letter", "email", "both"], "description": "Ausgabekanal"},
            "subject": {"type": "string", "description": "Betreffzeile"},
            "email_subject": {"type": "string", "description": "Abweichender E-Mail-Betreff"},
            "content": {"type": "string", "description": "Optionaler Fließtext"},
            "email_intro": {"type": "string", "description": "Optionale kurze Einleitung der E-Mail"},
            "customer_name": {"type": "string", "description": "Name oder Firmenname des Empfängers"},
            "customer_company": {"type": "string", "description": "Firmenname des Empfängers"},
            "customer_first_name": {"type": "string", "description": "Vorname des Kontakts"},
            "customer_last_name": {"type": "string", "description": "Nachname des Kontakts"},
            "customer_contact": {"type": "string", "description": "Ansprechpartner"},
            "customer_title": {"type": "string", "description": "Akademischer Titel"},
            "customer_salutation": {"type": "string", "enum": ["Herr", "Frau", "Divers", "Firma", "Neutral"]},
            "customer_street": {"type": "string", "description": "Straße des Empfängers"},
            "customer_zip": {"type": "string", "description": "PLZ des Empfängers"},
            "customer_city": {"type": "string", "description": "Ort des Empfängers"},
            "customer_country": {"type": "string", "description": "Land"},
            "recipient_email": {"type": "string", "description": "E-Mail-Adresse des Empfängers"},
            "buyer_electronic_address": {"type": "string", "description": "Elektronische Adresse des Empfängers"},
            "buyer_electronic_address_scheme": {"type": "string", "description": "schemeID der elektronischen Empfängeradresse"},
            "seller_electronic_address": {"type": "string", "description": "Elektronische Adresse des Verkäufers"},
            "seller_electronic_address_scheme": {"type": "string", "description": "schemeID der elektronischen Verkäuferadresse"},
            "cc": {"type": "array", "items": {"type": "string"}, "description": "CC-Empfänger"},
            "bcc": {"type": "array", "items": {"type": "string"}, "description": "BCC-Empfänger"},
            "reply_to": {"type": "string", "description": "Antwortadresse"},
            "document_kind": {
                "type": "string",
                "enum": sorted(COMMERCIAL_DOCUMENT_TYPES | COMMUNICATION_DOCUMENT_TYPES),
                "description": "Fachlicher Dokumenttyp",
            },
            "issue_date": {"type": "string", "description": "Belegdatum"},
            "currency": {"type": "string", "default": "EUR", "description": "Währung"},
            "buyer_reference": {"type": "string", "description": "Käuferreferenz / Leitweg-ID"},
            "purchase_order_reference": {"type": "string", "description": "Bestellreferenz"},
            "contract_reference": {"type": "string", "description": "Vertragsreferenz"},
            "project_reference": {"type": "string", "description": "Projektreferenz"},
            "project_id": {"type": "string", "description": "Projekt-ID"},
            "customer_id": {"type": "string", "description": "Kunden-ID"},
            "source_document_id": {"type": "string", "description": "Quelldokument-ID"},
            "source_document_number": {"type": "string", "description": "Quelldokument-Nummer"},
            "source_document_kind": {"type": "string", "description": "Quelldokument-Typ"},
            "source_document": {"type": "object", "description": "Optionales Referenzdokument für Konvertierungen"},
            "source_position_line_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: explizite Auswahl zu übernehmender Positions-IDs aus dem Quelldokument",
            },
            "source_position_quantities": {
                "type": "object",
                "additionalProperties": {"type": ["string", "number"]},
                "description": "Optional: Teilmengen je Quellpositions-ID",
            },
            "revision_of": {"type": "string", "description": "Revision eines bestehenden Dokuments"},
            "cancels_document_id": {"type": "string", "description": "Dokument-ID eines stornierten Dokuments"},
            "conversion_action": {"type": "string", "description": "Konvertierungsaktion fuer Folgebelege"},
            "delivery_note_reference": {"type": "string", "description": "Lieferscheinreferenz"},
            "original_invoice_number": {"type": "string", "description": "Referenzierte Ursprungsrechnung"},
            "billing_reference_document_number": {"type": "string", "description": "Alternativer Name fuer Belegreferenz"},
            "service_period_start": {"type": "string", "description": "Leistungszeitraum Start"},
            "service_period_end": {"type": "string", "description": "Leistungszeitraum Ende"},
            "payment_due_date": {"type": "string", "description": "Zahlungsfälligkeit"},
            "payment_terms": {"type": "string", "description": "Zahlungsbedingungen"},
            "payment_reference": {"type": "string", "description": "Zahlungsreferenz"},
            "payment_method_code": {"type": "string", "description": "Zahlungsmittelcode"},
            "prepaid_amount": {"type": ["string", "number"], "description": "Anzahlung"},
            "rounding_amount": {"type": ["string", "number"], "description": "Rundungsdifferenz auf Zahlbetragsebene"},
            "shipping_costs": {"type": ["string", "number", "object", "array"], "description": "Versandkosten als separater Zuschlag"},
            "reverse_charge": {"type": "boolean", "description": "Steuerschuldnerschaft des Leistungsempfängers"},
            "tax_exemption_reason": {"type": "string", "description": "Steuerbefreiungsgrund auf Belegebene"},
            "tax_exemption_reason_code": {"type": "string", "description": "Steuerbefreiungs-Code auf Belegebene"},
            "document_allowances": {"type": "array", "items": {"type": "object"}, "description": "Abzüge auf Belegebene"},
            "document_charges": {"type": "array", "items": {"type": "object"}, "description": "Zuschläge auf Belegebene"},
            "template_mode": {
                "type": "string",
                "enum": sorted(TEMPLATE_MODES),
                "default": "auto",
                "description": "Welche Vorlagen erzeugt werden sollen",
            },
            "template_profile": {"type": "string", "description": "Vorlagenprofil"},
            "generate_templates": {"type": "boolean", "description": "Vorlagenartefakte erzeugen"},
            "persist_to_database": {"type": "boolean", "description": "Datenbankziel für Vorlagen-/Dokumentmetadaten"},
            "document_settings": {"type": "object", "description": "Dokumentspezifische Overrides"},
            "company_logo_file": IMAGE_UPLOAD_SCHEMA,
            "positions": {"type": "array", "minItems": 1, "items": POSITION_SCHEMA, "description": "Positionen für Angebote und Rechnungen"},
            "not_included": {"type": "array", "items": {"type": "string"}, "description": "Nicht enthaltene Leistungen"},
            "attachments": {
                "type": "array",
                "items": {
                    "anyOf": [
                        {"type": "string"},
                        IMAGE_UPLOAD_SCHEMA,
                    ]
                },
                "description": "Anlagen",
            },
            "customer_number": {"type": "string", "description": "Kundennummer"},
            "project_number": {"type": "string", "description": "Projekt- oder Vorgangsnummer"},
            "offer_number": {"type": "string", "description": "Angebotsnummer"},
            "order_number": {"type": "string", "description": "Auftragsnummer"},
            "invoice_number": {"type": "string", "description": "Rechnungsnummer"},
            "invoice_date": {"type": "string", "description": "Rechnungsdatum"},
            "invoice_amount": {"type": "string", "description": "Rechnungsbetrag"},
            "document_number": {"type": "string", "description": "Dokumentnummer"},
            "offer_valid_until": {"type": "string", "description": "Angebotsgültigkeit"},
            "delivery_date": {"type": "string", "description": "Liefertermin"},
            "due_date": {"type": "string", "description": "Fälligkeitsdatum"},
            "response_deadline": {"type": "string", "description": "Rückmeldefrist"},
            "preferred_contact_method": {"type": "string", "enum": ["email", "phone", "letter"]},
            "our_reference": {"type": "string", "description": "Unser Zeichen"},
            "your_reference": {"type": "string", "description": "Ihre Zeichen"},
            "your_message": {"type": "string", "description": "Ihre Nachricht"},
            "missing_information": {"type": "array", "items": {"type": "string"}},
            "ready_for_sending": {"type": "boolean"},
            "status": {
                "type": "string",
                "enum": [
                    "draft",
                    "needs_review",
                    "approved",
                    "ready",
                    "queued",
                    "sent",
                    "delivered",
                    "failed",
                    "returned",
                    "answered",
                    "archived",
                    "cancelled",
                ],
            },
            "reply_to_message_id": {"type": "string", "description": "ID der ursprünglichen Nachricht"},
            "conversation_id": {"type": "string", "description": "ID des Kommunikationsverlaufs"},
            "previous_message": {"type": "string", "description": "Inhalt der vorherigen Nachricht"},
            "reply_goal": {"type": "string", "description": "Ziel der Antwort"},
            "email_signature_name": {"type": "string", "description": "Abweichender Unterzeichner"},
            "default_tone": {"type": "string", "enum": sorted(TONE_OPTIONS), "description": "Gewünschte Tonalität"},
            "plugin_settings": {"type": "object", "description": "Optionale runtime Settings-Overrides"},
            "output_formats": {
                "type": "array",
                "items": {"type": "string", "enum": ["json", "text", "html", "document_html", "email_html"]},
                "description": "Zusätzliche Ausgabeartefakte",
            },
        },
        "required": ["letter_type", "subject"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "success": {"type": "boolean"},
            "document_id": {"type": "string"},
            "document_type": {"type": "string"},
            "status": {"type": "string"},
            "ready_for_sending": {"type": "boolean"},
            "letter": {"type": "string"},
            "email": {
                "type": "object",
                "properties": {
                    "to": {"type": "array", "items": {"type": "string"}},
                    "cc": {"type": "array", "items": {"type": "string"}},
                    "bcc": {"type": "array", "items": {"type": "string"}},
                    "reply_to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body_text": {"type": "string"},
                    "body_html": {"type": "string"},
                    "html_enabled": {"type": "boolean"},
                    "attachments": {"type": "array", "items": {"type": "object"}},
                },
            },
            "content": {
                "type": "object",
                "properties": {
                    "letter_text": {"type": "string"},
                    "email_text": {"type": "string"},
                    "email_html": {"type": "string"},
                    "document_html": {"type": "string"},
                },
            },
            "document": {"type": "object"},
            "commercial_document": {"type": "object"},
            "totals": {"type": "object"},
            "artifacts": {"type": "array"},
            "template": {"type": "object"},
            "settings": {"type": "object"},
            "validation": {"type": "object"},
            "delivery": {"type": "object"},
            "metadata": {"type": "object"},
            "error": {"type": ["string", "object"]},
        },
    }

    def __init__(self, settings: dict[str, Any] | None = None):
        self.settings = settings or {}
        self._number_sequences = NumberSequenceStore()

    def _document_type_rule(self, value: Any) -> dict[str, Any]:
        normalized = self._normalize_document_kind(value)
        base: dict[str, Any] = {
            "requires_positions": False,
            "requires_offer_valid_until": False,
            "requires_due_date": False,
            "requires_delivery_date": False,
            "supports_einvoice": False,
            "required_fields": [],
        }
        visited: set[str] = set()
        current = normalized
        while current and current not in visited:
            visited.add(current)
            rule = DOCUMENT_TYPE_RULES.get(current)
            if not rule:
                break
            inherited = str(rule.get("inherits") or "").strip().lower()
            if inherited:
                current = inherited
                for key, item in rule.items():
                    if key in {"inherits", "required_fields"}:
                        continue
                    base[key] = item
                required_fields = cast(list[Any], rule.get("required_fields") or [])
                if required_fields:
                    merged = list(cast(list[str], base.get("required_fields") or []))
                    for field in required_fields:
                        text = str(field).strip()
                        if text and text not in merged:
                            merged.append(text)
                    base["required_fields"] = merged
                continue
            for key, item in rule.items():
                if key == "inherits":
                    continue
                if key == "required_fields":
                    merged = list(cast(list[str], base.get("required_fields") or []))
                    for field in cast(list[Any], item or []):
                        text = str(field).strip()
                        if text and text not in merged:
                            merged.append(text)
                    base[key] = merged
                else:
                    base[key] = item
            break
        return base

    def _document_type_required_fields(self, value: Any) -> list[str]:
        return [str(item).strip() for item in cast(list[Any], self._document_type_rule(value).get("required_fields") or []) if str(item).strip()]

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        try:
            data = dict(input_data)
            action = str(data.get("action") or "create_document").strip().lower() or "create_document"
            if action == "project_case_overview":
                tenant_id = self._resolve_tenant_id(data)
                return self._build_project_case_overview(data, tenant_id)
            if action != "create_document":
                return {"error": f"Unbekannte Aktion: {action}"}

            runtime_settings = self._resolve_settings(data)
            company = self._build_company_settings(runtime_settings)
            self._apply_runtime_defaults(data, runtime_settings, company)
            letter_type = self._normalize_letter_type(data.get("letter_type") or data.get("document_kind"))
            if letter_type not in self.LETTER_TYPES:
                return {"error": f"Ungültiger letter_type: {letter_type}"}
            data["letter_type"] = letter_type
            if not str(data.get("document_kind") or "").strip():
                data["document_kind"] = letter_type

            subject = str(data.get("subject") or "").strip()
            if not subject:
                return {"error": "Betreff ist erforderlich"}

            tenant_id = self._resolve_tenant_id(data)
            self._enrich_conversion_context_from_persistence(data, tenant_id)
            conversion = self._apply_conversion_action(data)

            data["document_number"] = self._ensure_document_number(
                data,
                runtime_settings,
                defer_reservation=bool(data.get("persist_to_database")),
            )

            recipient = self._build_recipient(data)
            logo_asset = self._normalize_logo_asset(data, company)
            salutation = self._build_salutation(data, company)
            body_paragraphs = self._resolve_body_paragraphs(data, company)
            positions = self._normalize_positions(data.get("positions"))
            attachments = self._normalize_attachments(data.get("attachments"))
            commercial_document = self._build_commercial_document(data, company, recipient, positions)
            validation = self._build_validation(
                data,
                company,
                recipient,
                attachments,
                body_paragraphs,
                positions,
                commercial_document,
            )
            status = self._resolve_status(data, validation)
            einvoice_request = _as_mapping(data.get("einvoice")) if isinstance(data.get("einvoice"), dict) else {}
            einvoice = self._build_einvoice_payload(commercial_document, company, recipient, einvoice_request)
            validation, status, validator_block_reason = self._apply_einvoice_delivery_policy(
                data=data,
                runtime_settings=runtime_settings,
                validation=validation,
                status=status,
                einvoice=einvoice,
            )

            metadata = self._build_metadata(data, status)
            reference = self._build_reference(data, metadata)
            delivery = self._build_delivery(data, company, subject)
            email = self._build_email(data, runtime_settings, company, recipient, reference, subject, salutation, body_paragraphs, delivery)
            delivery["subject"] = str(email.get("subject") or delivery.get("subject") or "").strip()
            if validator_block_reason:
                delivery["blocked"] = True
                delivery["block_reason"] = validator_block_reason
            else:
                delivery["blocked"] = False
                delivery["block_reason"] = ""

            document_html = self._build_document_html(
                company=company,
                recipient=recipient,
                reference=reference,
                salutation=salutation,
                body_paragraphs=body_paragraphs,
                signatory_name=str(data.get("email_signature_name") or company["default_signatory_name"] or company["manager"] or company["name"]),
                logo_asset=logo_asset,
                attachments=attachments,
                commercial_document=commercial_document,
                document_status=status,
            )

            document: dict[str, Any] = {
                "document_type": letter_type,
                "status": status,
                "ready_for_sending": validation["status"] == "ready",
                "sender": company,
                "recipient": recipient,
                "reference": reference,
                "subject": subject,
                "salutation": salutation,
                "body": {
                    "tone": str(data.get("default_tone") or company["default_tone"]),
                    "paragraphs": body_paragraphs,
                    "closing": company["base_closing_text"],
                },
                "signatory": {
                    "name": str(data.get("email_signature_name") or company["default_signatory_name"] or company["manager"] or company["name"]),
                    "position": company["default_signatory_position"] or company["profession"],
                },
                "attachments": attachments,
                "positions": positions,
                "relationships": {
                    "source_document_id": str(data.get("source_document_id") or "").strip(),
                    "source_document_number": str(data.get("source_document_number") or "").strip(),
                    "source_document_kind": str(data.get("source_document_kind") or "").strip(),
                    "project_id": str(data.get("project_id") or "").strip(),
                    "customer_id": str(data.get("customer_id") or "").strip(),
                    "revision_of": str(data.get("revision_of") or "").strip(),
                    "cancels_document_id": str(data.get("cancels_document_id") or "").strip(),
                    "conversion_action": str(data.get("conversion_action") or "").strip(),
                },
                "commercial_document": commercial_document,
                "missing_information": validation["missing_information"],
                "reply_context": {
                    "reply_to_message_id": str(data.get("reply_to_message_id") or "").strip(),
                    "conversation_id": str(data.get("conversation_id") or "").strip(),
                    "previous_message": str(data.get("previous_message") or "").strip(),
                    "reply_goal": str(data.get("reply_goal") or "").strip(),
                },
                "metadata": metadata,
                "template": {
                    "mode": str(data.get("template_mode") or "auto").strip().lower() or "auto",
                    "profile": str(data.get("template_profile") or "").strip(),
                    "document_html": document_html,
                    "email_html": email["body_html"],
                },
            }

            letter = self._render_plain_letter(document)
            template = self._build_template_payload(
                data=data,
                company=company,
                recipient=recipient,
                reference=reference,
                body_paragraphs=body_paragraphs,
                letter=letter,
                email=email,
                document_html=document_html,
                logo_asset=logo_asset,
                commercial_document=commercial_document,
                document_status=status,
            )
            artifacts = self._build_artifacts(template, reference, data)

            database = self._build_database_payload(data, metadata, reference, template, commercial_document, status)
            email["attachments"] = self._build_email_attachments(
                data=data,
                runtime_settings=runtime_settings,
                template=template,
                reference=reference,
                document=document,
                artifacts=artifacts,
                einvoice=einvoice,
            )
            if database.get("enabled"):
                persisted_payload = self._persist_document(
                    data=data,
                    runtime_settings=runtime_settings,
                    metadata=metadata,
                    reference=reference,
                    template=template,
                    document=document,
                    commercial_document=commercial_document,
                    artifacts=artifacts,
                    email=email,
                    einvoice=einvoice,
                )
                database["persisted"] = persisted_payload
                resolved_number = str(persisted_payload.get("document_number") or "").strip()
                if resolved_number and resolved_number != str(reference.get("document_number") or "").strip():
                    self._apply_document_number(
                        resolved_number=resolved_number,
                        data=data,
                        reference=reference,
                        document=document,
                        template=template,
                        artifacts=artifacts,
                        database=database,
                    )
            dispatch = await self._dispatch_email_via_plugin(
                data=data,
                runtime_settings=runtime_settings,
                metadata=metadata,
                reference=reference,
                document=document,
                delivery=delivery,
                email=email,
                database=database,
                validation=validation,
            )
            document["status"] = status
            document["ready_for_sending"] = validation["status"] == "ready"

            output: dict[str, Any] = {
                "success": True,
                "document_id": str(metadata.get("document_id") or ""),
                "document_type": letter_type,
                "status": status,
                "ready_for_sending": validation["status"] == "ready",
                "letter": letter,
                "email": email,
                "content": {
                    "letter_text": letter,
                    "email_text": str(email.get("body_text") or ""),
                    "email_html": str(email.get("body_html") or ""),
                    "document_html": document_html,
                },
                "document": document,
                "commercial_document": commercial_document,
                "totals": commercial_document.get("totals") or {},
                "artifacts": artifacts,
                "template": template,
                "settings": {
                    "resolved": self._public_settings(runtime_settings),
                    "sources": {
                        "tenant": bool(self.settings),
                        "plugin_override": isinstance(data.get("plugin_settings"), dict),
                        "document_override": isinstance(data.get("document_settings"), dict),
                    },
                },
                "validation": validation,
                "delivery": delivery,
                "metadata": metadata,
                "database": database,
                "conversion": conversion,
            }
            output["delivery"]["dispatch"] = dispatch
            if einvoice:
                output["einvoice"] = einvoice
            return output
        except Exception as exc:
            return {"error": f"Fehler bei der Briefgenerierung: {exc}"}

    def _resolve_tenant_id(self, data: dict[str, Any]) -> str:
        return str(data.get("tenant_id") or self.settings.get("tenant_id") or "default").strip() or "default"

    @staticmethod
    def _document_from_persisted_row(row: dict[str, Any]) -> dict[str, Any]:
        snapshot = _as_mapping(row.get("snapshot"))
        return {
            "document_id": str(row.get("document_id") or "").strip(),
            "document_number": str(row.get("document_number") or "").strip(),
            "document_kind": str(row.get("document_kind") or "").strip().lower(),
            "status": str(row.get("status") or "").strip(),
            "created_at": str(row.get("created_at") or "").strip(),
            "sent_at": str(row.get("sent_at") or "").strip(),
            "document": _as_mapping(snapshot.get("document")),
            "commercial_document": _as_mapping(snapshot.get("commercial_document")),
            "template": _as_mapping(snapshot.get("template")),
            "email": _as_mapping(snapshot.get("email")),
        }

    @staticmethod
    def _expected_source_kind_for_action(action: str) -> str:
        action_text = action.strip().lower()
        if not action_text:
            return ""
        if "_to_" not in action_text:
            return ""
        return action_text.split("_to_", 1)[0].strip().lower()

    @staticmethod
    def _source_candidate_sort_key(item: dict[str, Any]) -> tuple[str, str]:
        return (
            str(item.get("sent_at") or "").strip(),
            str(item.get("created_at") or "").strip(),
        )

    def _resolve_source_document_from_persistent_context(self, data: dict[str, Any], tenant_id: str) -> dict[str, Any]:
        action = str(data.get("conversion_action") or "").strip().lower()
        expected_source_kind = self._expected_source_kind_for_action(action)
        if not expected_source_kind:
            expected_source_kind = str(data.get("source_document_kind") or "").strip().lower()

        project_id = str(data.get("project_id") or "").strip()
        customer_id = str(data.get("customer_id") or "").strip()
        if not project_id and not customer_id:
            return {}

        candidates = DEFAULT_PERSISTENCE.list_project_documents(
            tenant_id=tenant_id,
            project_id=project_id,
            customer_id=customer_id,
            limit=2000,
        )

        normalized: list[dict[str, Any]] = [self._document_from_persisted_row(item) for item in candidates]
        filtered: list[dict[str, Any]] = []
        for item in normalized:
            kind = str(item.get("document_kind") or "").strip().lower()
            if expected_source_kind and kind != expected_source_kind:
                continue
            status = str(item.get("status") or "").strip().lower()
            if status in {"cancelled"}:
                continue
            filtered.append(item)

        if not filtered:
            return {}

        filtered.sort(key=self._source_candidate_sort_key, reverse=True)
        return filtered[0]

    def _enrich_conversion_context_from_persistence(self, data: dict[str, Any], tenant_id: str) -> None:
        if not str(data.get("conversion_action") or "").strip():
            return

        source_document = _as_mapping(data.get("source_document"))
        source_document_id = str(data.get("source_document_id") or "").strip()
        source_document_number = str(data.get("source_document_number") or "").strip()

        if not source_document and not source_document_id and not source_document_number:
            resolved_source = self._resolve_source_document_from_persistent_context(data, tenant_id)
            if resolved_source:
                source_document = resolved_source
                source_document_id = str(resolved_source.get("document_id") or "").strip()
                source_document_number = str(resolved_source.get("document_number") or "").strip()
                data["source_document"] = resolved_source
                data["source_document_id"] = source_document_id
                data["source_document_number"] = source_document_number
                if not str(data.get("source_document_kind") or "").strip():
                    data["source_document_kind"] = str(resolved_source.get("document_kind") or "").strip()

        if not source_document and (source_document_id or source_document_number):
            persisted = DEFAULT_PERSISTENCE.get_document_by_id_or_number(
                tenant_id=tenant_id,
                document_id=source_document_id,
                document_number=source_document_number,
            )
            if persisted:
                source_document = self._document_from_persisted_row(persisted)
                data["source_document"] = source_document
                if not source_document_id:
                    source_document_id = str(source_document.get("document_id") or "").strip()
                    if source_document_id:
                        data["source_document_id"] = source_document_id
                if not source_document_number:
                    source_document_number = str(source_document.get("document_number") or "").strip()
                    if source_document_number:
                        data["source_document_number"] = source_document_number

        has_followups = isinstance(data.get("source_document_followups"), list) and len(cast(list[Any], data.get("source_document_followups") or [])) > 0
        if has_followups:
            return

        if not source_document_id and source_document:
            source_document_id = str(source_document.get("document_id") or "").strip()
        if not source_document_number and source_document:
            source_document_number = str(source_document.get("document_number") or "").strip()

        if not source_document_id and not source_document_number:
            return

        followups = DEFAULT_PERSISTENCE.list_follow_up_documents(
            tenant_id=tenant_id,
            source_document_id=source_document_id,
            source_document_number=source_document_number,
            limit=1000,
        )
        data["source_document_followups"] = [self._document_from_persisted_row(item) for item in followups]

    def _build_project_case_overview(self, data: dict[str, Any], tenant_id: str) -> dict[str, Any]:
        requested_project_id = str(data.get("project_id") or "").strip()
        requested_customer_id = str(data.get("customer_id") or "").strip()
        source_document_id = str(data.get("source_document_id") or "").strip()
        source_document_number = str(data.get("source_document_number") or "").strip()

        source_row = DEFAULT_PERSISTENCE.get_document_by_id_or_number(
            tenant_id=tenant_id,
            document_id=source_document_id,
            document_number=source_document_number,
        ) if (source_document_id or source_document_number) else None

        source_document = self._document_from_persisted_row(source_row) if source_row else {}
        source_relationships = _as_mapping(_as_mapping(source_document.get("document")).get("relationships")) if source_document else {}
        project_id = requested_project_id or str(source_relationships.get("project_id") or "").strip()
        customer_id = requested_customer_id or str(source_relationships.get("customer_id") or "").strip()

        timeline_rows = DEFAULT_PERSISTENCE.list_project_documents(
            tenant_id=tenant_id,
            project_id=project_id,
            customer_id=customer_id,
            limit=1000,
        )
        timeline_documents = [self._document_from_persisted_row(item) for item in timeline_rows]

        followups: list[dict[str, Any]] = []
        if source_document:
            followup_rows = DEFAULT_PERSISTENCE.list_follow_up_documents(
                tenant_id=tenant_id,
                source_document_id=str(source_document.get("document_id") or "").strip(),
                source_document_number=str(source_document.get("document_number") or "").strip(),
                limit=1000,
            )
            followups = [self._document_from_persisted_row(item) for item in followup_rows]

        chain_payload: dict[str, Any] = {
            "source_document": source_document,
            "source_document_followups": followups,
        }
        quantity_chain: dict[str, Any]
        if source_document:
            quantity_chain = build_quantity_chain_snapshot(chain_payload)
        else:
            quantity_chain = {
                "source_kind": "",
                "follow_up_documents": 0,
                "lines": [],
                "totals": {
                    "delivered_quantity": "0",
                    "invoiced_quantity": "0",
                    "credited_quantity": "0",
                    "open_quantity": "0",
                },
            }

        status_counts: dict[str, int] = {}
        timeline: list[dict[str, Any]] = []
        for item in timeline_documents:
            status = str(item.get("status") or "").strip().lower() or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

            document_payload = _as_mapping(item.get("document"))
            relationships = _as_mapping(document_payload.get("relationships"))
            commercial_document = _as_mapping(item.get("commercial_document"))
            customer_visible = _as_mapping(commercial_document.get("customer_visible"))
            totals = _as_mapping(customer_visible.get("totals"))

            timeline.append(
                {
                    "document_id": str(item.get("document_id") or "").strip(),
                    "document_number": str(item.get("document_number") or "").strip(),
                    "document_kind": str(item.get("document_kind") or "").strip(),
                    "status": str(item.get("status") or "").strip(),
                    "created_at": str(item.get("created_at") or "").strip(),
                    "sent_at": str(item.get("sent_at") or "").strip(),
                    "source_document_id": str(relationships.get("source_document_id") or "").strip(),
                    "source_document_number": str(relationships.get("source_document_number") or "").strip(),
                    "conversion_action": str(relationships.get("conversion_action") or "").strip(),
                    "project_id": str(relationships.get("project_id") or "").strip(),
                    "customer_id": str(relationships.get("customer_id") or "").strip(),
                    "payable_amount": str(totals.get("payable_amount") or "").strip(),
                }
            )

        return {
            "success": True,
            "action": "project_case_overview",
            "project_case": {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "customer_id": customer_id,
                "timeline": sorted(timeline, key=lambda item: str(item.get("created_at") or "")),
                "status_view": {
                    "document_count": len(timeline),
                    "statuses": status_counts,
                },
                "source_document": {
                    "document_id": str(source_document.get("document_id") or "").strip(),
                    "document_number": str(source_document.get("document_number") or "").strip(),
                    "document_kind": str(source_document.get("document_kind") or "").strip(),
                } if source_document else {},
                "quantity_chain": quantity_chain,
            },
        }

    def _resolve_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        plugin_override = _as_mapping(data.get("plugin_settings"))
        document_override = _as_mapping(data.get("document_settings"))
        resolved = resolve_settings(("tenant", self.settings), ("plugin", plugin_override), ("document_override", document_override))
        return resolved.resolved_settings

    def _apply_position_defaults(self, data: dict[str, Any], runtime_settings: dict[str, Any]) -> None:
        raw_positions = data.get("positions")
        if not isinstance(raw_positions, list):
            return

        default_unit_code = str(runtime_settings.get("default_unit_code") or "C62").strip() or "C62"
        default_tax_category = str(runtime_settings.get("default_tax_category") or "S").strip().upper() or "S"
        raw_default_tax_rate = runtime_settings.get("default_tax_rate")
        default_tax_rate = "19" if raw_default_tax_rate in (None, "") else str(raw_default_tax_rate).strip() or "19"
        default_tax_exemption_enabled = _settings_truthy(runtime_settings.get("default_tax_exemption_enabled"))
        default_tax_exemption_reason = str(runtime_settings.get("default_tax_exemption_reason") or "").strip()
        default_tax_exemption_reason_code = str(runtime_settings.get("default_tax_exemption_reason_code") or "").strip()
        default_reverse_charge_enabled = _settings_truthy(runtime_settings.get("default_reverse_charge_enabled"))

        for item in cast(list[Any], raw_positions):
            if not isinstance(item, dict):
                continue

            position = cast(dict[str, Any], item)
            if not str(position.get("unit_code") or "").strip():
                position["unit_code"] = default_unit_code

            resolved_unit_code = str(position.get("unit_code") or default_unit_code).strip() or default_unit_code
            if not str(position.get("price_base_quantity_unit_code") or "").strip():
                position["price_base_quantity_unit_code"] = resolved_unit_code

            if not str(position.get("vat_category") or "").strip():
                position["vat_category"] = default_tax_category

            resolved_tax_category = str(position.get("vat_category") or default_tax_category).strip().upper() or default_tax_category
            if not str(position.get("vat_rate") or "").strip():
                position["vat_rate"] = default_tax_rate

            if resolved_tax_category == "AE" and default_reverse_charge_enabled and not str(position.get("tax_exemption_reason") or "").strip():
                position["tax_exemption_reason"] = default_tax_exemption_reason or str(runtime_settings.get("default_reverse_charge_note") or "Reverse charge").strip()
                if default_tax_exemption_reason_code and not str(position.get("tax_exemption_reason_code") or "").strip():
                    position["tax_exemption_reason_code"] = default_tax_exemption_reason_code

            if resolved_tax_category in {"E", "Z", "O", "K", "G"} and default_tax_exemption_enabled:
                if not str(position.get("tax_exemption_reason") or "").strip() and default_tax_exemption_reason:
                    position["tax_exemption_reason"] = default_tax_exemption_reason
                if not str(position.get("tax_exemption_reason_code") or "").strip() and default_tax_exemption_reason_code:
                    position["tax_exemption_reason_code"] = default_tax_exemption_reason_code

    def _apply_runtime_defaults(self, data: dict[str, Any], runtime_settings: dict[str, Any], company: dict[str, str]) -> None:
        default_einvoice_enabled_raw = runtime_settings.get("default_einvoice_enabled")
        if isinstance(default_einvoice_enabled_raw, bool):
            default_einvoice_enabled = default_einvoice_enabled_raw
        else:
            default_einvoice_enabled = str(default_einvoice_enabled_raw or "").strip().lower() in {"1", "true", "yes", "on"}

        default_reverse_charge_enabled = _settings_truthy(runtime_settings.get("default_reverse_charge_enabled"))
        default_tax_exemption_enabled = _settings_truthy(runtime_settings.get("default_tax_exemption_enabled"))

        self._apply_position_defaults(data, runtime_settings)

        if not str(data.get("currency") or "").strip():
            data["currency"] = str(company.get("default_currency") or "EUR").strip() or "EUR"

        if not str(data.get("payment_terms") or "").strip():
            data["payment_terms"] = str(company.get("default_payment_terms") or "").strip()

        if not str(data.get("payment_method_code") or "").strip():
            data["payment_method_code"] = str(company.get("default_payment_method_code") or "58").strip() or "58"

        if not str(data.get("buyer_reference") or "").strip() and company.get("default_buyer_reference"):
            data["buyer_reference"] = str(company.get("default_buyer_reference") or "").strip()

        if not str(data.get("payment_reference") or "").strip() and company.get("default_payment_reference"):
            data["payment_reference"] = str(company.get("default_payment_reference") or "").strip()

        if not str(data.get("seller_electronic_address") or "").strip() and company.get("electronic_address"):
            data["seller_electronic_address"] = str(company.get("electronic_address") or "").strip()

        if not str(data.get("seller_electronic_address_scheme") or "").strip() and company.get("electronic_address_scheme"):
            data["seller_electronic_address_scheme"] = str(company.get("electronic_address_scheme") or "").strip()

        position_categories: set[str] = set()
        for raw_position in cast(list[Any], data.get("positions") or []):
            position = _as_mapping(raw_position)
            category = str(position.get("vat_category") or "").strip().upper()
            if category:
                position_categories.add(category)
        default_tax_category = str(company.get("default_tax_category") or runtime_settings.get("default_tax_category") or "").strip().upper()
        has_reverse_charge_context = default_tax_category == "AE" or "AE" in position_categories
        has_exemption_context = default_tax_category in {"E", "Z", "O", "K", "G"} or bool(position_categories & {"E", "Z", "O", "K", "G"})

        if data.get("reverse_charge") is None and default_reverse_charge_enabled and has_reverse_charge_context:
            data["reverse_charge"] = True

        if not str(data.get("tax_exemption_reason") or "").strip() and company.get("default_tax_exemption_reason") and (default_tax_exemption_enabled or has_exemption_context or has_reverse_charge_context):
            data["tax_exemption_reason"] = str(company.get("default_tax_exemption_reason") or company.get("default_reverse_charge_note") or "").strip()

        if not str(data.get("tax_exemption_reason_code") or "").strip() and company.get("default_tax_exemption_reason_code") and (default_tax_exemption_enabled or has_exemption_context or has_reverse_charge_context):
            data["tax_exemption_reason_code"] = str(company.get("default_tax_exemption_reason_code") or "").strip()

        document_kind = self._normalize_document_kind(data.get("document_kind") or data.get("letter_type"))
        type_rule = self._document_type_rule(document_kind)

        if bool(type_rule.get("requires_due_date")) and not str(data.get("payment_due_date") or "").strip():
            payment_days = str(company.get("default_payment_days") or "14").strip() or "14"
            try:
                days = max(0, int(payment_days))
            except ValueError:
                days = 14

            issue_date = _parse_date(data.get("issue_date")) or datetime.now().date()
            data["issue_date"] = issue_date.isoformat()
            data["payment_due_date"] = (issue_date + timedelta(days=days)).isoformat()

        if bool(type_rule.get("requires_offer_valid_until")) and not str(data.get("offer_valid_until") or "").strip():
            offer_validity_days = str(runtime_settings.get("default_offer_validity_days") or "30").strip() or "30"
            try:
                offer_days = max(0, int(offer_validity_days))
            except ValueError:
                offer_days = 30

            issue_date = _parse_date(data.get("issue_date")) or datetime.now().date()
            data.setdefault("issue_date", issue_date.isoformat())
            data["offer_valid_until"] = (issue_date + timedelta(days=offer_days)).isoformat()

        einvoice_payload: dict[str, Any] = _as_mapping(data.get("einvoice"))
        if not einvoice_payload and default_einvoice_enabled:
            einvoice_payload = {
                "enabled": True,
                "standard": str(runtime_settings.get("default_einvoice_standard") or "xrechnung"),
                "profile": str(runtime_settings.get("default_einvoice_profile") or "en16931"),
                "syntax": str(runtime_settings.get("default_einvoice_syntax") or "UBL"),
            }
        elif einvoice_payload:
            if "standard" not in einvoice_payload and runtime_settings.get("default_einvoice_standard"):
                einvoice_payload["standard"] = str(runtime_settings.get("default_einvoice_standard"))
            if "profile" not in einvoice_payload and runtime_settings.get("default_einvoice_profile"):
                einvoice_payload["profile"] = str(runtime_settings.get("default_einvoice_profile"))
            if "syntax" not in einvoice_payload and runtime_settings.get("default_einvoice_syntax"):
                einvoice_payload["syntax"] = str(runtime_settings.get("default_einvoice_syntax"))

        if einvoice_payload:
            if bool(type_rule.get("supports_einvoice")):
                data["einvoice"] = einvoice_payload
            else:
                data.pop("einvoice", None)

    def _plugin_setting_keys(self) -> set[str]:
        raw_fields = PLUGIN_META.get("settingsFields")
        if not isinstance(raw_fields, list):
            return set()
        keys: set[str] = set()
        for raw_entry in cast(list[Any], raw_fields):
            entry = _as_mapping(raw_entry)
            if not entry:
                continue
            key = str(entry.get("key") or "").strip()
            if key:
                keys.add(key)
        return keys

    def _plugin_setting_field_map(self) -> dict[str, dict[str, Any]]:
        raw_fields = PLUGIN_META.get("settingsFields")
        if not isinstance(raw_fields, list):
            return {}
        field_map: dict[str, dict[str, Any]] = {}
        for raw_entry in cast(list[Any], raw_fields):
            entry = _as_mapping(raw_entry)
            key = str(entry.get("key") or "").strip()
            if key:
                field_map[key] = entry
        return field_map

    def _normalize_document_kind(self, value: Any) -> str:
        return normalize_document_kind(value)

    def _ensure_document_number(self, data: dict[str, Any], runtime_settings: dict[str, Any], *, defer_reservation: bool = False) -> str:
        existing = str(data.get("document_number") or "").strip()
        if existing:
            return existing
        if defer_reservation:
            return ""
        tenant_id = str(data.get("tenant_id") or self.settings.get("tenant_id") or "default").strip() or "default"
        sequence_settings = resolve_number_sequence_settings(
            runtime_settings,
            document_kind=str(data.get("document_kind") or data.get("letter_type") or "DOC"),
            tenant_id=tenant_id,
        )
        return self._number_sequences.next_number(
            prefix=sequence_settings.prefix,
            sequence_kind=sequence_settings.sequence_kind,
            tenant_id=tenant_id,
            year=sequence_settings.year,
            width=sequence_settings.width,
            pattern=sequence_settings.pattern,
            start_value=sequence_settings.start_value,
            year_reset=sequence_settings.year_reset,
        )

    def _normalize_logo_asset(self, data: dict[str, Any], company: dict[str, str]) -> dict[str, str]:
        raw = data.get("company_logo_file")
        if isinstance(raw, dict):
            payload = _as_mapping(raw)
            name = str(payload.get("name") or payload.get("file_name") or "").strip()
            mime_type = str(payload.get("mime_type") or "").strip()
            data_url = str(payload.get("data_url") or "").strip()
            content_base64 = str(payload.get("content_base64") or "").strip()
            url = str(payload.get("url") or "").strip()
            if not data_url and content_base64 and mime_type:
                data_url = f"data:{mime_type};base64,{content_base64}"
            return {
                "name": name or "Logo",
                "file_name": str(payload.get("file_name") or name or "logo").strip(),
                "mime_type": mime_type,
                "data_url": data_url or url,
                "fallback_text": str(payload.get("fallback_text") or "").strip(),
                "source": "upload" if data_url or content_base64 else ("url" if url else "unset"),
            }

        logo_url = str(company.get("logo_url") or "").strip()
        return {
            "name": "Kernschmiede" if str(company.get("logo_origin") or "") == "system" else "Logo",
            "file_name": "",
            "mime_type": "",
            "data_url": logo_url,
            "fallback_text": str(company.get("logo_fallback_text") or "").strip(),
            "source": str(company.get("logo_origin") or ("settings" if logo_url else "unset")),
        }

    def _normalize_positions(self, raw_positions: Any) -> list[dict[str, Any]]:
        return service_normalize_positions(raw_positions)

    def _apply_conversion_action(self, data: dict[str, Any]) -> dict[str, Any]:
        return apply_conversion_action(data)

    def _normalize_money_adjustments(self, raw_value: Any) -> dict[str, Any]:
        return service_normalize_money_adjustments(raw_value)

    def _build_commercial_document(
        self,
        data: dict[str, Any],
        company: dict[str, str],
        recipient: dict[str, str],
        positions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return build_commercial_document(data, company, recipient, positions)

    def _build_document_html(
        self,
        *,
        company: dict[str, str],
        recipient: dict[str, str],
        reference: dict[str, str],
        salutation: str,
        body_paragraphs: list[str],
        signatory_name: str,
        logo_asset: dict[str, str],
        attachments: list[dict[str, Any]],
        commercial_document: dict[str, Any],
        document_status: str,
    ) -> str:
        return build_document_html(
            company=company,
            recipient=recipient,
            reference=reference,
            salutation=salutation,
            body_paragraphs=body_paragraphs,
            signatory_name=signatory_name,
            logo_asset=logo_asset,
            attachments=attachments,
            commercial_document=commercial_document,
            document_status=document_status,
        )

    def _build_template_payload(
        self,
        *,
        data: dict[str, Any],
        company: dict[str, str],
        recipient: dict[str, str],
        reference: dict[str, str],
        body_paragraphs: list[str],
        letter: str,
        email: dict[str, Any],
        document_html: str,
        logo_asset: dict[str, str],
        commercial_document: dict[str, Any],
        document_status: str,
    ) -> dict[str, Any]:
        return build_template_payload(
            data=data,
            company=company,
            recipient=recipient,
            reference=reference,
            body_paragraphs=body_paragraphs,
            letter=letter,
            email=email,
            document_html=document_html,
            logo_asset=logo_asset,
            commercial_document=commercial_document,
            document_status=document_status,
        )

    def _build_artifacts(self, template: dict[str, Any], reference: dict[str, str], data: dict[str, Any]) -> list[dict[str, Any]]:
        return build_artifacts(template, reference, data)

    def _build_database_payload(
        self,
        data: dict[str, Any],
        metadata: dict[str, Any],
        reference: dict[str, str],
        template: dict[str, Any],
        commercial_document: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        return build_database_payload(data, metadata, reference, template, commercial_document, status)

    def _build_einvoice_payload(
        self,
        commercial_document: dict[str, Any],
        company: dict[str, str],
        recipient: dict[str, str],
        einvoice_request: dict[str, Any],
    ) -> dict[str, Any]:
        if not einvoice_request:
            return {}

        if not bool(einvoice_request.get("enabled") or einvoice_request.get("standard") or einvoice_request.get("profile")):
            return {}

        standard = str(einvoice_request.get("standard") or einvoice_request.get("profile") or "xrechnung").strip().lower()
        if standard in {"zugferd", "pdfa3", "zugferd_2_3", "zugferd_2.3"}:
            return build_zugferd_package(commercial_document, company, recipient)

        xrechnung = build_xrechnung_xml(commercial_document, company, recipient)
        return {**xrechnung, "validation": xrechnung}

    def _artifact_storage_key(self, artifact_directory: str, file_name: str) -> str:
        base_dir = artifact_directory.strip().strip("/")
        normalized_name = file_name.strip().lstrip("/")
        if not base_dir:
            return f"business_letter/{normalized_name}"
        return f"{base_dir}/{normalized_name}"

    def _validation_report_artifacts(self, einvoice: dict[str, Any], artifact_directory: str) -> list[dict[str, Any]]:
        report_dir_raw = str(os.getenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", "")).strip()
        if not report_dir_raw:
            return []
        report_dir = Path(report_dir_raw)
        if not report_dir.is_dir():
            return []

        report_files: list[str] = []
        official_validation = _as_mapping(einvoice.get("official_validation"))
        for section_name in ("schema", "schematron"):
            section = _as_mapping(official_validation.get(section_name))
            report_file = str(section.get("report_file") or "").strip()
            if report_file:
                report_files.append(report_file)
        summary_hint = str(_as_mapping(official_validation.get("schema")).get("report_file") or "").strip()
        if summary_hint.endswith("_official_schema.txt"):
            report_files.append(summary_hint.replace("_official_schema.txt", "_official_summary.json"))

        artifacts: list[dict[str, Any]] = []
        seen: set[str] = set()
        for file_name in report_files:
            if file_name in seen:
                continue
            seen.add(file_name)
            report_path = report_dir / file_name
            if not report_path.is_file():
                continue
            mime_type = "application/json" if report_path.suffix.lower() == ".json" else "text/plain"
            artifacts.append(
                {
                    "artifact_kind": "validation_report",
                    "storage_key": self._artifact_storage_key(artifact_directory, file_name),
                    "mime_type": mime_type,
                    "payload_text": report_path.read_text(encoding="utf-8"),
                    "metadata": {"report_file": file_name, "source": "validation"},
                }
            )
        return artifacts

    def _guest_mirror_with_retry(
        self,
        *,
        guest_db_path: str,
        document_id: str,
        document_number: str,
        payload: dict[str, Any],
        artifacts: list[dict[str, Any]],
        retries: int,
    ) -> dict[str, Any]:
        attempts = max(1, retries + 1)
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                result = DEFAULT_PERSISTENCE.mirror_to_guest_database(
                    guest_db_path=guest_db_path,
                    document_id=document_id,
                    document_number=document_number,
                    payload=payload,
                    artifacts=artifacts,
                )
                result["attempts"] = attempt
                result["status"] = "ok"
                return result
            except Exception as exc:
                last_error = exc
        if last_error is None:
            raise RuntimeError("Dual-save mirror failed without explicit error.")
        raise last_error

    def _persist_document(
        self,
        *,
        data: dict[str, Any],
        runtime_settings: dict[str, Any],
        metadata: dict[str, Any],
        reference: dict[str, str],
        template: dict[str, Any],
        document: dict[str, Any],
        commercial_document: dict[str, Any],
        artifacts: list[dict[str, Any]],
        email: dict[str, Any],
        einvoice: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        tenant_id = str(data.get("tenant_id") or self.settings.get("tenant_id") or "default").strip() or "default"
        document_id = str(metadata.get("document_id") or "").strip()
        document_number = str(reference.get("document_number") or document.get("reference", {}).get("document_number") or "").strip()
        created_by = str(metadata.get("created_by") or "plugin:business_letter").strip()
        approved_by = str(metadata.get("approved_by") or "").strip()
        revision_number = int(data.get("revision_number") or 1)
        dual_save_enabled = _settings_truthy(runtime_settings.get("dual_save_enabled"))
        dual_save_failure_mode = str(runtime_settings.get("dual_save_failure_mode") or "warn").strip().lower() or "warn"
        dual_save_retry_attempts = max(0, _int_setting(runtime_settings.get("dual_save_retry_attempts"), 3))
        artifact_directory = str(runtime_settings.get("artifact_directory") or "business_letter").strip() or "business_letter"
        retention_days = max(0, _int_setting(runtime_settings.get("retention_days"), 3650))
        verify_hashes = _settings_truthy(runtime_settings.get("enable_hash_verification"))
        immutable_after_release = _settings_truthy(runtime_settings.get("lock_released_documents"))
        store_validation_reports = _settings_truthy(runtime_settings.get("store_validation_reports")) or _settings_truthy(runtime_settings.get("archive_validation_report"))
        archive_pdf_xml_together = _settings_truthy(runtime_settings.get("archive_pdf_xml_together"))
        store_xml_artifact = _settings_truthy(runtime_settings.get("store_xml_artifact"))
        archive_group = f"archive:{document_number or document_id}" if archive_pdf_xml_together else ""

        payload_map: dict[str, str] = {
            "json": json.dumps({"document": document, "template": template, "commercial_document": commercial_document, "email": email}, ensure_ascii=False, sort_keys=True, default=str),
            "html": str(template.get("document_html") or ""),
            "email_html": str(email.get("body_html") or ""),
        }
        if any(str(artifact.get("kind") or "").strip() == "pdf" for artifact in artifacts):
            payload_map["pdf"] = build_pdf_payload(template, reference, document)
        if einvoice:
            xml_payload = str(einvoice.get("xml") or "")
            if xml_payload:
                standard_name = str(einvoice.get("standard") or "xrechnung").strip().lower()
                payload_map[standard_name] = xml_payload
                payload_map[f"{standard_name}_xml"] = xml_payload

        artifacts_for_persistence: list[dict[str, Any]] = []
        for artifact in artifacts:
            artifact_kind = str(artifact.get("kind") or "json").strip()
            payload_text = payload_map.get(artifact_kind, payload_map["json"])
            file_name = str(artifact.get("file_name") or artifact_kind)
            artifacts_for_persistence.append(
                {
                    "artifact_kind": artifact_kind,
                    "storage_key": self._artifact_storage_key(artifact_directory, file_name),
                    "mime_type": str(artifact.get("mime_type") or "application/octet-stream"),
                    "payload_text": payload_text,
                    "metadata": {"artifact": artifact},
                    "archive_group": archive_group if artifact_kind in {"pdf", "xrechnung_xml", "zugferd_xml", "cii_xml"} else "",
                }
            )

        if einvoice and (store_xml_artifact or archive_pdf_xml_together):
            xml_payload = str(einvoice.get("xml") or "")
            if xml_payload:
                standard_name = str(einvoice.get("standard") or "xrechnung").strip().lower()
                xml_kind = f"{standard_name}_xml"
                xml_file_name = "factur-x.xml" if standard_name == "zugferd" else f"{standard_name}.xml"
                artifacts_for_persistence.append(
                    {
                        "artifact_kind": xml_kind,
                        "storage_key": self._artifact_storage_key(artifact_directory, xml_file_name),
                        "mime_type": "application/xml",
                        "payload_text": xml_payload,
                        "metadata": {"einvoice": einvoice},
                        "archive_group": archive_group if archive_pdf_xml_together else "",
                    }
                )

        if store_validation_reports and einvoice:
            artifacts_for_persistence.extend(self._validation_report_artifacts(einvoice, artifact_directory))

        numbering_payload: dict[str, Any] | None = None
        if not document_number:
            sequence_settings = resolve_number_sequence_settings(
                runtime_settings,
                document_kind=str(data.get("document_kind") or data.get("letter_type") or "DOC"),
                tenant_id=tenant_id,
            )
            numbering_payload = {
                "prefix": sequence_settings.prefix,
                "sequence_kind": sequence_settings.sequence_kind,
                "year": sequence_settings.year,
                "width": sequence_settings.width,
                "pattern": sequence_settings.pattern,
                "start_value": sequence_settings.start_value,
                "year_reset": sequence_settings.year_reset,
            }

        persisted = DEFAULT_PERSISTENCE.persist_bundle_transactional(
            tenant_id=tenant_id,
            document_id=document_id,
            document_number=document_number,
            numbering=numbering_payload,
            template_profile=str(template.get("profile") or "").strip(),
            status=str(metadata.get("status") or "draft"),
            data_snapshot={"document": document, "template": template, "email": email, "commercial_document": commercial_document},
            document_kind=str(commercial_document.get("document_kind") or document.get("document_type") or "allgemein"),
            snapshot_json={"document": document, "template": template, "commercial_document": commercial_document, "email": email},
            created_by=created_by,
            approved_by=approved_by,
            sent_at=str(metadata.get("sent_at") or None) or None,
            revision_number=revision_number,
            reason=str(data.get("revision_reason") or "initial"),
            artifacts=artifacts_for_persistence,
            retention_days=retention_days,
            immutable_after_release=immutable_after_release,
            verify_hashes=verify_hashes,
        )

        resolved_document_number = str(persisted.get("document_number") or document_number).strip()
        for entry in artifacts_for_persistence:
            if str(entry.get("storage_key") or "").startswith("business_letter/") and ("business_letter/business_letter" in str(entry.get("storage_key") or "") or "business_letter/" + document_id in str(entry.get("storage_key") or "")):
                kind = str(entry.get("artifact_kind") or "json").strip() or "json"
                entry["storage_key"] = f"business_letter/{resolved_document_number}.{kind}"

        guest_mirror: dict[str, Any] | None = None
        if dual_save_enabled:
            guest_db_default = Path("data") / "database" / "chat_system.db"
            guest_db_path = str(data.get("guest_system_database_path") or runtime_settings.get("guest_system_database_path") or guest_db_default)
            mirror_payload: dict[str, Any] = {
                "metadata": metadata,
                "reference": reference,
                "document": document,
                "template": template,
                "commercial_document": commercial_document,
                "email": email,
                "einvoice": einvoice or {},
            }
            try:
                guest_mirror = self._guest_mirror_with_retry(
                    guest_db_path=guest_db_path,
                    document_id=document_id,
                    document_number=resolved_document_number,
                    payload=mirror_payload,
                    artifacts=artifacts_for_persistence,
                    retries=dual_save_retry_attempts,
                )
            except Exception as exc:
                if dual_save_failure_mode == "fail":
                    raise RuntimeError(f"Dual-save failed after {dual_save_retry_attempts + 1} attempts: {exc}") from exc
                guest_mirror = {
                    "path": guest_db_path,
                    "document_id": document_id,
                    "document_number": resolved_document_number,
                    "artifacts": len(artifacts_for_persistence),
                    "attempts": dual_save_retry_attempts + 1,
                    "status": "queued" if dual_save_failure_mode == "queue" else "warning",
                    "error": str(exc),
                }

        return {
            "tenant_id": tenant_id,
            "document_number": resolved_document_number,
            "plugin_storage": persisted,
            "guest_system_storage": guest_mirror,
            "dual_save": {
                "enabled": dual_save_enabled,
                "failure_mode": dual_save_failure_mode,
                "retry_attempts": dual_save_retry_attempts,
                "artifact_directory": artifact_directory,
                "retention_days": retention_days,
                "hash_verification": verify_hashes,
                "immutable_after_release": immutable_after_release,
            },
        }

    def _apply_document_number(
        self,
        *,
        resolved_number: str,
        data: dict[str, Any],
        reference: dict[str, str],
        document: dict[str, Any],
        template: dict[str, Any],
        artifacts: list[dict[str, Any]],
        database: dict[str, Any],
    ) -> None:
        data["document_number"] = resolved_number
        reference["document_number"] = resolved_number
        document_reference = _as_mapping(document.get("reference"))
        document_reference["document_number"] = resolved_number
        document["reference"] = document_reference
        template_reference = _as_mapping(template.get("reference"))
        template_reference["document_number"] = resolved_number
        template["reference"] = template_reference
        database["document_number"] = resolved_number
        database["storage_key"] = f"business_letter:{resolved_number}"

        layout = _as_mapping(template.get("layout"))
        default_filename_pattern = str(layout.get("default_filename_pattern") or "{document_number}").strip() or "{document_number}"
        default_pdf_filename_pattern = str(layout.get("default_pdf_filename_pattern") or "{document_number}.pdf").strip() or "{document_number}.pdf"

        for artifact in artifacts:
            kind = str(artifact.get("kind") or "json").strip() or "json"
            pattern = default_pdf_filename_pattern if kind == "pdf" else default_filename_pattern
            extension = {
                "email_html": ".email.html",
                "html": ".html",
                "json": ".json",
                "pdf": ".pdf",
            }.get(kind, f".{kind}")
            file_name = render_artifact_file_name(pattern, reference, data, extension=extension)
            artifact["file_name"] = file_name
            artifact["storage_reference"] = f"business_letter/{file_name}"

    def _public_settings(self, runtime_settings: dict[str, Any]) -> dict[str, Any]:
        public_keys = self._plugin_setting_keys()
        visible = public_settings(runtime_settings, public_keys)
        field_map = self._plugin_setting_field_map()
        masked: dict[str, Any] = {}
        for key, value in visible.items():
            field_type = str(field_map.get(key, {}).get("type") or "").strip().lower()
            if field_type == "password" or _SENSITIVE_SETTING_KEY_PATTERN.search(key):
                masked[key] = "********"
            else:
                masked[key] = value
        return masked

    def _normalize_letter_type(self, value: Any) -> str:
        return normalize_letter_type(value, self.LETTER_TYPE_ALIASES)

    def _build_company_settings(self, runtime_settings: dict[str, Any]) -> dict[str, str]:
        return build_company_settings(runtime_settings)

    def _build_recipient(self, data: dict[str, Any]) -> dict[str, str]:
        return build_recipient(data)

    def _build_salutation(self, data: dict[str, Any], company: dict[str, str]) -> str:
        return build_salutation(data, company)

    def _resolve_body_paragraphs(self, data: dict[str, Any], company: dict[str, str]) -> list[str]:
        return resolve_body_paragraphs(data, company)

    def _normalize_attachments(self, raw_attachments: Any) -> list[dict[str, Any]]:
        return normalize_attachments(raw_attachments)

    def _build_validation(
        self,
        data: dict[str, Any],
        company: dict[str, str],
        recipient: dict[str, str],
        attachments: list[dict[str, Any]],
        body_paragraphs: list[str],
        positions: list[dict[str, Any]],
        commercial_document: dict[str, Any],
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        missing_information: list[str] = []

        channel = str(data.get("communication_channel") or "letter").strip().lower()
        if channel not in {"letter", "email", "both"}:
            channel = "letter"

        subject = str(data.get("subject") or "").strip()
        if not subject:
            errors.append("Betreff fehlt.")
            missing_information.append("Betreff")

        recipient_name = str(recipient.get("name") or "").strip()
        recipient_company = str(recipient.get("company") or "").strip()
        if not recipient_name and not recipient_company:
            errors.append("Empfängername oder Firma fehlt.")
            missing_information.append("Empfängername oder Firma")

        commercial_kind = str(data.get("document_kind") or data.get("letter_type") or "").strip().lower()
        source_document_id = str(data.get("source_document_id") or "").strip()
        source_document_number = str(data.get("source_document_number") or "").strip()
        source_document_kind = str(data.get("source_document_kind") or "").strip().lower()
        has_source_reference = bool(source_document_id or source_document_number)
        type_rule = self._document_type_rule(commercial_kind)
        if bool(type_rule.get("requires_positions")) and not positions:
            errors.append("Für kaufmännische Dokumente sind Positionen erforderlich.")
            missing_information.append("Positionen")

        if channel in {"letter", "both"}:
            if not recipient.get("street"):
                errors.append("Vollständige Empfängeradresse fehlt (Straße).")
                missing_information.append("Straße und Hausnummer des Empfängers")
            if not recipient.get("postal_code"):
                errors.append("Vollständige Empfängeradresse fehlt (PLZ).")
                missing_information.append("PLZ des Empfängers")
            if not recipient.get("city"):
                errors.append("Vollständige Empfängeradresse fehlt (Ort).")
                missing_information.append("Ort des Empfängers")

        recipient_email = str(data.get("recipient_email") or "").strip()
        if channel in {"email", "both"}:
            if not recipient_email:
                errors.append("Empfänger-E-Mail fehlt.")
                missing_information.append("E-Mail-Adresse des Empfängers")
            elif not EMAIL_RE.match(recipient_email):
                errors.append("Empfänger-E-Mail ist ungültig.")

        for field_name in ("cc", "bcc"):
            raw = data.get(field_name)
            if isinstance(raw, list):
                for item in cast(list[Any], raw):
                    value = str(item).strip()
                    if value and not EMAIL_RE.match(value):
                        errors.append(f"Ungültige E-Mail-Adresse in {field_name.upper()}: {value}")

        signatory = str(data.get("email_signature_name") or company["default_signatory_name"] or company["manager"] or company["name"]).strip()
        if not signatory:
            errors.append("Unterzeichner fehlt.")
            missing_information.append("Unterzeichner")

        letter_type = str(data.get("letter_type") or "allgemein")
        if bool(type_rule.get("requires_offer_valid_until")) and not str(data.get("offer_valid_until") or "").strip():
            warnings.append("Angebotsgültigkeit wurde nicht angegeben.")
            missing_information.append("Angebotsgültigkeit")

        for key in self._document_type_required_fields(commercial_kind or letter_type):
            if not str(data.get(key) or "").strip():
                label = DOCUMENT_TYPE_FIELD_LABELS.get(key, key)
                errors.append(f"Für diesen Dokumenttyp ist {label} erforderlich.")
                missing_information.append(label)

        if commercial_kind == "stornorechnung":
            if not (str(data.get("original_invoice_number") or "").strip() or has_source_reference):
                errors.append("Stornorechnung benötigt eine Ursprungsrechnung als Bezugsdokument.")
                missing_information.append("Ursprungsrechnung")

        if commercial_kind == "gutschrift":
            if not (str(data.get("original_invoice_number") or "").strip() or has_source_reference):
                errors.append("Gutschrift benötigt ein Bezugsdokument (z. B. Rechnung).")
                missing_information.append("Bezugsdokument")

        if commercial_kind in self.DUNNING_REQUIRED_DOCUMENT_TYPES:
            if not str(data.get("invoice_number") or "").strip():
                errors.append("Für Mahnungen ist Rechnungsnummer erforderlich.")
                missing_information.append("Rechnungsnummer")
            if not str(data.get("due_date") or "").strip():
                errors.append("Für Mahnungen ist Fälligkeit erforderlich.")
                missing_information.append("Fälligkeit")
            if not has_source_reference:
                errors.append("Mahnung benötigt eine offene Rechnung als Bezugsdokument.")
                missing_information.append("Offene Rechnung")
            if source_document_kind and source_document_kind not in {"rechnung"}:
                errors.append("Mahnung darf nur auf eine Rechnung referenzieren.")

        if commercial_kind == "retourenschein":
            if not has_source_reference:
                errors.append("Retourenschein benötigt ein Bezugsdokument (Lieferschein oder Rechnung).")
                missing_information.append("Lieferschein oder Rechnung")
            if source_document_kind and source_document_kind not in {"lieferschein", "rechnung"}:
                errors.append("Retourenschein darf nur auf Lieferschein oder Rechnung referenzieren.")

        if commercial_kind == "abnahmeprotokoll" and source_document_kind and source_document_kind != "montagebericht":
            warnings.append("Abnahmeprotokoll kann optional einen Montagebericht referenzieren; aktueller Bezug ist ein anderer Dokumenttyp.")

        if bool(type_rule.get("requires_delivery_date")) and not str(data.get("delivery_date") or "").strip():
            warnings.append("Für diesen Dokumenttyp sollte ein Liefer- oder Leistungsdatum angegeben werden.")
            missing_information.append("Liefer- oder Leistungsdatum")

        if not str(data.get("document_number") or data.get("offer_number") or data.get("order_number") or data.get("invoice_number") or "").strip():
            warnings.append("Dokument- oder Vorgangsnummer wurde nicht angegeben.")
            missing_information.append("Dokument- oder Vorgangsnummer")

        due_date = _parse_date(data.get("due_date"))
        response_deadline = _parse_date(data.get("response_deadline"))
        if bool(type_rule.get("requires_due_date")) and due_date is None:
            warnings.append("Es fehlt eine Zahlungs- oder Rückmeldefrist.")
            missing_information.append("Zahlungs- oder Rückmeldefrist")
        elif due_date is None and response_deadline is None:
            warnings.append("Es fehlt eine Rückmelde- oder Zahlungsfrist.")
            missing_information.append("Rückmelde- oder Zahlungsfrist")

        if due_date and response_deadline and due_date < response_deadline:
            warnings.append("Möglicherweise widersprüchliche Termine zwischen Fälligkeit und Rückmeldefrist.")

        if commercial_document.get("totals", {}).get("payable_amount") not in {None, "", "0", "0.00"}:
            payable_amount = _money(commercial_document.get("totals", {}).get("payable_amount") or 0)
            if payable_amount > Decimal("0") and due_date is None and not str(data.get("payment_terms") or "").strip():
                errors.append("Bei positivem Zahlbetrag sind Fälligkeitsdatum oder Zahlungsbedingungen erforderlich.")
                missing_information.append("Zahlungsbedingungen oder Fälligkeit")

        for attachment in attachments:
            if attachment.get("required") and not attachment.get("included"):
                errors.append(f"Erforderliche Anlage fehlt: {attachment.get('name')}")
                missing_information.append(f"Anlage: {attachment.get('name')}")

        body_text = "\n".join(body_paragraphs)
        mentions_attachment = bool(re.search(r"(?i)anbei\s+erhalten\s+sie", body_text))
        if mentions_attachment and not attachments:
            warnings.append("Im Text wird auf Anlagen verwiesen, aber es wurden keine Anlagen hinterlegt.")

        placeholder_hit = self._contains_placeholder(recipient, company, data)
        if placeholder_hit:
            warnings.append("Platzhalterdaten erkannt; Versand vor Freigabe prüfen.")
            if bool(data.get("ready_for_sending")):
                errors.append("Platzhalterdaten blockieren den Versandstatus ready.")

        manual_missing = data.get("missing_information")
        if isinstance(manual_missing, list):
            for item in cast(list[Any], manual_missing):
                value = str(item).strip()
                if value and value not in missing_information:
                    missing_information.append(value)

        dedup_missing: list[str] = []
        for item in missing_information:
            if item not in dedup_missing:
                dedup_missing.append(item)

        status = "ready" if not errors and not dedup_missing else "needs_review"
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "missing_information": dedup_missing,
        }

    def _resolve_document_setting(self, runtime_settings: dict[str, Any], document_kind: str, key: str) -> Any:
        scope = _document_kind_setting_scope(document_kind)
        scoped_key = f"{key}_{scope}" if scope else key
        if scope and scoped_key in runtime_settings:
            return runtime_settings.get(scoped_key)
        return runtime_settings.get(key)

    def _setting_or_default(self, runtime_value: Any, fallback: Any) -> Any:
        return fallback if runtime_value in {None, ""} else runtime_value

    def _render_setting_template(
        self,
        template: str,
        *,
        data: dict[str, Any],
        company: dict[str, str],
        recipient: dict[str, str],
        reference: dict[str, str],
    ) -> str:
        values = _SafeFormatDict(
            document_kind=str(data.get("document_kind") or data.get("letter_type") or "").strip(),
            document_number=str(reference.get("document_number") or data.get("document_number") or "").strip(),
            subject=str(data.get("subject") or "").strip(),
            customer_name=str(recipient.get("name") or recipient.get("contact") or "").strip(),
            customer_company=str(recipient.get("company") or "").strip(),
            company_name=str(company.get("name") or "").strip(),
        )
        try:
            return template.format_map(values).strip()
        except Exception:
            return template.strip()

    def _parse_email_targets(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [text for text in (str(item).strip() for item in cast(list[Any], value)) if text]
        raw = str(value or "").strip()
        if not raw:
            return []
        normalized = raw.replace(";", ",").replace("\n", ",")
        return [item.strip() for item in normalized.split(",") if item.strip()]

    def _apply_einvoice_delivery_policy(
        self,
        *,
        data: dict[str, Any],
        runtime_settings: dict[str, Any],
        validation: dict[str, Any],
        status: str,
        einvoice: dict[str, Any],
    ) -> tuple[dict[str, Any], str, str | None]:
        channel = str(data.get("communication_channel") or "letter").strip().lower()
        validate_before_send = _settings_truthy(runtime_settings.get("validate_before_send"))
        block_on_validation_error = _settings_truthy(runtime_settings.get("block_send_on_validation_error"))
        if not einvoice or channel not in {"email", "both"} or not validate_before_send or not block_on_validation_error:
            return validation, status, None

        einvoice_valid = bool(einvoice.get("valid"))
        if einvoice_valid:
            return validation, status, None

        block_reason = "Versand blockiert: E-Rechnungsvalidierung fehlgeschlagen."
        errors = cast(list[str], validation.get("errors") or [])
        if block_reason not in errors:
            errors.append(block_reason)
        validation["errors"] = errors
        validation["status"] = "needs_review"
        return validation, "needs_review", block_reason

    def _resolve_status(self, data: dict[str, Any], validation: dict[str, Any]) -> str:
        requested = str(data.get("status") or "").strip().lower()
        ready_for_sending = bool(data.get("ready_for_sending")) if isinstance(data.get("ready_for_sending"), bool) else False

        if cast(list[Any], validation.get("errors") or []):
            return "needs_review"
        if requested in {"approved", "queued", "delivered", "failed", "returned", "answered", "archived", "cancelled"}:
            return requested
        if requested == "sent":
            return "queued" if ready_for_sending else "approved"
        if ready_for_sending:
            return "ready"
        return "draft"

    def _build_metadata(self, data: dict[str, Any], status: str) -> dict[str, Any]:
        now = datetime.now().astimezone()
        created_by = str(data.get("created_by") or "plugin:business_letter").strip()
        approved_by = str(data.get("approved_by") or "").strip()
        channel = str(data.get("communication_channel") or "letter").strip().lower()

        metadata: dict[str, Any] = {
            "document_id": str(data.get("document_id") or f"doc_{uuid4().hex}"),
            "created_at": str(data.get("created_at") or now.isoformat()),
            "created_by": created_by,
            "approved_at": str(data.get("approved_at") or ""),
            "approved_by": approved_by,
            "sent_at": str(data.get("sent_at") or ""),
            "channel": channel if channel in {"letter", "email", "both"} else "letter",
            "template_version": str(data.get("template_version") or "1.0"),
            "status": status,
            "conversation_id": str(data.get("conversation_id") or "").strip(),
        }
        return metadata

    def _build_reference(self, data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, str]:
        now = datetime.now().astimezone()
        generated_number = f"DOC-{now.strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        document_number = str(data.get("document_number") or generated_number).strip()

        return {
            "document_number": document_number,
            "our_reference": str(data.get("our_reference") or document_number).strip(),
            "your_reference": str(data.get("your_reference") or "-").strip(),
            "your_message": str(data.get("your_message") or "-").strip(),
            "customer_number": str(data.get("customer_number") or "").strip(),
            "project_number": str(data.get("project_number") or "").strip(),
            "offer_number": str(data.get("offer_number") or "").strip(),
            "order_number": str(data.get("order_number") or "").strip(),
            "invoice_number": str(data.get("invoice_number") or "").strip(),
            "date": datetime.now().strftime("%d.%m.%Y"),
            "metadata_document_id": str(metadata.get("document_id") or "").strip(),
        }

    def _build_delivery(self, data: dict[str, Any], company: dict[str, str], subject: str) -> dict[str, Any]:
        channel = str(data.get("communication_channel") or "letter").strip().lower()
        if channel not in {"letter", "email", "both"}:
            channel = "letter"

        reply_to = str(data.get("reply_to") or company.get("default_reply_to_address") or company.get("email_reply_to") or company.get("email") or "").strip()
        recipient_email = str(data.get("recipient_email") or "").strip()

        return {
            "channel": channel,
            "recipient": recipient_email,
            "subject": str(data.get("email_subject") or subject).strip(),
            "reply_to": reply_to,
            "requested_send_at": data.get("requested_send_at"),
            "preferred_contact_method": str(data.get("preferred_contact_method") or "").strip(),
        }

    def _build_email(
        self,
        data: dict[str, Any],
        runtime_settings: dict[str, Any],
        company: dict[str, str],
        recipient: dict[str, str],
        reference: dict[str, str],
        subject: str,
        salutation: str,
        body_paragraphs: list[str],
        delivery: dict[str, Any],
    ) -> dict[str, Any]:
        document_kind = str(data.get("document_kind") or data.get("letter_type") or "allgemein").strip().lower()
        greeting = str(data.get("email_intro") or "").strip() or company["default_email_greeting"]
        signature_name = str(data.get("email_signature_name") or company["default_signatory_name"] or company["manager"] or company["name"]).strip()
        signature = company["default_email_signature"]
        if signature_name:
            signature = signature.replace(company["default_signatory_name"], signature_name)

        to_values: list[str] = []
        if recipient.get("email"):
            to_values.append(str(recipient.get("email")))

        cc_values = self._parse_email_targets(data.get("cc"))
        default_cc = self._parse_email_targets(
            self._setting_or_default(self._resolve_document_setting(runtime_settings, document_kind, "default_cc"), company.get("default_cc"))
        )
        for value in default_cc:
            if value not in cc_values:
                cc_values.append(value)

        bcc_values = self._parse_email_targets(data.get("bcc"))
        default_bcc = self._parse_email_targets(
            self._setting_or_default(self._resolve_document_setting(runtime_settings, document_kind, "company_email_bcc"), company.get("email_bcc"))
        )
        for value in default_bcc:
            if value not in bcc_values:
                bcc_values.append(value)

        subject_template = str(
            self._setting_or_default(
                self._resolve_document_setting(runtime_settings, document_kind, "default_email_subject_template"),
                company.get("default_email_subject_template"),
            )
            or ""
        ).strip()
        resolved_subject = str(data.get("email_subject") or "").strip()
        if not resolved_subject and subject_template:
            resolved_subject = self._render_setting_template(
                subject_template,
                data=data,
                company=company,
                recipient=recipient,
                reference=reference,
            )
        if not resolved_subject:
            resolved_subject = subject

        html_enabled = _settings_truthy(
            self._setting_or_default(
                self._resolve_document_setting(runtime_settings, document_kind, "default_email_html_enabled"),
                company.get("default_email_html_enabled"),
            )
        )

        lines: list[str] = [greeting]
        if salutation and salutation != greeting:
            lines.extend(["", salutation])
        lines.append("")
        lines.extend(body_paragraphs)
        lines.extend(["", signature])

        disclaimer = company.get("default_email_disclaimer") or ""
        confidentiality = company.get("default_confidentiality_notice") or ""
        if disclaimer:
            lines.extend(["", disclaimer])
        if confidentiality:
            lines.extend(["", confidentiality])

        body_text = "\n".join(lines).strip()
        body_html = _escape_html_lines(body_text) if html_enabled else ""

        return {
            "to": to_values,
            "cc": cc_values,
            "bcc": bcc_values,
            "reply_to": str(delivery.get("reply_to") or "").strip(),
            "subject": resolved_subject,
            "body_text": body_text,
            "body_html": body_html,
            "html_enabled": html_enabled,
            "attachments": [],
        }

    def _build_email_attachments(
        self,
        *,
        data: dict[str, Any],
        runtime_settings: dict[str, Any],
        template: dict[str, Any],
        reference: dict[str, str],
        document: dict[str, Any],
        artifacts: list[dict[str, Any]],
        einvoice: dict[str, Any],
    ) -> list[dict[str, Any]]:
        document_kind = str(data.get("document_kind") or data.get("letter_type") or "allgemein").strip().lower()
        attachments: list[dict[str, Any]] = []

        attach_pdf = _settings_truthy(self._resolve_document_setting(runtime_settings, document_kind, "default_attach_pdf"))
        if attach_pdf:
            pdf_artifact = next((artifact for artifact in artifacts if str(artifact.get("kind") or "") == "pdf"), None)
            if pdf_artifact is not None:
                pdf_payload = build_pdf_payload(template, reference, document)
                if pdf_payload:
                    attachments.append(
                        {
                            "kind": "pdf",
                            "file_name": str(pdf_artifact.get("file_name") or "document.pdf"),
                            "mime_type": "application/pdf",
                            "content_base64": pdf_payload,
                            "storage_reference": str(pdf_artifact.get("storage_reference") or ""),
                            "included": True,
                        }
                    )

        attach_xml = _settings_truthy(self._resolve_document_setting(runtime_settings, document_kind, "default_attach_xml"))
        xml_payload = str(einvoice.get("xml") or "").strip()
        if attach_xml and xml_payload:
            standard = str(einvoice.get("standard") or "xrechnung").strip().lower()
            file_name = "factur-x.xml" if standard == "zugferd" else f"{standard}.xml"
            xml_attachment = {}
            if isinstance(einvoice.get("attachments"), list) and cast(list[Any], einvoice.get("attachments")):
                first = cast(list[Any], einvoice.get("attachments"))[0]
                if isinstance(first, dict):
                    xml_attachment = _as_mapping(first)
                    file_name = str(xml_attachment.get("file_name") or file_name)
            attachments.append(
                {
                    "kind": str(xml_attachment.get("kind") or f"{standard}_xml"),
                    "file_name": file_name,
                    "mime_type": str(xml_attachment.get("mime_type") or "application/xml"),
                    "content_base64": base64.b64encode(xml_payload.encode("utf-8")).decode("ascii"),
                    "included": True,
                }
            )

        return attachments

    def _delivery_should_dispatch(self, delivery: dict[str, Any], validation: dict[str, Any]) -> bool:
        channel = str(delivery.get("channel") or "").strip().lower()
        if channel not in {"email", "both"}:
            return False
        if bool(delivery.get("blocked")):
            return False
        return str(validation.get("status") or "").strip().lower() == "ready"

    def _dispatch_idempotency_key(
        self,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        email: dict[str, Any],
    ) -> str:
        attachment_fingerprints: list[dict[str, str]] = []
        for raw_item in cast(list[Any], email.get("attachments") or []):
            item = _as_mapping(raw_item)
            if not item:
                continue
            encoded = str(item.get("content_base64") or "").strip()
            attachment_fingerprints.append(
                {
                    "kind": str(item.get("kind") or ""),
                    "file_name": str(item.get("file_name") or ""),
                    "sha": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
                }
            )

        payload: dict[str, Any] = {
            "tenant_id": tenant_id,
            "document_id": document_id,
            "document_number": document_number,
            "to": email.get("to") or [],
            "cc": email.get("cc") or [],
            "bcc": email.get("bcc") or [],
            "subject": str(email.get("subject") or "").strip(),
            "body": str(email.get("body_text") or "").strip(),
            "attachments": attachment_fingerprints,
        }
        digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        return f"mail:{document_id}:{digest[:32]}"

    def _email_plugin_payload(
        self,
        *,
        delivery: dict[str, Any],
        email: dict[str, Any],
        provider: str,
    ) -> dict[str, Any]:
        attachments: list[dict[str, Any]] = []
        for raw_item in cast(list[Any], email.get("attachments") or []):
            item = _as_mapping(raw_item)
            if not item:
                continue
            file_name = str(item.get("file_name") or item.get("filename") or "attachment.bin").strip() or "attachment.bin"
            encoded = str(item.get("content_base64") or item.get("content") or "").strip()
            if not encoded:
                continue
            attachments.append(
                {
                    "filename": file_name,
                    "content": encoded,
                    "mime_type": str(item.get("mime_type") or "application/octet-stream").strip() or "application/octet-stream",
                }
            )

        return {
            "email": email,
            "delivery": delivery,
            "content": {
                "email_text": str(email.get("body_text") or ""),
                "email_html": str(email.get("body_html") or ""),
            },
            "provider": provider,
            "communication_channel": str(delivery.get("channel") or "email"),
            "attachments": attachments,
        }

    async def _send_via_email_plugin_interface(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            from app.tools.executor import PluginExecutor

            executor = PluginExecutor()
            return await executor.execute("email", payload)
        except Exception:
            # Fallback for contexts where the app plugin executor is unavailable.
            from plugins.email.plugin import EmailPlugin

            plugin = EmailPlugin()
            return await plugin.execute(payload)

    async def _dispatch_email_via_plugin(
        self,
        *,
        data: dict[str, Any],
        runtime_settings: dict[str, Any],
        metadata: dict[str, Any],
        reference: dict[str, str],
        document: dict[str, Any],
        delivery: dict[str, Any],
        email: dict[str, Any],
        database: dict[str, Any],
        validation: dict[str, Any],
    ) -> dict[str, Any]:
        if not self._delivery_should_dispatch(delivery, validation):
            return {"enabled": False, "status": "skipped", "reason": "not_dispatchable"}

        if not bool(database.get("enabled")):
            return {
                "enabled": False,
                "status": "skipped",
                "reason": "persistence_required",
                "message": "Dispatch-Queue erfordert persist_to_database=true.",
            }

        raw_dispatch_enabled = runtime_settings.get("dispatch_queue_enabled")
        dispatch_enabled = True if raw_dispatch_enabled in (None, "") else _settings_truthy(raw_dispatch_enabled)
        if not dispatch_enabled:
            return {"enabled": False, "status": "disabled"}

        provider = str(runtime_settings.get("dispatch_provider") or "smtp").strip().lower() or "smtp"
        max_attempts = max(1, _int_setting(runtime_settings.get("dispatch_retry_attempts"), 3))
        execute_now = _settings_truthy(runtime_settings.get("dispatch_execute_immediately"))

        tenant_id = str(data.get("tenant_id") or self.settings.get("tenant_id") or "default").strip() or "default"
        document_id = str(metadata.get("document_id") or "").strip()
        document_number = str(reference.get("document_number") or document.get("reference", {}).get("document_number") or "").strip()
        idempotency_key = self._dispatch_idempotency_key(
            tenant_id=tenant_id,
            document_id=document_id,
            document_number=document_number,
            email=email,
        )

        plugin_payload = self._email_plugin_payload(delivery=delivery, email=email, provider=provider)
        queue_item = DEFAULT_PERSISTENCE.enqueue_dispatch(
            tenant_id=tenant_id,
            document_id=document_id,
            document_number=document_number,
            idempotency_key=idempotency_key,
            channel=str(delivery.get("channel") or "email"),
            provider=provider,
            to_values=cast(list[str], email.get("to") or []),
            cc_values=cast(list[str], email.get("cc") or []),
            bcc_values=cast(list[str], email.get("bcc") or []),
            subject=str(email.get("subject") or "").strip(),
            payload=plugin_payload,
            max_attempts=max_attempts,
        )

        dispatch_summary: dict[str, Any] = {
            "enabled": True,
            "queue": queue_item,
            "idempotency_key": idempotency_key,
            "execute_immediately": execute_now,
            "provider": provider,
        }

        if queue_item.get("created") is False and str(queue_item.get("status") or "") in {"sent", "queued", "processing"}:
            dispatch_summary["status"] = "duplicate_suppressed"
            dispatch_summary["message"] = "Idempotenzschutz: identischer Versand existiert bereits."
        elif execute_now:
            plugin_result = await self._send_via_email_plugin_interface(plugin_payload)
            updated_queue = DEFAULT_PERSISTENCE.record_dispatch_attempt(
                dispatch_id=str(queue_item.get("dispatch_id") or ""),
                success=bool(plugin_result.get("success")),
                provider_result=plugin_result,
            )
            dispatch_summary["status"] = "sent" if bool(plugin_result.get("success")) else str(updated_queue.get("status") or "failed")
            dispatch_summary["result"] = plugin_result
            dispatch_summary["queue"] = updated_queue
        else:
            dispatch_summary["status"] = str(queue_item.get("status") or "queued")

        persisted_payload = _as_mapping(database.get("persisted"))
        if persisted_payload:
            dual_save = _as_mapping(persisted_payload.get("dual_save"))
            if dual_save and bool(dual_save.get("enabled")):
                guest_db_path = str(data.get("guest_system_database_path") or runtime_settings.get("guest_system_database_path") or "").strip()
                if guest_db_path:
                    try:
                        DEFAULT_PERSISTENCE.mirror_to_guest_database(
                            guest_db_path=guest_db_path,
                            document_id=document_id,
                            document_number=document_number,
                            payload={"dispatch_queue_item": dispatch_summary.get("queue") or {}},
                            artifacts=[],
                        )
                        dispatch_summary["guest_system_mirror"] = "ok"
                    except Exception as exc:
                        dispatch_summary["guest_system_mirror"] = f"failed: {exc}"

        return dispatch_summary

    def _normalize_email_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        emails: list[str] = []
        for item in cast(list[Any], value):
            text = str(item).strip()
            if text:
                emails.append(text)
        return emails

    def _contains_placeholder(self, recipient: dict[str, str], company: dict[str, str], data: dict[str, Any]) -> bool:
        return contains_placeholder(recipient, company, data)

    def _render_plain_letter(self, document: dict[str, Any]) -> str:
        return render_plain_letter(document)