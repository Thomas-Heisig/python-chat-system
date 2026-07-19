from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, cast

MONEY_QUANT = Decimal("0.01")
QUANTITY_QUANT = Decimal("0.001")
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")


def money(value: Any) -> Decimal:
    return Decimal(str(value or "0")).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def quantity(value: Any) -> Decimal:
    return Decimal(str(value or "0")).quantize(QUANTITY_QUANT, rounding=ROUND_HALF_UP)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = cast(dict[object, object], value)
    return {str(key): item for key, item in raw.items()}


def _as_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return cast(list[Any], value)


def _normalize_shipping_costs(raw_value: Any) -> list[dict[str, Any]]:
    if raw_value is None:
        return []
    if isinstance(raw_value, (str, int, float)) and raw_value in {"", 0, 0.0, "0", "0.00"}:
        return []
    if isinstance(raw_value, list):
        raw_items = _as_list(raw_value)
        normalized_items: list[dict[str, Any]] = []
        for item in raw_items:
            if isinstance(item, dict):
                normalized_items.append(_as_dict(item))
        return normalized_items
    if isinstance(raw_value, dict):
        return [_as_dict(raw_value)]
    return [{"reason": "Versandkosten", "amount": raw_value}]


def parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_document_kind(value: Any, commercial_types: set[str], communication_types: set[str]) -> str:
    raw = str(value or "allgemein").strip().lower()
    if raw in commercial_types or raw in communication_types:
        return raw
    return "allgemein"


def normalize_money_adjustments(
    raw_value: Any,
    *,
    base_amount: Any = None,
    default_vat_category: str = "S",
    default_vat_rate: Any = 0,
    default_tax_exemption_reason: str = "",
    default_tax_exemption_reason_code: str = "",
) -> dict[str, Any]:
    if not isinstance(raw_value, list):
        return {"items": [], "total": Decimal("0")}

    items: list[dict[str, Any]] = []
    total = Decimal("0")
    normalized_base_amount = money(base_amount or 0)
    for item in cast(list[Any], raw_value):
        if not isinstance(item, dict):
            continue
        payload = {str(key): value for key, value in cast(dict[object, Any], item).items()}
        amount = money(payload.get("amount") or 0)
        percentage = money(payload.get("percentage") or 0)
        if not amount and percentage and normalized_base_amount:
            amount = money(normalized_base_amount * percentage / Decimal("100"))
        total += amount
        items.append(
            {
                "reason": _text(payload.get("reason")),
                "reason_code": _text(payload.get("reason_code")),
                "amount": str(amount),
                "percentage": str(percentage),
                "vat_category": _text(payload.get("vat_category") or payload.get("tax_category") or default_vat_category).upper() or "S",
                "vat_rate": str(money(payload.get("vat_rate") or payload.get("tax_rate") or default_vat_rate or 0)),
                "tax_exemption_reason": _text(payload.get("tax_exemption_reason") or default_tax_exemption_reason),
                "tax_exemption_reason_code": _text(payload.get("tax_exemption_reason_code") or default_tax_exemption_reason_code),
            }
        )
    return {"items": items, "total": money(total)}


