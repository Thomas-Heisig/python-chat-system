from __future__ import annotations

from decimal import Decimal
from typing import Any, cast
from xml.sax.saxutils import escape

from plugins.business_letter.einvoice.cii import build_cii_xml
from plugins.business_letter.einvoice.official_validation import validate_xrechnung_official_conformance
from plugins.business_letter.einvoice.validation import validate_xrechnung_document, validate_xrechnung_xml_conformance


def _country_code(value: str) -> str:
    normalized = value.strip().upper()
    mapping = {
        "DE": "DE",
        "DEUTSCHLAND": "DE",
        "GERMANY": "DE",
        "AT": "AT",
        "OESTERREICH": "AT",
        "ÖSTERREICH": "AT",
        "AUSTRIA": "AT",
        "CH": "CH",
        "SCHWEIZ": "CH",
        "SWITZERLAND": "CH",
    }
    return mapping.get(normalized, "DE")


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = cast(dict[object, object], value)
    return {str(key): item for key, item in raw.items()}


def _as_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return cast(list[Any], value)


def build_xrechnung_xml(commercial_document: dict[str, Any], company: dict[str, str], recipient: dict[str, str]) -> dict[str, Any]:
    validation = validate_xrechnung_document(commercial_document, company, recipient)
    customer_visible = _as_dict(commercial_document.get("customer_visible"))
    totals = _as_dict(commercial_document.get("totals"))
    syntax = str(validation.get("syntax") or "UBL").strip().upper() or "UBL"
    tax_breakdown = _as_list(validation.get("tax_breakdown"))
    invoice_id = str(customer_visible.get("document_kind") or commercial_document.get("document_kind") or "INVOICE").strip() or "INVOICE"
    buyer_reference = str(validation.get("buyer_reference") or customer_visible.get("buyer_reference") or commercial_document.get("buyer_reference") or "").strip()
    issue_date = str(customer_visible.get("issue_date") or commercial_document.get("issue_date") or "").strip()
    payable_amount = str(totals.get("payable_amount") or "0.00").strip() or "0.00"
    tax_exclusive_amount = str(totals.get("tax_exclusive_amount") or "0.00").strip() or "0.00"
    tax_inclusive_amount = str(totals.get("tax_inclusive_amount") or "0.00").strip() or "0.00"
    tax_total_amount = str(totals.get("tax_total") or "0.00").strip() or "0.00"
    line_extension_total = str(totals.get("line_net_total") or tax_exclusive_amount).strip() or tax_exclusive_amount
    allowance_total = str(totals.get("allowance_total") or "0.00").strip() or "0.00"
    charge_total = str(totals.get("charge_total") or "0.00").strip() or "0.00"
    prepaid_amount = str(totals.get("prepaid_amount") or "0.00").strip() or "0.00"
    payable_rounding_amount = str(totals.get("payable_rounding_amount") or "0.00").strip() or "0.00"
    currency = str(totals.get("currency") or customer_visible.get("currency") or "EUR").strip() or "EUR"
    document_kind = str(customer_visible.get("document_kind") or commercial_document.get("document_kind") or "rechnung").strip().lower()
    seller = _as_dict(customer_visible.get("seller"))
    buyer = _as_dict(customer_visible.get("buyer"))
    seller_name = str(company.get("name") or "").strip() or str(validation.get("seller_vat_id") or "").strip() or "Seller"
    seller_street = str(company.get("street") or "").strip() or "Unknown Street"
    seller_city = str(company.get("city") or "").strip() or "Unknown City"
    seller_zip = str(company.get("zip") or "").strip() or "00000"
    seller_country = _country_code(str(company.get("country") or "DE"))
    buyer_name = str(validation.get("buyer_name") or "").strip() or "Buyer"
    buyer_street = str(buyer.get("street") or "").strip() or str(recipient.get("street") or "").strip() or "Unknown Street"
    buyer_city = str(buyer.get("city") or "").strip() or str(recipient.get("city") or "").strip() or "Unknown City"
    buyer_zip = str(buyer.get("postal_code") or "").strip() or str(recipient.get("postal_code") or "").strip() or "00000"
    buyer_country = _country_code(
        str(buyer.get("country") or "").strip()
        or str(recipient.get("country") or "DE").strip()
        or "DE"
    )
    payment_means_code = str(
        customer_visible.get("payment_means_code")
        or commercial_document.get("payment_means_code")
        or customer_visible.get("payment_method_code")
        or commercial_document.get("payment_method_code")
        or ""
    ).strip()
    positions = _as_list(commercial_document.get("positions"))
    document_allowances = _as_list(customer_visible.get("document_allowances"))
    document_charges = _as_list(customer_visible.get("document_charges"))
    purchase_order_reference = str(customer_visible.get("purchase_order_reference") or "").strip()
    contract_reference = str(customer_visible.get("contract_reference") or "").strip()
    project_reference = str(customer_visible.get("project_reference") or "").strip()
    delivery_note_reference = str(customer_visible.get("delivery_note_reference") or "").strip()
    original_invoice_number = str(customer_visible.get("original_invoice_number") or "").strip()
    payment_terms = str(customer_visible.get("payment_terms") or "").strip()
    payment_reference = str(customer_visible.get("payment_reference") or "").strip()
    seller_endpoint_id = str(seller.get("electronic_address") or company.get("electronic_address") or company.get("email") or "").strip()
    seller_endpoint_scheme = str(seller.get("electronic_address_scheme") or company.get("electronic_address_scheme") or "").strip()
    buyer_endpoint_id = str(buyer.get("electronic_address") or recipient.get("electronic_address") or recipient.get("email") or "").strip()
    buyer_endpoint_scheme = str(buyer.get("electronic_address_scheme") or recipient.get("electronic_address_scheme") or "").strip()
    seller_bank_name = str(seller.get("bank_name") or company.get("bank_name") or "").strip()
    seller_iban = str(seller.get("iban") or company.get("iban") or "").strip()
    seller_bic = str(seller.get("bic") or company.get("bic") or "").strip()
    seller_account_holder = str(seller.get("account_holder") or company.get("account_holder") or seller_name).strip()
    customization_id = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
    profile_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
    invoice_type_code = {
        "abschlagsrechnung": "326",
        "gutschrift": "381",
        "stornorechnung": "381",
    }.get(document_kind, "380")
    payload: dict[str, Any] = {
        "standard": "XRechnung",
        "profile": validation["profile"],
        "syntax": validation["syntax"],
        "valid": validation["valid"],
        "issues": validation.get("issues", []),
        "errors": validation["errors"],
        "warnings": validation.get("warnings", []),
        "buyer_reference": validation.get("buyer_reference", buyer_reference),
        "buyer_name": validation.get("buyer_name", ""),
        "seller_vat_id": validation.get("seller_vat_id", ""),
        "tax_breakdown": tax_breakdown,
        "schema_validation": {"valid": True, "rules": []},
        "schematron_validation": {"valid": True, "rules": []},
        "official_validation": {"executed": False, "valid": False, "status": "skipped"},
        "xml": "",
    }

    if validation["valid"] and syntax == "UBL":
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
            'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
            'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">',
            f"  <cbc:CustomizationID>{escape(customization_id)}</cbc:CustomizationID>",
            f"  <cbc:ProfileID>{escape(profile_id)}</cbc:ProfileID>",
            f"  <cbc:ID>{escape(invoice_id)}</cbc:ID>",
            f"  <cbc:IssueDate>{escape(issue_date)}</cbc:IssueDate>",
            f"  <cbc:InvoiceTypeCode>{escape(invoice_type_code)}</cbc:InvoiceTypeCode>",
            f"  <cbc:DocumentCurrencyCode>{escape(currency)}</cbc:DocumentCurrencyCode>",
            f"  <cbc:BuyerReference>{escape(buyer_reference)}</cbc:BuyerReference>",
        ]
        if purchase_order_reference:
            xml_lines.extend(["  <cac:OrderReference>", f"    <cbc:ID>{escape(purchase_order_reference)}</cbc:ID>", "  </cac:OrderReference>"])
        if contract_reference:
            xml_lines.extend(["  <cac:ContractDocumentReference>", f"    <cbc:ID>{escape(contract_reference)}</cbc:ID>", "  </cac:ContractDocumentReference>"])
        if project_reference:
            xml_lines.extend(["  <cac:ProjectReference>", f"    <cbc:ID>{escape(project_reference)}</cbc:ID>", "  </cac:ProjectReference>"])
        if delivery_note_reference:
            xml_lines.extend(["  <cac:DespatchDocumentReference>", f"    <cbc:ID>{escape(delivery_note_reference)}</cbc:ID>", "  </cac:DespatchDocumentReference>"])
        if original_invoice_number:
            xml_lines.extend(
                [
                    "  <cac:BillingReference>",
                    "    <cac:InvoiceDocumentReference>",
                    f"      <cbc:ID>{escape(original_invoice_number)}</cbc:ID>",
                    "    </cac:InvoiceDocumentReference>",
                    "  </cac:BillingReference>",
                ]
            )
        if payment_means_code:
            xml_lines.append("  <cac:PaymentMeans>")
            xml_lines.append(f"    <cbc:PaymentMeansCode>{escape(payment_means_code)}</cbc:PaymentMeansCode>")
            if payment_reference:
                xml_lines.append(f"    <cbc:PaymentID>{escape(payment_reference)}</cbc:PaymentID>")
            if seller_iban:
                xml_lines.extend(
                    [
                        "    <cac:PayeeFinancialAccount>",
                        f"      <cbc:ID>{escape(seller_iban)}</cbc:ID>",
                        f"      <cbc:Name>{escape(seller_account_holder)}</cbc:Name>",
                        "      <cac:FinancialInstitutionBranch>",
                        f"        <cbc:ID>{escape(seller_bic)}</cbc:ID>",
                        f"        <cbc:Name>{escape(seller_bank_name)}</cbc:Name>",
                        "      </cac:FinancialInstitutionBranch>",
                        "    </cac:PayeeFinancialAccount>",
                    ]
                )
            xml_lines.append("  </cac:PaymentMeans>")
        if payment_terms:
            xml_lines.extend(["  <cac:PaymentTerms>", f"    <cbc:Note>{escape(payment_terms)}</cbc:Note>", "  </cac:PaymentTerms>"])
        xml_lines.extend(
            [
                "  <cac:AccountingSupplierParty>",
                "    <cac:Party>",
                *([f"      <cbc:EndpointID schemeID=\"{escape(seller_endpoint_scheme)}\">{escape(seller_endpoint_id)}</cbc:EndpointID>"] if seller_endpoint_id and seller_endpoint_scheme else []),
                f"      <cac:PartyName><cbc:Name>{escape(seller_name)}</cbc:Name></cac:PartyName>",
                "      <cac:PostalAddress>",
                f"        <cbc:StreetName>{escape(seller_street)}</cbc:StreetName>",
                f"        <cbc:CityName>{escape(seller_city)}</cbc:CityName>",
                f"        <cbc:PostalZone>{escape(seller_zip)}</cbc:PostalZone>",
                f"        <cac:Country><cbc:IdentificationCode>{escape(seller_country)}</cbc:IdentificationCode></cac:Country>",
                "      </cac:PostalAddress>",
                "      <cac:PartyTaxScheme>",
                f"        <cbc:CompanyID>{escape(str(validation.get('seller_vat_id') or ''))}</cbc:CompanyID>",
                "        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>",
                "      </cac:PartyTaxScheme>",
                f"      <cac:PartyLegalEntity><cbc:RegistrationName>{escape(seller_name)}</cbc:RegistrationName></cac:PartyLegalEntity>",
                "    </cac:Party>",
                "  </cac:AccountingSupplierParty>",
                "  <cac:AccountingCustomerParty>",
                "    <cac:Party>",
                *([f"      <cbc:EndpointID schemeID=\"{escape(buyer_endpoint_scheme)}\">{escape(buyer_endpoint_id)}</cbc:EndpointID>"] if buyer_endpoint_id and buyer_endpoint_scheme else []),
                f"      <cac:PartyName><cbc:Name>{escape(buyer_name)}</cbc:Name></cac:PartyName>",
                "      <cac:PostalAddress>",
                f"        <cbc:StreetName>{escape(buyer_street)}</cbc:StreetName>",
                f"        <cbc:CityName>{escape(buyer_city)}</cbc:CityName>",
                f"        <cbc:PostalZone>{escape(buyer_zip)}</cbc:PostalZone>",
                f"        <cac:Country><cbc:IdentificationCode>{escape(buyer_country)}</cbc:IdentificationCode></cac:Country>",
                "      </cac:PostalAddress>",
                "    </cac:Party>",
                "  </cac:AccountingCustomerParty>",
            ]
        )
        if tax_breakdown:
            xml_lines.extend([
                "  <cac:TaxTotal>",
                f"    <cbc:TaxAmount currencyID=\"{escape(currency)}\">{escape(tax_total_amount)}</cbc:TaxAmount>",
            ])
            for raw_item in tax_breakdown:
                item = _as_dict(raw_item)
                xml_lines.extend(
                    [
                        "    <cac:TaxSubtotal>",
                        f"      <cbc:TaxableAmount currencyID=\"{escape(str(item.get('currency', currency)))}\">{escape(str(item.get('taxable_amount', '0.00')))}</cbc:TaxableAmount>",
                        f"      <cbc:TaxAmount currencyID=\"{escape(str(item.get('currency', currency)))}\">{escape(str(item.get('tax_amount', '0.00')))}</cbc:TaxAmount>",
                        "      <cac:TaxCategory>",
                        f"        <cbc:ID>{escape(str(item.get('category', '')))}</cbc:ID>",
                        f"        <cbc:Percent>{escape(str(item.get('rate', '0')))}</cbc:Percent>",
                        *([f"        <cbc:TaxExemptionReasonCode>{escape(str(item.get('tax_exemption_reason_code', '')))}</cbc:TaxExemptionReasonCode>"] if str(item.get('tax_exemption_reason_code', '')).strip() else []),
                        *([f"        <cbc:TaxExemptionReason>{escape(str(item.get('tax_exemption_reason', '')))}</cbc:TaxExemptionReason>"] if str(item.get('tax_exemption_reason', '')).strip() else []),
                        "        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>",
                        "      </cac:TaxCategory>",
                        "    </cac:TaxSubtotal>",
                    ]
                )
            xml_lines.append("  </cac:TaxTotal>")

        for adjustment, charge_indicator in [
            (document_allowances, False),
            (document_charges, True),
        ]:
            for raw_item in adjustment:
                item = _as_dict(raw_item)
                xml_lines.extend(
                    [
                        "  <cac:AllowanceCharge>",
                        f"    <cbc:ChargeIndicator>{str(charge_indicator).lower()}</cbc:ChargeIndicator>",
                        *([f"    <cbc:AllowanceChargeReasonCode>{escape(str(item.get('reason_code', '')))}</cbc:AllowanceChargeReasonCode>"] if str(item.get('reason_code', '')).strip() else []),
                        *([f"    <cbc:AllowanceChargeReason>{escape(str(item.get('reason', '')))}</cbc:AllowanceChargeReason>"] if str(item.get('reason', '')).strip() else []),
                        *([f"    <cbc:MultiplierFactorNumeric>{escape(str(item.get('percentage', '')))}</cbc:MultiplierFactorNumeric>"] if str(item.get('percentage', '')).strip() not in {'', '0.00', '0'} else []),
                        f"    <cbc:Amount currencyID=\"{escape(currency)}\">{escape(str(item.get('amount', '0.00')))}</cbc:Amount>",
                        "  </cac:AllowanceCharge>",
                    ]
                )

        xml_lines.extend(
            [
                "  <cac:LegalMonetaryTotal>",
                f"    <cbc:LineExtensionAmount currencyID=\"{escape(currency)}\">{escape(line_extension_total)}</cbc:LineExtensionAmount>",
                f"    <cbc:TaxExclusiveAmount currencyID=\"{escape(currency)}\">{escape(tax_exclusive_amount)}</cbc:TaxExclusiveAmount>",
                f"    <cbc:TaxInclusiveAmount currencyID=\"{escape(currency)}\">{escape(tax_inclusive_amount)}</cbc:TaxInclusiveAmount>",
                f"    <cbc:AllowanceTotalAmount currencyID=\"{escape(currency)}\">{escape(allowance_total)}</cbc:AllowanceTotalAmount>",
                f"    <cbc:ChargeTotalAmount currencyID=\"{escape(currency)}\">{escape(charge_total)}</cbc:ChargeTotalAmount>",
                f"    <cbc:PrepaidAmount currencyID=\"{escape(currency)}\">{escape(prepaid_amount)}</cbc:PrepaidAmount>",
                *([f"    <cbc:PayableRoundingAmount currencyID=\"{escape(currency)}\">{escape(payable_rounding_amount)}</cbc:PayableRoundingAmount>"] if payable_rounding_amount not in {"", "0.00", "0"} else []),
                f"    <cbc:PayableAmount currencyID=\"{escape(currency)}\">{escape(payable_amount)}</cbc:PayableAmount>",
                "  </cac:LegalMonetaryTotal>",
            ]
        )

        for index, raw_position in enumerate(positions, start=1):
            position = _as_dict(raw_position)
            quantity = str(position.get("quantity") or "0").strip() or "0"
            unit_code = str(position.get("unit_code") or "C62").strip() or "C62"
            base_quantity_value = str(position.get("price_base_quantity") or "1").strip() or "1"
            base_quantity_unit_code = str(position.get("price_base_quantity_unit_code") or unit_code).strip() or unit_code
            raw_line_amount = str(position.get("line_net_amount") or position.get("line_net") or "").strip()
            item_name = str(position.get("name") or "").strip()
            unit_price = str(position.get("price_net") or "0.00").strip() or "0.00"
            vat_rate = str(position.get("vat_rate") or "0").strip() or "0"
            category = str(position.get("vat_category") or "S").strip() or "S"
            tax_exemption_reason = str(position.get("tax_exemption_reason") or "").strip()
            tax_exemption_reason_code = str(position.get("tax_exemption_reason_code") or "").strip()

            line_amount = raw_line_amount
            if not line_amount:
                try:
                    line_amount = f"{(Decimal(quantity) * Decimal(unit_price)).quantize(Decimal('0.01')):.2f}"
                except Exception:
                    line_amount = "0.00"

            xml_lines.extend(
                [
                    "  <cac:InvoiceLine>",
                    f"    <cbc:ID>{index}</cbc:ID>",
                    f"    <cbc:InvoicedQuantity unitCode=\"{escape(unit_code)}\">{escape(quantity)}</cbc:InvoicedQuantity>",
                    f"    <cbc:LineExtensionAmount currencyID=\"{escape(currency)}\">{escape(line_amount)}</cbc:LineExtensionAmount>",
                    "    <cac:Item>",
                    f"      <cbc:Name>{escape(item_name)}</cbc:Name>",
                    "      <cac:ClassifiedTaxCategory>",
                    f"        <cbc:ID>{escape(category)}</cbc:ID>",
                    f"        <cbc:Percent>{escape(vat_rate)}</cbc:Percent>",
                    *([f"        <cbc:TaxExemptionReasonCode>{escape(tax_exemption_reason_code)}</cbc:TaxExemptionReasonCode>"] if tax_exemption_reason_code else []),
                    *([f"        <cbc:TaxExemptionReason>{escape(tax_exemption_reason)}</cbc:TaxExemptionReason>"] if tax_exemption_reason else []),
                    "        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>",
                    "      </cac:ClassifiedTaxCategory>",
                    "    </cac:Item>",
                    "    <cac:Price>",
                    f"      <cbc:PriceAmount currencyID=\"{escape(currency)}\">{escape(unit_price)}</cbc:PriceAmount>",
                    *([f"      <cbc:BaseQuantity unitCode=\"{escape(base_quantity_unit_code)}\">{escape(base_quantity_value)}</cbc:BaseQuantity>"] if base_quantity_value not in {"", "1", "1.000", "1.00"} else []),
                    "    </cac:Price>",
                    "  </cac:InvoiceLine>",
                ]
            )
        xml_lines.append("</Invoice>")
        payload["xml"] = "\n".join(xml_lines)

    if validation["valid"] and syntax == "CII":
        payload["xml"] = build_cii_xml(commercial_document, company, recipient, validation)

    xml_payload = str(payload.get("xml") or "")

    xml_validation = validate_xrechnung_xml_conformance(
        xml_payload,
        validation_context=validation,
        totals=totals,
        syntax=syntax,
    )
    payload["schema_validation"] = xml_validation.get("schema", {"valid": False, "rules": []})
    payload["schematron_validation"] = xml_validation.get("schematron", {"valid": False, "rules": []})
    payload["issues"] = [*payload.get("issues", []), *xml_validation.get("issues", [])]
    payload["errors"] = [*payload.get("errors", []), *xml_validation.get("errors", [])]
    payload["warnings"] = [*payload.get("warnings", []), *xml_validation.get("warnings", [])]
    payload["valid"] = bool(payload.get("valid")) and bool(xml_validation.get("valid"))

    official_validation = validate_xrechnung_official_conformance(
        xml_payload,
        report_prefix=f"xrechnung_{invoice_id}",
        syntax=syntax,
    )
    payload["official_validation"] = official_validation
    payload["issues"] = [*payload.get("issues", []), *official_validation.get("issues", [])]
    payload["errors"] = [*payload.get("errors", []), *official_validation.get("errors", [])]
    payload["warnings"] = [*payload.get("warnings", []), *official_validation.get("warnings", [])]
    if bool(official_validation.get("executed")):
        payload["valid"] = bool(payload.get("valid")) and bool(official_validation.get("valid"))

    return payload
