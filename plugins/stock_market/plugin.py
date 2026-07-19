# packages/plugins/stock_market/plugin.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "stock_market",
    "name": "Stock Market",
    "description": "Aktienkurse und Börsendaten (Alpha Vantage API)",
    "category": "📊 Business & Analytics",
    "apiKeyRequired": True,
    "intentPattern": r"\b(aktie|kurs|börse|dax|nasdaq|s&p|markt|wertpapier|stock|share)\b",
    "status": "implemented",
    "settingsFields": [],
}


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key_raw, item_raw in cast(dict[object, Any], value).items():
        normalized[str(key_raw)] = item_raw
    return normalized


class StockMarketPlugin:
    name = "stock_market"
    description = "Aktienkurse und Börsendaten (Alpha Vantage API)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["quote", "search", "daily", "intraday", "overview"],
                "default": "quote",
                "description": "Aktion: quote (aktueller Kurs), search (Suche), daily (Tagesdaten), intraday (Echtzeit), overview (Unternehmensübersicht).",
            },
            "symbol": {
                "type": "string",
                "description": "Aktiensymbol (z.B. AAPL, MSFT, DAX).",
            },
            "keywords": {
                "type": "string",
                "description": "Suchbegriff für Aktiensuche (z.B. 'Apple', 'Microsoft').",
            },
            "interval": {
                "type": "string",
                "enum": ["1min", "5min", "15min", "30min", "60min"],
                "default": "5min",
                "description": "Intervall für Intraday-Daten (nur für intraday).",
            },
            "outputsize": {
                "type": "string",
                "enum": ["compact", "full"],
                "default": "compact",
                "description": "Datenmenge: compact (100 Datensätze) oder full (vollständig).",
            },
        },
        "required": ["symbol"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "symbol": {"type": "string"},
            "price": {"type": "number"},
            "change": {"type": "number"},
            "change_percent": {"type": "number"},
            "volume": {"type": "integer"},
            "high": {"type": "number"},
            "low": {"type": "number"},
            "open": {"type": "number"},
            "previous_close": {"type": "number"},
            "timestamp": {"type": "string"},
            "results": {"type": "array"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.base_url = "https://www.alphavantage.co/query"

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    def _format_timestamp(self, timestamp: str) -> str:
        """Formatiert einen Zeitstempel für die Ausgabe."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return timestamp

    async def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Führt einen Request an die Alpha Vantage API durch."""
        if not self._is_configured():
            return {"error": "Alpha Vantage API-Key nicht konfiguriert. Setze ALPHA_VANTAGE_API_KEY in der Umgebung."}

        params["apikey"] = self.api_key

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"error": "Ungültiger API-Key. Prüfe ALPHA_VANTAGE_API_KEY."}
                if e.response.status_code == 429:
                    return {"error": "Rate-Limit überschritten (5 Anfragen pro Minute). Bitte später erneut versuchen."}
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

        data = _as_dict(payload)

        if "Information" in data:
            return {"error": str(data["Information"])}

        if "Error Message" in data:
            return {"error": str(data["Error Message"])}

        if "Note" in data:
            return {"error": str(data["Note"])}

        return data

    async def _get_quote(self, symbol: str) -> dict[str, Any]:
        """Ruft den aktuellen Aktienkurs ab."""
        params = {"function": "GLOBAL_QUOTE", "symbol": symbol}
        result = await self._request(params)

        if "error" in result:
            return result

        data = result.get("Global Quote", {})
        if not data:
            return {"error": f"Keine Daten für Symbol '{symbol}' gefunden."}

        return {
            "symbol": data.get("01. symbol", ""),
            "price": float(data.get("05. price", 0)),
            "change": float(data.get("09. change", 0)),
            "change_percent": float(data.get("10. change percent", "0%").replace("%", "")),
            "volume": int(data.get("06. volume", 0)),
            "high": float(data.get("03. high", 0)),
            "low": float(data.get("04. low", 0)),
            "open": float(data.get("02. open", 0)),
            "previous_close": float(data.get("08. previous close", 0)),
            "timestamp": self._format_timestamp(data.get("07. latest trading day", "")),
        }

    async def _search_symbols(self, keywords: str) -> dict[str, Any]:
        """Sucht nach Aktiensymbolen."""
        params = {"function": "SYMBOL_SEARCH", "keywords": keywords}
        result = await self._request(params)

        if "error" in result:
            return result

        matches_raw = result.get("bestMatches", [])
        matches: list[dict[str, Any]] = []
        if isinstance(matches_raw, list):
            for raw_match in cast(list[Any], matches_raw):
                match_map = _as_dict(raw_match)
                if match_map:
                    matches.append(match_map)
        if not matches:
            return {"error": f"Keine Symbole für '{keywords}' gefunden."}

        results: list[dict[str, Any]] = []
        for match in matches:
            results.append({
                "symbol": match.get("1. symbol", ""),
                "name": match.get("2. name", ""),
                "type": match.get("3. type", ""),
                "region": match.get("4. region", ""),
                "currency": match.get("8. currency", ""),
            })

        return {"results": results}

    async def _get_daily(self, symbol: str, outputsize: str) -> dict[str, Any]:
        """Ruft tägliche historische Daten ab."""
        params = {"function": "TIME_SERIES_DAILY_ADJUSTED", "symbol": symbol, "outputsize": outputsize}
        result = await self._request(params)

        if "error" in result:
            return result

        time_series = _as_dict(result.get("Time Series (Daily)", {}))
        if not time_series:
            return {"error": f"Keine Tagesdaten für Symbol '{symbol}' gefunden."}

        results: list[dict[str, Any]] = []
        for date, values in sorted(time_series.items(), reverse=True)[:30]:
            values_map = _as_dict(values)
            results.append({
                "date": date,
                "open": float(values_map.get("1. open", 0)),
                "high": float(values_map.get("2. high", 0)),
                "low": float(values_map.get("3. low", 0)),
                "close": float(values_map.get("4. close", 0)),
                "adjusted_close": float(values_map.get("5. adjusted close", 0)),
                "volume": int(values_map.get("6. volume", 0)),
            })

        return {"results": results}

    async def _get_intraday(self, symbol: str, interval: str, outputsize: str) -> dict[str, Any]:
        """Ruft Intraday-Daten (Echtzeit) ab."""
        params = {"function": "TIME_SERIES_INTRADAY", "symbol": symbol, "interval": interval, "outputsize": outputsize}
        result = await self._request(params)

        if "error" in result:
            return result

        key = f"Time Series ({interval})"
        time_series = _as_dict(result.get(key, {}))
        if not time_series:
            return {"error": f"Keine Intraday-Daten für Symbol '{symbol}' gefunden."}

        results: list[dict[str, Any]] = []
        for timestamp, values in sorted(time_series.items(), reverse=True)[:50]:
            values_map = _as_dict(values)
            results.append({
                "timestamp": self._format_timestamp(timestamp),
                "open": float(values_map.get("1. open", 0)),
                "high": float(values_map.get("2. high", 0)),
                "low": float(values_map.get("3. low", 0)),
                "close": float(values_map.get("4. close", 0)),
                "volume": int(values_map.get("5. volume", 0)),
            })

        return {"results": results}

    async def _get_overview(self, symbol: str) -> dict[str, Any]:
        """Ruft Unternehmensübersicht ab."""
        params = {"function": "OVERVIEW", "symbol": symbol}
        result = await self._request(params)

        if "error" in result:
            return result

        if not result:
            return {"error": f"Keine Übersicht für Symbol '{symbol}' gefunden."}

        return {
            "symbol": result.get("Symbol", ""),
            "name": result.get("Name", ""),
            "description": result.get("Description", ""),
            "sector": result.get("Sector", ""),
            "industry": result.get("Industry", ""),
            "market_cap": result.get("MarketCapitalization", ""),
            "pe_ratio": result.get("PERatio", ""),
            "dividend_yield": result.get("DividendYield", ""),
            "eps": result.get("EPS", ""),
            "book_value": result.get("BookValue", ""),
        }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = str(input_data.get("action", "quote")).lower()
        symbol = str(input_data.get("symbol", "")).strip().upper()
        keywords = str(input_data.get("keywords", "")).strip()
        interval = str(input_data.get("interval", "5min")).strip()
        outputsize = str(input_data.get("outputsize", "compact")).strip()

        if not symbol and action != "search":
            return {"success": False, "error": "symbol ist erforderlich (für quote, daily, intraday, overview)."}

        if not keywords and action == "search":
            return {"success": False, "error": "keywords ist für search erforderlich."}

        try:
            if action == "quote":
                result = await self._get_quote(symbol)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, **result}

            elif action == "search":
                result = await self._search_symbols(keywords)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, **result}

            elif action == "daily":
                result = await self._get_daily(symbol, outputsize)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "symbol": symbol, **result}

            elif action == "intraday":
                result = await self._get_intraday(symbol, interval, outputsize)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "symbol": symbol, "interval": interval, **result}

            elif action == "overview":
                result = await self._get_overview(symbol)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, **result}

            else:
                return {"success": False, "error": f"Unbekannte Aktion: {action}"}

        except Exception as e:
            return {"success": False, "error": f"Fehler: {str(e)}"}


