from __future__ import annotations


def country_code(value: str) -> str:
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
