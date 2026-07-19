from __future__ import annotations

import html
from typing import Any, cast


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: Any, fallback: float) -> float:
    try:
        return float(str(value or "").strip())
    except ValueError:
        return fallback


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = cast(dict[object, object], value)
    return {str(key): item for key, item in raw.items()}


def _as_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return cast(list[Any], value)


def _footer_lines(company: dict[str, str]) -> list[str]:
    lines: list[str] = []
    footer_text = str(company.get("footer_text") or "").strip()
    if footer_text:
        lines.append(footer_text)

    if _truthy(company.get("show_bank_details_in_footer")):
        bank_parts = [
            str(company.get("bank_name") or "").strip(),
            str(company.get("iban") or "").strip(),
            str(company.get("bic") or "").strip(),
        ]
        bank_line = " · ".join(part for part in bank_parts if part)
        if bank_line:
            lines.append(bank_line)

    if _truthy(company.get("show_legal_details_in_footer")):
        legal_parts = [
            str(company.get("legal_form") or "").strip(),
            str(company.get("registry_number") or "").strip(),
            str(company.get("registry_court") or "").strip(),
            str(company.get("vat_id") or "").strip(),
        ]
        legal_line = " · ".join(part for part in legal_parts if part)
        if legal_line:
            lines.append(legal_line)

    return lines


def escape_html_lines(text: str) -> str:
    blocks = text.split("\n\n") if text.strip() else []
    rendered: list[str] = []
    for block in blocks:
        escaped = html.escape(block.strip()).replace("\n", "<br>")
        rendered.append(f"<p>{escaped}</p>")
    return "\n".join(rendered)


