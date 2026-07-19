# 📄 News Plugin

**ID:** `news`  
**Kategorie:** 📊 Business & Analytics  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das News Plugin ruft **aktuelle Nachrichten** von der **NewsAPI** ab. Es unterstützt:

- **Suche nach Schlagwörtern** (z.B. "Granit", "Naturstein")
- **Top-Headlines** (nach Kategorie, Land, Quelle)
- **Sortierung** (Relevanz, Popularität, Datum)
- **Sprach- und Länderfilter**

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(nachrichten|news|aktuelle|meldungen|headlines|schlagzeilen)\b
```

**Beispiele:**

- _"Zeige mir aktuelle Nachrichten zu Granit."_
- _"Was gibt es Neues in der Steinbranche?"_
- _"Top-Headlines aus Deutschland."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable       | Beschreibung    | Erforderlich |
| -------------- | --------------- | ------------ |
| `NEWS_API_KEY` | NewsAPI API-Key | ✅           |

### NewsAPI-Key erhalten

1. Registriere dich auf [newsapi.org](https://newsapi.org/register)
2. Erhalte einen kostenlosen API-Key (100 Anfragen pro Tag)
3. Setze den Key als `NEWS_API_KEY` in der Umgebung.

---

## 📦 Input-Schema

```json
{
  "query": "Granit",
  "category": "business",
  "country": "de",
  "source": "bbc-news",
  "page_size": 5,
  "page": 1,
  "sort_by": "publishedAt",
  "language": "de",
  "from_date": "2026-06-01",
  "to_date": "2026-06-28"
}
```

| Feld        | Typ     | Standard      | Beschreibung                                                                                    |
| ----------- | ------- | ------------- | ----------------------------------------------------------------------------------------------- |
| `query`     | string  | –             | Suchbegriff (erforderlich)                                                                      |
| `category`  | string  | `general`     | `business`, `entertainment`, `general`, `health`, `science`, `sports`, `technology`             |
| `country`   | string  | `de`          | Ländercode (z.B. `de`, `us`, `gb`)                                                              |
| `source`    | string  | –             | Nachrichtenquelle (z.B. `bbc-news`)                                                             |
| `page_size` | integer | `5`           | Anzahl Artikel pro Seite (1–100)                                                                |
| `page`      | integer | `1`           | Seitennummer                                                                                    |
| `sort_by`   | string  | `publishedAt` | `relevancy`, `popularity`, `publishedAt`                                                        |
| `language`  | string  | `de`          | Sprachcode (`ar`, `de`, `en`, `es`, `fr`, `he`, `it`, `nl`, `no`, `pt`, `ru`, `sv`, `ud`, `zh`) |
| `from_date` | string  | –             | Datum im Format `YYYY-MM-DD` (ab diesem Datum)                                                  |
| `to_date`   | string  | –             | Datum im Format `YYYY-MM-DD` (bis zu diesem Datum)                                              |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "total_results": 42,
  "query": "Granit",
  "articles": [
    {
      "title": "Granitmarkt wächst 2026",
      "description": "Die Nachfrage nach Granit steigt weiter...",
      "url": "https://example.com/article",
      "source": "Handelsblatt",
      "author": "Max Mustermann",
      "published_at": "2026-06-28T10:00:00Z",
      "content": "Der Granitmarkt verzeichnet ein Wachstum von 15%..."
    }
  ]
}
```

---

## 🧪 Beispiele

### 1. Nachrichten zu Granit

**Input:**

```json
{
  "query": "Granit",
  "language": "de",
  "page_size": 3
}
```

### 2. Top-Headlines aus Deutschland (Business)

**Input:**

```json
{
  "category": "business",
  "country": "de",
  "page_size": 5
}
```

### 3. Nachrichten von einer bestimmten Quelle

**Input:**

```json
{
  "source": "bbc-news",
  "query": "stone",
  "language": "en"
}
```

### 4. Nachrichten aus einem Zeitraum

**Input:**

```json
{
  "query": "Granit",
  "from_date": "2026-06-20",
  "to_date": "2026-06-28",
  "sort_by": "publishedAt"
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/news/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key"

**Lösung:** Prüfe `NEWS_API_KEY` in der Umgebung. Der Key muss korrekt und aktiv sein.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Der kostenlose Plan erlaubt 100 Anfragen pro Tag. Warte bis zum nächsten Tag oder upgrade.

### Fehler: "Keine Ergebnisse gefunden"

**Lösung:** Prüfe, ob der Suchbegriff korrekt ist. Möglicherweise gibt es keine Artikel für die angegebenen Filter.

---

## 📊 Preise (NewsAPI)

| Tier           | Anfragen/Tag | Preis       |
| -------------- | ------------ | ----------- |
| **Kostenlos**  | 100          | 0 €         |
| **Business**   | 5.000        | $50/Monat   |
| **Enterprise** | > 5.000      | Individuell |

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Zeige mir aktuelle Nachrichten zu Granit."_
>
> **Elisa:** _"Ich habe 42 Artikel gefunden. Die neuesten:_
>
> 1. _Granitmarkt wächst 2026 – Handelsblatt_
> 2. _Neue Granit-Farben 2026 – Steinwelt_
> 3. _Granit versus Marmor – Vergleich – Naturstein.de_"

---

## 📚 Siehe auch

- [NewsAPI Dokumentation](https://newsapi.org/docs)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
