# 📄 Summarizer Plugin

**ID:** `summarizer`  
**Kategorie:** 🧠 NLP & Content  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Summarizer Plugin erstellt **Zusammenfassungen von langen Texten** – ideal für:

- Zusammenfassung von Kundenanfragen
- Verdichtung von Artikeln oder Dokumenten
- Kurzfassung von Konversationen

Es unterstützt zwei Modi:

- **Extractive** – Wählt die wichtigsten Sätze aus dem Originaltext aus.
- **Abstractive** – Generiert eine neue, flüssige Zusammenfassung (mit Transformers-Modellen).

Der Modus `auto` wählt automatisch den besten Ansatz basierend auf der Textlänge und verfügbaren Modellen.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(zusammenfassen|kurzfassung|summary|resümee|text verdichten)\b
```

**Beispiele:**

- _"Fasse diesen Text zusammen."_
- _"Erstelle eine Kurzfassung für den Kunden."_
- _"Textverdichtung für den Artikel."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

Keine erforderlich. Für **abstractive Summarization** wird `transformers` benötigt:

```bash
pip install transformers
```

Falls `transformers` nicht installiert ist, fällt das Plugin automatisch auf **extractive** zurück.

---

## 📦 Input-Schema

```json
{
  "text": "Langer Text hier...",
  "mode": "auto",
  "max_length": 150,
  "min_length": 30,
  "ratio": 0.3,
  "language": "auto"
}
```

| Feld         | Typ     | Standard | Beschreibung                                                          |
| ------------ | ------- | -------- | --------------------------------------------------------------------- |
| `text`       | string  | –        | Der zu zusammenfassende Text (erforderlich)                           |
| `mode`       | string  | `auto`   | `extractive`, `abstractive`, `auto`                                   |
| `max_length` | integer | `150`    | Maximale Länge der Zusammenfassung (in Wörtern)                       |
| `min_length` | integer | `30`     | Minimale Länge der Zusammenfassung (in Wörtern)                       |
| `ratio`      | number  | `0.3`    | Verhältnis der Zusammenfassung zur Originaltextlänge (für extractive) |
| `language`   | string  | `auto`   | Sprache des Textes (`de`, `en`, `fr`, `es`, `it`, `auto`)             |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "summary": "Granit ist ein magmatisches Gestein. Es ist hart, säurebeständig und ideal für Küchenarbeitsplatten.",
  "method": "extractive",
  "original_length": 150,
  "summary_length": 45,
  "reduction_percent": 70.0,
  "message": "Zusammenfassung erstellt (extractive). Reduziert von 150 auf 45 Wörter (70.0%)."
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "text ist erforderlich."
}
```

---

## 🧪 Beispiele

### 1. Extractive Summarization

**Input:**

```json
{
  "text": "Granit ist ein magmatisches Gestein. Es ist sehr hart und säurebeständig. Granit wird oft für Küchenarbeitsplatten verwendet. Marmor ist ein metamorphes Gestein. Marmor ist weicher und säureempfindlich. Marmor wird häufig für Böden und Wandverkleidungen genutzt.",
  "mode": "extractive",
  "ratio": 0.4
}
```

**Output:**

```json
{
  "success": true,
  "summary": "Granit ist ein magmatisches Gestein. Es ist sehr hart und säurebeständig. Marmor ist ein metamorphes Gestein. Marmor ist weicher und säureempfindlich.",
  "method": "extractive",
  "original_length": 30,
  "summary_length": 18,
  "reduction_percent": 40.0
}
```

### 2. Abstractive Summarization (mit transformers)

**Input:**

```json
{
  "text": "Langer Text hier...",
  "mode": "abstractive",
  "max_length": 80,
  "min_length": 20
}
```

### 3. Auto-Modus

**Input:**

```json
{
  "text": "Langer Text hier...",
  "mode": "auto"
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/summarizer/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Erweiterbarkeit

### Abstractive Modelle

Das Plugin kann mit verschiedenen Transformers-Modellen erweitert werden:

```python
# Für Englisch:
model_name = "google/pegasus-xsum"
# Für Deutsch:
model_name = "google/pegasus-multi_news"
# Für andere Sprachen:
model_name = "facebook/bart-large-cnn"
```

### Extractive Scoring

Die aktuelle Implementierung verwendet Wortfrequenz. Alternativen:

- **TF-IDF** – Gewichtet Wörter nach ihrer Seltenheit
- **TextRank** – Graph-basiertes Ranking von Sätzen
- **BERT** – Semantische Ähnlichkeit

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Fasse diesen Artikel für mich zusammen: ..."_
>
> **Elisa:** _"Zusammenfassung erstellt (extractive). Reduziert von 250 auf 75 Wörter (70%). Hier ist die Kurzfassung: ..."_

> **Nutzer:** _"Gib mir eine Kurzfassung der Kundenanfrage."_
>
> **Elisa:** _"Kurzfassung: Der Kunde sucht eine Granit-Arbeitsplatte in schwarz mit polierter Oberfläche und fragt nach einem Angebot."_

---

## 📚 Siehe auch

- [Hugging Face Transformers](https://huggingface.co/docs/transformers/index)
- [TextRank Algorithm](https://en.wikipedia.org/wiki/TextRank)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
