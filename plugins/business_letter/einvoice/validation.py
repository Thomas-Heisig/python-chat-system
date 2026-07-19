from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, cast
from xml.etree import ElementTree as ET

from plugins.business_letter.services.calculation import money


_ISO_4217_CURRENCY_CODES = {
    "EUR",
    "USD",
    "GBP",
    "CHF",
    "SEK",
    "NOK",
    "DKK",
    "PLN",
    "CZK",
}

_UNCL5305_TAX_CATEGORY_CODES = {
    "S",
    "Z",
    "E",
    "AE",
    "K",
    "G",
    "O",
    "L",
    "M",
}

_UNCL4461_PAYMENT_MEANS_CODES = {
    "30",
    "31",
    "42",
    "48",
    "49",
    "57",
    "58",
    "59",
    "60",
    "97",
}

_UNECE_REC20_UNIT_CODES = {
    "C62",
    "H87",
    "KGM",
    "GRM",
    "MTR",
    "MTK",
    "MTQ",
    "LTR",
    "DAY",
    "HUR",
}


def _issue(code: str, path: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "path": path, "message": message, "severity": severity}


def _dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = cast(dict[object, object], value)
    return {str(key): item for key, item in raw.items()}


def _list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    raw = cast(list[Any], value)
    return [_dict(item) for item in raw if isinstance(item, dict)]


