# packages/plugins/weather/plugin.py
from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, cast
from urllib.parse import quote

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "weather",
    "name": "Weather",
    "description": "Aktuelle Wetterdaten mit Multi-Provider-Fallback (Open-Meteo, OpenWeather u.a.)",
    "category": "🌐 Core / Web",
    "apiKeyRequired": False,
    "intentPattern": r"\b(wetter|temperatur|regen|sonne|wind|vorhersage|klima)\b",
    "status": "implemented",
    "settingsFields": [
        {
            "key": "provider_mode",
            "label": "Provider-Modus",
            "type": "select",
            "default": "auto",
            "group": "Verbindung",
            "options": [
                {"value": "auto", "label": "Auto (Fallback-Kette)"},
                {"value": "open_meteo", "label": "Open-Meteo (ohne API-Key)"},
                {"value": "openweather", "label": "OpenWeather"},
                {"value": "weatherapi", "label": "WeatherAPI.com"},
                {"value": "tomorrowio", "label": "Tomorrow.io"},
                {"value": "visual_crossing", "label": "Visual Crossing"},
                {"value": "pirateweather", "label": "PirateWeather"},
                {"value": "dwd_brightsky", "label": "DWD (Bright Sky API)"},
                {"value": "eris", "label": "Eris (Proxy)"},
            ],
        },
        {
            "key": "fallback_providers",
            "label": "Fallback-Provider (CSV)",
            "type": "string",
            "default": "open_meteo,openweather,weatherapi,tomorrowio,visual_crossing,pirateweather,dwd_brightsky,eris",
            "group": "Verbindung",
        },
        {
            "key": "default_city",
            "label": "Standard-Ort",
            "type": "string",
            "default": "Berlin",
            "group": "Verbindung",
        },
        {
            "key": "default_country",
            "label": "Standard-Land (ISO-2)",
            "type": "string",
            "default": "DE",
            "group": "Verbindung",
        },
        {
            "key": "request_timeout_seconds",
            "label": "HTTP-Timeout (Sekunden)",
            "type": "number",
            "default": 15,
            "group": "Laufzeit",
        },
        {
            "key": "units",
            "label": "Einheiten",
            "type": "select",
            "default": "metric",
            "group": "Laufzeit",
            "options": [
                {"value": "metric", "label": "Celsius"},
                {"value": "imperial", "label": "Fahrenheit"},
            ],
        },
        {
            "key": "forecast_days",
            "label": "Vorhersage-Tage",
            "type": "number",
            "default": 3,
            "group": "Laufzeit",
        },
        {
            "key": "open_meteo_timezone",
            "label": "Open-Meteo Zeitzone",
            "type": "string",
            "default": "auto",
            "group": "Laufzeit",
        },
        {
            "key": "lang",
            "label": "Antwortsprache",
            "type": "select",
            "default": "de",
            "group": "Laufzeit",
            "options": [
                {"value": "de", "label": "Deutsch"},
                {"value": "en", "label": "English"},
            ],
        },
        {
            "key": "eris_base_url",
            "label": "Eris Base-URL (optional)",
            "type": "string",
            "default": "",
            "group": "Verbindung",
        },
    ],
}


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key_raw, item_raw in cast(dict[object, Any], value).items():
        normalized[str(key_raw)] = item_raw
    return normalized


