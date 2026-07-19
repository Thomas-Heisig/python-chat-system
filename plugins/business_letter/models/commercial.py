from __future__ import annotations

from typing import Any

from plugins.business_letter.constants import COMMERCIAL_DOCUMENT_TYPES, COMMUNICATION_DOCUMENT_TYPES
from plugins.business_letter.services.calculation import calculate_commercial_document


def normalize_document_kind(value: Any) -> str:
    raw = str(value or "allgemein").strip().lower()
    if raw in COMMERCIAL_DOCUMENT_TYPES or raw in COMMUNICATION_DOCUMENT_TYPES:
        return raw
    return "allgemein"


def build_commercial_document(
    data: dict[str, Any],
    company: dict[str, str],
    recipient: dict[str, str],
    positions: list[dict[str, Any]],
) -> dict[str, Any]:
    document = calculate_commercial_document(data=data, company=company, recipient=recipient, positions=positions)
    return document
