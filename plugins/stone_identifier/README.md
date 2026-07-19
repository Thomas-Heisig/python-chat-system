# 📄 Stone Identifier Plugin

**ID:** `stone_identifier`  
**Kategorie:** 🏢 Spezial (Naturstein)  
**Status:** ✅ Implementiert (Text-Modus) / ⬜ Bild-Modus geplant

## 📝 Beschreibung

Das Stone Identifier Plugin ermöglicht die **Identifikation von Natursteinen** anhand von:

- **Textbeschreibungen** – z. B. "schwarzer Stein mit weißen Punkten", "weißer Marmor mit Adern"
- **Bildern** – (geplant) über externe Bilderkennungs-APIs (Google Vision, Replicate, etc.)

Es durchsucht eine lokale Datenbank nach passenden Steinen und gibt die besten Übereinstimmungen zurück.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(stein|granit|marmor|quarzit|schiefer|travertin|erkennen|identifizieren|welcher stein)\b
```

**Beispiele:**

- _"Welcher Stein ist das? Beschreibung: schwarz, feinkörnig."_
- _"Ich habe einen Stein mit weißen Adern – was ist das?"_
- _"Identifiziere diesen Stein: hart, schwarz, glitzernd."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable        | Beschreibung            | Standard          |
| --------------- | ----------------------- | ----------------- |
| `STONE_DB_PATH` | Pfad zur JSON-Datenbank | `./stone_db.json` |

Für Bilderkennung wird zusätzlich ein API-Key für den jeweiligen Dienst benötigt (z. B. `GOOGLE_VISION_API_KEY`).

---

## 📦 Input-Schema

```json
{
  "query": "schwarzer Stein mit weißen Punkten",
  "mode": "text",
  "image_url": "https://example.com/stone.jpg",
  "api_key": "your-api-key"
}
```

| Feld        | Typ    | Beschreibung                                          |
| ----------- | ------ | ----------------------------------------------------- |
| `query`     | string | Textbeschreibung oder Suchbegriff (erforderlich)      |
| `mode`      | string | `text` (Standard) oder `image`                        |
| `image_url` | string | URL des Bildes (nur für `image`-Modus)                |
| `api_key`   | string | API-Key für externe Bilderkennung (für `image`-Modus) |

---

## 📤 Output-Schema

### Erfolg (Text-Modus)

```json
{
  "success": true,
  "identified_stone": {
    "name": "Nero Assoluto",
    "type": "Granit",
    "origin": "Indien",
    "colors": ["schwarz", "dunkelgrau"],
    "patterns": ["feinkörnig", "glitzernd"],
    "characteristics": ["hart", "säurebeständig"],
    "uses": ["Küchenarbeitsplatten", "Böden"],
    "hardness": 7
  },
  "matches": [
    {
      "name": "Nero Assoluto",
      "type": "Granit",
      "score": 10,
      "colors": ["schwarz", "dunkelgrau"]
    },
    {
      "name": "Grauer Schiefer",
      "type": "Schiefer",
      "score": 5,
      "colors": ["grau", "anthrazit"]
    }
  ],
  "message": "Stein identifiziert: Nero Assoluto (Score: 10)"
}
```

### Fehler

```json
{
  "success": false,
  "error": "Kein passender Stein für die Beschreibung gefunden."
}
```

---

## 🧪 Beispiele

### 1. Text-Identifikation

**Input:**

```json
{
  "query": "schwarz, feinkörnig, hart"
}
```

**Output:** (siehe oben)

### 2. Text-Identifikation mit Teilübereinstimmung

**Input:**

```json
{
  "query": "weißer Marmor mit Adern"
}
```

**Output:** `Carrara` oder ähnliche weiße Marmore.

### 3. Bild-Identifikation (Platzhalter)

**Input:**

```json
{
  "mode": "image",
  "image_url": "https://example.com/stone.jpg",
  "api_key": "your-google-vision-key"
}
```

**Output:** (in aktueller Version nicht implementiert – geplant)

---

## 📁 Datei-Struktur

```text
packages/plugins/stone_identifier/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📁 Speicherort der Datenbank

Standardmäßig wird die Datenbank in einer JSON-Datei gespeichert:

```text
./stone_db.json
```

---

## 🔧 Erweiterbarkeit

Die Datenbank kann um neue Steine, Eigenschaften und Synonyme erweitert werden:

```python
_STONE_DB.append({
    "id": "neuer_stein",
    "name": "Neuer Stein",
    "type": "Granit",
    "origin": "China",
    "colors": ["rot", "braun"],
    "patterns": ["grobkörnig", "gestreift"],
    "characteristics": ["hart", "wetterfest"],
    "uses": ["Böden", "Außenbereich"],
    "texture": "grob",
    "hardness": 6,
})
```

---

## 🚀 Geplante Erweiterungen (Bild-Modus)

- **Google Vision Integration**: Nutzt die Google Vision API zur Label-Erkennung.
- **Replicate Integration**: Nutzt Bildklassifikationsmodelle von Replicate.
- **Self-Hosted Modelle**: Lokale ML-Modelle für die Erkennung (z. B. TensorFlow Lite).

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Ich habe einen Stein, der schwarz ist und glitzert. Was könnte das sein?"_
>
> **Elisa:** _"Das klingt nach Nero Assoluto Granit. Er ist schwarz, feinkörnig und glitzert leicht. Er ist sehr hart und säurebeständig. Möchtest du mehr Details?"_

---

## 📚 Siehe auch

- [Stone Colors Plugin](../stone_colors)
- [Care Instructions Plugin](../care_instructions)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
