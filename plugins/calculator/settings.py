from __future__ import annotations

from typing import Any


def resolve_angle_mode(input_data: dict[str, Any], runtime_settings: dict[str, Any]) -> str:
    candidate = input_data.get("angle_mode", runtime_settings.get("angle_mode", "rad"))
    if isinstance(candidate, str) and candidate.strip().lower() == "deg":
        return "deg"
    return "rad"


def resolve_precision(input_data: dict[str, Any], runtime_settings: dict[str, Any]) -> int:
    candidate = input_data.get("precision", runtime_settings.get("precision", 8))
    try:
        value = int(candidate)
    except Exception:
        return 8
    return max(0, min(12, value))
