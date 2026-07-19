from __future__ import annotations

from decimal import Decimal
from typing import Any, TypedDict, cast


class ConversionRule(TypedDict):
    action: str
    source_kind: str
    target_kind: str
    copy_positions: bool


CONVERSION_RULES: dict[str, ConversionRule] = {
    "angebot_to_auftragsbestaetigung": {
        "action": "angebot_to_auftragsbestaetigung",
        "source_kind": "angebot",
        "target_kind": "auftragsbestaetigung",
        "copy_positions": True,
    },
    "auftragsbestaetigung_to_lieferschein": {
        "action": "auftragsbestaetigung_to_lieferschein",
        "source_kind": "auftragsbestaetigung",
        "target_kind": "lieferschein",
        "copy_positions": True,
    },
    "lieferschein_to_rechnung": {
        "action": "lieferschein_to_rechnung",
        "source_kind": "lieferschein",
        "target_kind": "rechnung",
        "copy_positions": True,
    },
    "rechnung_to_stornorechnung": {
        "action": "rechnung_to_stornorechnung",
        "source_kind": "rechnung",
        "target_kind": "stornorechnung",
        "copy_positions": True,
    },
    "rechnung_to_gutschrift": {
        "action": "rechnung_to_gutschrift",
        "source_kind": "rechnung",
        "target_kind": "gutschrift",
        "copy_positions": True,
    },
    "rechnung_to_zahlungserinnerung": {
        "action": "rechnung_to_zahlungserinnerung",
        "source_kind": "rechnung",
        "target_kind": "zahlungserinnerung",
        "copy_positions": False,
    },
    "montagebericht_to_abnahmeprotokoll": {
        "action": "montagebericht_to_abnahmeprotokoll",
        "source_kind": "montagebericht",
        "target_kind": "abnahmeprotokoll",
        "copy_positions": False,
    },
}

_INVOICE_LIKE_KINDS = {"rechnung", "abschlagsrechnung", "schlussrechnung", "proformarechnung"}
_PAYMENT_LIKE_KINDS = {"zahlung", "zahlungseingang", "zahlungsbestaetigung", "remittance", "kontoauszug"}
_CREDIT_LIKE_KINDS = {"gutschrift", "stornorechnung"}
_DELIVERY_LIKE_KINDS = {"lieferschein", "teillieferschein", "sammellieferschein"}

