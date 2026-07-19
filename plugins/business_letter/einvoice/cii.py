from __future__ import annotations

from typing import Any, cast
from xml.sax.saxutils import escape


def _cii_date(value: str) -> str:
    text = (value or "").strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text.replace("-", "")
    return text


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = cast(dict[object, object], value)
    return {str(key): item for key, item in raw.items()}


def _as_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return cast(list[Any], value)


def build_cii_xml(
    commercial_document: dict[str, Any],
    company: dict[str, str],
    recipient: dict[str, str],
    validation: dict[str, Any],
) -> str:
    customer_visible = _as_dict(commercial_document.get("customer_visible"))
    totals = _as_dict(commercial_document.get("totals"))
    tax_breakdown = _as_list(validation.get("tax_breakdown"))
    positions = _as_list(commercial_document.get("positions"))
    seller = _as_dict(customer_visible.get("seller"))
    buyer = _as_dict(customer_visible.get("buyer"))

    document_kind = str(customer_visible.get("document_kind") or commercial_document.get("document_kind") or "rechnung").strip().lower()
    invoice_type_code = {
        "abschlagsrechnung": "326",
        "gutschrift": "381",
        "stornorechnung": "381",
        "schlussrechnung": "877",
    }.get(document_kind, "380")

    profile_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
    customization_id = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
    invoice_id = str(customer_visible.get("document_kind") or commercial_document.get("document_kind") or "INVOICE").strip() or "INVOICE"
    issue_date = _cii_date(str(customer_visible.get("issue_date") or commercial_document.get("issue_date") or "").strip())
    due_date = _cii_date(str(customer_visible.get("payment_due_date") or "").strip())
    buyer_reference = str(validation.get("buyer_reference") or customer_visible.get("buyer_reference") or commercial_document.get("buyer_reference") or "").strip()
    purchase_order_reference = str(customer_visible.get("purchase_order_reference") or "").strip()
    contract_reference = str(customer_visible.get("contract_reference") or "").strip()
    project_reference = str(customer_visible.get("project_reference") or "").strip()
    delivery_note_reference = str(customer_visible.get("delivery_note_reference") or "").strip()
    original_invoice_number = str(customer_visible.get("original_invoice_number") or "").strip()
    currency = str(totals.get("currency") or customer_visible.get("currency") or "EUR").strip() or "EUR"
    payment_means_code = str(
        customer_visible.get("payment_means_code")
        or commercial_document.get("payment_means_code")
        or customer_visible.get("payment_method_code")
        or commercial_document.get("payment_method_code")
        or ""
    ).strip()
    payment_terms = str(customer_visible.get("payment_terms") or "").strip()
    payment_reference = str(customer_visible.get("payment_reference") or "").strip()

    seller_name = str(seller.get("name") or company.get("name") or validation.get("seller_vat_id") or "Seller").strip() or "Seller"
    seller_vat_id = str(validation.get("seller_vat_id") or company.get("vat_id") or "").strip()
    seller_tax_id = str(seller.get("tax_id") or company.get("tax_id") or "").strip()
    seller_endpoint = str(seller.get("electronic_address") or company.get("electronic_address") or "").strip()
    seller_endpoint_scheme = str(seller.get("electronic_address_scheme") or company.get("electronic_address_scheme") or "").strip()
    seller_postal = str(seller.get("postal_code") or company.get("zip") or "").strip()
    seller_city = str(seller.get("city") or company.get("city") or "").strip()
    seller_country = str(seller.get("country") or company.get("country") or "DE").strip() or "DE"
    seller_iban = str(seller.get("iban") or company.get("iban") or "").strip()
    seller_bic = str(seller.get("bic") or company.get("bic") or "").strip()

    buyer_name = str(validation.get("buyer_name") or buyer.get("name") or recipient.get("company") or recipient.get("name") or "Buyer").strip() or "Buyer"
    buyer_endpoint = str(buyer.get("electronic_address") or recipient.get("electronic_address") or "").strip()
    buyer_endpoint_scheme = str(buyer.get("electronic_address_scheme") or recipient.get("electronic_address_scheme") or "").strip()
    buyer_postal = str(buyer.get("postal_code") or recipient.get("postal_code") or "").strip()
    buyer_city = str(buyer.get("city") or recipient.get("city") or "").strip()
    buyer_country = str(buyer.get("country") or recipient.get("country") or "DE").strip() or "DE"

    line_total_amount = str(totals.get("line_net_total") or totals.get("tax_exclusive_amount") or "0.00").strip() or "0.00"
    allowance_total_amount = str(totals.get("allowance_total") or "0.00").strip() or "0.00"
    charge_total_amount = str(totals.get("charge_total") or "0.00").strip() or "0.00"
    tax_basis_total_amount = str(totals.get("tax_exclusive_amount") or "0.00").strip() or "0.00"
    tax_total_amount = str(totals.get("tax_total") or "0.00").strip() or "0.00"
    rounding_amount = str(totals.get("payable_rounding_amount") or totals.get("rounding_amount") or "0.00").strip() or "0.00"
    grand_total_amount = str(totals.get("tax_inclusive_amount") or "0.00").strip() or "0.00"
    prepaid_amount = str(totals.get("prepaid_amount") or "0.00").strip() or "0.00"
    due_payable_amount = str(totals.get("payable_amount") or "0.00").strip() or "0.00"

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"',
        '                          xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"',
        '                          xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100"',
        '                          xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">',
        '  <rsm:ExchangedDocumentContext>',
        '    <ram:BusinessProcessSpecifiedDocumentContextParameter>',
        f'      <ram:ID>{escape(profile_id)}</ram:ID>',
        '    </ram:BusinessProcessSpecifiedDocumentContextParameter>',
        '    <ram:GuidelineSpecifiedDocumentContextParameter>',
        f'      <ram:ID>{escape(customization_id)}</ram:ID>',
        '    </ram:GuidelineSpecifiedDocumentContextParameter>',
        '  </rsm:ExchangedDocumentContext>',
        '  <rsm:ExchangedDocument>',
        f'    <ram:ID>{escape(invoice_id)}</ram:ID>',
        f'    <ram:TypeCode>{escape(invoice_type_code)}</ram:TypeCode>',
        '    <ram:IssueDateTime>',
        f'      <udt:DateTimeString format="102">{escape(issue_date)}</udt:DateTimeString>',
        '    </ram:IssueDateTime>',
        '  </rsm:ExchangedDocument>',
        '  <rsm:SupplyChainTradeTransaction>',
    ]

    for index, raw_position in enumerate(positions, start=1):
        position = _as_dict(raw_position)
        quantity = str(position.get("quantity") or "0").strip() or "0"
        unit_code = str(position.get("unit_code") or "C62").strip() or "C62"
        line_amount = str(position.get("line_net_amount") or "0.00").strip() or "0.00"
        item_name = str(position.get("name") or "").strip()
        item_description = str(position.get("description") or "").strip()
        unit_price = str(position.get("price_net") or "0.00").strip() or "0.00"
        base_quantity = str(position.get("price_base_quantity") or "1").strip() or "1"
        base_quantity_unit_code = str(position.get("price_base_quantity_unit_code") or unit_code).strip() or unit_code
        vat_rate = str(position.get("vat_rate") or "0").strip() or "0"
        category = str(position.get("vat_category") or "S").strip() or "S"
        tax_exemption_reason = str(position.get("tax_exemption_reason") or "").strip()
        tax_exemption_reason_code = str(position.get("tax_exemption_reason_code") or "").strip()
        allowances = _as_list(position.get("allowances"))
        charges = _as_list(position.get("charges"))

        xml_lines.extend(
            [
                '    <ram:IncludedSupplyChainTradeLineItem>',
                '      <ram:AssociatedDocumentLineDocument>',
                f'        <ram:LineID>{index}</ram:LineID>',
                '      </ram:AssociatedDocumentLineDocument>',
                '      <ram:SpecifiedTradeProduct>',
                f'        <ram:Name>{escape(item_name)}</ram:Name>',
                *([f'        <ram:Description>{escape(item_description)}</ram:Description>'] if item_description else []),
                '      </ram:SpecifiedTradeProduct>',
                '      <ram:SpecifiedLineTradeAgreement>',
                '        <ram:NetPriceProductTradePrice>',
                f'          <ram:ChargeAmount>{escape(unit_price)}</ram:ChargeAmount>',
                *([f'          <ram:BasisQuantity unitCode="{escape(base_quantity_unit_code)}">{escape(base_quantity)}</ram:BasisQuantity>'] if base_quantity not in {'', '1', '1.000', '1.00'} else []),
                '        </ram:NetPriceProductTradePrice>',
                '      </ram:SpecifiedLineTradeAgreement>',
                '      <ram:SpecifiedLineTradeDelivery>',
                f'        <ram:BilledQuantity unitCode="{escape(unit_code)}">{escape(quantity)}</ram:BilledQuantity>',
                '      </ram:SpecifiedLineTradeDelivery>',
                '      <ram:SpecifiedLineTradeSettlement>',
                '        <ram:ApplicableTradeTax>',
                '          <ram:TypeCode>VAT</ram:TypeCode>',
                f'          <ram:CategoryCode>{escape(category)}</ram:CategoryCode>',
                *([f'          <ram:ExemptionReasonCode>{escape(tax_exemption_reason_code)}</ram:ExemptionReasonCode>'] if tax_exemption_reason_code else []),
                *([f'          <ram:ExemptionReason>{escape(tax_exemption_reason)}</ram:ExemptionReason>'] if tax_exemption_reason else []),
                f'          <ram:RateApplicablePercent>{escape(vat_rate)}</ram:RateApplicablePercent>',
                '        </ram:ApplicableTradeTax>',
            ]
        )

        for item, charge_indicator in [*[(entry, True) for entry in charges], *[(entry, False) for entry in allowances]]:
            item_dict = _as_dict(item)
            amount = str(item_dict.get("amount") or "0.00").strip() or "0.00"
            percentage = str(item_dict.get("percentage") or "").strip()
            base_amount = str(item_dict.get("base_amount") or line_amount).strip() or line_amount
            reason = str(item_dict.get("reason") or "").strip()
            reason_code = str(item_dict.get("reason_code") or "").strip()
            xml_lines.extend(
                [
                    '        <ram:SpecifiedTradeAllowanceCharge>',
                    '          <ram:ChargeIndicator>',
                    f'            <udt:Indicator>{str(charge_indicator).lower()}</udt:Indicator>',
                    '          </ram:ChargeIndicator>',
                    *([f'          <ram:CalculationPercent>{escape(percentage)}</ram:CalculationPercent>'] if percentage not in {'', '0', '0.00'} else []),
                    *([f'          <ram:BasisAmount>{escape(base_amount)}</ram:BasisAmount>'] if percentage not in {'', '0', '0.00'} else []),
                    f'          <ram:ActualAmount>{escape(amount)}</ram:ActualAmount>',
                    *([f'          <ram:ReasonCode>{escape(reason_code)}</ram:ReasonCode>'] if reason_code else []),
                    *([f'          <ram:Reason>{escape(reason)}</ram:Reason>'] if reason else []),
                    '        </ram:SpecifiedTradeAllowanceCharge>',
                ]
            )

        xml_lines.extend(
            [
                '        <ram:SpecifiedTradeSettlementLineMonetarySummation>',
                f'          <ram:LineTotalAmount>{escape(line_amount)}</ram:LineTotalAmount>',
                '        </ram:SpecifiedTradeSettlementLineMonetarySummation>',
                '      </ram:SpecifiedLineTradeSettlement>',
                '    </ram:IncludedSupplyChainTradeLineItem>',
            ]
        )

    xml_lines.extend(
        [
            '    <ram:ApplicableHeaderTradeAgreement>',
            f'      <ram:BuyerReference>{escape(buyer_reference)}</ram:BuyerReference>',
            '      <ram:SellerTradeParty>',
            f'        <ram:Name>{escape(seller_name)}</ram:Name>',
            *(['        <ram:PostalTradeAddress>', f'          <ram:PostcodeCode>{escape(seller_postal)}</ram:PostcodeCode>', f'          <ram:CityName>{escape(seller_city)}</ram:CityName>', f'          <ram:CountryID>{escape(seller_country)}</ram:CountryID>', '        </ram:PostalTradeAddress>'] if (seller_postal or seller_city or seller_country) else []),
            *(['        <ram:URIUniversalCommunication>', f'          <ram:URIID schemeID="{escape(seller_endpoint_scheme)}">{escape(seller_endpoint)}</ram:URIID>', '        </ram:URIUniversalCommunication>'] if seller_endpoint and seller_endpoint_scheme else []),
            *(['        <ram:SpecifiedTaxRegistration>', f'          <ram:ID schemeID="VA">{escape(seller_vat_id)}</ram:ID>', '        </ram:SpecifiedTaxRegistration>'] if seller_vat_id else []),
            *(['        <ram:SpecifiedTaxRegistration>', f'          <ram:ID schemeID="FC">{escape(seller_tax_id)}</ram:ID>', '        </ram:SpecifiedTaxRegistration>'] if seller_tax_id else []),
            '      </ram:SellerTradeParty>',
            '      <ram:BuyerTradeParty>',
            f'        <ram:Name>{escape(buyer_name)}</ram:Name>',
            *(['        <ram:PostalTradeAddress>', f'          <ram:PostcodeCode>{escape(buyer_postal)}</ram:PostcodeCode>', f'          <ram:CityName>{escape(buyer_city)}</ram:CityName>', f'          <ram:CountryID>{escape(buyer_country)}</ram:CountryID>', '        </ram:PostalTradeAddress>'] if (buyer_postal or buyer_city or buyer_country) else []),
            *(['        <ram:URIUniversalCommunication>', f'          <ram:URIID schemeID="{escape(buyer_endpoint_scheme)}">{escape(buyer_endpoint)}</ram:URIID>', '        </ram:URIUniversalCommunication>'] if buyer_endpoint and buyer_endpoint_scheme else []),
            '      </ram:BuyerTradeParty>',
            *(['      <ram:BuyerOrderReferencedDocument>', f'        <ram:IssuerAssignedID>{escape(purchase_order_reference)}</ram:IssuerAssignedID>', '      </ram:BuyerOrderReferencedDocument>'] if purchase_order_reference else []),
            *(['      <ram:ContractReferencedDocument>', f'        <ram:IssuerAssignedID>{escape(contract_reference)}</ram:IssuerAssignedID>', '      </ram:ContractReferencedDocument>'] if contract_reference else []),
            *(['      <ram:AdditionalReferencedDocument>', f'        <ram:IssuerAssignedID>{escape(delivery_note_reference)}</ram:IssuerAssignedID>', '        <ram:TypeCode>130</ram:TypeCode>', '      </ram:AdditionalReferencedDocument>'] if delivery_note_reference else []),
            *(['      <ram:SpecifiedProcuringProject>', f'        <ram:ID>{escape(project_reference)}</ram:ID>', '        <ram:Name>Project reference</ram:Name>', '      </ram:SpecifiedProcuringProject>'] if project_reference else []),
            '    </ram:ApplicableHeaderTradeAgreement>',
            '    <ram:ApplicableHeaderTradeDelivery/>',
            '    <ram:ApplicableHeaderTradeSettlement>',
            f'      <ram:InvoiceCurrencyCode>{escape(currency)}</ram:InvoiceCurrencyCode>',
        ]
    )

    if payment_means_code:
        xml_lines.extend(
            [
                '      <ram:SpecifiedTradeSettlementPaymentMeans>',
                f'        <ram:TypeCode>{escape(payment_means_code)}</ram:TypeCode>',
                *(['        <ram:Information>', f'          <ram:ID>{escape(payment_reference)}</ram:ID>', '        </ram:Information>'] if False and payment_reference else []),
                *(['        <ram:PayeePartyCreditorFinancialAccount>', f'          <ram:IBANID>{escape(seller_iban)}</ram:IBANID>', *([f'          <ram:AccountName>{escape(seller_name)}</ram:AccountName>'] if seller_name else []), '        </ram:PayeePartyCreditorFinancialAccount>'] if seller_iban else []),
                *(['        <ram:PayeeSpecifiedCreditorFinancialInstitution>', f'          <ram:BICID>{escape(seller_bic)}</ram:BICID>', '        </ram:PayeeSpecifiedCreditorFinancialInstitution>'] if seller_bic else []),
                '      </ram:SpecifiedTradeSettlementPaymentMeans>',
            ]
        )

    if payment_terms or due_date:
        xml_lines.extend(['      <ram:SpecifiedTradePaymentTerms>'])
        if payment_terms:
            xml_lines.append(f'        <ram:Description>{escape(payment_terms)}</ram:Description>')
        if due_date:
            xml_lines.extend(['        <ram:DueDateDateTime>', f'          <udt:DateTimeString format="102">{escape(due_date)}</udt:DateTimeString>', '        </ram:DueDateDateTime>'])
        xml_lines.append('      </ram:SpecifiedTradePaymentTerms>')

    for raw_item in tax_breakdown:
        item = _as_dict(raw_item)
        category = str(item.get("category") or "S").strip() or "S"
        rate = str(item.get("rate") or "0").strip() or "0"
        taxable_amount = str(item.get("taxable_amount") or "0.00").strip() or "0.00"
        tax_amount = str(item.get("tax_amount") or "0.00").strip() or "0.00"
        tax_exemption_reason = str(item.get("tax_exemption_reason") or "").strip()
        tax_exemption_reason_code = str(item.get("tax_exemption_reason_code") or "").strip()
        xml_lines.extend(
            [
                '      <ram:ApplicableTradeTax>',
                f'        <ram:CalculatedAmount>{escape(tax_amount)}</ram:CalculatedAmount>',
                '        <ram:TypeCode>VAT</ram:TypeCode>',
                f'        <ram:BasisAmount>{escape(taxable_amount)}</ram:BasisAmount>',
                f'        <ram:CategoryCode>{escape(category)}</ram:CategoryCode>',
                *([f'        <ram:ExemptionReasonCode>{escape(tax_exemption_reason_code)}</ram:ExemptionReasonCode>'] if tax_exemption_reason_code else []),
                *([f'        <ram:ExemptionReason>{escape(tax_exemption_reason)}</ram:ExemptionReason>'] if tax_exemption_reason else []),
                f'        <ram:RateApplicablePercent>{escape(rate)}</ram:RateApplicablePercent>',
                '      </ram:ApplicableTradeTax>',
            ]
        )

    xml_lines.extend(
        [
            '      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>',
            f'        <ram:LineTotalAmount>{escape(line_total_amount)}</ram:LineTotalAmount>',
            f'        <ram:ChargeTotalAmount>{escape(charge_total_amount)}</ram:ChargeTotalAmount>',
            f'        <ram:AllowanceTotalAmount>{escape(allowance_total_amount)}</ram:AllowanceTotalAmount>',
            f'        <ram:TaxBasisTotalAmount>{escape(tax_basis_total_amount)}</ram:TaxBasisTotalAmount>',
            f'        <ram:TaxTotalAmount currencyID="{escape(currency)}">{escape(tax_total_amount)}</ram:TaxTotalAmount>',
            f'        <ram:RoundingAmount>{escape(rounding_amount)}</ram:RoundingAmount>',
            f'        <ram:GrandTotalAmount>{escape(grand_total_amount)}</ram:GrandTotalAmount>',
            f'        <ram:TotalPrepaidAmount>{escape(prepaid_amount)}</ram:TotalPrepaidAmount>',
            f'        <ram:DuePayableAmount>{escape(due_payable_amount)}</ram:DuePayableAmount>',
            '      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>',
            *(['      <ram:InvoiceReferencedDocument>', f'        <ram:IssuerAssignedID>{escape(original_invoice_number)}</ram:IssuerAssignedID>', '      </ram:InvoiceReferencedDocument>'] if original_invoice_number else []),
            '    </ram:ApplicableHeaderTradeSettlement>',
            '  </rsm:SupplyChainTradeTransaction>',
            '</rsm:CrossIndustryInvoice>',
        ]
    )

    return '\n'.join(xml_lines)