# 📄 Google Search Plugin

**ID:** `google_search`  
**Kategorie:** 🌐 Core / Web  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Google Search Plugin ermöglicht die **Websuche mit Google** über die **Google Custom Search JSON API**. Es liefert Suchergebnisse mit Titel, Snippet und URL.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(google|suche|finde|search|googlen)\b
```

**Beispiele:**

- _"Google mal nach Granit-Angeboten."_
- _"Suche mit Google nach Naturstein."_
- _"Finde Infos zu Quarzit."_

---

## ⚙️ Konfiguration

### Google Custom Search API einrichten

1. **Google Cloud Project** erstellen oder auswählen
2. **Custom Search API** aktivieren
3. **API-Key** generieren
4. **Search Engine** erstellen (Programmable Search Engine)
5. **Search Engine ID (CX)** kopieren

### Umgebungsvariablen

| Variable                | Beschreibung                 | Erforderlich |
| ----------------------- | ---------------------------- | ------------ |
| `GOOGLE_SEARCH_API_KEY` | Google Custom Search API-Key | ✅           |
| `GOOGLE_SEARCH_CX`      | Search Engine ID (CX)        | ✅           |

### Search Engine erstellen

1. Gehe zu [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Klicke auf **"Neue Suchmaschine erstellen"**
3. Gib eine Website zur Suche ein (z.B. `*` für alle Websites)
4. Wähle den Suchtyp (z.B. "Die gesamte Suche betonen")
5. Klicke auf **"Erstellen"**
6. Kopiere die **Suchmaschinen-ID** (`cx`)

---

## 📦 Input-Schema

```json
{
  "query": "Granit Angebote",
  "num": 5,
  "start": 1,
  "language": "de",
  "site": "wikipedia.org",
  "safe": "medium",
  "date_restrict": "w1"
}
```

| Feld            | Typ     | Standard | Beschreibung                                                  |
| --------------- | ------- | -------- | ------------------------------------------------------------- |
| `query`         | string  | –        | Suchbegriff (erforderlich)                                    |
| `num`           | integer | `5`      | Anzahl der Ergebnisse (1-10)                                  |
| `start`         | integer | `1`      | Startindex für Paginierung                                    |
| `language`      | string  | `de`     | Sprachcode (z.B. `de`, `en`, `fr`)                            |
| `site`          | string  | –        | Website-Filter (z.B. `wikipedia.org`)                         |
| `safe`          | string  | `medium` | SafeSearch: `off`, `medium`, `high`                           |
| `date_restrict` | string  | –        | Zeitraum: `d1` (Tag), `w1` (Woche), `m1` (Monat), `y1` (Jahr) |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "total_results": 123456,
  "query": "Granit Angebote",
  "search_terms": "Granit Angebote",
  "results": [
    {
      "title": "Granit Angebote – Heishg Naturstein",
      "snippet": "Entdecken Sie unsere aktuellen Granit Angebote...",
      "url": "https://www.heishg-naturstein.de/granit",
      "display_url": "www.heishg-naturstein.de",
      "cache_url": "cache_id"
    }
  ]
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Google Search nicht konfiguriert. Setze GOOGLE_SEARCH_API_KEY und GOOGLE_SEARCH_CX in der Umgebung."
}
```

---

## 🧪 Beispiele

### 1. Einfache Suche

**Input:**

```json
{
  "query": "Naturstein Granit",
  "num": 3
}
```

**Output:**

```json
{
  "success": true,
  "total_results": 125000,
  "query": "Naturstein Granit",
  "results": [...]
}
```

### 2. Suche auf Wikipedia

**Input:**

```json
{
  "query": "Marmor",
  "site": "wikipedia.org",
  "num": 3
}
```

### 3. Aktuelle Ergebnisse (letzte Woche)

**Input:**

```json
{
  "query": "Granit Preise",
  "date_restrict": "w1",
  "num": 5
}
```

### 4. Nur deutsche Ergebnisse

**Input:**

```json
{
  "query": "Quarzit Arbeitsplatte",
  "language": "de",
  "safe": "high"
}
```

---

## 📁 Datei-Struktur

```tree
packages/plugins/google_search/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key oder CX-ID"

**Lösung:** Prüfe `GOOGLE_SEARCH_API_KEY` und `GOOGLE_SEARCH_CX` in der Umgebung. Stelle sicher, dass die Custom Search API aktiviert ist.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Die Google Custom Search API hat ein Limit von 100 Anfragen pro Tag für den kostenlosen Tier. Warte bis zum nächsten Tag oder upgrade auf den kostenpflichtigen Tier.

### Fehler: "Keine Ergebnisse gefunden"

**Lösung:** Prüfe, ob der Suchbegriff korrekt ist. Möglicherweise gibt es keine Ergebnisse für die angegebene Website oder Sprache.

---

## 📊 Preise (Google Custom Search API)

| Tier          | Anfragen/Tag | Preis                |
| ------------- | ------------ | -------------------- |
| **Kostenlos** | 100          | 0 €                  |
| **Standard**  | 10.000       | $5 pro 1000 Anfragen |
| **Premium**   | > 10.000     | Individuell          |

> **Hinweis:** Die Kosten können sich ändern. Prüfe die aktuellen Preise in der [Google Cloud Console](https://cloud.google.com/apis/).

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Google mal nach aktuellen Granit-Angeboten."_
>
> **Elisa:** _"Ich habe 125.000 Ergebnisse gefunden. Die Top 3:_

> 1. _Granit Angebote – Heishg Naturstein_
> 2. _Granit-Sonderaktionen – Steinwelt_
> 3. _Granit-Platten günstig kaufen – Baumarkt_

> _Möchtest du einen bestimmten Link öffnen?"_

> **Nutzer:** _"Suche auf Wikipedia nach Marmor."_
>
> **Elisa:** _"Ich habe 5 Ergebnisse auf Wikipedia gefunden. Hier ist der erste: Marmor – Wikipedia – Beschreibung..."_

---

## 📚 Siehe auch

- [Google Custom Search API Dokumentation](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
