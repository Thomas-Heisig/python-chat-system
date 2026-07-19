from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
import struct
import textwrap
from typing import Any, cast


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT_MARGIN = 72
TOP_MARGIN = 72
FONT_SIZE = 11
LEADING = 14
LINES_PER_PAGE = 44


class LogoResolutionError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def _font_resource_name(font_family: str) -> tuple[str, str]:
    normalized = str(font_family or "").strip().lower()
    if "merriweather" in normalized or "serif" in normalized:
        return "F2", "Times-Roman"
    if "plex mono" in normalized or "mono" in normalized or "courier" in normalized:
        return "F3", "Courier"
    return "F1", "Helvetica"


def _mm_to_pt(mm: float) -> float:
    return mm * 72.0 / 25.4


def _as_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _pdf_date_now() -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("D:%Y%m%d%H%M%SZ")


def _normalize_layout_template(value: Any) -> str:
    candidate = str(value or "classic").strip().lower()
    if candidate not in {"classic", "modern", "workshop"}:
        return "classic"
    return candidate


def _parse_hex_color(value: str) -> tuple[float, float, float]:
    raw = str(value or "").strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) != 6:
        return 0.137, 0.275, 0.384
    try:
        red = int(raw[0:2], 16) / 255.0
        green = int(raw[2:4], 16) / 255.0
        blue = int(raw[4:6], 16) / 255.0
    except ValueError:
        return 0.137, 0.275, 0.384
    return red, green, blue


def _lighten_rgb(rgb: tuple[float, float, float], factor: float) -> tuple[float, float, float]:
    clamped = max(0.0, min(1.0, factor))
    red = rgb[0] + (1.0 - rgb[0]) * clamped
    green = rgb[1] + (1.0 - rgb[1]) * clamped
    blue = rgb[2] + (1.0 - rgb[2]) * clamped
    return red, green, blue


def _decode_jpeg_dimensions(content: bytes) -> tuple[int, int] | None:
    if len(content) < 4 or not content.startswith(b"\xff\xd8"):
        return None
    index = 2
    length = len(content)
    while index + 9 < length:
        if content[index] != 0xFF:
            index += 1
            continue
        marker = content[index + 1]
        index += 2
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > length:
            return None
        segment_length = struct.unpack(">H", content[index : index + 2])[0]
        if segment_length < 2 or index + segment_length > length:
            return None
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if segment_length < 7:
                return None
            height = struct.unpack(">H", content[index + 3 : index + 5])[0]
            width = struct.unpack(">H", content[index + 5 : index + 7])[0]
            if width <= 0 or height <= 0:
                return None
            return width, height
        index += segment_length
    return None


def _decode_png_rgb_image(content: bytes) -> dict[str, Any] | None:
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    index = 8
    width = 0
    height = 0
    bit_depth = 0
    color_type = 0
    interlace = 0
    idat_parts: list[bytes] = []
    while index + 8 <= len(content):
        chunk_length = struct.unpack(">I", content[index : index + 4])[0]
        chunk_type = content[index + 4 : index + 8]
        data_start = index + 8
        data_end = data_start + chunk_length
        crc_end = data_end + 4
        if crc_end > len(content):
            return None
        chunk_data = content[data_start:data_end]
        if chunk_type == b"IHDR":
            if len(chunk_data) != 13:
                return None
            width = struct.unpack(">I", chunk_data[0:4])[0]
            height = struct.unpack(">I", chunk_data[4:8])[0]
            bit_depth = chunk_data[8]
            color_type = chunk_data[9]
            interlace = chunk_data[12]
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break
        index = crc_end

    if width <= 0 or height <= 0 or not idat_parts:
        return None
    if bit_depth != 8 or color_type != 2 or interlace != 0:
        return None

    return {
        "mime_type": "image/png",
        "width": width,
        "height": height,
        "stream_bytes": b"".join(idat_parts),
        "filter": "FlateDecode",
        "decode_parms": f"/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns {width}",
    }