def normalize_positions(raw_positions: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_positions, list):
        return []

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(cast(list[Any], raw_positions), start=1):
        if not isinstance(item, dict):
            continue
        position = {str(key): value for key, value in cast(dict[object, Any], item).items()}
        line_id = str(position.get("line_id") or f"{index:03d}").strip()
        name = str(position.get("name") or position.get("description") or "").strip()
        quantity_value = quantity(position.get("quantity") or 0)
        unit_code = str(position.get("unit_code") or "C62").strip()
        unit_label = str(position.get("unit_label") or unit_code).strip()
        price_net = money(position.get("price_net") or 0)
        base_quantity = quantity(position.get("price_base_quantity") or 1)
        base_quantity_unit_code = str(position.get("price_base_quantity_unit_code") or unit_code).strip() or unit_code
        vat_category = str(position.get("vat_category") or "S").strip().upper()
        vat_rate = money(position.get("vat_rate") or 0)
        tax_exemption_reason = _text(position.get("tax_exemption_reason"))
        tax_exemption_reason_code = _text(position.get("tax_exemption_reason_code"))
        if vat_category == "AE" and not tax_exemption_reason:
            tax_exemption_reason = "Reverse charge"
        if vat_category in {"E", "Z", "O", "K", "G"} and not tax_exemption_reason:
            tax_exemption_reason = "Steuerbefreite Lieferung/Leistung"

        base_line_amount = quantity_value * (price_net / base_quantity if base_quantity else Decimal("0"))
        allowances = normalize_money_adjustments(
            position.get("allowances"),
            base_amount=base_line_amount,
            default_vat_category=vat_category,
            default_vat_rate=vat_rate,
            default_tax_exemption_reason=tax_exemption_reason,
            default_tax_exemption_reason_code=tax_exemption_reason_code,
        )
        charges = normalize_money_adjustments(
            position.get("charges"),
            base_amount=base_line_amount,
            default_vat_category=vat_category,
            default_vat_rate=vat_rate,
            default_tax_exemption_reason=tax_exemption_reason,
            default_tax_exemption_reason_code=tax_exemption_reason_code,
        )

        line_net_amount = money(base_line_amount - allowances["total"] + charges["total"])

        normalized.append(
            {
                "line_id": line_id,
                "article_number": str(position.get("article_number") or "").strip(),
                "seller_item_id": str(position.get("seller_item_id") or "").strip(),
                "buyer_item_id": str(position.get("buyer_item_id") or "").strip(),
                "name": name,
                "description": str(position.get("description") or "").strip(),
                "quantity": str(quantity_value),
                "unit_code": unit_code,
                "unit_label": unit_label,
                "price_net": str(price_net),
                "price_base_quantity": str(base_quantity),
                "price_base_quantity_unit_code": base_quantity_unit_code,
                "vat_category": vat_category,
                "vat_rate": str(vat_rate),
                "tax_exemption_reason": tax_exemption_reason,
                "tax_exemption_reason_code": tax_exemption_reason_code,
                "allowances": allowances["items"],
                "charges": charges["items"],
                "line_net_amount": str(line_net_amount),
                "service_period_start": str(position.get("service_period_start") or "").strip(),
                "service_period_end": str(position.get("service_period_end") or "").strip(),
                "project_reference": str(position.get("project_reference") or "").strip(),
                "accounting_cost": str(position.get("accounting_cost") or "").strip(),
                "material": {str(key): value for key, value in cast(dict[object, Any], position.get("material") or {}).items()} if isinstance(position.get("material"), dict) else {},
                "stone_details": {str(key): value for key, value in cast(dict[object, Any], position.get("stone_details") or {}).items()} if isinstance(position.get("stone_details"), dict) else {},
            }
        )
    return normalized