class WeatherPlugin:
    name = "weather"
    description = "Aktuelle Wetterdaten mit konfigurierbarem Multi-Provider-Fallback"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "Stadtname (z.B. 'Berlin', 'London', 'New York').",
            },
            "country": {
                "type": "string",
                "description": "Ländercode (z.B. 'DE', 'US', 'GB'). Optional.",
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "default": "metric",
                "description": "Temperatureinheit: metric (°C), imperial (°F).",
            },
            "forecast": {
                "type": "boolean",
                "default": False,
                "description": "Soll die 5-Tage-Vorhersage abgerufen werden?",
            },
            "days": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "default": 3,
                "description": "Anzahl der Tage für die Vorhersage (1-5, nur mit forecast=true).",
            },
            "lang": {
                "type": "string",
                "enum": ["de", "en", "fr", "es", "it", "ru", "zh", "ja"],
                "default": "de",
                "description": "Sprache der Wetterbeschreibung.",
            },
        },
        "required": ["city"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "city": {"type": "string"},
            "country": {"type": "string"},
            "temperature": {"type": "number"},
            "feels_like": {"type": "number"},
            "humidity": {"type": "number"},
            "pressure": {"type": "number"},
            "wind_speed": {"type": "number"},
            "wind_direction": {"type": "number"},
            "weather": {"type": "string"},
            "description": {"type": "string"},
            "icon": {"type": "string"},
            "sunrise": {"type": "string"},
            "sunset": {"type": "string"},
            "forecast": {"type": "array"},
            "error": {"type": "string"},
        },
    }

    def __init__(self, settings: dict[str, Any] | None = None):
        self._settings: dict[str, Any] = _as_dict(settings)
        self.timeout_seconds = max(3.0, float(os.getenv("WEATHER_TIMEOUT_SECONDS", "15")))

        self.provider_mode = os.getenv("WEATHER_PROVIDER", "auto").strip().lower()
        fallback_env = os.getenv(
            "WEATHER_PROVIDER_FALLBACK",
            "open_meteo,openweather,weatherapi,tomorrowio,visual_crossing,pirateweather,dwd_brightsky,eris",
        )
        self.fallback_providers = [
            item.strip().lower() for item in fallback_env.split(",") if item.strip()
        ]

        self.api_key = (
            os.getenv("WEATHER_API_KEY", "")
            or os.getenv("OPENWEATHER_API_KEY", "")
            or os.getenv("OPENWEATHERMAP_API_KEY", "")
        )
        self.weatherapi_key = os.getenv("WEATHERAPI_API_KEY", "") or os.getenv("WEATHERAPI_KEY", "")
        self.tomorrowio_key = os.getenv("TOMORROWIO_API_KEY", "")
        self.visual_crossing_key = os.getenv("VISUAL_CROSSING_API_KEY", "")
        self.pirateweather_key = os.getenv("PIRATEWEATHER_API_KEY", "")

        self.eris_base_url = os.getenv("ERIS_WEATHER_BASE_URL", "").strip().rstrip("/")
        self.open_meteo_timezone = os.getenv("OPEN_METEO_TIMEZONE", "auto").strip() or "auto"

        self.openweather_base_url = "https://api.openweathermap.org/data/2.5"
        self.open_meteo_forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.open_meteo_geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weatherapi_base_url = "https://api.weatherapi.com/v1"
        self.tomorrowio_base_url = "https://api.tomorrow.io/v4/weather"
        self.visual_crossing_base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
        self.pirateweather_base_url = "https://api.pirateweather.net/forecast"
        self.dwd_brightsky_base_url = "https://api.brightsky.dev"

        self._apply_settings_overrides()

    def set_settings(self, settings: dict[str, Any]) -> None:
        self._settings = _as_dict(settings)
        self._apply_settings_overrides()

    def _integration_settings(self) -> dict[str, Any]:
        raw = self._settings.get("integrations", {})
        return _as_dict(raw)

    def _resolve_setting(self, key: str, env_names: list[str], default: str = "") -> str:
        value = self._settings.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

        integration_value = self._integration_settings().get(key)
        if isinstance(integration_value, str) and integration_value.strip():
            return integration_value.strip()

        for env_name in env_names:
            candidate = os.getenv(env_name, "").strip()
            if candidate:
                return candidate
        return default

    def _apply_settings_overrides(self) -> None:
        provider_mode_value = self._settings.get("provider_mode")
        if isinstance(provider_mode_value, str) and provider_mode_value.strip():
            self.provider_mode = provider_mode_value.strip().lower()

        fallback_value = self._settings.get("fallback_providers")
        if isinstance(fallback_value, str) and fallback_value.strip():
            self.fallback_providers = [item.strip().lower() for item in fallback_value.split(",") if item.strip()]

        timeout_value = self._settings.get("request_timeout_seconds")
        if isinstance(timeout_value, (int, float)):
            self.timeout_seconds = max(3.0, float(timeout_value))

        open_meteo_timezone_value = self._settings.get("open_meteo_timezone")
        if isinstance(open_meteo_timezone_value, str) and open_meteo_timezone_value.strip():
            self.open_meteo_timezone = open_meteo_timezone_value.strip()

        eris_base_url_value = self._settings.get("eris_base_url")
        if isinstance(eris_base_url_value, str) and eris_base_url_value.strip():
            self.eris_base_url = eris_base_url_value.strip().rstrip("/")

        self.api_key = self._resolve_setting(
            "openweather_api_key",
            ["WEATHER_API_KEY", "OPENWEATHER_API_KEY", "OPENWEATHERMAP_API_KEY"],
            self.api_key,
        )
        self.weatherapi_key = self._resolve_setting(
            "weatherapi_api_key",
            ["WEATHERAPI_API_KEY", "WEATHERAPI_KEY"],
            self.weatherapi_key,
        )
        self.tomorrowio_key = self._resolve_setting(
            "tomorrowio_api_key",
            ["TOMORROWIO_API_KEY"],
            self.tomorrowio_key,
        )
        self.visual_crossing_key = self._resolve_setting(
            "visual_crossing_api_key",
            ["VISUAL_CROSSING_API_KEY"],
            self.visual_crossing_key,
        )
        self.pirateweather_key = self._resolve_setting(
            "pirateweather_api_key",
            ["PIRATEWEATHER_API_KEY"],
            self.pirateweather_key,
        )

    def _is_configured(self) -> bool:
        # Konfiguriert, wenn mind. ein provider ohne Key laeuft oder ein API-Key-Provider verfuegbar ist.
        return True

    def _provider_enabled(self, provider: str) -> bool:
        if provider in {"open_meteo", "dwd_brightsky"}:
            return True
        if provider == "openweather":
            return bool(self.api_key)
        if provider == "weatherapi":
            return bool(self.weatherapi_key)
        if provider == "tomorrowio":
            return bool(self.tomorrowio_key)
        if provider == "visual_crossing":
            return bool(self.visual_crossing_key)
        if provider == "pirateweather":
            return bool(self.pirateweather_key)
        if provider == "eris":
            return bool(self.eris_base_url)
        return False

    def _provider_order(self) -> list[str]:
        if self.provider_mode and self.provider_mode != "auto":
            return [self.provider_mode]
        return self.fallback_providers or ["open_meteo", "openweather"]

    def _weather_code_to_text(self, code: int, lang: str) -> tuple[str, str]:
        mapping = {
            0: ("Clear", "Klar"),
            1: ("Mainly clear", "Meist klar"),
            2: ("Partly cloudy", "Teilweise bewoelkt"),
            3: ("Overcast", "Bedeckt"),
            45: ("Fog", "Nebel"),
            48: ("Depositing rime fog", "Raureifnebel"),
            51: ("Light drizzle", "Leichter Nieselregen"),
            53: ("Drizzle", "Nieselregen"),
            55: ("Dense drizzle", "Starker Nieselregen"),
            56: ("Light freezing drizzle", "Leichter gefrierender Nieselregen"),
            57: ("Freezing drizzle", "Gefrierender Nieselregen"),
            61: ("Slight rain", "Leichter Regen"),
            63: ("Rain", "Regen"),
            65: ("Heavy rain", "Starker Regen"),
            66: ("Light freezing rain", "Leichter gefrierender Regen"),
            67: ("Freezing rain", "Gefrierender Regen"),
            71: ("Slight snow", "Leichter Schneefall"),
            73: ("Snow", "Schneefall"),
            75: ("Heavy snow", "Starker Schneefall"),
            77: ("Snow grains", "Schneegraupel"),
            80: ("Rain showers", "Regenschauer"),
            81: ("Moderate rain showers", "Maessige Regenschauer"),
            82: ("Violent rain showers", "Starke Regenschauer"),
            85: ("Snow showers", "Schneeschauer"),
            86: ("Heavy snow showers", "Starke Schneeschauer"),
            95: ("Thunderstorm", "Gewitter"),
            96: ("Thunderstorm with hail", "Gewitter mit Hagel"),
            99: ("Strong thunderstorm with hail", "Starkes Gewitter mit Hagel"),
        }
        en, de = mapping.get(code, ("Unknown", "Unbekannt"))
        return (en, de) if lang == "en" else (en, de)

    async def _http_get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

        if not isinstance(payload, dict):
            return {"error": "Ungueltige Antwort vom Wetterdienst."}
        return _as_dict(payload)

    async def _geocode_city(self, city: str, country: str | None, lang: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "name": city,
            "count": 1,
            "language": "de" if lang not in {"de", "en"} else lang,
            "format": "json",
        }
        if country:
            params["country"] = country

        result = await self._http_get(self.open_meteo_geocode_url, params)
        if "error" in result:
            return result

        rows_raw = result.get("results", [])
        if not isinstance(rows_raw, list) or not rows_raw:
            return {"error": f"Stadt nicht gefunden: {city}"}

        row = _as_dict(rows_raw[0])
        return {
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "city": row.get("name", city),
            "country": row.get("country_code", country or ""),
        }

    def _format_timestamp(self, timestamp: int) -> str:
        """Formatiert einen Unix-Timestamp."""
        try:
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(timestamp)

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Führt einen Request an die OpenWeatherMap API durch."""
        if not self._is_configured():
            return {"error": "Kein Wetterprovider konfiguriert."}

        params["appid"] = self.api_key
        url = f"{self.openweather_base_url}{endpoint}"

        result = await self._http_get(url, params)
        if "error" in result:
            return result

        cod = str(result.get("cod", ""))
        if cod == "401":
            return {"error": "Ungueltiger API-Key. Pruefe WEATHER_API_KEY."}
        if cod == "404":
            return {"error": "Stadt nicht gefunden. Ueberpruefe den Stadtnamen."}
        return result

    async def _get_openweather_current(self, city: str, country: str | None, units: str, lang: str) -> dict[str, Any]:
        """Ruft aktuelle Wetterdaten ab."""
        q = f"{city},{country}" if country else city
        params = {"q": q, "units": units, "lang": lang}

        result = await self._request("/weather", params)
        if "error" in result:
            return result

        data = _as_dict(result)

        return {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", country or ""),
            "temperature": round(data.get("main", {}).get("temp", 0), 1),
            "feels_like": round(data.get("main", {}).get("feels_like", 0), 1),
            "humidity": data.get("main", {}).get("humidity", 0),
            "pressure": data.get("main", {}).get("pressure", 0),
            "wind_speed": data.get("wind", {}).get("speed", 0),
            "wind_direction": data.get("wind", {}).get("deg", 0),
            "weather": data.get("weather", [{}])[0].get("main", ""),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "icon": data.get("weather", [{}])[0].get("icon", ""),
            "sunrise": self._format_timestamp(data.get("sys", {}).get("sunrise", 0)),
            "sunset": self._format_timestamp(data.get("sys", {}).get("sunset", 0)),
            "timezone": data.get("timezone", 0),
        }

    async def _get_openweather_forecast(self, city: str, country: str | None, units: str, days: int, lang: str) -> list[dict[str, Any]]:
        """Ruft die 5-Tage-Vorhersage ab."""
        q = f"{city},{country}" if country else city
        params: dict[str, Any] = {"q": q, "units": units, "lang": lang, "cnt": days * 8}  # 8 Einträge pro Tag

        result = await self._request("/forecast", params)
        if "error" in result:
            return []

        data = result
        forecast_raw = data.get("list", [])
        forecast_list: list[dict[str, Any]] = []
        if isinstance(forecast_raw, list):
            for raw_item in cast(list[Any], forecast_raw):
                item = _as_dict(raw_item)
                if item:
                    forecast_list.append(item)

        # Gruppieren nach Tagen
        forecast_by_day: dict[str, list[dict[str, Any]]] = {}
        for item in forecast_list:
            dt = datetime.fromtimestamp(item.get("dt", 0), tz=timezone.utc)
            date_key = dt.strftime("%Y-%m-%d")
            if date_key not in forecast_by_day:
                forecast_by_day[date_key] = []
            forecast_by_day[date_key].append(item)

        # Pro Tag die wichtigsten Daten
        forecast: list[dict[str, Any]] = []
        for i, (date, items) in enumerate(forecast_by_day.items()):
            if i >= days:
                break
            avg_temp = sum(item.get("main", {}).get("temp", 0) for item in items) / len(items)
            min_temp = min(item.get("main", {}).get("temp", 0) for item in items)
            max_temp = max(item.get("main", {}).get("temp", 0) for item in items)
            weather = items[0].get("weather", [{}])[0].get("main", "")
            description = items[0].get("weather", [{}])[0].get("description", "")
            icon = items[0].get("weather", [{}])[0].get("icon", "")

            forecast.append({
                "date": date,
                "temperature_avg": round(avg_temp, 1),
                "temperature_min": round(min_temp, 1),
                "temperature_max": round(max_temp, 1),
                "weather": weather,
                "description": description,
                "icon": icon,
            })

        return forecast

    async def _get_open_meteo(self, city: str, country: str | None, units: str, days: int, lang: str, forecast_enabled: bool) -> dict[str, Any]:
        geo = await self._geocode_city(city, country, lang)
        if "error" in geo:
            return geo

        latitude = geo.get("latitude")
        longitude = geo.get("longitude")
        if latitude is None or longitude is None:
            return {"error": "Keine Geokoordinaten gefunden."}

        params: dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
            "timezone": self.open_meteo_timezone,
            "forecast_days": max(1, min(16, days)),
        }
        if units == "imperial":
            params["temperature_unit"] = "fahrenheit"
            params["wind_speed_unit"] = "mph"

        result = await self._http_get(self.open_meteo_forecast_url, params)
        if "error" in result:
            return result

        current = _as_dict(result.get("current", {}))
        daily = _as_dict(result.get("daily", {}))
        weather_code = int(current.get("weather_code", 0))
        weather_en, weather_de = self._weather_code_to_text(weather_code, lang)

        response: dict[str, Any] = {
            "city": geo.get("city", city),
            "country": geo.get("country", country or ""),
            "temperature": round(float(current.get("temperature_2m", 0.0)), 1),
            "feels_like": round(float(current.get("apparent_temperature", 0.0)), 1),
            "humidity": int(current.get("relative_humidity_2m", 0) or 0),
            "pressure": int(current.get("pressure_msl", 0) or 0),
            "wind_speed": float(current.get("wind_speed_10m", 0.0) or 0.0),
            "wind_direction": int(current.get("wind_direction_10m", 0) or 0),
            "weather": weather_en,
            "description": weather_de if lang == "de" else weather_en,
            "icon": str(weather_code),
            "sunrise": "",
            "sunset": "",
            "provider": "open_meteo",
        }

        sunrise_list = daily.get("sunrise", [])
        sunset_list = daily.get("sunset", [])
        if isinstance(sunrise_list, list) and sunrise_list:
            response["sunrise"] = str(cast(Any, sunrise_list[0]))
        if isinstance(sunset_list, list) and sunset_list:
            response["sunset"] = str(cast(Any, sunset_list[0]))

        if forecast_enabled:
            dates = cast(list[Any], daily.get("time", [])) if isinstance(daily.get("time", []), list) else []
            min_t = cast(list[Any], daily.get("temperature_2m_min", [])) if isinstance(daily.get("temperature_2m_min", []), list) else []
            max_t = cast(list[Any], daily.get("temperature_2m_max", [])) if isinstance(daily.get("temperature_2m_max", []), list) else []
            code_list = cast(list[Any], daily.get("weather_code", [])) if isinstance(daily.get("weather_code", []), list) else []

            forecast: list[dict[str, Any]] = []
            for i in range(min(days, len(dates), len(min_t), len(max_t), len(code_list))):
                code_i = int(code_list[i] or 0)
                en_i, de_i = self._weather_code_to_text(code_i, lang)
                forecast.append(
                    {
                        "date": str(dates[i]),
                        "temperature_avg": round((float(min_t[i]) + float(max_t[i])) / 2.0, 1),
                        "temperature_min": round(float(min_t[i]), 1),
                        "temperature_max": round(float(max_t[i]), 1),
                        "weather": en_i,
                        "description": de_i if lang == "de" else en_i,
                        "icon": str(code_i),
                    }
                )
            response["forecast"] = forecast

        return response

    async def _get_weatherapi(self, city: str, country: str | None, units: str, days: int, lang: str, forecast_enabled: bool) -> dict[str, Any]:
        if not self.weatherapi_key:
            return {"error": "WeatherAPI-Key fehlt (WEATHERAPI_API_KEY)."}

        q = f"{city},{country}" if country else city
        endpoint = "/forecast.json" if forecast_enabled else "/current.json"
        params: dict[str, Any] = {
            "key": self.weatherapi_key,
            "q": q,
            "lang": "de" if lang == "de" else "en",
            "aqi": "no",
        }
        if forecast_enabled:
            params["days"] = max(1, min(10, days))
            params["alerts"] = "no"

        result = await self._http_get(f"{self.weatherapi_base_url}{endpoint}", params)
        if "error" in result:
            return result

        current = _as_dict(result.get("current", {}))
        location = _as_dict(result.get("location", {}))
        condition = _as_dict(current.get("condition", {}))

        temperature = float(current.get("temp_c", 0.0)) if units == "metric" else float(current.get("temp_f", 0.0))
        feels_like = float(current.get("feelslike_c", 0.0)) if units == "metric" else float(current.get("feelslike_f", 0.0))

        payload: dict[str, Any] = {
            "city": location.get("name", city),
            "country": location.get("country", country or ""),
            "temperature": round(temperature, 1),
            "feels_like": round(feels_like, 1),
            "humidity": int(current.get("humidity", 0) or 0),
            "pressure": int(current.get("pressure_mb", 0) or 0),
            "wind_speed": float(current.get("wind_kph", 0.0) or 0.0),
            "wind_direction": 0,
            "weather": str(condition.get("text", "")),
            "description": str(condition.get("text", "")),
            "icon": str(condition.get("icon", "")),
            "sunrise": "",
            "sunset": "",
            "provider": "weatherapi",
        }

        if forecast_enabled:
            forecast_raw = _as_dict(result.get("forecast", {})).get("forecastday", [])
            forecast_list: list[dict[str, Any]] = []
            if isinstance(forecast_raw, list):
                for row_raw in cast(list[Any], forecast_raw)[:days]:
                    row = _as_dict(row_raw)
                    day = _as_dict(row.get("day", {}))
                    cond = _as_dict(day.get("condition", {}))
                    min_key = "mintemp_c" if units == "metric" else "mintemp_f"
                    max_key = "maxtemp_c" if units == "metric" else "maxtemp_f"
                    forecast_list.append(
                        {
                            "date": row.get("date", ""),
                            "temperature_avg": round(float(day.get("avgtemp_c", 0.0) if units == "metric" else day.get("avgtemp_f", 0.0)), 1),
                            "temperature_min": round(float(day.get(min_key, 0.0)), 1),
                            "temperature_max": round(float(day.get(max_key, 0.0)), 1),
                            "weather": str(cond.get("text", "")),
                            "description": str(cond.get("text", "")),
                            "icon": str(cond.get("icon", "")),
                        }
                    )
            payload["forecast"] = forecast_list

            if isinstance(forecast_raw, list) and forecast_raw:
                first = _as_dict(cast(list[Any], forecast_raw)[0])
                astro = _as_dict(first.get("astro", {}))
                payload["sunrise"] = str(astro.get("sunrise", ""))
                payload["sunset"] = str(astro.get("sunset", ""))

        return payload

    async def _get_visual_crossing(self, city: str, country: str | None, units: str, days: int, lang: str, forecast_enabled: bool) -> dict[str, Any]:
        if not self.visual_crossing_key:
            return {"error": "Visual Crossing API-Key fehlt (VISUAL_CROSSING_API_KEY)."}

        location = quote(f"{city},{country}" if country else city)
        params: dict[str, Any] = {
            "unitGroup": "metric" if units == "metric" else "us",
            "key": self.visual_crossing_key,
            "contentType": "json",
            "lang": "de" if lang == "de" else "en",
            "include": "current,days" if forecast_enabled else "current",
        }

        url = f"{self.visual_crossing_base_url}/{location}"
        result = await self._http_get(url, params)
        if "error" in result:
            return result

        current = _as_dict(result.get("currentConditions", {}))
        payload: dict[str, Any] = {
            "city": city,
            "country": country or "",
            "temperature": round(float(current.get("temp", 0.0)), 1),
            "feels_like": round(float(current.get("feelslike", 0.0)), 1),
            "humidity": int(current.get("humidity", 0) or 0),
            "pressure": int(current.get("pressure", 0) or 0),
            "wind_speed": float(current.get("windspeed", 0.0) or 0.0),
            "wind_direction": int(current.get("winddir", 0) or 0),
            "weather": str(current.get("conditions", "")),
            "description": str(current.get("conditions", "")),
            "icon": str(current.get("icon", "")),
            "sunrise": str(current.get("sunrise", "")),
            "sunset": str(current.get("sunset", "")),
            "provider": "visual_crossing",
        }

        if forecast_enabled:
            days_raw = result.get("days", [])
            forecast: list[dict[str, Any]] = []
            if isinstance(days_raw, list):
                for row_raw in cast(list[Any], days_raw)[:days]:
                    row = _as_dict(row_raw)
                    forecast.append(
                        {
                            "date": row.get("datetime", ""),
                            "temperature_avg": round(float(row.get("temp", 0.0) or 0.0), 1),
                            "temperature_min": round(float(row.get("tempmin", 0.0) or 0.0), 1),
                            "temperature_max": round(float(row.get("tempmax", 0.0) or 0.0), 1),
                            "weather": str(row.get("conditions", "")),
                            "description": str(row.get("conditions", "")),
                            "icon": str(row.get("icon", "")),
                        }
                    )
            payload["forecast"] = forecast

        return payload

    async def _get_pirateweather(self, city: str, country: str | None, units: str, days: int, lang: str, forecast_enabled: bool) -> dict[str, Any]:
        if not self.pirateweather_key:
            return {"error": "PirateWeather API-Key fehlt (PIRATEWEATHER_API_KEY)."}

        geo = await self._geocode_city(city, country, lang)
        if "error" in geo:
            return geo

        latitude = geo.get("latitude")
        longitude = geo.get("longitude")
        if latitude is None or longitude is None:
            return {"error": "Keine Geokoordinaten gefunden."}

        url = f"{self.pirateweather_base_url}/{self.pirateweather_key}/{latitude},{longitude}"
        params: dict[str, Any] = {
            "units": "si" if units == "metric" else "us",
            "lang": "de" if lang == "de" else "en",
            "exclude": "minutely,alerts,flags",
        }

        result = await self._http_get(url, params)
        if "error" in result:
            return result

        current = _as_dict(result.get("currently", {}))
        payload: dict[str, Any] = {
            "city": geo.get("city", city),
            "country": geo.get("country", country or ""),
            "temperature": round(float(current.get("temperature", 0.0) or 0.0), 1),
            "feels_like": round(float(current.get("apparentTemperature", 0.0) or 0.0), 1),
            "humidity": int(float(current.get("humidity", 0.0) or 0.0) * 100),
            "pressure": int(current.get("pressure", 0) or 0),
            "wind_speed": float(current.get("windSpeed", 0.0) or 0.0),
            "wind_direction": int(current.get("windBearing", 0) or 0),
            "weather": str(current.get("summary", "")),
            "description": str(current.get("summary", "")),
            "icon": str(current.get("icon", "")),
            "sunrise": "",
            "sunset": "",
            "provider": "pirateweather",
        }

        if forecast_enabled:
            daily = _as_dict(result.get("daily", {})).get("data", [])
            forecast: list[dict[str, Any]] = []
            if isinstance(daily, list):
                for row_raw in cast(list[Any], daily)[:days]:
                    row = _as_dict(row_raw)
                    dt = int(row.get("time", 0) or 0)
                    forecast.append(
                        {
                            "date": datetime.fromtimestamp(dt, tz=timezone.utc).strftime("%Y-%m-%d") if dt else "",
                            "temperature_avg": round(float(row.get("temperatureHigh", 0.0) or 0.0), 1),
                            "temperature_min": round(float(row.get("temperatureLow", 0.0) or 0.0), 1),
                            "temperature_max": round(float(row.get("temperatureHigh", 0.0) or 0.0), 1),
                            "weather": str(row.get("summary", "")),
                            "description": str(row.get("summary", "")),
                            "icon": str(row.get("icon", "")),
                        }
                    )
                    if not payload.get("sunrise"):
                        sunrise_ts = int(row.get("sunriseTime", 0) or 0)
                        payload["sunrise"] = self._format_timestamp(sunrise_ts) if sunrise_ts else ""
                    if not payload.get("sunset"):
                        sunset_ts = int(row.get("sunsetTime", 0) or 0)
                        payload["sunset"] = self._format_timestamp(sunset_ts) if sunset_ts else ""
            payload["forecast"] = forecast

        return payload

    async def _get_dwd_brightsky(self, city: str, country: str | None, units: str, days: int, lang: str, forecast_enabled: bool) -> dict[str, Any]:
        geo = await self._geocode_city(city, country, lang)
        if "error" in geo:
            return geo

        latitude = geo.get("latitude")
        longitude = geo.get("longitude")
        if latitude is None or longitude is None:
            return {"error": "Keine Geokoordinaten gefunden."}

        current_params = {"lat": latitude, "lon": longitude}
        current_result = await self._http_get(f"{self.dwd_brightsky_base_url}/current_weather", current_params)
        if "error" in current_result:
            return current_result

        current = _as_dict(current_result.get("weather", {}))
        source = _as_dict(current_result.get("sources", [{}])[0] if isinstance(current_result.get("sources", []), list) and current_result.get("sources", []) else {})

        temp_c = float(current.get("temperature", 0.0) or 0.0)
        wind_kmh = float(current.get("wind_speed", 0.0) or 0.0)
        pressure = int(current.get("pressure_msl", 0) or 0)

        payload: dict[str, Any] = {
            "city": source.get("station_name", geo.get("city", city)),
            "country": geo.get("country", country or ""),
            "temperature": round(temp_c if units == "metric" else (temp_c * 9 / 5) + 32, 1),
            "feels_like": round(temp_c if units == "metric" else (temp_c * 9 / 5) + 32, 1),
            "humidity": int(current.get("relative_humidity", 0) or 0),
            "pressure": pressure,
            "wind_speed": round(wind_kmh if units == "metric" else wind_kmh * 0.621371, 1),
            "wind_direction": int(current.get("wind_direction", 0) or 0),
            "weather": str(current.get("condition", "")),
            "description": str(current.get("condition", "")),
            "icon": str(current.get("icon", "")),
            "sunrise": "",
            "sunset": "",
            "provider": "dwd_brightsky",
        }

        if forecast_enabled:
            start_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            last_date = datetime.fromtimestamp(
                datetime.now(tz=timezone.utc).timestamp() + (days * 86400), tz=timezone.utc
            ).strftime("%Y-%m-%d")
            params: dict[str, Any] = {
                "lat": latitude,
                "lon": longitude,
                "date": start_date,
                "last_date": last_date,
            }
            weather_result = await self._http_get(f"{self.dwd_brightsky_base_url}/weather", params)
            if "error" not in weather_result:
                weather_rows = weather_result.get("weather", [])
                by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
                if isinstance(weather_rows, list):
                    for row_raw in cast(list[Any], weather_rows):
                        row = _as_dict(row_raw)
                        ts = str(row.get("timestamp", ""))
                        day = ts[:10] if len(ts) >= 10 else ""
                        if day:
                            by_day[day].append(row)

                forecast: list[dict[str, Any]] = []
                for day, rows in list(by_day.items())[:days]:
                    temps = [float(_as_dict(r).get("temperature", 0.0) or 0.0) for r in rows]
                    cond = str(_as_dict(rows[0]).get("condition", "")) if rows else ""
                    if not temps:
                        continue
                    min_t = min(temps)
                    max_t = max(temps)
                    avg_t = sum(temps) / len(temps)
                    if units != "metric":
                        min_t = (min_t * 9 / 5) + 32
                        max_t = (max_t * 9 / 5) + 32
                        avg_t = (avg_t * 9 / 5) + 32
                    forecast.append(
                        {
                            "date": day,
                            "temperature_avg": round(avg_t, 1),
                            "temperature_min": round(min_t, 1),
                            "temperature_max": round(max_t, 1),
                            "weather": cond,
                            "description": cond,
                            "icon": "",
                        }
                    )
                payload["forecast"] = forecast

        return payload

    async def _get_eris(self, city: str, country: str | None, units: str, days: int, lang: str, forecast_enabled: bool) -> dict[str, Any]:
        if not self.eris_base_url:
            return {"error": "ERIS_WEATHER_BASE_URL ist nicht gesetzt."}

        params: dict[str, Any] = {
            "city": city,
            "country": country or "",
            "units": units,
            "lang": lang,
            "forecast": str(bool(forecast_enabled)).lower(),
            "days": days,
        }
        result = await self._http_get(f"{self.eris_base_url}/weather", params)
        if "error" in result:
            return result

        # Erwartetes Eris-Format: entweder OpenWeather-aehnlich oder bereits normalisiert.
        if "success" in result and "temperature" in result:
            result["provider"] = "eris"
            return result

        current = _as_dict(result.get("current", result))
        payload: dict[str, Any] = {
            "city": current.get("city", city),
            "country": current.get("country", country or ""),
            "temperature": float(current.get("temperature", 0.0) or 0.0),
            "feels_like": float(current.get("feels_like", 0.0) or 0.0),
            "humidity": int(current.get("humidity", 0) or 0),
            "pressure": int(current.get("pressure", 0) or 0),
            "wind_speed": float(current.get("wind_speed", 0.0) or 0.0),
            "wind_direction": int(current.get("wind_direction", 0) or 0),
            "weather": str(current.get("weather", "")),
            "description": str(current.get("description", "")),
            "icon": str(current.get("icon", "")),
            "sunrise": str(current.get("sunrise", "")),
            "sunset": str(current.get("sunset", "")),
            "provider": "eris",
        }
        forecast = result.get("forecast", [])
        if forecast_enabled and isinstance(forecast, list):
            payload["forecast"] = cast(list[dict[str, Any]], forecast)
        return payload

    async def _fetch_by_provider(
        self,
        provider: str,
        city: str,
        country: str | None,
        units: str,
        days: int,
        lang: str,
        forecast_enabled: bool,
    ) -> dict[str, Any]:
        if provider == "open_meteo":
            return await self._get_open_meteo(city, country, units, days, lang, forecast_enabled)
        if provider == "openweather":
            current = await self._get_openweather_current(city, country, units, lang)
            if "error" in current:
                return current
            result: dict[str, Any] = dict(current)
            if forecast_enabled:
                result["forecast"] = await self._get_openweather_forecast(city, country, units, days, lang)
            result["provider"] = "openweather"
            return result
        if provider == "weatherapi":
            return await self._get_weatherapi(city, country, units, days, lang, forecast_enabled)
        if provider == "tomorrowio":
            return await self._get_tomorrowio(city, country, units, days, lang, forecast_enabled)
        if provider == "visual_crossing":
            return await self._get_visual_crossing(city, country, units, days, lang, forecast_enabled)
        if provider == "pirateweather":
            return await self._get_pirateweather(city, country, units, days, lang, forecast_enabled)
        if provider == "dwd_brightsky":
            return await self._get_dwd_brightsky(city, country, units, days, lang, forecast_enabled)
        if provider == "eris":
            return await self._get_eris(city, country, units, days, lang, forecast_enabled)
        return {"error": f"Unbekannter Wetterprovider: {provider}"}

    async def _get_tomorrowio(self, city: str, country: str | None, units: str, days: int, lang: str, forecast_enabled: bool) -> dict[str, Any]:
        if not self.tomorrowio_key:
            return {"error": "Tomorrow.io API-Key fehlt (TOMORROWIO_API_KEY)."}

        q = f"{city},{country}" if country else city
        current_params: dict[str, Any] = {
            "apikey": self.tomorrowio_key,
            "location": q,
            "units": "metric" if units == "metric" else "imperial",
            "timesteps": "current",
            "fields": "temperature,temperatureApparent,humidity,pressureSurfaceLevel,windSpeed,windDirection,weatherCode,sunriseTime,sunsetTime",
        }

        current_result = await self._http_get(f"{self.tomorrowio_base_url}/realtime", current_params)
        if "error" in current_result:
            return current_result

        data = _as_dict(current_result.get("data", {}))
        values = _as_dict(data.get("values", {}))

        payload: dict[str, Any] = {
            "city": city,
            "country": country or "",
            "temperature": round(float(values.get("temperature", 0.0) or 0.0), 1),
            "feels_like": round(float(values.get("temperatureApparent", 0.0) or 0.0), 1),
            "humidity": int(values.get("humidity", 0) or 0),
            "pressure": int(values.get("pressureSurfaceLevel", 0) or 0),
            "wind_speed": float(values.get("windSpeed", 0.0) or 0.0),
            "wind_direction": int(values.get("windDirection", 0) or 0),
            "weather": str(values.get("weatherCode", "")),
            "description": str(values.get("weatherCode", "")),
            "icon": str(values.get("weatherCode", "")),
            "sunrise": str(values.get("sunriseTime", "")),
            "sunset": str(values.get("sunsetTime", "")),
            "provider": "tomorrowio",
        }

        if forecast_enabled:
            forecast_params: dict[str, Any] = {
                "apikey": self.tomorrowio_key,
                "location": q,
                "units": "metric" if units == "metric" else "imperial",
                "timesteps": "1d",
                "fields": "temperatureAvg,temperatureMin,temperatureMax,weatherCode",
                "endTime": "nowPlus{}d".format(max(1, min(5, days))),
            }
            forecast_result = await self._http_get(f"{self.tomorrowio_base_url}/forecast", forecast_params)
            if "error" not in forecast_result:
                timelines = _as_dict(forecast_result.get("timelines", {}))
                daily = timelines.get("daily", [])
                forecast: list[dict[str, Any]] = []
                if isinstance(daily, list):
                    for row_raw in cast(list[Any], daily)[:days]:
                        row = _as_dict(row_raw)
                        values_row = _as_dict(row.get("values", {}))
                        time = str(row.get("time", ""))
                        forecast.append(
                            {
                                "date": time[:10],
                                "temperature_avg": round(float(values_row.get("temperatureAvg", 0.0) or 0.0), 1),
                                "temperature_min": round(float(values_row.get("temperatureMin", 0.0) or 0.0), 1),
                                "temperature_max": round(float(values_row.get("temperatureMax", 0.0) or 0.0), 1),
                                "weather": str(values_row.get("weatherCode", "")),
                                "description": str(values_row.get("weatherCode", "")),
                                "icon": str(values_row.get("weatherCode", "")),
                            }
                        )
                payload["forecast"] = forecast

        return payload

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        city = str(input_data.get("city", "")).strip()
        if not city:
            return {"success": False, "error": "Stadtname ist erforderlich."}

        country = str(input_data.get("country", "")).strip().upper() or None
        units = str(input_data.get("units", "metric")).strip()
        forecast_enabled = bool(input_data.get("forecast", False))
        days = max(1, min(5, int(input_data.get("days", 3))))
        lang = str(input_data.get("lang", "de")).strip()

        requested_provider = str(input_data.get("provider", "")).strip().lower()
        provider_order = [requested_provider] if requested_provider else self._provider_order()

        if not provider_order:
            return {"success": False, "error": "Keine Wetterprovider in der Fallback-Liste konfiguriert."}

        result: dict[str, Any] | None = None
        provider_errors: list[str] = []

        for provider in provider_order:
            if not self._provider_enabled(provider):
                provider_errors.append(f"{provider}: nicht konfiguriert")
                continue

            candidate = await self._fetch_by_provider(provider, city, country, units, days, lang, forecast_enabled)
            if "error" in candidate:
                provider_errors.append(f"{provider}: {candidate['error']}")
                continue

            result = dict(candidate)
            break

        if result is None:
            return {
                "success": False,
                "error": "Kein Wetterprovider lieferte Daten.",
                "provider_errors": provider_errors,
            }

        unit_symbol = "°C" if units == "metric" else "°F"
        result["unit"] = unit_symbol
        result["success"] = True
        if provider_errors:
            result["fallback_info"] = provider_errors

        return result