def validate_xrechnung_xml_conformance(
    xml_payload: str,
    *,
    validation_context: dict[str, Any],
    totals: dict[str, Any],
    syntax: str = "UBL",
) -> dict[str, Any]:
    if syntax.strip().upper() == "CII":
        return validate_xrechnung_cii_conformance(xml_payload, validation_context=validation_context, totals=totals)

    issues: list[dict[str, str]] = []
    schema_rules: list[dict[str, Any]] = []
    schematron_rules: list[dict[str, Any]] = []

    if not xml_payload.strip():
        issues.append(_issue("XR-SCHEMA-000", "xml", "XML-Payload fehlt.", "error"))
        return {
            "valid": False,
            "issues": issues,
            "schema": {"valid": False, "rules": schema_rules},
            "schematron": {"valid": False, "rules": schematron_rules},
            "errors": list(issues),
            "warnings": [],
        }

    root: ET.Element | None = None
    try:
        root = ET.fromstring(xml_payload)
        schema_rules.append({"rule_id": "XR-SCHEMA-001", "severity": "info", "status": "pass", "message": "XML ist wohlgeformt."})
    except ET.ParseError as exc:
        msg = f"XML nicht wohlgeformt: {exc}"
        issues.append(_issue("XR-SCHEMA-001", "xml", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-001", "severity": "error", "status": "fail", "message": msg})
        return {
            "valid": False,
            "issues": issues,
            "schema": {"valid": False, "rules": schema_rules},
            "schematron": {"valid": False, "rules": schematron_rules},
            "errors": list(issues),
            "warnings": [],
        }

    assert root is not None
    if not root.tag.endswith("Invoice"):
        msg = "Wurzelelement muss Invoice sein."
        issues.append(_issue("XR-SCHEMA-002", "xml.root", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-002", "severity": "error", "status": "fail", "message": msg})
    else:
        schema_rules.append({"rule_id": "XR-SCHEMA-002", "severity": "info", "status": "pass", "message": "Wurzelelement Invoice vorhanden."})

    def local_name(tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def find_child(element: ET.Element, child_name: str) -> ET.Element | None:
        for child in list(element):
            if local_name(child.tag) == child_name:
                return child
        return None

    def find_node(path: str) -> ET.Element | None:
        node: ET.Element | None = root
        for segment in path.split("/"):
            if node is None:
                return None
            node = find_child(node, segment)
        return node

    def find_text(path: str) -> str:
        node = find_node(path)
        return (node.text or "").strip() if node is not None and node.text else ""

    invoice_id = find_text("ID")
    if not invoice_id:
        msg = "Invoice ID fehlt."
        issues.append(_issue("XR-SCHEMA-003", "ID", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-003", "severity": "error", "status": "fail", "message": msg})
    else:
        schema_rules.append({"rule_id": "XR-SCHEMA-003", "severity": "info", "status": "pass", "message": "Invoice ID vorhanden."})

    buyer_ref = find_text("BuyerReference")
    if not buyer_ref:
        msg = "BuyerReference fehlt."
        issues.append(_issue("XR-SCHEMA-004", "BuyerReference", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-004", "severity": "error", "status": "fail", "message": msg})
    else:
        schema_rules.append({"rule_id": "XR-SCHEMA-004", "severity": "info", "status": "pass", "message": "BuyerReference vorhanden."})

    issue_date_text = find_text("IssueDate")
    if not issue_date_text:
        msg = "IssueDate fehlt."
        issues.append(_issue("XR-SCHEMA-006", "IssueDate", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-006", "severity": "error", "status": "fail", "message": msg})
    else:
        try:
            datetime.strptime(issue_date_text, "%Y-%m-%d")
            schema_rules.append({"rule_id": "XR-SCHEMA-006", "severity": "info", "status": "pass", "message": "IssueDate im ISO-Format YYYY-MM-DD."})
        except ValueError:
            msg = "IssueDate muss im Format YYYY-MM-DD sein."
            issues.append(_issue("XR-SCHEMA-006", "IssueDate", msg, "error"))
            schema_rules.append({"rule_id": "XR-SCHEMA-006", "severity": "error", "status": "fail", "message": msg})

    payable_amount_text = find_text("LegalMonetaryTotal/PayableAmount")
    payable_decimal = Decimal("0")
    try:
        payable_decimal = Decimal(payable_amount_text or "0")
        schema_rules.append({"rule_id": "XR-SCHEMA-005", "severity": "info", "status": "pass", "message": "PayableAmount numerisch."})
    except Exception:
        msg = "PayableAmount ist nicht numerisch."
        issues.append(_issue("XR-SCHEMA-005", "PayableAmount", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-005", "severity": "error", "status": "fail", "message": msg})

    document_currency = find_text("DocumentCurrencyCode")
    if not document_currency:
        msg = "DocumentCurrencyCode fehlt."
        issues.append(_issue("XR-SCHEMA-007", "DocumentCurrencyCode", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-007", "severity": "error", "status": "fail", "message": msg})
    elif document_currency not in _ISO_4217_CURRENCY_CODES:
        msg = f"DocumentCurrencyCode '{document_currency}' ist nicht in der erlaubten Codeliste."
        issues.append(_issue("XR-SCHEMA-007", "DocumentCurrencyCode", msg, "error"))
        schema_rules.append({"rule_id": "XR-SCHEMA-007", "severity": "error", "status": "fail", "message": msg})
    else:
        schema_rules.append({"rule_id": "XR-SCHEMA-007", "severity": "info", "status": "pass", "message": "DocumentCurrencyCode gueltig."})

    payment_means_code = find_text("PaymentMeans/PaymentMeansCode")
    if payment_means_code:
        if payment_means_code not in _UNCL4461_PAYMENT_MEANS_CODES:
            msg = f"PaymentMeansCode '{payment_means_code}' ist nicht in der erlaubten Codeliste."
            issues.append(_issue("XR-SCH-004", "PaymentMeansCode", msg, "error"))
            schematron_rules.append({"rule_id": "XR-SCH-004", "severity": "error", "status": "fail", "message": msg})
        else:
            schematron_rules.append({"rule_id": "XR-SCH-004", "severity": "info", "status": "pass", "message": "PaymentMeansCode gueltig."})
    else:
        schematron_rules.append({"rule_id": "XR-SCH-004", "severity": "warning", "status": "pass", "message": "PaymentMeansCode optional nicht gesetzt."})

    expected_buyer_ref = str(validation_context.get("buyer_reference") or "").strip()
    if expected_buyer_ref and buyer_ref != expected_buyer_ref:
        msg = "BuyerReference in XML und Kontext weichen voneinander ab."
        issues.append(_issue("XR-SCH-001", "BuyerReference", msg, "warning"))
        schematron_rules.append({"rule_id": "XR-SCH-001", "severity": "warning", "status": "fail", "message": msg})
    else:
        schematron_rules.append({"rule_id": "XR-SCH-001", "severity": "info", "status": "pass", "message": "BuyerReference konsistent."})

    expected_payable_text = str(totals.get("payable_amount") or "0").strip() or "0"
    try:
        expected_payable = Decimal(expected_payable_text)
        if payable_decimal != expected_payable:
            msg = "PayableAmount stimmt nicht mit der berechneten Summe überein."
            issues.append(_issue("XR-SCH-002", "PayableAmount", msg, "error"))
            schematron_rules.append({"rule_id": "XR-SCH-002", "severity": "error", "status": "fail", "message": msg})
        else:
            schematron_rules.append({"rule_id": "XR-SCH-002", "severity": "info", "status": "pass", "message": "PayableAmount konsistent."})
    except Exception:
        msg = "Erwartete PayableAmount konnte nicht geprüft werden."
        issues.append(_issue("XR-SCH-002", "PayableAmount", msg, "warning"))
        schematron_rules.append({"rule_id": "XR-SCH-002", "severity": "warning", "status": "fail", "message": msg})

    tax_subtotals: list[ET.Element] = []
    tax_total_node = find_node("TaxTotal")
    if tax_total_node is not None:
        for child in list(tax_total_node):
            if local_name(child.tag) == "TaxSubtotal":
                tax_subtotals.append(child)

    invoice_lines: list[ET.Element] = []
    for child in list(root):
        if local_name(child.tag) == "InvoiceLine":
            invoice_lines.append(child)

    invalid_tax_categories = 0
    for subtotal in tax_subtotals:
        category_container = find_child(subtotal, "TaxCategory")
        category_node = find_child(category_container, "ID") if category_container is not None else None
        category = (category_node.text or "").strip() if category_node is not None and category_node.text else ""
        if category and category not in _UNCL5305_TAX_CATEGORY_CODES:
            invalid_tax_categories += 1
    if invalid_tax_categories:
        msg = "Eine oder mehrere TaxCategory-Codes sind ausserhalb der erlaubten Codeliste."
        issues.append(_issue("XR-SCH-005", "TaxCategory", msg, "error"))
        schematron_rules.append({"rule_id": "XR-SCH-005", "severity": "error", "status": "fail", "message": msg})
    else:
        schematron_rules.append({"rule_id": "XR-SCH-005", "severity": "info", "status": "pass", "message": "TaxCategory-Codes gueltig."})

    invalid_unit_codes = 0
    for line in invoice_lines:
        quantity_node = find_child(line, "InvoicedQuantity")
        unit_code = (quantity_node.attrib.get("unitCode") or "").strip().upper() if quantity_node is not None else ""
        if unit_code and unit_code not in _UNECE_REC20_UNIT_CODES:
            invalid_unit_codes += 1
    if invalid_unit_codes:
        msg = "Eine oder mehrere InvoicedQuantity unitCode-Werte sind nicht in der erlaubten Codeliste."
        issues.append(_issue("XR-SCH-006", "InvoiceLine.InvoicedQuantity@unitCode", msg, "error"))
        schematron_rules.append({"rule_id": "XR-SCH-006", "severity": "error", "status": "fail", "message": msg})
    else:
        schematron_rules.append({"rule_id": "XR-SCH-006", "severity": "info", "status": "pass", "message": "InvoicedQuantity unitCode-Werte gueltig."})

    schema_valid = not any(rule.get("severity") == "error" and rule.get("status") == "fail" for rule in schema_rules)
    schematron_valid = not any(rule.get("severity") == "error" and rule.get("status") == "fail" for rule in schematron_rules)
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    warnings = [issue for issue in issues if issue.get("severity") == "warning"]
    return {
        "valid": schema_valid and schematron_valid,
        "issues": issues,
        "schema": {"valid": schema_valid, "rules": schema_rules},
        "schematron": {"valid": schematron_valid, "rules": schematron_rules},
        "errors": errors,
        "warnings": warnings,
    }


def validate_xrechnung_cii_conformance(
    xml_payload: str,
    *,
    validation_context: dict[str, Any],
    totals: dict[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    schema_rules: list[dict[str, Any]] = []
    schematron_rules: list[dict[str, Any]] = []

    if not xml_payload.strip():
        issues.append(_issue("XR-CII-SCHEMA-000", "xml", "XML-Payload fehlt.", "error"))
        return {
            "valid": False,
            "issues": issues,
            "schema": {"valid": False, "rules": schema_rules},
            "schematron": {"valid": False, "rules": schematron_rules},
            "errors": list(issues),
            "warnings": [],
        }

    try:
        root = ET.fromstring(xml_payload)
        schema_rules.append({"rule_id": "XR-CII-SCHEMA-001", "severity": "info", "status": "pass", "message": "CII-XML ist wohlgeformt."})
    except ET.ParseError as exc:
        msg = f"CII-XML nicht wohlgeformt: {exc}"
        issues.append(_issue("XR-CII-SCHEMA-001", "xml", msg, "error"))
        schema_rules.append({"rule_id": "XR-CII-SCHEMA-001", "severity": "error", "status": "fail", "message": msg})
        return {
            "valid": False,
            "issues": issues,
            "schema": {"valid": False, "rules": schema_rules},
            "schematron": {"valid": False, "rules": schematron_rules},
            "errors": list(issues),
            "warnings": [],
        }

    def local_name(tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    if local_name(root.tag) != "CrossIndustryInvoice":
        msg = "Wurzelelement muss CrossIndustryInvoice sein."
        issues.append(_issue("XR-CII-SCHEMA-002", "xml.root", msg, "error"))
        schema_rules.append({"rule_id": "XR-CII-SCHEMA-002", "severity": "error", "status": "fail", "message": msg})
    else:
        schema_rules.append({"rule_id": "XR-CII-SCHEMA-002", "severity": "info", "status": "pass", "message": "Wurzelelement CrossIndustryInvoice vorhanden."})

    def find_by_local_name(element: ET.Element, name: str) -> list[ET.Element]:
        return [child for child in element.iter() if local_name(child.tag) == name]

    def first_text(name: str) -> str:
        for node in find_by_local_name(root, name):
            if node.text and node.text.strip():
                return node.text.strip()
        return ""

    def path_text(path: list[str]) -> str:
        current_nodes: list[ET.Element] = [root]
        for segment in path:
            next_nodes: list[ET.Element] = []
            for node in current_nodes:
                next_nodes.extend([child for child in list(node) if local_name(child.tag) == segment])
            if not next_nodes:
                return ""
            current_nodes = next_nodes
        for node in current_nodes:
            if node.text and node.text.strip():
                return node.text.strip()
        return ""

    invoice_id = first_text("ID")
    if not invoice_id:
        issues.append(_issue("XR-CII-SCHEMA-003", "ram:ID", "Invoice ID fehlt.", "error"))

    buyer_reference = first_text("BuyerReference")
    if not buyer_reference:
        issues.append(_issue("XR-CII-SCHEMA-004", "ram:BuyerReference", "BuyerReference fehlt.", "error"))

    document_currency = first_text("InvoiceCurrencyCode")
    if not document_currency:
        issues.append(_issue("XR-CII-SCHEMA-005", "ram:InvoiceCurrencyCode", "InvoiceCurrencyCode fehlt.", "error"))
    elif document_currency not in _ISO_4217_CURRENCY_CODES:
        issues.append(_issue("XR-CII-SCHEMA-005", "ram:InvoiceCurrencyCode", f"InvoiceCurrencyCode '{document_currency}' ist nicht in der erlaubten Codeliste.", "error"))

    due_payable_amount_text = first_text("DuePayableAmount")
    due_payable_amount = Decimal("0")
    try:
        due_payable_amount = Decimal(due_payable_amount_text or "0")
    except Exception:
        issues.append(_issue("XR-CII-SCHEMA-006", "ram:DuePayableAmount", "DuePayableAmount ist nicht numerisch.", "error"))

    endpoint_nodes = [node for node in find_by_local_name(root, "URIID") if node.attrib.get("schemeID")]
    if len(endpoint_nodes) < 2:
        issues.append(_issue("XR-CII-SCH-001", "ram:URIID", "Buyer- und Seller-EndpointID sollen vorhanden sein.", "warning"))

    payment_type_code = path_text([
        "SupplyChainTradeTransaction",
        "ApplicableHeaderTradeSettlement",
        "SpecifiedTradeSettlementPaymentMeans",
        "TypeCode",
    ])
    if payment_type_code and payment_type_code not in _UNCL4461_PAYMENT_MEANS_CODES and payment_type_code != "VAT":
        issues.append(_issue("XR-CII-SCH-004", "ram:TypeCode", f"PaymentMeansCode '{payment_type_code}' ist nicht in der erlaubten Codeliste.", "error"))

    for quantity_node in find_by_local_name(root, "BilledQuantity"):
        unit_code = (quantity_node.attrib.get("unitCode") or "").strip().upper()
        if unit_code and unit_code not in _UNECE_REC20_UNIT_CODES:
            issues.append(_issue("XR-CII-SCH-006", "ram:BilledQuantity@unitCode", f"Einheiten-Code '{unit_code}' ist nicht in der erlaubten Codeliste.", "error"))

    for category_node in find_by_local_name(root, "CategoryCode"):
        category = (category_node.text or "").strip()
        if category and category not in _UNCL5305_TAX_CATEGORY_CODES:
            issues.append(_issue("XR-CII-SCH-005", "ram:CategoryCode", f"TaxCategory '{category}' ist nicht in der erlaubten Codeliste.", "error"))

    for basis_quantity in find_by_local_name(root, "BasisQuantity"):
        try:
            if Decimal((basis_quantity.text or "0").strip() or "0") <= 0:
                issues.append(_issue("XR-CII-SCH-007", "ram:BasisQuantity", "Preisbasismenge muss größer als 0 sein.", "error"))
        except Exception:
            issues.append(_issue("XR-CII-SCH-007", "ram:BasisQuantity", "Preisbasismenge ist nicht numerisch.", "error"))

    rounding_amount = Decimal(first_text("RoundingAmount") or "0")
    prepaid_amount = Decimal(first_text("TotalPrepaidAmount") or "0")
    grand_total_amount = Decimal(first_text("GrandTotalAmount") or "0")
    expected_due = money(totals.get("payable_amount") or 0)
    if due_payable_amount_text and money(due_payable_amount) != expected_due:
        issues.append(_issue("XR-CII-SCH-002", "ram:DuePayableAmount", "DuePayableAmount stimmt nicht mit der berechneten Summe überein.", "error"))

    if due_payable_amount_text and money(due_payable_amount) != money(grand_total_amount - prepaid_amount + rounding_amount):
        issues.append(_issue("XR-CII-SCH-003", "ram:DuePayableAmount", "DuePayableAmount ist rechnerisch inkonsistent.", "error"))

    schema_valid = not any(issue["code"].startswith("XR-CII-SCHEMA") and issue["severity"] == "error" for issue in issues)
    schematron_valid = not any(issue["code"].startswith("XR-CII-SCH") and issue["severity"] == "error" for issue in issues)
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    warnings = [issue for issue in issues if issue.get("severity") == "warning"]
    return {
        "valid": schema_valid and schematron_valid,
        "issues": issues,
        "schema": {"valid": schema_valid, "rules": schema_rules},
        "schematron": {"valid": schematron_valid, "rules": schematron_rules},
        "errors": errors,
        "warnings": warnings,
    }


def validate_xrechnung_document(commercial_document: dict[str, Any], company: dict[str, str], recipient: dict[str, str]) -> dict[str, Any]:
    einvoice = _dict(commercial_document.get("einvoice"))
    customer_visible = _dict(commercial_document.get("customer_visible"))
    if not einvoice:
        einvoice = _dict(customer_visible.get("einvoice"))
    totals = _dict(commercial_document.get("totals"))
    positions = _list(commercial_document.get("positions"))
    vat_breakdown = _list(commercial_document.get("vat_breakdown"))
    if not vat_breakdown:
        vat_breakdown = _list(customer_visible.get("vat_breakdown"))

    profile = str(einvoice.get("profile") or "basic").strip() or "basic"
    syntax = str(einvoice.get("syntax") or "UBL").strip().upper() or "UBL"
    issues: list[dict[str, str]] = []

    buyer_reference = str(customer_visible.get("buyer_reference") or commercial_document.get("buyer_reference") or "").strip()
    if not buyer_reference:
        issues.append(_issue("BR-DE-001", "buyer_reference", "Käuferreferenz / Leitweg-ID fehlt."))

    buyer = _dict(customer_visible.get("buyer"))
    buyer_name = str(buyer.get("name") or "").strip() or str(recipient.get("company") or recipient.get("name") or "").strip()
    if not buyer_name:
        issues.append(_issue("BR-DE-002", "buyer.name", "Käufername fehlt."))

    buyer_endpoint = str(buyer.get("electronic_address") or "").strip()
    buyer_endpoint_scheme = str(buyer.get("electronic_address_scheme") or "").strip()
    if buyer_endpoint and not buyer_endpoint_scheme:
        issues.append(_issue("BR-DE-004", "buyer.electronic_address_scheme", "Elektronische Käuferadresse benötigt ein schemeID."))

    seller_vat_id = str(company.get("vat_id") or "").strip()
    if not seller_vat_id:
        issues.append(_issue("BR-DE-003", "seller.vat_id", "USt-IdNr. fehlt."))

    seller = _dict(customer_visible.get("seller"))
    seller_endpoint = str(seller.get("electronic_address") or "").strip()
    seller_endpoint_scheme = str(seller.get("electronic_address_scheme") or "").strip()
    if seller_endpoint and not seller_endpoint_scheme:
        issues.append(_issue("BR-DE-005", "seller.electronic_address_scheme", "Elektronische Verkäuferadresse benötigt ein schemeID."))

    if not positions:
        issues.append(_issue("BR-DE-010", "invoice_lines", "Mindestens eine Rechnungsposition ist erforderlich."))
    else:
        for idx, position in enumerate(positions, start=1):
            unit_code = str(position.get("unit_code") or "").strip().upper()
            if not unit_code:
                issues.append(_issue("BR-CL-004", f"positions[{idx}].unit_code", "Einheiten-Code fehlt."))
            elif unit_code not in _UNECE_REC20_UNIT_CODES:
                issues.append(_issue("BR-CL-004", f"positions[{idx}].unit_code", f"Einheiten-Code '{unit_code}' ist nicht in der erlaubten Codeliste."))
            base_quantity = money(position.get("price_base_quantity") or 1)
            if base_quantity <= 0:
                issues.append(_issue("BR-DE-011", f"positions[{idx}].price_base_quantity", "Preisbasismenge muss größer als 0 sein."))

    if not str(totals.get("payable_amount") or "").strip():
        issues.append(_issue("BR-DE-020", "totals.payable_amount", "Zahlbetrag fehlt."))

    currency = str(totals.get("currency") or customer_visible.get("currency") or "EUR").strip() or "EUR"
    if currency not in _ISO_4217_CURRENCY_CODES:
        issues.append(_issue("BR-CL-001", "currency", f"Waehrungscode '{currency}' ist nicht in der erlaubten Codeliste."))

    payment_means_code = str(
        customer_visible.get("payment_means_code")
        or commercial_document.get("payment_means_code")
        or customer_visible.get("payment_method_code")
        or commercial_document.get("payment_method_code")
        or ""
    ).strip()
    if payment_means_code and payment_means_code not in _UNCL4461_PAYMENT_MEANS_CODES:
        issues.append(_issue("BR-CL-002", "payment_means_code", f"PaymentMeansCode '{payment_means_code}' ist nicht in der erlaubten Codeliste."))

    tax_breakdown: list[dict[str, Any]] = []
    for item in vat_breakdown:
        category = str(item.get("category") or "S").strip() or "S"
        if category not in _UNCL5305_TAX_CATEGORY_CODES:
            issues.append(_issue("BR-CL-003", "vat_breakdown.category", f"TaxCategory '{category}' ist nicht in der erlaubten Codeliste."))
        rate = str(item.get("rate") or "0").strip() or "0"
        taxable_amount = str(item.get("taxable_amount") or "0.00").strip() or "0.00"
        tax_amount = str(item.get("tax_amount") or "0.00").strip() or "0.00"
        tax_exemption_reason = str(item.get("tax_exemption_reason") or "").strip()
        tax_exemption_reason_code = str(item.get("tax_exemption_reason_code") or "").strip()
        if category in {"AE", "E", "Z", "O", "K", "G"} and not tax_exemption_reason:
            issues.append(_issue("BR-DE-050", "vat_breakdown.tax_exemption_reason", f"TaxCategory '{category}' benötigt einen Steuerbefreiungs- oder Reverse-Charge-Grund."))
        tax_breakdown.append(
            {
                "category": category,
                "rate": rate,
                "taxable_amount": taxable_amount,
                "tax_amount": tax_amount,
                "currency": currency,
                "tax_exemption_reason": tax_exemption_reason,
                "tax_exemption_reason_code": tax_exemption_reason_code,
            }
        )

    for idx, position in enumerate(positions, start=1):
        line_tax_category = str(position.get("vat_category") or "S").strip() or "S"
        if line_tax_category not in _UNCL5305_TAX_CATEGORY_CODES:
            issues.append(_issue("BR-CL-003", f"positions[{idx}].vat_category", f"TaxCategory '{line_tax_category}' ist nicht in der erlaubten Codeliste."))

    reverse_charge = str(customer_visible.get("payment_method_code") or "").strip().upper() == "AE"
    if reverse_charge and not seller_vat_id:
        issues.append(_issue("BR-DE-030", "tax.reverse_charge", "Reverse-Charge benötigt eine Verkäufer-USt-IdNr."))

    if positions and not tax_breakdown:
        issues.append(_issue("BR-DE-040", "vat_breakdown", "Steueraufschlüsselung fehlt."))

    tax_total_expected = money(totals.get("tax_total") or 0)
    tax_total_from_breakdown = sum((money(item.get("tax_amount") or 0) for item in tax_breakdown), start=money(0))
    if tax_breakdown and tax_total_expected != tax_total_from_breakdown:
        issues.append(_issue("BR-DE-041", "totals.tax_total", "Steuersumme passt nicht zur Aufschlüsselung."))

    tax_exclusive_expected = money(totals.get("tax_exclusive_amount") or 0)
    taxable_total_from_breakdown = sum((money(item.get("taxable_amount") or 0) for item in tax_breakdown), start=money(0))
    if tax_breakdown and tax_exclusive_expected != taxable_total_from_breakdown:
        issues.append(_issue("BR-DE-042", "totals.tax_exclusive_amount", "Steuerbare Summe passt nicht zur Aufschlüsselung."))

    tax_inclusive_expected = money(totals.get("tax_inclusive_amount") or 0)
    prepaid_amount = money(totals.get("prepaid_amount") or 0)
    payable_rounding_amount = money(totals.get("payable_rounding_amount") or totals.get("rounding_amount") or 0)
    payable_amount = money(totals.get("payable_amount") or 0)
    if payable_amount != money(tax_inclusive_expected - prepaid_amount + payable_rounding_amount):
        issues.append(_issue("BR-DE-043", "totals.payable_amount", "Zahlbetrag ist rechnerisch inkonsistent."))

    return {
        "valid": not any(issue.get("severity") == "error" for issue in issues),
        "standard": "XRechnung",
        "profile": profile,
        "syntax": syntax,
        "buyer_reference": buyer_reference,
        "buyer_name": buyer_name,
        "seller_vat_id": seller_vat_id,
        "tax_breakdown": tax_breakdown,
        "issues": issues,
        "errors": [issue for issue in issues if issue.get("severity") == "error"],
        "warnings": [issue for issue in issues if issue.get("severity") == "warning"],
    }