def _file_extension(file_name: str) -> str:
    candidate = str(file_name or "").strip().lower()
    if "." not in candidate:
        return ""
    return candidate.rsplit(".", 1)[-1]


def _detect_binary_image_type(content: bytes) -> str:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8"):
        return "image/jpeg"
    return ""


def _strict_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_logo_image(
    logo_asset: dict[str, Any] | None,
    *,
    strict_mode: bool,
    max_bytes: int,
) -> dict[str, Any] | None:
    if not isinstance(logo_asset, dict):
        return None

    file_path = str(logo_asset.get("file_path") or logo_asset.get("path") or "").strip()
    if file_path:
        if strict_mode:
            raise LogoResolutionError(
                "logo_local_path_not_supported",
                "Renderer akzeptiert nur bereits aufgeloeste Logo-Daten und keine Dateipfade.",
            )
        return None

    data_url = str(logo_asset.get("data_url") or "").strip()
    if not data_url:
        return None
    lowered = data_url.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        if strict_mode:
            raise LogoResolutionError(
                "logo_external_url_forbidden",
                "Externe Logo-URLs sind im Renderer nicht erlaubt.",
            )
        return None
    if not lowered.startswith("data:"):
        if strict_mode:
            raise LogoResolutionError(
                "logo_data_url_required",
                "Logo muss als data:-URL mit Base64-Daten uebergeben werden.",
            )
        return None

    header, separator, encoded = data_url.partition(",")
    if not separator:
        if strict_mode:
            raise LogoResolutionError("logo_data_url_invalid", "Logo-data-URL ist unvollstaendig.")
        return None
    if ";base64" not in header.lower():
        if strict_mode:
            raise LogoResolutionError("logo_base64_required", "Logo-data-URL muss Base64-kodiert sein.")
        return None
    mime_type = header[5:].split(";", 1)[0].strip().lower()
    if mime_type not in {"image/jpeg", "image/jpg", "image/png"}:
        if strict_mode:
            raise LogoResolutionError("logo_mime_not_supported", f"Nicht unterstuetzter Logo-MIME-Type: {mime_type or 'leer'}")
        return None
    try:
        binary = base64.b64decode(encoded.strip(), validate=True)
    except (binascii.Error, ValueError):
        if strict_mode:
            raise LogoResolutionError("logo_base64_invalid", "Logo-Bilddaten enthalten ungueltiges Base64.")
        return None
    if not binary:
        if strict_mode:
            raise LogoResolutionError("logo_empty_binary", "Logo-Bilddaten sind leer.")
        return None

    if len(binary) > max(1, max_bytes):
        if strict_mode:
            raise LogoResolutionError(
                "logo_too_large",
                f"Logo-Bilddaten ({len(binary)} Bytes) ueberschreiten das Limit ({max_bytes} Bytes).",
            )
        return None

    detected_mime = _detect_binary_image_type(binary)
    if not detected_mime:
        if strict_mode:
            raise LogoResolutionError("logo_binary_format_invalid", "Logo-Bilddaten sind kein gueltiges PNG/JPEG.")
        return None

    normalized_mime = "image/jpeg" if mime_type == "image/jpg" else mime_type
    if detected_mime != normalized_mime:
        if strict_mode:
            raise LogoResolutionError(
                "logo_mime_binary_mismatch",
                f"MIME-Type ({normalized_mime}) passt nicht zum Bildformat ({detected_mime}).",
            )
        return None

    file_name = str(logo_asset.get("file_name") or logo_asset.get("name") or "").strip()
    extension = _file_extension(file_name)
    if extension:
        if extension in {"jpg", "jpeg"} and detected_mime != "image/jpeg":
            if strict_mode:
                raise LogoResolutionError("logo_extension_mismatch", "Dateiendung .jpg/.jpeg passt nicht zum Bildformat.")
            return None
        if extension == "png" and detected_mime != "image/png":
            if strict_mode:
                raise LogoResolutionError("logo_extension_mismatch", "Dateiendung .png passt nicht zum Bildformat.")
            return None

    if detected_mime == "image/jpeg":
        dimensions = _decode_jpeg_dimensions(binary)
        if not dimensions:
            if strict_mode:
                raise LogoResolutionError("logo_jpeg_corrupt", "JPEG-Bilddaten sind beschaedigt oder unvollstaendig.")
            return None
        width, height = dimensions
        return {
            "mime_type": "image/jpeg",
            "width": width,
            "height": height,
            "stream_bytes": binary,
            "filter": "DCTDecode",
            "decode_parms": None,
        }

    resolved_png = _decode_png_rgb_image(binary)
    if not resolved_png and strict_mode:
        raise LogoResolutionError(
            "logo_png_not_supported_or_corrupt",
            "PNG muss RGB/8-bit ohne Interlacing sein und gueltige IDAT-Daten enthalten.",
        )
    return resolved_png


