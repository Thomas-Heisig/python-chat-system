from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


def _issue(code: str, path: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "path": path, "message": message, "severity": severity}


def _write_report(report_dir: Path | None, file_name: str, content: str) -> None:
    if report_dir is None:
        return
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / file_name).write_text(content, encoding="utf-8")


def _resolve_report_dir() -> Path | None:
    raw = str(os.getenv("BUSINESS_LETTER_VALIDATION_REPORT_DIR", "")).strip()
    if not raw:
        return None
    return Path(raw)


def _resolve_path(raw: str | None) -> Path | None:
    text = (raw or "").strip()
    if not text:
        return None
    candidate = Path(text)
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def _extract_rule_ids(*texts: str) -> list[str]:
    # Typical rule identifiers in EN16931/XRechnung outputs (e.g. BR-CO-10, BR-DE-001, XR-...)
    pattern = re.compile(r"\b(?:BR|BT|BG|XR|XRECHNUNG|EN16931)(?:-[A-Z0-9]+){1,5}\b", re.IGNORECASE)
    seen: set[str] = set()
    ordered: list[str] = []
    for text in texts:
        for match in pattern.findall(text or ""):
            normalized = match.upper()
            if normalized not in seen:
                seen.add(normalized)
                ordered.append(normalized)
    return ordered


def _classify_outputs(schema_output: str, schematron_output: str) -> dict[str, bool]:
    combined = f"{schema_output}\n{schematron_output}".lower()
    return {
        "xml_syntax": any(token in combined for token in ["parser error", "xml declaration allowed only", "not well-formed"]),
        "xsd": any(token in (schema_output or "").lower() for token in ["fails to validate", "schemas validity error", "element '"]),
        "schematron": any(token in (schematron_output or "").lower() for token in ["schematron validity error", "failed to validate"]),
        "en16931": any(token in combined for token in ["en16931", "br-co", "br-dec", "br-s", "br-"]),
        "xrechnung_specific": any(token in combined for token in ["br-de", "xrechnung", "xr-"]),
    }


def validate_xrechnung_official_conformance(
    xml_payload: str,
    *,
    xsd_path: str | None = None,
    schematron_path: str | None = None,
    report_prefix: str | None = None,
    syntax: str = "UBL",
) -> dict[str, Any]:
    xmllint_path = shutil.which("xmllint")
    report_dir = _resolve_report_dir()
    prefix = report_prefix or datetime.now().strftime("xrechnung_%Y%m%d_%H%M%S")

    normalized_syntax = syntax.strip().upper() or "UBL"
    if normalized_syntax == "CII":
        resolved_xsd = _resolve_path(xsd_path or os.getenv("XRECHNUNG_CII_XSD_PATH") or os.getenv("XRECHNUNG_XSD_PATH"))
        resolved_schematron = _resolve_path(schematron_path or os.getenv("XRECHNUNG_CII_SCHEMATRON_PATH") or os.getenv("XRECHNUNG_SCHEMATRON_PATH"))
    else:
        resolved_xsd = _resolve_path(xsd_path or os.getenv("XRECHNUNG_XSD_PATH"))
        resolved_schematron = _resolve_path(schematron_path or os.getenv("XRECHNUNG_SCHEMATRON_PATH"))

    if not xmllint_path:
        return {
            "executed": False,
            "valid": False,
            "status": "skipped",
            "message": "xmllint not available.",
            "schema": {"executed": False, "valid": False, "status": "skipped"},
            "schematron": {"executed": False, "valid": False, "status": "skipped"},
            "issues": [_issue("XR-OFFICIAL-000", "xml", "xmllint not available.", "warning")],
            "errors": [],
            "warnings": [_issue("XR-OFFICIAL-000", "xml", "xmllint not available.", "warning")],
        }

    if resolved_xsd is None or resolved_schematron is None:
        missing_parts: list[str] = []
        if resolved_xsd is None:
            missing_parts.append("XRECHNUNG_XSD_PATH")
        if resolved_schematron is None:
            missing_parts.append("XRECHNUNG_SCHEMATRON_PATH")
        message = "Official validation skipped: missing " + ", ".join(missing_parts)
        warning = _issue("XR-OFFICIAL-001", "xml", message, "warning")
        return {
            "executed": False,
            "valid": False,
            "status": "skipped",
            "message": message,
            "schema": {"executed": False, "valid": False, "status": "skipped"},
            "schematron": {"executed": False, "valid": False, "status": "skipped"},
            "issues": [warning],
            "errors": [],
            "warnings": [warning],
        }

    with tempfile.TemporaryDirectory(prefix="xrechnung_official_") as tmp_dir:
        xml_file = Path(tmp_dir) / "invoice.xml"
        xml_file.write_text(xml_payload, encoding="utf-8")

        schema_cmd = [xmllint_path, "--noout", "--schema", str(resolved_xsd), str(xml_file)]
        schema_proc = subprocess.run(schema_cmd, capture_output=True, text=True)
        schema_valid = schema_proc.returncode == 0
        schema_output = (schema_proc.stdout or "") + (schema_proc.stderr or "")

        schematron_cmd = [xmllint_path, "--noout", "--schematron", str(resolved_schematron), str(xml_file)]
        schematron_proc = subprocess.run(schematron_cmd, capture_output=True, text=True)
        schematron_valid = schematron_proc.returncode == 0
        schematron_output = (schematron_proc.stdout or "") + (schematron_proc.stderr or "")

    _write_report(report_dir, f"{prefix}_official_schema.txt", schema_output)
    _write_report(report_dir, f"{prefix}_official_schematron.txt", schematron_output)
    _write_report(
        report_dir,
        f"{prefix}_official_summary.json",
        json.dumps(
            {
                "schema_valid": schema_valid,
                "schematron_valid": schematron_valid,
                "syntax": normalized_syntax,
                "xsd_path": str(resolved_xsd),
                "schematron_path": str(resolved_schematron),
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    rule_ids = _extract_rule_ids(schema_output, schematron_output)
    classification = _classify_outputs(schema_output, schematron_output)

    issues: list[dict[str, str]] = []
    if not schema_valid:
        issues.append(
            _issue(
                "XR-OFFICIAL-XSD",
                "xml",
                "Official XSD validation failed.",
                "error",
            )
        )
    if not schematron_valid:
        issues.append(
            _issue(
                "XR-OFFICIAL-SCH",
                "xml",
                "Official Schematron validation failed.",
                "error",
            )
        )

    return {
        "executed": True,
        "valid": schema_valid and schematron_valid,
        "status": "passed" if schema_valid and schematron_valid else "failed",
        "rule_ids": rule_ids,
        "classification": classification,
        "schema": {
            "executed": True,
            "valid": schema_valid,
            "status": "passed" if schema_valid else "failed",
            "xsd_path": str(resolved_xsd),
            "report_file": f"{prefix}_official_schema.txt" if report_dir else "",
        },
        "schematron": {
            "executed": True,
            "valid": schematron_valid,
            "status": "passed" if schematron_valid else "failed",
            "schematron_path": str(resolved_schematron),
            "report_file": f"{prefix}_official_schematron.txt" if report_dir else "",
        },
        "issues": issues,
        "errors": [issue for issue in issues if issue.get("severity") == "error"],
        "warnings": [issue for issue in issues if issue.get("severity") == "warning"],
    }