def calculate_commercial_document(
    *,
    data: dict[str, Any],
    company: dict[str, str],
    recipient: dict[str, str],
    positions: list[dict[str, Any]],
) -> dict[str, Any]:
    document_kind = str(data.get("document_kind") or data.get("letter_type") or "allgemein").strip().lower()
    line_net_total = sum((money(position.get("line_net_amount") or 0) for position in positions), start=Decimal("0"))

    default_category = "S"
    default_rate = Decimal("0")
    default_exemption_reason = ""
    default_exemption_code = ""
    if positions:
        first_position = positions[0]
        default_category = str(first_position.get("vat_category") or "S").strip().upper() or "S"
        default_rate = money(first_position.get("vat_rate") or 0)
        default_exemption_reason = _text(first_position.get("tax_exemption_reason"))
        default_exemption_code = _text(first_position.get("tax_exemption_reason_code"))

    document_allowance_items = data.get("document_allowances")
    document_charge_items = list(_as_list(data.get("document_charges"))) if isinstance(data.get("document_charges"), list) else ([] if data.get("document_charges") is None else [data.get("document_charges")])
    document_charge_items.extend(_normalize_shipping_costs(data.get("shipping_costs")))

    allowances = normalize_money_adjustments(
        document_allowance_items,
        base_amount=line_net_total,
        default_vat_category=default_category,
        default_vat_rate=default_rate,
        default_tax_exemption_reason=default_exemption_reason,
        default_tax_exemption_reason_code=default_exemption_code,
    )
    charges = normalize_money_adjustments(
        document_charge_items,
        base_amount=line_net_total,
        default_vat_category=default_category,
        default_vat_rate=default_rate,
        default_tax_exemption_reason=default_exemption_reason,
        default_tax_exemption_reason_code=default_exemption_code,
    )

    tax_breakdown: list[dict[str, Any]] = []
    vat_groups: dict[tuple[str, str, str, str], Decimal] = {}

    def add_tax_group(
        category: str,
        rate_text: str,
        taxable_amount: Decimal,
        *,
        tax_exemption_reason: str = "",
        tax_exemption_reason_code: str = "",
    ) -> None:
        key = (
            category.strip().upper() or "S",
            str(money(rate_text or 0)),
            tax_exemption_reason.strip(),
            tax_exemption_reason_code.strip(),
        )
        vat_groups[key] = vat_groups.get(key, Decimal("0")) + money(taxable_amount)

    for position in positions:
        add_tax_group(
            str(position.get("vat_category") or "S"),
            str(position.get("vat_rate") or "0"),
            money(position.get("line_net_amount") or 0),
            tax_exemption_reason=_text(position.get("tax_exemption_reason")),
            tax_exemption_reason_code=_text(position.get("tax_exemption_reason_code")),
        )

    for item in allowances["items"]:
        add_tax_group(
            str(item.get("vat_category") or default_category),
            str(item.get("vat_rate") or default_rate),
            -money(item.get("amount") or 0),
            tax_exemption_reason=_text(item.get("tax_exemption_reason")),
            tax_exemption_reason_code=_text(item.get("tax_exemption_reason_code")),
        )

    for item in charges["items"]:
        add_tax_group(
            str(item.get("vat_category") or default_category),
            str(item.get("vat_rate") or default_rate),
            money(item.get("amount") or 0),
            tax_exemption_reason=_text(item.get("tax_exemption_reason")),
            tax_exemption_reason_code=_text(item.get("tax_exemption_reason_code")),
        )

    reverse_charge = bool(data.get("reverse_charge")) or any(str(position.get("vat_category") or "").strip().upper() == "AE" for position in positions)

    tax_total = Decimal("0")
    for (category, rate_text, exemption_reason, exemption_code), taxable_amount in vat_groups.items():
        rate = money(rate_text)
        tax_amount = money(taxable_amount * rate / Decimal("100"))
        tax_total += tax_amount
        effective_exemption_reason = exemption_reason
        if category == "AE" and not effective_exemption_reason:
            effective_exemption_reason = _text(data.get("tax_exemption_reason")) or "Reverse charge"
        if category in {"E", "Z", "O", "K", "G"} and not effective_exemption_reason:
            effective_exemption_reason = _text(data.get("tax_exemption_reason")) or "Steuerbefreite Lieferung/Leistung"
        effective_exemption_code = exemption_code or _text(data.get("tax_exemption_reason_code"))
        tax_breakdown.append(
            {
                "category": category,
                "rate": str(rate),
                "taxable_amount": str(money(taxable_amount)),
                "tax_amount": str(tax_amount),
                "tax_exemption_reason": effective_exemption_reason,
                "tax_exemption_reason_code": effective_exemption_code,
            }
        )

    tax_exclusive_amount = money(line_net_total - allowances["total"] + charges["total"])
    tax_inclusive_amount = money(tax_exclusive_amount + tax_total)
    prepaid_amount = money(data.get("prepaid_amount") or 0)
    payable_rounding_amount = money(data.get("rounding_amount") or 0)
    payable_amount = money(tax_inclusive_amount - prepaid_amount + payable_rounding_amount)

    issue_date = parse_date(data.get("issue_date")) or datetime.now().date()
    service_period_start = parse_date(data.get("service_period_start"))
    service_period_end = parse_date(data.get("service_period_end"))
    payment_due_date = parse_date(data.get("payment_due_date"))

    internal_data = _as_dict(data.get("internal"))
    einvoice_data = _as_dict(data.get("einvoice"))

    internal_snapshot = {
        "raw_document_kind": document_kind,
        "internal_notes": str(internal_data.get("notes") or "").strip(),
        "supplier": str(internal_data.get("supplier") or "").strip(),
        "purchase_price": str(internal_data.get("purchase_price") or "").strip(),
        "margin": str(internal_data.get("margin") or "").strip(),
        "slab_number": str(internal_data.get("slab_number") or "").strip(),
    }

    customer_visible: dict[str, Any] = {
        "document_kind": document_kind,
        "issue_date": issue_date.isoformat(),
        "currency": str(data.get("currency") or "EUR").strip() or "EUR",
        "buyer_reference": str(data.get("buyer_reference") or "").strip(),
        "purchase_order_reference": str(data.get("purchase_order_reference") or "").strip(),
        "contract_reference": str(data.get("contract_reference") or "").strip(),
        "project_reference": str(data.get("project_reference") or "").strip(),
        "delivery_note_reference": str(data.get("delivery_note_reference") or "").strip(),
        "original_invoice_number": str(data.get("original_invoice_number") or data.get("billing_reference_document_number") or "").strip(),
        "service_period_start": service_period_start.isoformat() if service_period_start else "",
        "service_period_end": service_period_end.isoformat() if service_period_end else "",
        "payment_due_date": payment_due_date.isoformat() if payment_due_date else "",
        "payment_terms": str(data.get("payment_terms") or "").strip(),
        "payment_reference": str(data.get("payment_reference") or "").strip(),
        "payment_method_code": str(data.get("payment_method_code") or "").strip(),
        "reverse_charge": reverse_charge,
        "tax_exemption_reason": _text(data.get("tax_exemption_reason")),
        "tax_exemption_reason_code": _text(data.get("tax_exemption_reason_code")),
        "seller": {
            "name": company["name"],
            "email": company["email"],
            "vat_id": company["vat_id"],
            "tax_id": company["tax_id"],
            "street": company["street"],
            "postal_code": company["zip"],
            "city": company["city"],
            "country": company["country"],
            "electronic_address": _text(data.get("seller_electronic_address") or company.get("electronic_address")),
            "electronic_address_scheme": _text(data.get("seller_electronic_address_scheme") or company.get("electronic_address_scheme")),
            "bank_name": company.get("bank_name", ""),
            "iban": company.get("iban", ""),
            "bic": company.get("bic", ""),
            "account_holder": company.get("account_holder", ""),
        },
        "buyer": {
            "name": recipient.get("company") or recipient.get("name") or recipient.get("contact") or "",
            "email": recipient.get("email") or "",
            "street": recipient.get("street") or "",
            "postal_code": recipient.get("postal_code") or "",
            "city": recipient.get("city") or "",
            "country": recipient.get("country") or "",
            "electronic_address": _text(data.get("buyer_electronic_address") or ""),
            "electronic_address_scheme": _text(data.get("buyer_electronic_address_scheme") or ""),
        },
        "positions": [
            {
                "line_id": position.get("line_id"),
                "name": position.get("name"),
                "description": position.get("description"),
                "quantity": position.get("quantity"),
                "unit_code": position.get("unit_code"),
                "unit_label": position.get("unit_label"),
                "price_net": position.get("price_net"),
                "line_net_amount": position.get("line_net_amount"),
                "vat_category": position.get("vat_category"),
                "vat_rate": position.get("vat_rate"),
                "service_period_start": position.get("service_period_start"),
                "service_period_end": position.get("service_period_end"),
                "project_reference": position.get("project_reference"),
            }
            for position in positions
        ],
        "document_allowances": allowances["items"],
        "document_charges": charges["items"],
        "totals": {
            "line_net_total": str(money(line_net_total)),
            "allowance_total": str(allowances["total"]),
            "charge_total": str(charges["total"]),
            "tax_exclusive_amount": str(tax_exclusive_amount),
            "tax_total": str(money(tax_total)),
            "tax_inclusive_amount": str(tax_inclusive_amount),
            "prepaid_amount": str(prepaid_amount),
            "payable_rounding_amount": str(payable_rounding_amount),
            "payable_amount": str(payable_amount),
            "currency": str(data.get("currency") or "EUR").strip() or "EUR",
        },
        "vat_breakdown": tax_breakdown,
        "einvoice": einvoice_data,
    }

    return {
        "document_kind": document_kind,
        "customer_visible": customer_visible,
        "internal": internal_snapshot,
        "totals": customer_visible["totals"],
        "positions": positions,
    }
