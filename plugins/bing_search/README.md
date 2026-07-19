# Bing Search Plugin

````markdown
# Bing Search Plugin

**ID:** `bing_search`  
**Kategorie:** 🌐 Core / Web  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Bing Search Plugin führt eine **Websuche** über die **Bing Web Search API** von Microsoft durch. Es liefert:

- Suchergebnisse mit Titel, Snippet und URL
- Anzahl der geschätzten Ergebnisse
- Unterstützung für verschiedene Märkte (z.B. `de-DE`, `en-US`)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(bing|suche|finde|google|search)\b
```
````

**Beispiele:**

- _"Bing Suche nach Granit Angeboten."_
- _"Finde mit Bing Informationen zu Marmor."_
- _"Search Bing for granite countertops."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable              | Beschreibung        | Erforderlich |
| --------------------- | ------------------- | ------------ |
| `BING_SEARCH_API_KEY` | Bing Search API-Key | ✅           |

### Bing Search API-Key erhalten

1. Registriere dich im [Azure Portal](https://portal.azure.com/)
2. Erstelle eine **Bing Search** Ressource (oder verwende die kostenlose Testversion)
3. Erhalte den **API-Key** aus der Ressource
4. Setze den Key als `BING_SEARCH_API_KEY` in der Umgebung.

> **Hinweis:** Der kostenlose Plan erlaubt 1000 Anfragen pro Monat.

---

## 📦 Input-Schema

```json
{
  "query": "Granit Angebote",
  "count": 5,
  "mkt": "de-DE"
}
```

| Feld    | Typ     | Standard | Beschreibung                           |
| ------- | ------- | -------- | -------------------------------------- |
| `query` | string  | –        | Suchbegriff (erforderlich)             |
| `count` | integer | `5`      | Anzahl der Ergebnisse (1–10)           |
| `mkt`   | string  | `de-DE`  | Markt (z.B. `de-DE`, `en-US`, `en-GB`) |

---

## 📤 Output-Schema

```json
{
  "results": [
    {
      "title": "Granit Angebote – Heishg Naturstein",
      "snippet": "Entdecken Sie unsere aktuellen Granit Angebote...",
      "url": "https://www.heishg-naturstein.de/granit",
      "display_url": "www.heishg-naturstein.de"
    }
  ],
  "total_count": 12345
}
```

**Bei Fehlern:**

```json
{
  "error": "Bing Search API-Key fehlt. Setze BING_SEARCH_API_KEY in der Umgebung."
}
```

---

## 🧪 Beispiele

### 1. Suche nach Granit (Deutschland)

**Input:**

```json
{
  "query": "Granit Angebote",
  "count": 5,
  "mkt": "de-DE"
}
```

### 2. Suche nach Marmor (USA)

**Input:**

```json
{
  "query": "marble countertops",
  "count": 3,
  "mkt": "en-US"
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/bing_search/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📊 Preise (Bing Search API)

| Tier          | Anfragen/Monat | Preis      |
| ------------- | -------------- | ---------- |
| **Kostenlos** | 1000           | 0 €        |
| **S1**        | 10.000         | $7/Monat   |
| **S2**        | 100.000        | $25/Monat  |
| **S3**        | 1.000.000      | $250/Monat |

---

## 🔧 Fehlerbehebung

### Fehler: "Bing Search API-Key fehlt"

**Lösung:** Prüfe `BING_SEARCH_API_KEY` in der Umgebung oder setze den Key in den Plugin-Einstellungen.

### Fehler: "HTTP-Fehler: 401"

**Lösung:** Der API-Key ist ungültig oder abgelaufen. Überprüfe den Key im Azure Portal.

### Fehler: "HTTP-Fehler: 429"

**Lösung:** Rate-Limit überschritten. Warte einige Minuten oder upgrade den Plan.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Bing Suche nach Granit Angeboten."_
>
> **Elisa:** _"Ich habe 12.345 Ergebnisse gefunden. Die Top 5:_
>
> 1. _Granit Angebote – Heishg Naturstein_
> 2. _..._"

---

## 📚 Siehe auch

- [WebSearch Plugin](../websearch)
- [Google Search Plugin](../google_search)
- [Bing Web Search API Dokumentation](https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/overview)
- [Plugins Übersicht](../README.md)

---

**Letzte Aktualisierung:** 2026-06-28

```

```
