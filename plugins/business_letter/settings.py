from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, cast


SETTING_SOURCE_ORDER = (
    "system_defaults",
    "tenant",
    "user",
    "location",
    "plugin",
    "document_override",
)


@dataclass(slots=True)
class ResolvedSettings:
    resolved_settings: dict[str, Any]
    setting_sources: dict[str, str]
    unknown_settings: list[str]

@dataclass(slots=True)
class NumberSequenceSettings:
    prefix: str
    sequence_kind: str
    pattern: str | None
    width: int
    year: int | None
    start_value: int
    year_reset: bool


def _numbering_scope(document_kind: str) -> str:
    normalized = str(document_kind or "").strip().lower()
    aliases = {
        "angebot_treppe": "angebot",
        "preisangebot": "angebot",
        "angebotsaenderung": "angebot",
        "angebotsstornierung": "angebot",
        "mahnung_1": "mahnung",
        "mahnung_2": "mahnung",
        "mahnung_3": "mahnung",
        "zahlungserinnerung": "mahnung",
        "inkassouebergabe": "mahnung",
        "verzugszinsberechnung": "mahnung",
        "bestellbestaetigung": "auftragsbestaetigung",
        "auftragsaenderung": "auftragsbestaetigung",
        "auftragsstornierung": "auftragsbestaetigung",
        "teillieferschein": "lieferschein",
        "sammellieferschein": "lieferschein",
        "versandanzeige": "lieferschein",
        "proformarechnung": "rechnung",
        "belastungsanzeige": "rechnung",
        "zahlungsavis": "rechnung",
        "kontoauszug": "rechnung",
        "zahlungsbestaetigung": "rechnung",
        "anzahlungsanforderung": "abschlagsrechnung",
    }
    return aliases.get(normalized, normalized or "document")


def _as_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    mapping = cast(dict[Any, Any], value)
    return {str(key): item for key, item in mapping.items()}

def _to_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def resolve_settings(
    *scopes: tuple[str, dict[str, Any] | None],
    strict: bool = False,
    known_keys: Iterable[str] | None = None,
) -> ResolvedSettings:
    resolved: dict[str, Any] = {}
    sources: dict[str, str] = {}
    unknown: list[str] = []
    allowed = set(known_keys or [])

    for scope_name, raw_values in scopes:
        values = _as_mapping(raw_values)
        for key, value in values.items():
            if allowed and key not in allowed:
                if key not in unknown:
                    unknown.append(key)
                continue
            resolved[key] = value
            sources[key] = scope_name

    if strict and unknown:
        raise ValueError("Unbekannte Settings: " + ", ".join(sorted(unknown)))

    return ResolvedSettings(resolved_settings=resolved, setting_sources=sources, unknown_settings=unknown)


def public_settings(settings: dict[str, Any], allowed_keys: Iterable[str]) -> dict[str, Any]:
    allowed = set(allowed_keys)
    return {key: value for key, value in settings.items() if key in allowed}

def resolve_number_sequence_settings(
    settings: dict[str, Any],
    *,
    document_kind: str,
    tenant_id: str = "default",
) -> NumberSequenceSettings:
    runtime_settings = _as_mapping(settings)
    scope = _numbering_scope(document_kind)

    scoped_prefix_key = f"{scope}_document_number_prefix"
    scoped_sequence_key = f"{scope}_document_number_sequence_kind"
    scoped_pattern_key = f"{scope}_document_number_pattern"
    scoped_width_key = f"{scope}_document_number_width"
    scoped_year_key = f"{scope}_document_number_year"
    scoped_start_value_key = f"{scope}_document_number_start_value"
    scoped_year_reset_key = f"{scope}_document_number_year_reset"

    raw_prefix = str(runtime_settings.get(scoped_prefix_key) or runtime_settings.get("document_number_prefix") or scope or "DOC").strip().upper()
    prefix = raw_prefix[:12] or "DOC"

    sequence_kind = str(runtime_settings.get(scoped_sequence_key) or runtime_settings.get("document_number_sequence_kind") or f"business_letter:{scope or prefix}").strip()
    if not sequence_kind:
        sequence_kind = f"business_letter:{scope or prefix}"

    pattern = str(runtime_settings.get(scoped_pattern_key) or runtime_settings.get("document_number_pattern") or "").strip() or None
    width = _to_int(runtime_settings.get(scoped_width_key), _to_int(runtime_settings.get("document_number_width"), 5)) or 5
    width = max(1, min(12, width))
    year = _to_int(runtime_settings.get(scoped_year_key), _to_int(runtime_settings.get("document_number_year")))
    start_value = _to_int(runtime_settings.get(scoped_start_value_key), _to_int(runtime_settings.get("document_number_start_value"), 1)) or 1
    start_value = max(1, start_value)

    raw_year_reset = runtime_settings.get(scoped_year_reset_key)
    if raw_year_reset is None:
        raw_year_reset = runtime_settings.get("document_number_year_reset")
    if isinstance(raw_year_reset, bool):
        year_reset = raw_year_reset
    else:
        year_reset = str(raw_year_reset or "true").strip().lower() in {"1", "true", "yes", "on"}

    return NumberSequenceSettings(
        prefix=prefix,
        sequence_kind=sequence_kind,
        pattern=pattern,
        width=width,
        year=year,
        start_value=start_value,
        year_reset=year_reset,
    )
