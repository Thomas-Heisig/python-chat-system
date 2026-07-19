from __future__ import annotations

import base64
import json
from typing import Any, cast

from plugins.business_letter.renderers.pdf import render_pdf_document
from plugins.business_letter.services.persistence import BusinessLetterPersistence


DEFAULT_PERSISTENCE = BusinessLetterPersistence()


def render_artifact_file_name(pattern: str, reference: dict[str, str], data: dict[str, Any], *, extension: str = "") -> str:
    document_number = str(reference.get("document_number") or data.get("document_number") or "business_letter").strip() or "business_letter"
    document_kind = str(data.get("document_kind") or data.get("letter_type") or "document").strip() or "document"
    rendered = pattern.format(
        document_number=document_number,
        document_kind=document_kind,
        date=str(reference.get("date") or "").strip(),
    ).strip()
    if not rendered:
        rendered = document_number
    if extension and not rendered.lower().endswith(extension.lower()):
        rendered = f"{rendered}{extension}"
    return rendered


def build_artifacts(template: dict[str, Any], reference: dict[str, str], data: dict[str, Any]) -> list[dict[str, Any]]:
    layout_raw = template.get("layout")
    layout = cast(dict[str, Any], layout_raw) if isinstance(layout_raw, dict) else {}
    default_filename_pattern = str(layout.get("default_filename_pattern") or "{document_number}").strip() or "{document_number}"
    default_pdf_filename_pattern = str(layout.get("default_pdf_filename_pattern") or "{document_number}.pdf").strip() or "{document_number}.pdf"
    json_name = render_artifact_file_name(default_filename_pattern, reference, data, extension=".json")
    html_name = render_artifact_file_name(default_filename_pattern, reference, data, extension=".html")
    artifacts = [
        {"kind": "json", "mime_type": "application/json", "file_name": json_name, "storage_reference": f"business_letter/{json_name}"},
        {"kind": "html", "mime_type": "text/html", "file_name": html_name, "storage_reference": f"business_letter/{html_name}"},
    ]
    if str(template.get("document_html") or template.get("letter_text") or "").strip():
        pdf_name = render_artifact_file_name(default_pdf_filename_pattern, reference, data, extension=".pdf")
        artifacts.append(
            {"kind": "pdf", "mime_type": "application/pdf", "file_name": pdf_name, "storage_reference": f"business_letter/{pdf_name}"}
        )
    if template.get("email_html"):
        email_name = render_artifact_file_name(default_filename_pattern, reference, data, extension=".email.html")
        artifacts.append(
            {"kind": "email_html", "mime_type": "text/html", "file_name": email_name, "storage_reference": f"business_letter/{email_name}"}
        )
    return artifacts


def build_pdf_payload(template: dict[str, Any], reference: dict[str, str], document: dict[str, Any]) -> str:
    content = str(template.get("letter_text") or template.get("document_html") or "").strip()
    layout_raw = template.get("layout")
    layout = cast(dict[str, Any], layout_raw) if isinstance(layout_raw, dict) else {}
    layout_summary: list[str] = []
    if layout:
        font_family = str(layout.get("font_family") or "").strip()
        font_size = str(layout.get("font_size_pt") or "").strip()
        margin = str(layout.get("page_margin_mm") or "").strip()
        accent = str(layout.get("accent_color") or "").strip()
        logo_width = str(layout.get("logo_width_mm") or "").strip()
        logo_position = str(layout.get("logo_position") or "").strip()
        logo_present = bool(layout.get("logo_present"))
        if font_family or font_size or margin or accent:
            layout_summary.append(
                f"LAYOUT font={font_family or '-'} size_pt={font_size or '-'} margin_mm={margin or '-'} accent={accent or '-'}"
            )
        if logo_width or logo_position or logo_present:
            layout_summary.append(
                f"LAYOUT logo_present={'yes' if logo_present else 'no'} logo_width_mm={logo_width or '-'} logo_position={logo_position or '-'}"
            )
        if layout_summary:
            summary_block = "\n".join(layout_summary)
            content = f"{summary_block}\n\n{content}" if content else summary_block
    if not content:
        content = json.dumps(document, ensure_ascii=False, sort_keys=True, default=str)
    pdf_payload = render_pdf_document(
        content,
        title=str(reference.get("document_number") or "business_letter"),
        layout_options=layout,
        logo_asset=cast(dict[str, Any], template.get("logo") or {}),
    )
    pdf_bytes = pdf_payload.get("bytes")
    if isinstance(pdf_bytes, (bytes, bytearray)):
        return base64.b64encode(bytes(pdf_bytes)).decode("ascii")
    return ""


def build_database_payload(
    data: dict[str, Any],
    metadata: dict[str, Any],
    reference: dict[str, str],
    template: dict[str, Any],
    commercial_document: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    document_number = str(reference.get("document_number") or metadata.get("document_id") or "").strip()
    document_id = str(metadata.get("document_id") or "").strip()
    return {
        "enabled": bool(data.get("persist_to_database")),
        "document_number": document_number,
        "document_id": document_id,
        "status": status,
        "template_profile": str(template.get("profile") or "").strip(),
        "storage_key": f"business_letter:{document_number or document_id}",
        "tables": {
            "document_templates": "document_templates",
            "commercial_documents": "commercial_documents",
            "document_versions": "document_versions",
            "document_artifacts": "document_artifacts",
            "document_events": "document_events",
            "number_sequences": "number_sequences",
            "dispatch_queue": "dispatch_queue",
            "dispatch_history": "dispatch_history",
        },
        "summary": {
            "document_type": str(commercial_document.get("document_kind") or data.get("letter_type") or "").strip(),
            "currency": str(commercial_document.get("totals", {}).get("currency") or "EUR"),
            "payable_amount": str(commercial_document.get("totals", {}).get("payable_amount") or "0.00"),
        },
        "snapshot": {
            "document_kind": str(commercial_document.get("document_kind") or "").strip(),
            "visible": commercial_document.get("customer_visible") or {},
            "internal": commercial_document.get("internal") or {},
        },
    }
