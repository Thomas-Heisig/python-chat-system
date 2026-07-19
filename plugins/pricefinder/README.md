# Price Finder Plugin

ID: pricefinder  
Kategorie: E-Commerce & Preis  
Status: implemented

## Beschreibung

Das Plugin bietet eine universelle Preisabfrage fuer:

- Materialien (z. B. Granit, Marmor, Fliesen)
- Dienstleistungen (z. B. Verlegung, Einbau, Versiegelung)
- Zubehoer (z. B. Kleber, Fugenmasse)

Der Ablauf ist:

1. Lokale Suche in der Preisdatenbank
2. Optionaler Internet-Fallback (DuckDuckGo API + DuckDuckGo HTML)
3. Preisaggregation (min/avg/max)
4. Material-Enrichment (Bild + Zusatzinformationen primaer aus Wikipedia; optionaler Google-Fallback)
5. Rueckfrage fuer Referenzspeicherung (ueber Orchestrator)

## Schablonen-Compliance

- Metadaten in `PLUGIN_META` in `plugin.py`
- Dynamische Settings ueber `settingsFields`
- Keine hardcoded Plugin-Settings im Frontend

## Dynamische Meta-Settings (Maximal)

Dieses Plugin liefert folgende `settingsFields`:

- `mode` (select: local-only/hybrid/internet-only, Gruppe Allgemein)
- `default_currency` (select, Gruppe Allgemein)
- `default_unit` (select, Gruppe Allgemein)
- `default_entity_type` (select, Gruppe Allgemein)
- `enable_web_fallback` (boolean, Gruppe Internet)
- `search_provider` (select, Gruppe Internet)
- `http_timeout_seconds` (number, Gruppe Internet)
- `enable_material_details` (boolean, Gruppe Internet)
- `enable_google_image` (boolean, Gruppe Internet, Standard: aus)
- `enable_knowledge_graph` (boolean, Gruppe Internet)
- `price_min` (number, Gruppe Validierung)
- `price_max` (number, Gruppe Validierung)
- `auto_derive_material_from_variant` (boolean, Gruppe Validierung)
- `return_raw_search_text` (boolean, Gruppe Debug)

## Umgebungsvariablen

- `PRICE_STORAGE_PATH` (Pfad zur lokalen Preisdatenbank)
- `PRICEFINDER_MODE` (`local-only`, `hybrid`, `internet-only`)
- `PRICEFINDER_ENABLE_WEB_FALLBACK` (`true`/`false`)
- `PRICEFINDER_DEFAULT_CURRENCY` (`EUR`, `USD`, `CHF`, `GBP`)
- `PRICEFINDER_DEFAULT_UNIT` (`qm`, `lfm`, `stueck`)
- `PRICEFINDER_DEFAULT_ENTITY_TYPE` (`material`, `service`, `accessory`)
- `PRICEFINDER_HTTP_TIMEOUT_SECONDS`
- `PRICEFINDER_SEARCH_PROVIDER` (`auto`, `duckduckgo`, `duckduckgo_html`)
- `PRICEFINDER_ENABLE_MATERIAL_DETAILS`
- `PRICEFINDER_ENABLE_GOOGLE_IMAGE` (default: `false`, optional aktivierbar)
- `PRICEFINDER_ENABLE_KNOWLEDGE_GRAPH`
- `PRICEFINDER_PRICE_MIN`
- `PRICEFINDER_PRICE_MAX`
- `PRICEFINDER_AUTO_DERIVE_MATERIAL`
- `PRICEFINDER_RETURN_RAW_SEARCH_TEXT`
- `GOOGLE_SEARCH_API_KEY` (optional fuer spaeteren Bildfallback ueber spezialisierte Quellen)
- `GOOGLE_SEARCH_CX` (optional fuer spaeteren Bildfallback ueber spezialisierte Quellen)
- `GOOGLE_KNOWLEDGE_GRAPH_API_KEY` (optional fuer Zusatzinfos)

## Input (universell)

```json
{
  "entity_name": "verlegung",
  "entity_type": "service",
  "area": 25,
  "unit": "qm",
  "currency": "EUR"
}
```

## Input (legacy-kompatibel Material)

```json
{
  "material": "granit",
  "variant": "bianco sardo",
  "format": "60x60",
  "thickness": "3cm",
  "quantity": 12,
  "currency": "EUR"
}
```

## Output-Beispiele

### Lokaler Treffer (Service)

```json
{
  "success": true,
  "source": "local",
  "entity_name": "Verlegung",
  "entity_type": "service",
  "price": 45.0,
  "currency": "EUR",
  "unit": "qm",
  "total_price": 1125.0
}
```

### Internet-Fallback

```json
{
  "success": true,
  "source": "internet",
  "entity_name": "Nero Assoluto",
  "entity_type": "material",
  "currency": "EUR",
  "unit": "qm",
  "prices": {
    "min": 145.0,
    "avg": 178.5,
    "max": 220.0,
    "count": 8
  },
  "image_url": "https://upload.wikimedia.org/...",
  "thumbnail_url": "https://upload.wikimedia.org/...",
  "external_url": "https://de.wikipedia.org/wiki/...",
  "additional_info": {
    "wikipedia": "Kurzbeschreibung ...",
    "knowledge_graph": {
      "name": "...",
      "description": "..."
    }
  }
}
```

### Details ohne Preis (Fallback)

```json
{
  "success": true,
  "source": "details-only",
  "entity_name": "Jura Gelb",
  "entity_type": "material",
  "message": "Keine verlaesslichen Preise gefunden, aber Zusatzinformationen und Bild sind verfuegbar.",
  "image_url": "https://...",
  "external_url": "https://de.wikipedia.org/wiki/...",
  "additional_info": {
    "wikipedia": "..."
  }
}
```

## Hinweise

- Die lokale DB ist als JSON-Datei ausgelegt und kann schrittweise erweitert werden.
- Die Internetrecherche extrahiert textuell auffindbare Preisangaben; bei fehlenden Preisen koennen dennoch Bild/Zusatzinfos geliefert werden.
- Bilder werden standardmaessig zuerst aus Wikipedia verwendet; externe Bildquellen koennen spaeter gezielt zugeschaltet werden.
- Fuer persistente Freigabeprozesse ist die Orchestrator-Bestaetigung vorgesehen (Preis und/oder Zusatzinfos speichern).
