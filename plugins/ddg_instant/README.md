# 📄 DuckDuckGo Instant Answer Plugin

**ID:** `ddg_instant`  
**Kategorie:** 🌐 Core / Web  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Plugin nutzt die **DuckDuckGo Instant Answer API**, um **sofortige Antworten auf Faktenfragen** zu liefern – ohne dass eine vollständige Websuche erforderlich ist. Es eignet sich hervorragend für:

- Wetterabfragen
- Definitionen
- Begriffserklärungen
- Kurze Fakten

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(wetter|definition|bedeutung|instant|antwort|sofort|was ist|wer ist)\b
```

**Beispiele:**

- _"Was ist Granit?"_
- _"Wetter in Berlin"_
- _"Definition Marmor"_
- _"Wer war Albert Einstein?"_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit**, es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "query": "Wetter in Berlin"
}
```

| Feld    | Typ    | Beschreibung                                  |
| ------- | ------ | --------------------------------------------- |
| `query` | string | Die Frage oder der Suchbegriff (erforderlich) |

---

## 📤 Output-Schema

```json
{
  "abstract": "Granit ist ein magmatisches Tiefengestein...",
  "definition": "Granit: ein hartes Gestein...",
  "answer": "22°C, sonnig",
  "type": "A",
  "heading": "Granit",
  "source": "https://de.wikipedia.org/wiki/Granit"
}
```

**Bei Fehlern:**

```json
{
  "error": "Keine sofortige Antwort für 'xyz' gefunden."
}
```

---

## 🧪 Beispiele

### 1. Wetterabfrage

**Input:**

```json
{
  "query": "Wetter Berlin"
}
```

**Output:**

```json
{
  "answer": "22°C, sonnig",
  "source": "https://wetter.com/berlin"
}
```

### 2. Definition

**Input:**

```json
{
  "query": "Definition Granit"
}
```

**Output:**

```json
{
  "definition": "Granit: ein magmatisches Tiefengestein, das hauptsächlich aus Quarz, Feldspat und Glimmer besteht.",
  "source": "https://de.wikipedia.org/wiki/Granit"
}
```

### 3. Begriffserklärung

**Input:**

```json
{
  "query": "was ist marmor"
}
```

**Output:**

```json
{
  "abstract": "Marmor ist ein metamorphes Gestein, das aus Kalkstein entsteht...",
  "heading": "Marmor",
  "source": "https://de.wikipedia.org/wiki/Marmor"
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/ddg_instant/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── plugin copy.py     # Backup (optional)
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Keine sofortige Antwort gefunden"

**Ursache:** Die DuckDuckGo Instant Answer API hat keine direkte Antwort für die Anfrage geliefert.

**Lösung:** Verwende das `websearch` Plugin für eine allgemeine Suche oder präzisiere die Frage.

### Fehler: "HTTP-Fehler: 429"

**Ursache:** Rate-Limit überschritten.

**Lösung:** Warte einige Sekunden und versuche es erneut.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Was ist Granit?"_
>
> **Elisa:** _"Granit ist ein magmatisches Tiefengestein, das hauptsächlich aus Quarz, Feldspat und Glimmer besteht. Möchten Sie mehr über Eigenschaften oder Verwendung wissen?"_

---

## 📚 Siehe auch

- [DuckDuckGo Instant Answer API](https://duckduckgo.com/api)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
