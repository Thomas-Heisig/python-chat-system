# packages/plugins/currency_converter/plugin.py
from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "currency_converter",
    "name": "Currency Converter",
    "description": "Währungsumrechnung (EUR, USD, GBP, CHF, etc.) mit Echtzeit-Wechselkursen",
    "category": "📊 Business & Analytics",
    "apiKeyRequired": True,
    "intentPattern": r"\b(euro|dollar|umrechnen|wechselkurs|währung|kurs|währungsrechner)\b",
    "status": "implemented",
    "settingsFields": [],
}


class CurrencyConverterPlugin:
    name = "currency_converter"
    description = "Währungsumrechnung mit Echtzeit-Wechselkursen (unterstützt Fixer.io, Frankfurter, ExchangeRate-API)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Der umzurechnende Betrag.",
            },
            "from_currency": {
                "type": "string",
                "minLength": 3,
                "maxLength": 3,
                "pattern": "^[A-Z]{3}$",
                "description": "ISO-Währungscode der Ausgangswährung (z.B. EUR, USD, GBP).",
                "default": "EUR",
            },
            "to_currency": {
                "type": "string",
                "minLength": 3,
                "maxLength": 3,
                "pattern": "^[A-Z]{3}$",
                "description": "ISO-Währungscode der Zielwährung (z.B. EUR, USD, GBP).",
                "default": "USD",
            },
            "date": {
                "type": "string",
                "description": "Datum für historische Kurse im Format YYYY-MM-DD (optional, verwendet sonst aktuellen Kurs).",
            },
            "source": {
                "type": "string",
                "enum": ["fixer", "frankfurter", "exchangerate"],
                "default": "frankfurter",
                "description": "API-Quelle für Wechselkurse.",
            },
        },
        "required": ["amount"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "amount": {"type": "number"},
            "from_currency": {"type": "string"},
            "to_currency": {"type": "string"},
            "converted_amount": {"type": "number"},
            "rate": {"type": "number"},
            "date": {"type": "string"},
            "source": {"type": "string"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    # Unterstützte Währungen (häufigste)
    SUPPORTED_CURRENCIES = [
        "AED", "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR",
        "GBP", "HKD", "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW",
        "MXN", "MYR", "NOK", "NZD", "PHP", "PLN", "RON", "RUB", "SEK", "SGD",
        "THB", "TRY", "USD", "ZAR"
    ]

    def __init__(self):
        self.api_key = os.getenv("FIXER_API_KEY", os.getenv("EXCHANGERATE_API_KEY", ""))
        self.cache: dict[str, tuple[float, dict[str, float]]] = {}
        self.cache_ttl = 3600  # 1 Stunde Cache

    def _get_base_url(self, source: str) -> str:
        if source == "fixer":
            return "https://data.fixer.io/api"
        elif source == "exchangerate":
            return "https://api.exchangerate-api.com/v4"
        else:  # frankfurter default
            return "https://api.frankfurter.app"

    def _get_cache_key(self, from_currency: str, to_currency: str, date: str | None = None) -> str:
        date_str = date or "latest"
        return f"{from_currency}_{to_currency}_{date_str}"

    async def _fetch_rates(
        self, from_currency: str, to_currency: str, date: str | None = None, source: str = "frankfurter"
    ) -> dict[str, Any]:
        """Ruft Wechselkurse von der gewählten API ab."""
        base_url = self._get_base_url(source)
        date_str = date or "latest"
        cache_key = self._get_cache_key(from_currency, to_currency, date)

        # Cache prüfen
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data

        # API-Anfrage
        params = {"from": from_currency, "to": to_currency}
        headers = {}
        if source == "fixer":
            params["access_key"] = self.api_key
            params["base"] = from_currency
            url = f"{base_url}/{date_str}"
        elif source == "exchangerate":
            url = f"{base_url}/latest/{from_currency}"
        else:  # frankfurter
            url = f"{base_url}/{date_str}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler beim Abrufen der Wechselkurse: {str(e)}"}

        if isinstance(data, dict) and data.get("success") is False:
            return {"error": data.get("error", {}).get("info", "Unbekannter Fehler")}

        # Cache speichern
        self.cache[cache_key] = (time.time(), data)

        return data

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        amount = input_data.get("amount")
        if amount is None:
            return {"error": "Betrag (amount) ist erforderlich."}

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return {"error": "Ungültiger Betrag. Bitte eine Zahl angeben."}

        from_currency = str(input_data.get("from_currency", "EUR")).upper().strip()
        to_currency = str(input_data.get("to_currency", "USD")).upper().strip()
        date = str(input_data.get("date", "")).strip() or None
        source = str(input_data.get("source", "frankfurter")).lower()

        # Validierung der Währungscodes
        if from_currency not in self.SUPPORTED_CURRENCIES:
            return {
                "error": f"Nicht unterstützte Ausgangswährung '{from_currency}'. "
                         f"Unterstützt: {', '.join(self.SUPPORTED_CURRENCIES[:10])}..."
            }
        if to_currency not in self.SUPPORTED_CURRENCIES:
            return {
                "error": f"Nicht unterstützte Zielwährung '{to_currency}'. "
                         f"Unterstützt: {', '.join(self.SUPPORTED_CURRENCIES[:10])}..."
            }

        if from_currency == to_currency:
            return {
                "success": True,
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": amount,
                "rate": 1.0,
                "date": date or "today",
                "source": source,
                "message": "Ausgangs- und Zielwährung sind identisch.",
            }

        # API-Key prüfen (nur für Fixer)
        if source == "fixer" and not self.api_key:
            return {"error": "API-Key für Fixer.io fehlt. Setze FIXER_API_KEY in der Umgebung."}

        # Wechselkurse abrufen
        rates_data = await self._fetch_rates(from_currency, to_currency, date, source)

        if "error" in rates_data:
            return {"error": rates_data["error"]}

        # Kurse extrahieren
        rate = None
        if source == "fixer":
            # Fixer.io: rates ist dict mit Währungscode → Kurs
            rates = rates_data.get("rates", {})
            if to_currency in rates:
                rate = rates[to_currency]
        elif source == "exchangerate":
            # ExchangeRate-API: rates ist dict mit Währungscode → Kurs
            rates = rates_data.get("rates", {})
            if to_currency in rates:
                rate = rates[to_currency]
        else:  # frankfurter
            # Frankfurter: rates ist dict mit Währungscode → Kurs
            rates = rates_data.get("rates", {})
            if to_currency in rates:
                rate = rates[to_currency]

        if rate is None:
            return {"error": f"Kein Wechselkurs für {from_currency} → {to_currency} gefunden."}

        converted = amount * rate

        return {
            "success": True,
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": round(converted, 2),
            "rate": round(rate, 4),
            "date": rates_data.get("date", date or "today"),
            "source": source,
            "message": f"{amount} {from_currency} = {round(converted, 2)} {to_currency} (Kurs: {round(rate, 4)})",
        }
    