def _xmp_packet(*, title: str, metadata: dict[str, Any] | None, pdfa_part: int, pdfa_conformance: str) -> bytes:
        meta = metadata or {}
        doc_type = str(meta.get("document_type") or "invoice")
        profile_name = str(meta.get("profile") or "en16931")
        guideline = str(meta.get("guideline") or "urn:cen.eu:en16931:2017")
        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        xmp = f"""<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
    <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
        <rdf:Description rdf:about=''
            xmlns:pdfaid='http://www.aiim.org/pdfa/ns/id/'
            xmlns:dc='http://purl.org/dc/elements/1.1/'
            xmlns:xmp='http://ns.adobe.com/xap/1.0/'
            xmlns:zf='urn:ferd:pdfa:CrossIndustryDocument:invoice:1p0#'>
            <pdfaid:part>{pdfa_part}</pdfaid:part>
            <pdfaid:conformance>{pdfa_conformance}</pdfaid:conformance>
            <dc:title><rdf:Alt><rdf:li xml:lang='x-default'>{title}</rdf:li></rdf:Alt></dc:title>
            <xmp:CreateDate>{created}</xmp:CreateDate>
            <xmp:ModifyDate>{created}</xmp:ModifyDate>
            <zf:DocumentType>{doc_type}</zf:DocumentType>
            <zf:ConformanceLevel>{profile_name}</zf:ConformanceLevel>
            <zf:DocumentFileName>factur-x.xml</zf:DocumentFileName>
            <zf:Version>2.3</zf:Version>
            <zf:Profile>{guideline}</zf:Profile>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""
        return xmp.encode("utf-8")


def _wrap_paragraph(text: str, width: int = 90) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines() or [text]:
        line = raw_line.rstrip()
        if not line:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(line, width=width, break_long_words=False, replace_whitespace=False) or [""])
    return lines


def _split_pages(lines: list[str]) -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if len(current) >= LINES_PER_PAGE:
            pages.append(current)
            current = []
        current.append(line)
    if current or not pages:
        pages.append(current)
    return pages


def _page_stream(
    lines: list[str],
    *,
    font_resource_name: str,
    font_size: int,
    leading: int,
    left_margin: int,
    top_margin: int,
    footer_lines: list[str],
    show_page_numbers: bool,
    page_number: int,
    page_count: int,
    watermark_text: str,
    accent_rgb: tuple[float, float, float],
    layout_template: str,
    logo_draw: dict[str, Any] | None,
    logo_text_draw: dict[str, Any] | None,
) -> bytes:
    commands: list[str] = []

    if page_number == 1:
        if layout_template == "modern":
            line_y = PAGE_HEIGHT - top_margin + 2
            commands.extend(
                [
                    "q",
                    f"{accent_rgb[0]:.3f} {accent_rgb[1]:.3f} {accent_rgb[2]:.3f} RG",
                    "2 w",
                    f"{left_margin} {line_y:.2f} m {PAGE_WIDTH - left_margin} {line_y:.2f} l S",
                    "Q",
                ]
            )
        elif layout_template == "workshop":
            bar_x = max(8.0, float(left_margin) - 13.0)
            bar_y = max(8.0, float(left_margin) * 0.4)
            bar_height = PAGE_HEIGHT - (bar_y * 2.0)
            commands.extend(
                [
                    "q",
                    f"{accent_rgb[0]:.3f} {accent_rgb[1]:.3f} {accent_rgb[2]:.3f} rg",
                    f"{bar_x:.2f} {bar_y:.2f} 6.00 {bar_height:.2f} re f",
                    "Q",
                ]
            )

        if logo_draw:
            logo_width = float(logo_draw.get("width_pt") or 0.0)
            logo_height = float(logo_draw.get("height_pt") or 0.0)
            resource_name = str(logo_draw.get("resource_name") or "ImLogo")
            position = str(logo_draw.get("position") or "left").strip().lower()
            if logo_width > 0.0 and logo_height > 0.0:
                if position == "center":
                    logo_x = (PAGE_WIDTH - logo_width) / 2.0
                elif position == "right":
                    logo_x = PAGE_WIDTH - left_margin - logo_width
                else:
                    logo_x = float(left_margin)
                logo_x = max(8.0, min(PAGE_WIDTH - logo_width - 8.0, logo_x))
                logo_y = PAGE_HEIGHT - top_margin + 8
                max_logo_y = PAGE_HEIGHT - logo_height - 8
                logo_y = max(8.0, min(max_logo_y, logo_y))
                commands.extend(
                    [
                        "q",
                        f"{logo_width:.2f} 0 0 {logo_height:.2f} {logo_x:.2f} {logo_y:.2f} cm",
                        f"/{resource_name} Do",
                        "Q",
                    ]
                )
        elif logo_text_draw:
            text = str(logo_text_draw.get("text") or "").strip()
            if text:
                position = str(logo_text_draw.get("position") or "left").strip().lower()
                font_size = max(18, int(float(logo_text_draw.get("font_size") or 26)))
                if position == "center":
                    logo_x = PAGE_WIDTH / 2.0 - (len(text) * font_size * 0.18)
                elif position == "right":
                    logo_x = PAGE_WIDTH - left_margin - max(120.0, len(text) * font_size * 0.48)
                else:
                    logo_x = float(left_margin)
                logo_y = PAGE_HEIGHT - top_margin + 22
                commands.extend(
                    [
                        "q",
                        f"{accent_rgb[0]:.3f} {accent_rgb[1]:.3f} {accent_rgb[2]:.3f} rg",
                        "BT",
                        f"/{font_resource_name} {font_size} Tf",
                        f"{logo_x:.2f} {logo_y:.2f} Td",
                        f"({_escape_pdf_text(text)}) Tj",
                        "ET",
                        "Q",
                    ]
                )

    if watermark_text:
        watermark_font_size = max(font_size * 4, 24)
        watermark_rgb = _lighten_rgb(accent_rgb, 0.78)
        commands.extend(
            [
                "q",
                f"{watermark_rgb[0]:.3f} {watermark_rgb[1]:.3f} {watermark_rgb[2]:.3f} rg",
                f"BT /{font_resource_name} {watermark_font_size} Tf 140 420 Td 0.87 0.5 -0.5 0.87 0 0 Tm ({_escape_pdf_text(watermark_text)}) Tj ET",
                "Q",
            ]
        )

    commands.extend(["BT", f"/{font_resource_name} {font_size} Tf", f"{leading} TL", f"{left_margin} {PAGE_HEIGHT - top_margin} Td"])
    for index, line in enumerate(lines):
        commands.append(f"({_escape_pdf_text(line)}) Tj")
        if index != len(lines) - 1:
            commands.append("T*")
    commands.append("ET")

    if footer_lines or show_page_numbers:
        footer_text_lines = list(footer_lines)
        if show_page_numbers:
            footer_text_lines.append(f"Seite {page_number}/{page_count}")
        footer_y = max(24, left_margin // 2)
        commands.extend(
            [
                f"{accent_rgb[0]:.3f} {accent_rgb[1]:.3f} {accent_rgb[2]:.3f} rg",
                "BT",
                f"/{font_resource_name} {max(font_size - 2, 8)} Tf",
                f"{max(leading - 2, 10)} TL",
                f"{left_margin} {footer_y} Td",
            ]
        )
        for index, line in enumerate(footer_text_lines):
            commands.append(f"({_escape_pdf_text(line)}) Tj")
            if index != len(footer_text_lines) - 1:
                commands.append("T*")
        commands.append("ET")
        commands.append("0 g")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _build_pdf_bytes(
    page_lines: list[list[str]],
    title: str,
    *,
    attachments: list[dict[str, Any]] | None = None,
    xmp_metadata: dict[str, Any] | None = None,
    pdfa_part: int = 3,
    pdfa_conformance: str = "B",
    layout_options: dict[str, Any] | None = None,
    logo_asset: dict[str, Any] | None = None,
) -> bytes:
    objects: list[bytes] = []
    layout = layout_options or {}
    font_resource_name, base_font_name = _font_resource_name(str(layout.get("font_family") or "Helvetica"))
    font_size = max(8, int(float(layout.get("font_size_pt") or FONT_SIZE)))
    leading = max(font_size + 3, int(float(layout.get("leading") or max(font_size + 3, LEADING))))
    left_margin = max(24, int(_mm_to_pt(_as_float(layout.get("page_margin_mm"), 25.4))))
    top_margin = left_margin
    raw_footer_lines = layout.get("footer_lines")
    footer_candidates = cast(list[Any], raw_footer_lines) if isinstance(raw_footer_lines, list) else []
    footer_lines = [str(item).strip() for item in footer_candidates if str(item).strip()]
    show_page_numbers = bool(layout.get("show_page_numbers"))
    watermark_text = str(layout.get("draft_watermark_text") or "").strip() if bool(layout.get("show_draft_watermark")) else ""
    accent_rgb = _parse_hex_color(str(layout.get("accent_color") or "#234662"))
    layout_template = _normalize_layout_template(layout.get("layout_template"))
    logo_strict_mode = _strict_bool(layout.get("logo_strict_mode"))
    logo_max_bytes = max(1, int(_as_float(layout.get("logo_max_bytes"), 1_048_576.0)))

    def add(content: bytes) -> int:
        objects.append(content)
        return len(objects)

    catalog_id = add(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add(b"<< /Type /Pages /Kids [] /Count 0 >>")
    font_id = add(f"<< /Type /Font /Subtype /Type1 /BaseFont /{base_font_name} >>".encode("ascii"))
    logo_resource_name = "ImLogo"
    logo_object_id: int | None = None
    logo_draw: dict[str, Any] | None = None
    logo_text_draw: dict[str, Any] | None = None
    resolved_logo = _resolve_logo_image(
        logo_asset,
        strict_mode=logo_strict_mode,
        max_bytes=logo_max_bytes,
    )
    if resolved_logo:
        image_stream = bytes(resolved_logo.get("stream_bytes") or b"")
        image_width = int(resolved_logo.get("width") or 0)
        image_height = int(resolved_logo.get("height") or 0)
        image_filter = str(resolved_logo.get("filter") or "").strip()
        if image_stream and image_width > 0 and image_height > 0 and image_filter:
            image_dictionary = (
                f"<< /Type /XObject /Subtype /Image /Width {image_width} /Height {image_height} "
                "/ColorSpace /DeviceRGB /BitsPerComponent 8 "
                f"/Filter /{image_filter} "
            )
            decode_parms = str(resolved_logo.get("decode_parms") or "").strip()
            if decode_parms:
                image_dictionary += f"/DecodeParms << {decode_parms} >> "
            image_dictionary += f"/Length {len(image_stream)} >>\nstream\n"
            logo_object_id = add(image_dictionary.encode("ascii") + image_stream + b"\nendstream")

            logo_width_mm = max(8.0, _as_float(layout.get("logo_width_mm"), 32.0))
            logo_width_pt = max(24.0, min(PAGE_WIDTH / 2.0, _mm_to_pt(logo_width_mm)))
            logo_height_pt = max(12.0, min(96.0, logo_width_pt * (image_height / max(image_width, 1))))
            logo_draw = {
                "resource_name": logo_resource_name,
                "position": str(layout.get("logo_position") or "left").strip().lower(),
                "width_pt": logo_width_pt,
                "height_pt": logo_height_pt,
            }
    if logo_draw is None:
        fallback_text = str((logo_asset or {}).get("fallback_text") or "").strip()
        if fallback_text:
            logo_text_draw = {
                "text": fallback_text,
                "position": str(layout.get("logo_position") or "left").strip().lower(),
                "font_size": max(20.0, min(34.0, _mm_to_pt(max(8.0, _as_float(layout.get("logo_width_mm"), 32.0))) / 3.2)),
            }

    page_ids: list[int] = []
    content_ids: list[int] = []

    for index, lines in enumerate(page_lines, start=1):
        stream = _page_stream(
            lines,
            font_resource_name=font_resource_name,
            font_size=font_size,
            leading=leading,
            left_margin=left_margin,
            top_margin=top_margin,
            footer_lines=footer_lines,
            show_page_numbers=show_page_numbers,
            page_number=index,
            page_count=len(page_lines),
            watermark_text=watermark_text,
            accent_rgb=accent_rgb,
            layout_template=layout_template,
            logo_draw=logo_draw,
            logo_text_draw=logo_text_draw,
        )
        content_ids.append(add(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"))
        xobject_clause = ""
        if logo_object_id:
            xobject_clause = f" /XObject << /{logo_resource_name} {logo_object_id} 0 R >>"
        page_ids.append(
            add(
                (
                    f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                    f"/Resources << /Font << /{font_resource_name} {font_id} 0 R >>{xobject_clause} >> /Contents {content_ids[-1]} 0 R >>"
                ).encode("ascii")
            )
        )

    metadata_xml = _xmp_packet(title=title, metadata=xmp_metadata, pdfa_part=pdfa_part, pdfa_conformance=pdfa_conformance)
    metadata_id = add(b"<< /Type /Metadata /Subtype /XML /Length " + str(len(metadata_xml)).encode("ascii") + b" >>\nstream\n" + metadata_xml + b"\nendstream")

    file_spec_ids: list[int] = []
    if attachments:
        for attachment in attachments:
            file_name = str(attachment.get("file_name") or "attachment.bin").strip() or "attachment.bin"
            mime_type = str(attachment.get("mime_type") or "application/octet-stream").strip() or "application/octet-stream"
            relationship = str(attachment.get("relationship") or "Alternative").strip() or "Alternative"
            content_bytes = attachment.get("content_bytes")
            if isinstance(content_bytes, bytearray):
                content_bytes = bytes(content_bytes)
            if not isinstance(content_bytes, bytes):
                content_bytes = str(attachment.get("content") or "").encode("utf-8")

            ef_stream = b"<< /Type /EmbeddedFile /Subtype /" + mime_type.replace("/", "#2F").encode("ascii", errors="ignore") + b" /Length " + str(len(content_bytes)).encode("ascii") + b" >>\nstream\n" + content_bytes + b"\nendstream"
            ef_id = add(ef_stream)
            file_spec = (
                f"<< /Type /Filespec /F ({_escape_pdf_text(file_name)}) /UF ({_escape_pdf_text(file_name)}) "
                f"/AFRelationship /{relationship} /EF << /F {ef_id} 0 R /UF {ef_id} 0 R >> >>"
            ).encode("latin-1", errors="replace")
            file_spec_ids.append(add(file_spec))

    kids = "[" + " ".join(f"{page_id} 0 R" for page_id in page_ids) + "]"
    objects[catalog_id - 1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[pages_id - 1] = f"<< /Type /Pages /Kids {kids} /Count {len(page_ids)} >>".encode("ascii")
    af_clause = ""
    names_clause = ""
    if file_spec_ids:
        af_clause = " /AF [" + " ".join(f"{obj_id} 0 R" for obj_id in file_spec_ids) + "]"
        embedded_names: list[str] = []
        for index, spec_id in enumerate(file_spec_ids, start=1):
            embedded_names.append(f"(attachment_{index}) {spec_id} 0 R")
        names_clause = " /Names << /EmbeddedFiles << /Names [" + " ".join(embedded_names) + "] >> >>"
    objects[catalog_id - 1] = (
        f"<< /Type /Catalog /Pages 2 0 R /Metadata {metadata_id} 0 R{af_clause}{names_clause} >>"
    ).encode("ascii")

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets: list[int] = []
    body = bytearray(header)
    for object_id, content in enumerate(objects, start=1):
        offsets.append(len(body))
        body.extend(f"{object_id} 0 obj\n".encode("ascii"))
        body.extend(content)
        body.extend(b"\nendobj\n")

    xref_start = len(body)
    body.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    body.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        body.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    body.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R /Info << /Title ({_escape_pdf_text(title)}) /Producer (business_letter_pdf_renderer) /CreationDate ({_pdf_date_now()}) >> >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("latin-1", errors="replace")
    )
    return bytes(body)


def render_pdf_document(
    text: str,
    *,
    title: str = "business_letter",
    attachments: list[dict[str, Any]] | None = None,
    xmp_metadata: dict[str, Any] | None = None,
    pdfa_part: int = 3,
    pdfa_conformance: str = "B",
    layout_options: dict[str, Any] | None = None,
    logo_asset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    layout = layout_options or {}
    font_size = max(8, int(float(layout.get("font_size_pt") or FONT_SIZE)))
    leading = max(font_size + 3, int(float(layout.get("leading") or max(font_size + 3, LEADING))))
    page_margin_mm = float(layout.get("page_margin_mm") or 25.4)
    left_margin = max(24, int(_mm_to_pt(page_margin_mm)))
    raw_footer_lines = layout.get("footer_lines")
    footer_candidates = cast(list[Any], raw_footer_lines) if isinstance(raw_footer_lines, list) else []
    footer_line_count = len([item for item in footer_candidates if str(item).strip()])
    if bool(layout.get("show_page_numbers")):
        footer_line_count += 1
    usable_height = PAGE_HEIGHT - (left_margin * 2)
    lines_per_page = max(12, int(usable_height // max(leading, 1)) - footer_line_count - 2)

    lines: list[str] = []
    for paragraph in text.split("\n\n"):
        wrap_width = max(32, int((PAGE_WIDTH - (left_margin * 2)) / max(font_size * 0.58, 4.5)))
        wrapped = _wrap_paragraph(paragraph, width=wrap_width)
        lines.extend(wrapped or [""])
        lines.append("")
    if lines:
        lines.pop()

    original_lines_per_page = globals()["LINES_PER_PAGE"]
    globals()["LINES_PER_PAGE"] = lines_per_page
    try:
        pages = _split_pages(lines)
    finally:
        globals()["LINES_PER_PAGE"] = original_lines_per_page
    pdf_bytes = _build_pdf_bytes(
        pages,
        title,
        attachments=attachments,
        xmp_metadata=xmp_metadata,
        pdfa_part=pdfa_part,
        pdfa_conformance=pdfa_conformance,
        layout_options=layout,
        logo_asset=logo_asset,
    )
    return {
        "mime_type": "application/pdf",
        "title": title,
        "page_count": len(pages),
        "bytes": pdf_bytes,
        "size_bytes": len(pdf_bytes),
        "pdfa_part": pdfa_part,
        "pdfa_conformance": pdfa_conformance,
        "embedded_file_count": len(attachments or []),
        "text_preview": text,
    }