_ACTION_ALLOWED_SOURCE_STATUSES: dict[str, set[str]] = {
    "angebot_to_auftragsbestaetigung": {"needs_review", "approved", "ready", "queued", "sent", "delivered", "archived"},
    "auftragsbestaetigung_to_lieferschein": {"needs_review", "approved", "ready", "queued", "sent", "delivered", "archived"},
    "lieferschein_to_rechnung": {"needs_review", "approved", "ready", "queued", "sent", "delivered", "archived"},
    "rechnung_to_stornorechnung": {"needs_review", "approved", "ready", "queued", "sent", "delivered", "archived"},
    "rechnung_to_gutschrift": {"needs_review", "approved", "ready", "queued", "sent", "delivered", "archived"},
    "rechnung_to_zahlungserinnerung": {"needs_review", "approved", "ready", "queued", "sent", "delivered", "archived"},
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = cast(dict[object, Any], value)
    return {str(key): item for key, item in raw.items()}


def _as_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return cast(list[Any], value)


def _read_nested(root: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = root
    for key in path:
        if not isinstance(node, dict):
            return None
        node = cast(dict[str, Any], node).get(key)
    return node


def _first_text(root: dict[str, Any], paths: list[tuple[str, ...]]) -> str:
    for path in paths:
        value = _text(_read_nested(root, path))
        if value:
            return value
    return ""


def _first_list(root: dict[str, Any], paths: list[tuple[str, ...]]) -> list[Any]:
    for path in paths:
        value = _read_nested(root, path)
        if isinstance(value, list):
            return _as_list(value)
    return []


def _to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    text = _text(value)
    if not text:
        return default
    try:
        return Decimal(text)
    except Exception:
        return default


def _normalize_source_position(item: dict[str, Any], index: int) -> dict[str, Any]:
    line_id = _text(item.get("line_id")) or f"{index:03d}"
    quantity = _text(item.get("quantity")) or "1"
    unit_code = _text(item.get("unit_code")) or "C62"
    price_net = _text(item.get("price_net"))
    if not price_net:
        price_net = _text(item.get("unit_price"))
    if not price_net:
        price_net = "0"
    vat_rate = _text(item.get("vat_rate")) or "19"
    vat_category = _text(item.get("vat_category")) or "S"

    return {
        "line_id": line_id,
        "article_number": _text(item.get("article_number")),
        "name": _text(item.get("name") or item.get("description")) or f"Position {index}",
        "description": _text(item.get("description") or item.get("name")),
        "quantity": quantity,
        "unit_code": unit_code,
        "price_net": price_net,
        "vat_category": vat_category,
        "vat_rate": vat_rate,
        "stone_details": _as_mapping(item.get("stone_details")),
    }


def _normalize_line_key(item: dict[str, Any], index: int) -> str:
    explicit = _text(item.get("line_id"))
    if explicit:
        return explicit
    article = _text(item.get("article_number"))
    if article:
        return f"article:{article}"
    name = _text(item.get("name") or item.get("description"))
    if name:
        return f"name:{name.lower()}"
    return f"idx:{index}"


def _extract_source_document(data: dict[str, Any]) -> dict[str, Any]:
    source_document = _as_mapping(data.get("source_document"))
    if source_document:
        return source_document
    return {}


def _extract_source_kind(data: dict[str, Any], source_document: dict[str, Any]) -> str:
    direct = _text(data.get("source_document_kind"))
    if direct:
        return direct
    return _first_text(
        source_document,
        [
            ("document_kind",),
            ("document_type",),
            ("document", "document_type"),
            ("document", "commercial_document", "document_kind"),
            ("commercial_document", "document_kind"),
        ],
    )


def _extract_source_status(source_document: dict[str, Any]) -> str:
    return _first_text(
        source_document,
        [
            ("status",),
            ("document", "status"),
            ("commercial_document", "status"),
            ("document", "commercial_document", "status"),
        ],
    ).lower()


def _extract_source_id(data: dict[str, Any], source_document: dict[str, Any]) -> str:
    direct = _text(data.get("source_document_id"))
    if direct:
        return direct
    return _first_text(
        source_document,
        [
            ("document_id",),
            ("metadata", "document_id"),
            ("document", "metadata", "document_id"),
            ("document", "document_id"),
        ],
    )


def _extract_source_number(data: dict[str, Any], source_document: dict[str, Any]) -> str:
    direct = _text(data.get("source_document_number"))
    if direct:
        return direct
    return _first_text(
        source_document,
        [
            ("document_number",),
            ("reference", "document_number"),
            ("document", "reference", "document_number"),
            ("document", "document_number"),
        ],
    )


def _extract_source_positions(source_document: dict[str, Any]) -> list[dict[str, Any]]:
    raw_positions = _first_list(
        source_document,
        [
            ("positions",),
            ("commercial_document", "positions"),
            ("document", "positions"),
            ("document", "commercial_document", "positions"),
        ],
    )

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(raw_positions, start=1):
        mapping = _as_mapping(item)
        if not mapping:
            continue
        normalized.append(_normalize_source_position(mapping, index))
    return normalized


def _extract_follow_up_documents(data: dict[str, Any], source_document: dict[str, Any]) -> list[dict[str, Any]]:
    direct = _as_list(data.get("source_document_followups"))
    if not direct:
        direct = _as_list(source_document.get("follow_up_documents"))
    follow_ups: list[dict[str, Any]] = []
    for item in direct:
        mapping = _as_mapping(item)
        if mapping:
            follow_ups.append(mapping)
    return follow_ups


def _extract_document_positions(document: dict[str, Any]) -> list[dict[str, Any]]:
    return _extract_source_positions(document)


def _extract_document_kind(document: dict[str, Any]) -> str:
    kind = _text(document.get("document_kind"))
    if kind:
        return kind.lower()
    payload = _as_mapping(document.get("document"))
    if payload:
        candidate = _text(payload.get("document_type"))
        if candidate:
            return candidate.lower()
    return ""


def _sum_followup_quantities_by_line(follow_ups: list[dict[str, Any]], relevant_kinds: set[str]) -> dict[str, Decimal]:
    aggregated: dict[str, Decimal] = {}
    for document in follow_ups:
        kind = _extract_document_kind(document)
        if kind not in relevant_kinds:
            continue
        positions = _extract_document_positions(document)
        for index, position in enumerate(positions, start=1):
            key = _normalize_line_key(position, index)
            quantity = _to_decimal(position.get("quantity"), Decimal("0"))
            if quantity <= 0:
                continue
            aggregated[key] = aggregated.get(key, Decimal("0")) + quantity
    return aggregated


def _sum_followup_totals(follow_ups: list[dict[str, Any]], relevant_kinds: set[str]) -> Decimal:
    total = Decimal("0")
    for document in follow_ups:
        kind = _extract_document_kind(document)
        if kind not in relevant_kinds:
            continue
        customer_visible = _as_mapping(_read_nested(document, ("commercial_document", "customer_visible")))
        totals = _as_mapping(customer_visible.get("totals"))
        amount = _to_decimal(
            totals.get("payable_amount")
            or document.get("payment_amount")
            or document.get("amount")
            or document.get("invoice_amount"),
            Decimal("0"),
        )
        if amount > 0:
            total += amount
    return total


def _apply_delivery_to_invoice_remaining_logic(
    data: dict[str, Any],
    source_positions: list[dict[str, Any]],
    quantity_overrides: dict[str, Decimal],
    selected_line_ids: set[str],
    follow_ups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    already_invoiced_by_line = _sum_followup_quantities_by_line(follow_ups, _INVOICE_LIKE_KINDS)
    converted: list[dict[str, Any]] = []

    for index, source in enumerate(source_positions, start=1):
        line_id = _text(source.get("line_id"))
        if line_id and line_id not in selected_line_ids:
            continue
        line_key = _normalize_line_key(source, index)
        base_quantity = _to_decimal(source.get("quantity"), Decimal("0"))
        already_invoiced = already_invoiced_by_line.get(line_key, Decimal("0"))
        open_quantity = base_quantity - already_invoiced
        if open_quantity <= 0:
            continue

        requested_quantity = quantity_overrides.get(line_id, open_quantity)
        effective_quantity = min(requested_quantity, open_quantity)
        if effective_quantity <= 0:
            continue

        item = dict(source)
        item["quantity"] = str(effective_quantity)
        item["source_quantity"] = str(base_quantity)
        item["already_invoiced_quantity"] = str(already_invoiced)
        item["remaining_quantity"] = str(open_quantity)
        converted.append(item)

    return converted


def _apply_credit_or_storno_sign_logic(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for item in positions:
        updated = dict(item)
        price = _to_decimal(updated.get("price_net"), Decimal("0"))
        if price > 0:
            updated["price_net"] = str(-price)
        converted.append(updated)
    return converted


def _apply_reminder_open_amount_logic(
    data: dict[str, Any],
    source_document: dict[str, Any],
    follow_ups: list[dict[str, Any]],
) -> Decimal:
    source_amount_text = _first_text(source_document, [("commercial_document", "customer_visible", "totals", "payable_amount"), ("invoice_amount",)])
    source_amount = _to_decimal(source_amount_text, Decimal("0"))
    if source_amount <= 0:
        source_amount = _to_decimal(data.get("invoice_amount"), Decimal("0"))

    paid = _sum_followup_totals(follow_ups, _PAYMENT_LIKE_KINDS)
    credited = _sum_followup_totals(follow_ups, _CREDIT_LIKE_KINDS)
    open_amount = source_amount - paid - credited
    if open_amount < 0:
        open_amount = Decimal("0")

    if open_amount > 0:
        data["invoice_amount"] = str(open_amount)
        data["invoice_open_amount"] = str(open_amount)
    elif source_amount > 0:
        data["invoice_open_amount"] = "0"
    return open_amount


def build_quantity_chain_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    source_document = _extract_source_document(data)
    source_kind = _extract_source_kind(data, source_document).lower()
    source_positions = _extract_source_positions(source_document)
    follow_ups = _extract_follow_up_documents(data, source_document)

    if not source_positions:
        return {
            "source_kind": source_kind,
            "follow_up_documents": len(follow_ups),
            "lines": [],
            "totals": {
                "delivered_quantity": "0",
                "invoiced_quantity": "0",
                "credited_quantity": "0",
                "open_quantity": "0",
            },
        }

    delivered_by_line = _sum_followup_quantities_by_line(follow_ups, _DELIVERY_LIKE_KINDS)
    invoiced_by_line = _sum_followup_quantities_by_line(follow_ups, _INVOICE_LIKE_KINDS)
    credited_by_line = _sum_followup_quantities_by_line(follow_ups, _CREDIT_LIKE_KINDS)

    lines: list[dict[str, Any]] = []
    total_delivered = Decimal("0")
    total_invoiced = Decimal("0")
    total_credited = Decimal("0")
    total_open = Decimal("0")

    for index, source in enumerate(source_positions, start=1):
        line_id = _text(source.get("line_id")) or str(index)
        line_key = _normalize_line_key(source, index)
        source_quantity = _to_decimal(source.get("quantity"), Decimal("0"))
        delivered_followup = delivered_by_line.get(line_key, Decimal("0"))
        invoiced_quantity = invoiced_by_line.get(line_key, Decimal("0"))
        credited_quantity = credited_by_line.get(line_key, Decimal("0"))

        if source_kind in _DELIVERY_LIKE_KINDS:
            delivered_quantity = source_quantity
        elif delivered_followup > 0:
            delivered_quantity = delivered_followup
        else:
            delivered_quantity = source_quantity

        open_quantity = delivered_quantity - invoiced_quantity
        if open_quantity < 0:
            open_quantity = Decimal("0")

        total_delivered += delivered_quantity
        total_invoiced += invoiced_quantity
        total_credited += credited_quantity
        total_open += open_quantity

        lines.append(
            {
                "line_id": line_id,
                "name": _text(source.get("name") or source.get("description")) or f"Position {index}",
                "source_quantity": str(source_quantity),
                "delivered_quantity": str(delivered_quantity),
                "invoiced_quantity": str(invoiced_quantity),
                "credited_quantity": str(credited_quantity),
                "open_quantity": str(open_quantity),
            }
        )

    return {
        "source_kind": source_kind,
        "follow_up_documents": len(follow_ups),
        "lines": lines,
        "totals": {
            "delivered_quantity": str(total_delivered),
            "invoiced_quantity": str(total_invoiced),
            "credited_quantity": str(total_credited),
            "open_quantity": str(total_open),
        },
    }


def _copy_if_empty(data: dict[str, Any], key: str, value: Any) -> None:
    if _text(data.get(key)):
        return
    text = _text(value)
    if text:
        data[key] = text


def _copy_from_source_document(data: dict[str, Any], source_document: dict[str, Any], source_number: str) -> None:
    _copy_if_empty(data, "project_id", _first_text(source_document, [("project_id",), ("document", "relationships", "project_id")]))
    _copy_if_empty(data, "customer_id", _first_text(source_document, [("customer_id",), ("document", "relationships", "customer_id")]))
    _copy_if_empty(data, "project_reference", _first_text(source_document, [("project_reference",), ("commercial_document", "customer_visible", "project_reference")]))
    _copy_if_empty(data, "order_number", _first_text(source_document, [("order_number",), ("commercial_document", "customer_visible", "purchase_order_reference")]))

    recipient = _as_mapping(_read_nested(source_document, ("document", "recipient")))
    if recipient:
        _copy_if_empty(data, "customer_name", recipient.get("name") or recipient.get("company"))
        _copy_if_empty(data, "customer_company", recipient.get("company") or recipient.get("name"))
        _copy_if_empty(data, "customer_street", recipient.get("street"))
        _copy_if_empty(data, "customer_zip", recipient.get("postal_code"))
        _copy_if_empty(data, "customer_city", recipient.get("city"))
        _copy_if_empty(data, "customer_country", recipient.get("country"))
        _copy_if_empty(data, "recipient_email", recipient.get("email"))

    if source_number:
        if _text(data.get("document_kind")) == "stornorechnung":
            _copy_if_empty(data, "original_invoice_number", source_number)
        if _text(data.get("document_kind")) == "gutschrift":
            _copy_if_empty(data, "original_invoice_number", source_number)

    source_issue_date = _first_text(source_document, [("commercial_document", "customer_visible", "issue_date"), ("document", "reference", "date")])
    source_due_date = _first_text(source_document, [("commercial_document", "customer_visible", "payment_due_date"), ("due_date",)])
    source_amount = _first_text(source_document, [("commercial_document", "customer_visible", "totals", "payable_amount"), ("invoice_amount",)])

    if _text(data.get("document_kind")) in {"zahlungserinnerung", "mahnung_1", "mahnung_2", "mahnung_3"}:
        _copy_if_empty(data, "invoice_number", source_number)
        _copy_if_empty(data, "invoice_date", source_issue_date)
        _copy_if_empty(data, "invoice_amount", source_amount)
        _copy_if_empty(data, "due_date", source_due_date)


def _resolve_selected_line_ids(data: dict[str, Any], available_positions: list[dict[str, Any]]) -> set[str]:
    explicit = {_text(item) for item in _as_list(data.get("source_position_line_ids")) if _text(item)}
    if explicit:
        return explicit
    return {_text(item.get("line_id")) for item in available_positions if _text(item.get("line_id"))}


def _resolve_quantity_overrides(data: dict[str, Any]) -> dict[str, Decimal]:
    raw = _as_mapping(data.get("source_position_quantities"))
    resolved: dict[str, Decimal] = {}
    for key, value in raw.items():
        line_id = _text(key)
        if not line_id:
            continue
        qty = _to_decimal(value, Decimal("0"))
        if qty > 0:
            resolved[line_id] = qty
    return resolved


def _copy_positions_from_source(data: dict[str, Any], source_document: dict[str, Any]) -> int:
    source_positions = _extract_source_positions(source_document)
    if not source_positions:
        return 0

    selected_line_ids = _resolve_selected_line_ids(data, source_positions)
    quantity_overrides = _resolve_quantity_overrides(data)

    copied_positions: list[dict[str, Any]] = []
    for item in source_positions:
        line_id = _text(item.get("line_id"))
        if line_id and line_id not in selected_line_ids:
            continue
        copied = dict(item)
        if line_id in quantity_overrides:
            copied["quantity"] = str(quantity_overrides[line_id])
        copied_positions.append(copied)

    if copied_positions:
        data["positions"] = copied_positions
    return len(copied_positions)


def apply_conversion_action(data: dict[str, Any]) -> dict[str, Any]:
    action = _text(data.get("conversion_action")).lower()
    if not action:
        return {"applied": False, "reason": "no_action"}

    rule = CONVERSION_RULES.get(action)
    if rule is None:
        allowed = ", ".join(sorted(CONVERSION_RULES.keys()))
        raise ValueError(f"Unbekannte Konvertierungsaktion '{action}'. Erlaubte Aktionen: {allowed}")

    target_kind = _text(data.get("document_kind") or data.get("letter_type")).lower()
    if target_kind and target_kind != rule["target_kind"]:
        raise ValueError(
            f"Konvertierungsaktion '{action}' ist nur für Zieltyp '{rule['target_kind']}' erlaubt (aktuell: '{target_kind}')."
        )

    source_document = _extract_source_document(data)
    source_kind = _extract_source_kind(data, source_document).lower()
    source_status = _extract_source_status(source_document)
    source_id = _extract_source_id(data, source_document)
    source_number = _extract_source_number(data, source_document)

    if source_kind and source_kind != rule["source_kind"]:
        raise ValueError(
            f"Konvertierungsaktion '{action}' erwartet Quelldokument-Typ '{rule['source_kind']}' (aktuell: '{source_kind}')."
        )

    if not source_kind:
        source_kind = rule["source_kind"]

    allowed_statuses = _ACTION_ALLOWED_SOURCE_STATUSES.get(action, set())
    if source_status and allowed_statuses and source_status not in allowed_statuses:
        readable = ", ".join(sorted(allowed_statuses))
        raise ValueError(
            f"Konvertierungsaktion '{action}' ist für Quelldokument-Status '{source_status}' nicht erlaubt "
            f"(erlaubt: {readable})."
        )

    if not source_id and not source_number:
        raise ValueError(
            "Konvertierungsaktion benötigt ein Referenzdokument (source_document_id oder source_document_number)."
        )

    data["source_document_kind"] = source_kind
    if source_id:
        data["source_document_id"] = source_id
    if source_number:
        data["source_document_number"] = source_number

    _copy_from_source_document(data, source_document, source_number)

    follow_ups = _extract_follow_up_documents(data, source_document)

    copied_position_count = 0
    if rule["copy_positions"]:
        source_positions = _extract_source_positions(source_document)
        selected_line_ids = _resolve_selected_line_ids(data, source_positions)
        quantity_overrides = _resolve_quantity_overrides(data)

        copied_positions: list[dict[str, Any]] = []
        if action == "lieferschein_to_rechnung":
            copied_positions = _apply_delivery_to_invoice_remaining_logic(
                data=data,
                source_positions=source_positions,
                quantity_overrides=quantity_overrides,
                selected_line_ids=selected_line_ids,
                follow_ups=follow_ups,
            )
        else:
            for item in source_positions:
                line_id = _text(item.get("line_id"))
                if line_id and line_id not in selected_line_ids:
                    continue
                copied = dict(item)
                if line_id in quantity_overrides:
                    copied["quantity"] = str(quantity_overrides[line_id])
                copied_positions.append(copied)

        if action in {"rechnung_to_stornorechnung", "rechnung_to_gutschrift"}:
            copied_positions = _apply_credit_or_storno_sign_logic(copied_positions)

        if copied_positions:
            data["positions"] = copied_positions
        copied_position_count = len(copied_positions)

        if action == "lieferschein_to_rechnung" and copied_position_count <= 0:
            raise ValueError("Keine offene Restmenge für die Rechnungsstellung verfügbar.")

    reminder_open_amount: Decimal | None = None
    if action == "rechnung_to_zahlungserinnerung":
        reminder_open_amount = _apply_reminder_open_amount_logic(data, source_document, follow_ups)
        if reminder_open_amount <= Decimal("0"):
            raise ValueError("Für die gewählte Rechnung besteht kein offener Betrag mehr.")

    quantity_chain = build_quantity_chain_snapshot(data)

    return {
        "applied": True,
        "action": action,
        "source_kind": source_kind,
        "target_kind": rule["target_kind"],
        "copied_positions": copied_position_count,
        "source_document_number": source_number,
        "source_document_id": source_id,
        "source_document_status": source_status,
        "follow_up_documents": len(follow_ups),
        "open_amount": str(reminder_open_amount) if reminder_open_amount is not None else "",
        "quantity_chain": quantity_chain,
    }
