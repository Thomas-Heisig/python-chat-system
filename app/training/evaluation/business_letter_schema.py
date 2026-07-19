from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, cast


ALLOWED_DOCUMENT_TYPES = {
    "geschaeftsbrief",
    "geschaeftsbrief_allgemein",
    "angebot",
    "angebot_treppe",
    "angebotserinnerung",
    "auftragsbestaetigung",
    "terminbestaetigung",
    "terminverschiebung",
    "lieferankuendigung",
    "fertigstellungsanzeige",
    "abnahme",
    "abnahmeprotokoll",
    "rechnung",
    "rechnung_begleitschreiben",
    "zahlungserinnerung",
    "mahnung",
    "mahnung_1",
    "mahnung_2",
    "maengelantwort",
    "maengelanzeige",
    "reklamation_eingang",
    "reklamation_antwort",
    "informationsanforderung",
    "dokumentenanforderung",
    "begleitschreiben",
    "allgemein",
}

ALLOWED_STATUS_VALUES = {
    "draft",
    "blocked",
    "ready",
    "needs_review",
    "approved",
    "queued",
    "sent",
    "delivered",
    "failed",
    "returned",
    "answered",
    "archived",
    "cancelled",
}

FORBIDDEN_TEXT_PATTERNS = [
    re.compile(r"(?im)^\s{0,3}#{1,6}\s+"),
    re.compile(r"(?m)[\|+\-=]{8,}"),
    re.compile(r"(?i)ich habe (ihre|deine) (anforderung|anfrage) verstanden"),
    re.compile(r"(?i)vorlesen"),
    re.compile(r"(?i)anlage\s*:\s*(konto|bank|iban|bic)"),
]


@dataclass(slots=True)
class BusinessLetterValidationResult:
    valid: bool
    errors: list[str]
    payload: dict[str, Any] | None = None


def validate_business_letter_json_text(text: str) -> BusinessLetterValidationResult:
    try:
        payload_raw = json.loads(text)
    except json.JSONDecodeError as exc:
        return BusinessLetterValidationResult(valid=False, errors=[f"invalid_json:{exc.msg}"])

    if not isinstance(payload_raw, dict):
        return BusinessLetterValidationResult(valid=False, errors=["root_must_be_object"])

    payload = cast(dict[str, Any], payload_raw)
    errors: list[str] = []

    document_container = _get_dict(payload, "document")
    effective = document_container if document_container else payload

    document_type = _coerce_string(effective.get("document_type"))
    if not document_type:
        errors.append("missing_document_type")
    elif document_type.lower() not in ALLOWED_DOCUMENT_TYPES:
        errors.append("invalid_document_type")

    status = _coerce_string(effective.get("status"))
    if not status:
        validation_obj = _get_dict(payload, "validation")
        status = _coerce_string(validation_obj.get("status"))
    if not status:
        errors.append("missing_status")
    elif status.lower() not in ALLOWED_STATUS_VALUES:
        errors.append("invalid_status")

    subject = _coerce_string(effective.get("subject"))
    if not subject:
        subject = _coerce_string(payload.get("subject"))
    if not subject:
        email_obj = _get_dict(payload, "email")
        subject = _coerce_string(email_obj.get("subject"))
    if not subject:
        errors.append("missing_or_empty:subject")

    salutation = _coerce_string(effective.get("salutation"))
    if not salutation:
        errors.append("missing_or_empty:salutation")

    closing = _coerce_string(effective.get("closing"))
    if not closing:
        body_obj = _get_dict(effective, "body")
        closing = _coerce_string(body_obj.get("closing"))
    if not closing:
        errors.append("missing_or_empty:closing")

    body_paragraphs = _extract_body_paragraphs(payload, effective)
    if not body_paragraphs:
        errors.append("body_paragraphs_required")
    else:
        for idx, item in enumerate(body_paragraphs):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"body_paragraphs_invalid:{idx}")

    missing_information = _extract_missing_information(payload, effective)
    if missing_information is None:
        errors.append("missing_information_must_be_list")
    else:
        for idx, item in enumerate(missing_information):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"missing_information_invalid:{idx}")

    ready_for_sending = effective.get("ready_for_sending")
    if ready_for_sending is None:
        ready_for_sending = payload.get("ready_for_sending")
    if ready_for_sending is not None and not isinstance(ready_for_sending, bool):
        errors.append("ready_for_sending_must_be_boolean")

    for path, value in _iter_text_fields(payload, effective, body_paragraphs, missing_information or []):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"forbidden_pattern:{path}")
                break

    if errors:
        return BusinessLetterValidationResult(valid=False, errors=errors, payload=payload)
    return BusinessLetterValidationResult(valid=True, errors=[], payload=payload)


def _get_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


def _coerce_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _extract_body_paragraphs(payload: dict[str, Any], effective: dict[str, Any]) -> list[str]:
    body_paragraphs = effective.get("body_paragraphs")
    if isinstance(body_paragraphs, list):
        return [str(item) for item in body_paragraphs]

    body_obj = _get_dict(effective, "body")
    body_lines = body_obj.get("paragraphs")
    if isinstance(body_lines, list):
        return [str(item) for item in body_lines]

    content_obj = _get_dict(payload, "content")
    letter_text = _coerce_string(content_obj.get("letter_text"))
    if letter_text:
        return [paragraph.strip() for paragraph in letter_text.split("\n") if paragraph.strip()]

    email_obj = _get_dict(payload, "email")
    email_text = _coerce_string(email_obj.get("body_text"))
    if email_text:
        return [paragraph.strip() for paragraph in email_text.split("\n") if paragraph.strip()]

    return []


def _extract_missing_information(payload: dict[str, Any], effective: dict[str, Any]) -> list[Any] | None:
    direct = effective.get("missing_information")
    if isinstance(direct, list):
        return cast(list[Any], direct)

    validation_obj = _get_dict(payload, "validation")
    nested = validation_obj.get("missing_information")
    if isinstance(nested, list):
        return cast(list[Any], nested)

    if direct is None and nested is None:
        return []
    return None


def _iter_text_fields(
    payload: dict[str, Any],
    effective: dict[str, Any],
    body_paragraphs: list[str],
    missing_information: list[Any],
) -> list[tuple[str, str]]:
    text_fields: list[tuple[str, str]] = []

    for key in ("subject", "salutation", "closing"):
        value = effective.get(key)
        if isinstance(value, str):
            text_fields.append((key, value))

    body_obj = _get_dict(effective, "body")
    closing = body_obj.get("closing")
    if isinstance(closing, str):
        text_fields.append(("body.closing", closing))

    for idx, value in enumerate(body_paragraphs):
        text_fields.append((f"body_paragraphs[{idx}]", value))

    for idx, value in enumerate(missing_information):
        if isinstance(value, str):
            text_fields.append((f"missing_information[{idx}]", value))

    email_obj = _get_dict(payload, "email")
    for key in ("subject", "body_text", "body_html"):
        value = email_obj.get(key)
        if isinstance(value, str):
            text_fields.append((f"email.{key}", value))

    content_obj = _get_dict(payload, "content")
    for key in ("letter_text", "email_text", "email_html"):
        value = content_obj.get(key)
        if isinstance(value, str):
            text_fields.append((f"content.{key}", value))

    return text_fields
