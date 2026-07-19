# 📄 Text Analyzer Plugin

**ID:** `text_analyzer`  
**Kategorie:** 🧠 NLP & Content  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Text Analyzer Plugin analysiert Texte auf:

- **Sprache** – Automatische Erkennung (Deutsch, Englisch, etc.)
- **Sentiment** – Stimmung (positiv, negativ, neutral) mit Punktewert
- **Schlüsselwörter** – Wichtigste Wörter mit Häufigkeit und Kontext
- **Themen** – Themenbasierte Klassifikation (z. B. Stein, Farbe, Verarbeitung)
- **Zusammenfassung** – Kurze Zusammenfassung des Textes

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(analysiere|bewerte|text|stimmung|sentiment|schlüsselwort|thema|sprache)\b
```

**Beispiele:**

- _"Analysiere diesen Text: ..."_
- _"Was ist die Stimmung dieser Nachricht?"_
- _"Extrahiere die Schlüsselwörter aus dem Text."_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit** – es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "text": "Granit ist ein sehr hartes und säurebeständiges Gestein. Es wird oft für Küchenarbeitsplatten verwendet. Ich finde Granit einfach großartig!",
  "analysis_type": "all",
  "max_keywords": 5,
  "language": "auto"
}
```

| Feld            | Typ     | Standard | Beschreibung                                        |
| --------------- | ------- | -------- | --------------------------------------------------- |
| `text`          | string  | –        | Der zu analysierende Text (erforderlich)            |
| `analysis_type` | string  | `all`    | `all`, `sentiment`, `keywords`, `topics`, `summary` |
| `max_keywords`  | integer | `5`      | Maximale Anzahl von Schlüsselwörtern (1–20)         |
| `language`      | string  | `auto`   | `de`, `en`, `fr`, `es`, `it`, `auto`                |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "text_length": 120,
  "word_count": 20,
  "language": "de",
  "sentiment": {
    "score": 0.35,
    "polarity": "positiv",
    "emoji": "😊",
    "positive_words": 3,
    "negative_words": 0,
    "neutral_words": 17,
    "sentiment_breakdown": {
      "positive": 15.0,
      "neutral": 85.0,
      "negative": 0.0
    }
  },
  "keywords": [
    {
      "word": "granit",
      "count": 3,
      "relevance": 15.0,
      "context": "Granit ist ein sehr hartes und säurebeständiges Gestein."
    },
    {
      "word": "arbeitsplatten",
      "count": 1,
      "relevance": 5.0,
      "context": "Es wird oft für Küchenarbeitsplatten verwendet."
    }
  ],
  "topics": [
    { "topic": "Stein/Material", "score": 2 },
    { "topic": "Eigenschaften", "score": 2 },
    { "topic": "Verwendung", "score": 1 }
  ],
  "summary": "Granit ist ein sehr hartes und säurebeständiges Gestein. Es wird oft für Küchenarbeitsplatten verwendet."
}
```

---

## 🧪 Beispiele

### 1. Vollständige Analyse

**Input:**

```json
{
  "text": "Granit ist ein sehr hartes und säurebeständiges Gestein. Es wird oft für Küchenarbeitsplatten verwendet. Ich finde Granit einfach großartig!"
}
```

**Output:** (siehe oben)

### 2. Nur Sentiment

**Input:**

```json
{
  "text": "Ich bin sehr zufrieden mit dem Granit. Er sieht fantastisch aus!",
  "analysis_type": "sentiment"
}
```

**Output:**

```json
{
  "success": true,
  "sentiment": {
    "score": 0.45,
    "polarity": "positiv",
    "emoji": "😊",
    "positive_words": 2,
    "negative_words": 0
  }
}
```

### 3. Nur Schlüsselwörter

**Input:**

```json
{
  "text": "Nero Assoluto ist ein schwarzer Granit aus Indien. Er ist sehr hart und wird für Küchenarbeitsplatten verwendet.",
  "analysis_type": "keywords",
  "max_keywords": 5
}
```

**Output:** `nero assoluto`, `granit`, `indien`, `hart`, `küchenarbeitsplatten`

---

## 📁 Datei-Struktur

```text
packages/plugins/text_analyzer/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Erweiterbarkeit

Die Sentiment-Wortlisten können um domänenspezifische Begriffe erweitert werden:

```python
_POSITIVE_WORDS["de"].extend(["robust", "langlebig", "pflegeleicht"])
_NEGATIVE_WORDS["de"].extend(["rissig", "porös", "fleckig"])
```

Die Themenliste kann an die jeweilige Domäne angepasst werden:

```python
topic_keywords = {
    "Stein/Material": ["granit", "marmor", "quarzit", "schiefer"],
    "Farbe": ["schwarz", "weiß", "grau", "beige"],
    # ...
}
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Analysiere diesen Text: 'Nero Assoluto ist ein schwarzer Granit aus Indien. Er ist sehr hart und wird für Küchenarbeitsplatten verwendet.'"_
>
> **Elisa:** _"Textanalyse (20 Wörter, Deutsch):_
>
> - _Sentiment: positiv (😊, Score: 0.35)_
> - _Schlüsselwörter: Nero Assoluto (2), Granit (1), Indien (1), hart (1), Küchenarbeitsplatten (1)_
> - _Themen: Stein/Material, Eigenschaften, Verwendung"_

---

## 📚 Siehe auch

- [Summarizer Plugin](../summarizer)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
