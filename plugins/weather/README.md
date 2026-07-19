# Weather Plugin

ID: weather  
Kategorie: Core / Web  
Status: implemented

## Beschreibung

Das Plugin liefert aktuelle Wetterdaten und optionale Vorhersagen mit einer
konfigurierbaren Multi-Provider-Strategie.

Unterstuetzte Provider:

- Open-Meteo (ohne API-Key)
- OpenWeather
- WeatherAPI.com
- Visual Crossing
- PirateWeather
- DWD ueber Bright Sky API
- Eris (optional per eigener Base-URL)

Standardmaessig arbeitet das Plugin im Modus `auto` mit Fallback-Kette.

## Schablonen-Compliance

- Metadaten stehen in `PLUGIN_META` in `plugin.py`.
- Plugin-Settings werden dynamisch ueber `settingsFields` geladen.
- Keine hardcoded Settings-Listen im Frontend.

## Dynamische Meta-Settings

Dieses Plugin liefert folgende `settingsFields`:

- `provider_mode` (select, Gruppe Verbindung)
- `fallback_providers` (string/CSV, Gruppe Verbindung)
- `default_city` (string, Gruppe Verbindung)
- `default_country` (string, Gruppe Verbindung)
- `request_timeout_seconds` (number, Gruppe Laufzeit)
- `units` (select: metric/imperial, Gruppe Laufzeit)
- `forecast_days` (number, Gruppe Laufzeit)
- `open_meteo_timezone` (string, Gruppe Laufzeit)
- `lang` (select: de/en, Gruppe Laufzeit)
- `eris_base_url` (string, Gruppe Verbindung)

## Erforderliche Umgebungsvariable

Optional, je nach Provider:

- OpenWeather: `WEATHER_API_KEY` oder `OPENWEATHER_API_KEY` oder `OPENWEATHERMAP_API_KEY`
- WeatherAPI: `WEATHERAPI_API_KEY` oder `WEATHERAPI_KEY`
- Visual Crossing: `VISUAL_CROSSING_API_KEY`
- PirateWeather: `PIRATEWEATHER_API_KEY`
- Eris: `ERIS_WEATHER_BASE_URL`

Ohne API-Key nutzbar:

- Open-Meteo
- DWD (Bright Sky)

Zusatzoptionen:

- `WEATHER_PROVIDER` (z. B. `auto`, `open_meteo`, `openweather`)
- `WEATHER_PROVIDER_FALLBACK` (CSV-Reihenfolge)
- `WEATHER_TIMEOUT_SECONDS`
- `OPEN_METEO_TIMEZONE`

## Beispiel-Input

```json
{
  "city": "Berlin",
  "country": "DE",
  "provider": "auto",
  "units": "metric",
  "forecast": true,
  "days": 3,
  "lang": "de"
}
```

## Beispiel-Output

```json
{
  "success": true,
  "provider": "open_meteo",
  "city": "Berlin",
  "country": "DE",
  "temperature": 21.4,
  "weather": "Clouds",
  "description": "aufgelockert bewoelkt"
}
```
