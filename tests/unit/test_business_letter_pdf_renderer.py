from __future__ import annotations

import re
import pytest

from plugins.business_letter.renderers.pdf import render_pdf_document


_JPEG_1X1_DATA_URL = (
    "data:image/jpeg;base64,"
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////"
    "wAARCAABAAEDAREAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAHhP//"
    "EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAQUCb//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQMBAT8Bj//EABQRAQAAAAAAAAAAAAAAAAAAAAD/"
    "2gAIAQIBAT8Bj//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEABj8Cf//Z"
)


def _pdf_text(payload: dict[str, object]) -> str:
    return bytes(payload["bytes"]).decode("latin-1", errors="ignore")


def _logo_x_position(pdf_text: str) -> float:
    match = re.search(r"\n([0-9]+\.[0-9]+) 0 0 ([0-9]+\.[0-9]+) ([0-9]+\.[0-9]+) ([0-9]+\.[0-9]+) cm\n/ImLogo Do\n", pdf_text)
    assert match is not None
    return float(match.group(3))


def test_pdf_renderer_embeds_logo_and_positions_left_center_right() -> None:
    positions: dict[str, float] = {}
    for position in ("left", "center", "right"):
        payload = render_pdf_document(
            "Logo positions test.",
            title=f"logo-{position}",
            layout_options={
                "logo_width_mm": 30,
                "logo_position": position,
                "layout_template": "classic",
            },
            logo_asset={"data_url": _JPEG_1X1_DATA_URL},
        )
        pdf_text = _pdf_text(payload)
        assert "/Subtype /Image" in pdf_text
        assert "/ImLogo Do" in pdf_text
        positions[position] = _logo_x_position(pdf_text)

    assert positions["left"] < positions["center"]
    assert positions["center"] < positions["right"]


def test_pdf_renderer_applies_layout_template_and_accent_color() -> None:
    modern_pdf = render_pdf_document(
        "Modern layout test.",
        title="layout-modern",
        layout_options={
            "layout_template": "modern",
            "accent_color": "#005a36",
            "footer_lines": ["Footer"],
            "show_page_numbers": True,
        },
    )
    workshop_pdf = render_pdf_document(
        "Workshop layout test.",
        title="layout-workshop",
        layout_options={
            "layout_template": "workshop",
            "accent_color": "#005a36",
            "footer_lines": ["Footer"],
            "show_page_numbers": True,
        },
    )

    modern_text = _pdf_text(modern_pdf)
    workshop_text = _pdf_text(workshop_pdf)

    assert "0.000 0.353 0.212 rg" in modern_text
    assert "0.000 0.353 0.212 RG" in modern_text
    assert " m " in modern_text and " l S" in modern_text
    assert " re f" in workshop_text


def test_pdf_renderer_ignores_remote_logo_url_without_network_dependency() -> None:
    payload = render_pdf_document(
        "Remote logo must not be fetched.",
        title="logo-remote",
        layout_options={"logo_width_mm": 28, "logo_position": "right"},
        logo_asset={"data_url": "https://example.com/logo.png"},
    )

    pdf_text = _pdf_text(payload)
    assert "/Subtype /Image" not in pdf_text
    assert "/ImLogo Do" not in pdf_text


def test_pdf_renderer_ignores_invalid_logo_data_url() -> None:
    payload = render_pdf_document(
        "Invalid data URL must be ignored.",
        title="logo-invalid",
        layout_options={"logo_width_mm": 28, "logo_position": "left"},
        logo_asset={"data_url": "data:image/png;base64,%%not-base64%%"},
    )

    pdf_text = _pdf_text(payload)
    assert "/Subtype /Image" not in pdf_text
    assert "/ImLogo Do" not in pdf_text


def test_pdf_renderer_strict_mode_rejects_invalid_base64() -> None:
    with pytest.raises(ValueError, match="logo_base64_invalid"):
        render_pdf_document(
            "Strict invalid base64.",
            title="logo-strict-invalid-base64",
            layout_options={"logo_strict_mode": True},
            logo_asset={"data_url": "data:image/png;base64,%%not-base64%%"},
        )


def test_pdf_renderer_strict_mode_rejects_unsupported_mime_type() -> None:
    with pytest.raises(ValueError, match="logo_mime_not_supported"):
        render_pdf_document(
            "Strict unsupported mime.",
            title="logo-strict-unsupported-mime",
            layout_options={"logo_strict_mode": True},
            logo_asset={"data_url": "data:image/gif;base64,R0lGODdhAQABAIABAP///wAAACwAAAAAAQABAAACAkQBADs="},
        )


def test_pdf_renderer_strict_mode_rejects_empty_binary() -> None:
    with pytest.raises(ValueError, match="logo_empty_binary"):
        render_pdf_document(
            "Strict empty binary.",
            title="logo-strict-empty-binary",
            layout_options={"logo_strict_mode": True},
            logo_asset={"data_url": "data:image/png;base64,"},
        )


def test_pdf_renderer_strict_mode_rejects_oversized_logo_data() -> None:
    with pytest.raises(ValueError, match="logo_too_large"):
        render_pdf_document(
            "Strict oversized logo.",
            title="logo-strict-too-large",
            layout_options={"logo_strict_mode": True, "logo_max_bytes": 32},
            logo_asset={"data_url": _JPEG_1X1_DATA_URL},
        )


def test_pdf_renderer_strict_mode_rejects_external_url() -> None:
    with pytest.raises(ValueError, match="logo_external_url_forbidden"):
        render_pdf_document(
            "Strict external URL.",
            title="logo-strict-external-url",
            layout_options={"logo_strict_mode": True},
            logo_asset={"data_url": "https://example.com/logo.png"},
        )


def test_pdf_renderer_strict_mode_rejects_local_path_assets() -> None:
    with pytest.raises(ValueError, match="logo_local_path_not_supported"):
        render_pdf_document(
            "Strict local path.",
            title="logo-strict-local-path",
            layout_options={"logo_strict_mode": True},
            logo_asset={"file_path": "C:/nonexistent/logo.png"},
        )


def test_pdf_renderer_strict_mode_rejects_extension_mismatch() -> None:
    with pytest.raises(ValueError, match="logo_extension_mismatch"):
        render_pdf_document(
            "Strict extension mismatch.",
            title="logo-strict-extension-mismatch",
            layout_options={"logo_strict_mode": True},
            logo_asset={"data_url": _JPEG_1X1_DATA_URL, "file_name": "logo.png"},
        )


def test_pdf_renderer_strict_mode_rejects_mime_binary_mismatch() -> None:
    with pytest.raises(ValueError, match="logo_mime_binary_mismatch"):
        render_pdf_document(
            "Strict mime binary mismatch.",
            title="logo-strict-mime-mismatch",
            layout_options={"logo_strict_mode": True},
            logo_asset={
                "data_url": _JPEG_1X1_DATA_URL.replace("data:image/jpeg;base64", "data:image/png;base64"),
            },
        )
