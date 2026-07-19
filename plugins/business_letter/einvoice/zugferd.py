from __future__ import annotations

import base64
from typing import Any, cast

from plugins.business_letter.renderers.pdf import render_pdf_document
from plugins.business_letter.einvoice.xrechnung import build_xrechnung_xml


_ZUGFERD_PROFILES: dict[str, dict[str, str]] = {
    "minimum": {"name": "MINIMUM", "guideline": "urn:factur-x.eu:1p0:minimum"},
    "basicwl": {"name": "BASIC WL", "guideline": "urn:factur-x.eu:1p0:basicwl"},
    "basic": {"name": "BASIC", "guideline": "urn:factur-x.eu:1p0:basic"},
    "en16931": {"name": "EN 16931", "guideline": "urn:cen.eu:en16931:2017"},
    "extended": {"name": "EXTENDED", "guideline": "urn:factur-x.eu:1p0:extended"},
}


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = cast(dict[object, object], value)
    return {str(key): item for key, item in raw.items()}


def _resolve_profile(profile_value: str) -> dict[str, str]:
    normalized = profile_value.strip().lower().replace("_", "").replace("-", "")
    if normalized in _ZUGFERD_PROFILES:
        return _ZUGFERD_PROFILES[normalized]
    if normalized == "comfort":
        return _ZUGFERD_PROFILES["en16931"]
    return _ZUGFERD_PROFILES["en16931"]


def build_zugferd_package(commercial_document: dict[str, Any], company: dict[str, str], recipient: dict[str, str]) -> dict[str, Any]:
    xrechnung = build_xrechnung_xml(commercial_document, company, recipient)
    totals = _as_dict(commercial_document.get("totals"))
    profile_info = _resolve_profile(str(xrechnung.get("profile") or "en16931"))
    document_title = str(commercial_document.get("document_kind") or "ZUGFeRD").strip() or "ZUGFeRD"
    xml_payload = str(xrechnung.get("xml") or "")
    xml_bytes = xml_payload.encode("utf-8")
    pdf_payload = render_pdf_document(
        "\n".join(
            [
                f"Dokument: {document_title}",
                f"Käuferreferenz: {xrechnung.get('buyer_reference', '')}",
                f"Käufer: {xrechnung.get('buyer_name', '')}",
                f"Zahlbetrag: {str(totals.get('payable_amount') or '')}",
            ]
        ),
        title=document_title,
        attachments=[
            {
                "file_name": "factur-x.xml",
                "mime_type": "application/xml",
                "relationship": "Alternative",
                "content_bytes": xml_bytes,
            }
        ],
        xmp_metadata={
            "document_type": "INVOICE",
            "profile": profile_info["name"],
            "guideline": profile_info["guideline"],
        },
        pdfa_part=3,
        pdfa_conformance="B",
    )
    pdf_bytes_raw = pdf_payload.get("bytes")
    pdf_bytes = bytes(pdf_bytes_raw) if isinstance(pdf_bytes_raw, (bytes, bytearray)) else b""
    return {
        "standard": "ZUGFeRD",
        "profile": profile_info["name"],
        "profile_name": profile_info["name"],
        "guideline": profile_info["guideline"],
        "pdfa3_profile": "PDF/A-3B",
        "pdfa3_required": True,
        "pdf": pdf_payload,
        "pdf_mime_type": pdf_payload.get("mime_type"),
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii") if pdf_bytes else "",
        "xml": xml_payload,
        "xmp_metadata": {
            "embedded_xml": True,
            "document_type": "INVOICE",
            "profile": profile_info["name"],
            "guideline": profile_info["guideline"],
            "attachment_name": "factur-x.xml",
        },
        "validation": xrechnung,
        "attachments": [
            {
                "kind": "facturx_xml",
                "file_name": "factur-x.xml",
                "mime_type": "application/xml",
                "relationship": "Alternative",
            }
        ],
    }