def build_document_html(
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
    accent_color = str(company.get("accent_color") or "#234662").strip() or "#234662"
    font_family = str(company.get("default_font_family") or "Source Sans 3").strip() or "Source Sans 3"
    font_size_pt = _as_float(company.get("default_font_size_pt"), 11.0)
    page_margin_mm = _as_float(company.get("page_margin_mm"), 20.0)
    logo_width_mm = _as_float(company.get("logo_width_mm"), 32.0)
    logo_position = str(company.get("logo_position") or "left").strip().lower() or "left"
    justify_map = {"left": "flex-start", "center": "center", "right": "flex-end"}
    footer_lines = _footer_lines(company)
    watermark_text = str(company.get("draft_watermark_text") or "").strip()
    show_watermark = document_status in {"draft", "needs_review"} and bool(watermark_text)

    header_parts: list[str] = []
    if logo_asset.get("data_url"):
        header_parts.append(
            f'<div style="display:flex;justify-content:{justify_map.get(logo_position, "flex-start")};margin-bottom:16px">'
            f'<img alt="{html.escape(logo_asset.get("name") or "Logo")}" src="{html.escape(logo_asset["data_url"])}" style="width:{logo_width_mm:.0f}mm;max-width:100%;max-height:72px;object-fit:contain"></div>'
        )

    header_parts.append(f"<h1 style='color:{html.escape(accent_color)};margin:0 0 8px'>{html.escape(company['name'])}</h1>")
    header_parts.append(
        f"<p>{html.escape(company['street'])}<br>{html.escape(company['zip'])} {html.escape(company['city'])}<br>{html.escape(company['country'])}</p>"
    )
    header_parts.append(
        f"<p><strong>Dokumentnummer:</strong> {html.escape(reference.get('document_number') or '')}<br><strong>Datum:</strong> {html.escape(reference.get('date') or '')}</p>"
    )

    body_html = escape_html_lines("\n\n".join(body_paragraphs))
    attachment_html = ""
    if attachments:
        items: list[str] = []
        for attachment in attachments:
            name = html.escape(str(attachment.get("name") or "").strip())
            file_name = html.escape(str(attachment.get("file_name") or "").strip())
            label = f"{name} ({file_name})" if file_name else name
            items.append(f"<li>{label}</li>")
        attachment_html = f"<h2>Anlagen</h2><ul>{''.join(items)}</ul>"

    positions_html = ""
    if commercial_document.get("positions"):
        rows: list[str] = []
        for position in cast(list[dict[str, Any]], _as_list(commercial_document.get("positions"))):
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(position.get('line_id') or ''))}</td>"
                f"<td>{html.escape(str(position.get('name') or ''))}</td>"
                f"<td>{html.escape(str(position.get('quantity') or ''))}</td>"
                f"<td>{html.escape(str(position.get('unit_label') or position.get('unit_code') or ''))}</td>"
                f"<td>{html.escape(str(position.get('price_net') or ''))}</td>"
                f"<td>{html.escape(str(position.get('line_net_amount') or ''))}</td>"
                "</tr>"
            )
        positions_html = (
            "<h2>Positionen</h2>"
            f"<table border='1' cellspacing='0' cellpadding='6' style='border-collapse:collapse;width:100%;border-color:{html.escape(accent_color)}'>"
            "<thead><tr><th>Nr.</th><th>Bezeichnung</th><th>Menge</th><th>Einheit</th><th>Preis</th><th>Netto</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )

    totals = _as_dict(commercial_document.get("totals"))
    totals_html = ""
    if totals:
        totals_html = (
            "<h2>Summen</h2>"
            f"<p>Netto: {html.escape(str(totals.get('tax_exclusive_amount') or ''))}<br>"
            f"Steuer: {html.escape(str(totals.get('tax_total') or ''))}<br>"
            f"Brutto: {html.escape(str(totals.get('tax_inclusive_amount') or ''))}</p>"
        )

    footer_html = ""
    if footer_lines:
        footer_items = "<br>".join(html.escape(line) for line in footer_lines)
        page_number_line = "<br><span>Seite 1/1</span>" if _truthy(company.get("show_page_numbers")) else ""
        footer_html = (
            f"<footer style='margin-top:24px;padding-top:12px;border-top:2px solid {html.escape(accent_color)};"
            f"font-size:{max(font_size_pt - 2, 8):.0f}pt;color:{html.escape(accent_color)}'>{footer_items}{page_number_line}</footer>"
        )

    return "\n".join(
        [
            "<html><body style='position:relative;line-height:1.5;"
            f"font-family:{html.escape(font_family)},sans-serif;font-size:{font_size_pt:.0f}pt;"
            f"margin:{page_margin_mm:.0f}mm;color:#1e2b36'>",
            (
                f"<div style='position:fixed;inset:0;display:flex;align-items:center;justify-content:center;"
                f"font-size:{max(font_size_pt * 4, 24):.0f}pt;color:rgba(35,70,98,0.12);transform:rotate(-24deg);"
                f"pointer-events:none;user-select:none'>{html.escape(watermark_text)}</div>"
            ) if show_watermark else "",
            *header_parts,
            f"<p><strong>Empfänger:</strong> {html.escape(recipient.get('company') or recipient.get('name') or recipient.get('contact') or '')}</p>",
            f"<p>{html.escape(salutation)}</p>",
            body_html,
            positions_html,
            totals_html,
            attachment_html,
            f"<p>{html.escape(signatory_name)}</p>",
            footer_html,
            "</body></html>",
        ]
    )


def build_template_payload(
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
    return {
        "mode": str(data.get("template_mode") or "auto").strip().lower() or "auto",
        "profile": str(data.get("template_profile") or "").strip(),
        "letter_text": letter,
        "email_text": str(email.get("body_text") or ""),
        "email_html": str(email.get("body_html") or ""),
        "document_html": document_html,
        "logo": logo_asset,
        "company": {"name": company["name"], "city": company["city"], "country": company["country"]},
        "recipient": recipient,
        "reference": reference,
        "body_paragraphs": body_paragraphs,
        "commercial_document": commercial_document,
        "document_status": document_status,
        "layout": {
            "layout_template": company.get("layout_template"),
            "logo_strict_mode": company.get("logo_strict_mode"),
            "logo_max_bytes": company.get("logo_max_bytes"),
            "font_family": company.get("default_font_family"),
            "font_size_pt": company.get("default_font_size_pt"),
            "page_margin_mm": company.get("page_margin_mm"),
            "logo_width_mm": company.get("logo_width_mm"),
            "logo_position": company.get("logo_position"),
            "logo_present": bool(logo_asset.get("data_url")),
            "accent_color": company.get("accent_color"),
            "footer_lines": _footer_lines(company),
            "show_page_numbers": _truthy(company.get("show_page_numbers")),
            "draft_watermark_text": company.get("draft_watermark_text"),
            "show_draft_watermark": document_status in {"draft", "needs_review"},
            "default_filename_pattern": company.get("default_filename_pattern") or "{document_number}",
            "default_pdf_filename_pattern": company.get("default_pdf_filename_pattern") or "{document_number}.pdf",
        },
    }


def render_plain_letter(document: dict[str, Any]) -> str:
    sender_raw = document.get("sender")
    sender: dict[str, Any] = cast(dict[str, Any], sender_raw) if isinstance(sender_raw, dict) else {}

    recipient_raw = document.get("recipient")
    recipient: dict[str, Any] = cast(dict[str, Any], recipient_raw) if isinstance(recipient_raw, dict) else {}

    reference_raw = document.get("reference")
    reference: dict[str, Any] = cast(dict[str, Any], reference_raw) if isinstance(reference_raw, dict) else {}

    body_raw = document.get("body")
    body: dict[str, Any] = cast(dict[str, Any], body_raw) if isinstance(body_raw, dict) else {}

    signatory_raw = document.get("signatory")
    signatory: dict[str, Any] = cast(dict[str, Any], signatory_raw) if isinstance(signatory_raw, dict) else {}

    body_paragraphs_raw = body.get("paragraphs")
    body_paragraphs: list[Any] = cast(list[Any], body_paragraphs_raw) if isinstance(body_paragraphs_raw, list) else []

    attachments_raw = document.get("attachments")
    attachments: list[Any] = cast(list[Any], attachments_raw) if isinstance(attachments_raw, list) else []

    missing_raw = document.get("missing_information")
    missing_information: list[Any] = cast(list[Any], missing_raw) if isinstance(missing_raw, list) else []

    lines: list[str] = []

    template_raw = document.get("template")
    template_data: dict[str, Any] = cast(dict[str, Any], template_raw) if isinstance(template_raw, dict) else {}
    logo_asset = _as_dict(template_data.get("logo"))
    if logo_asset.get("data_url"):
        lines.append(f"Logo: {logo_asset.get('name') or 'Logo'}")
    elif sender.get("logo_url"):
        lines.append(f"Logo: {sender['logo_url']}")
    lines.append(str(sender.get("name") or ""))
    lines.append(f"{sender.get('street', '')}, {sender.get('zip', '')} {sender.get('city', '')}".strip(", "))
    lines.append(f"Telefon: {sender.get('phone', '')} | E-Mail: {sender.get('email', '')}".strip())
    if sender.get("website"):
        lines.append(f"Web: {sender.get('website')}")
    lines.append("")

    if recipient.get("company"):
        lines.append(str(recipient.get("company")))
    if recipient.get("contact"):
        lines.append(f"z. Hd. {recipient.get('contact')}")
    elif recipient.get("name"):
        lines.append(str(recipient.get("name")))
    if recipient.get("street"):
        lines.append(str(recipient.get("street")))
    if recipient.get("postal_code") or recipient.get("city"):
        lines.append(f"{recipient.get('postal_code', '')} {recipient.get('city', '')}".strip())
    if recipient.get("country"):
        lines.append(str(recipient.get("country")))
    lines.append("")
    lines.append(f"Betreff: {document.get('subject') or ''}")
    lines.append(f"Beleg: {reference.get('document_number') or ''}")
    lines.append(f"Datum: {reference.get('date') or ''}")
    lines.append("")
    lines.append(str(document.get("salutation") or ""))
    lines.append("")

    for paragraph in body_paragraphs:
        text = str(paragraph).strip()
        if text:
            lines.append(text)
            lines.append("")

    commercial_document_raw = document.get("commercial_document")
    commercial_document = cast(dict[str, Any], commercial_document_raw) if isinstance(commercial_document_raw, dict) else {}
    totals = _as_dict(commercial_document.get("totals"))
    if totals:
        lines.append("Summen:")
        lines.append(f"Netto: {totals.get('tax_exclusive_amount', '')}")
        lines.append(f"Steuer: {totals.get('tax_total', '')}")
        lines.append(f"Brutto: {totals.get('tax_inclusive_amount', '')}")
        lines.append("")

    if attachments:
        lines.append("Anlagen:")
        for attachment in attachments:
            name = str(attachment.get("name") or "").strip()
            file_name = str(attachment.get("file_name") or "").strip()
            label = f"{name} ({file_name})" if file_name else name
            lines.append(f"- {label}")
        lines.append("")

    if missing_information:
        lines.append("Hinweis: fehlende Informationen:")
        for item in missing_information:
            lines.append(f"- {item}")
        lines.append("")

    lines.append(str(body.get("closing") or "Mit freundlichen Grüßen"))
    lines.append(str(signatory.get("name") or sender.get("manager") or sender.get("name") or ""))
    if signatory.get("position"):
        lines.append(str(signatory.get("position")))

    return "\n".join(lines).strip()
