# 📄 Tone Rewriter Plugin

**ID:** `tone_rewriter`  
**Kategorie:** 🧠 NLP & Content  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Tone Rewriter Plugin schreibt Texte in **verschiedenen Stimmungen/Tönen** um – ideal für:

- Anpassung von Kundenkommunikation (professionell, freundlich, überzeugend)
- Umformulierung von Angeboten und Anfragen
- Anpassung an verschiedene Zielgruppen

**Unterstützte Töne:**

| Ton            | Beschreibung                         | Beispiele                                |
| -------------- | ------------------------------------ | ---------------------------------------- |
| `professional` | Professionell, sachlich, distanziert | Firmenkommunikation, offizielle Anfragen |
| `friendly`     | Freundlich, persönlich, warm         | Kundenkommunikation, Smalltalk           |
| `persuasive`   | Überzeugend, werblich, aktiv         | Angebote, Verkaufstexte                  |
| `formal`       | Sehr formell, höflich                | Offizielle Schreiben, Behörden           |
| `casual`       | Locker, informell, persönlich        | Chat, soziale Medien                     |
| `enthusiastic` | Begeistert, motiviert, dynamisch     | Projekte, Präsentationen                 |
| `empathetic`   | Einfühlsam, verständnisvoll          | Beschwerden, schwierige Themen           |
| `concise`      | Knapp, präzise, auf den Punkt        | Kurzmitteilungen, Zusammenfassungen      |
| `detailed`     | Ausführlich, detailliert             | Berichte, Erklärungen                    |
| `humorous`     | Witzig, unterhaltsam, locker         | Social Media, Team-Kommunikation         |
| `neutral`      | Neutral, sachlich                    | Fakten, Informationen                    |

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(ton|stil|umschreiben|neu schreiben|freundlich|professionell|sachlich|formell|locker)\b
```

**Beispiele:**

- _"Schreibe diesen Text in einem freundlichen Ton."_
- _"Kannst du das professioneller formulieren?"_
- _"Mach den Text etwas lockerer."_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit** – es sind keine Umgebungsvariablen erforderlich.

---

## 📦 Input-Schema

```json
{
  "text": "Ihre Anfrage wurde erhalten. Wir werden uns in Kürze bei Ihnen melden.",
  "tone": "friendly",
  "target_audience": "customer",
  "preserve_keywords": true,
  "language": "auto"
}
```

| Feld                | Typ     | Standard       | Beschreibung                                                                                                                             |
| ------------------- | ------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `text`              | string  | –              | Der zu bearbeitende Text (erforderlich)                                                                                                  |
| `tone`              | string  | `professional` | `professional`, `friendly`, `persuasive`, `formal`, `casual`, `enthusiastic`, `empathetic`, `concise`, `detailed`, `humorous`, `neutral` |
| `target_audience`   | string  | `general`      | `general`, `expert`, `customer`, `partner`, `internal`                                                                                   |
| `preserve_keywords` | boolean | `true`         | Fachspezifische Begriffe beibehalten                                                                                                     |
| `language`          | string  | `auto`         | `de`, `en`, `auto`                                                                                                                       |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "original": "Ihre Anfrage wurde erhalten. Wir werden uns in Kürze bei Ihnen melden.",
  "rewritten": "Hallo! Deine Anfrage ist bei uns eingegangen. Wir melden uns gleich bei dir! 😊",
  "tone": "friendly",
  "target_audience": "customer",
  "changes": [
    "'Anfrage' → 'Anliegen'",
    "'erhalten' → 'bekommen'",
    "'melden' → 'gleich melden'",
    "Emoji hinzugefügt"
  ],
  "language": "de",
  "message": "Text erfolgreich in den Ton 'friendly' umgeschrieben. 4 Änderungen vorgenommen."
}
```

---

## 🧪 Beispiele

### 1. Professionell → Freundlich

**Input:**

```json
{
  "text": "Ihre Anfrage wurde erhalten. Wir werden uns in Kürze bei Ihnen melden.",
  "tone": "friendly"
}
```

**Output:**

```json
{
  "rewritten": "Hallo! Deine Anfrage ist bei uns eingegangen. Wir melden uns gleich bei dir! 😊",
  "tone": "friendly"
}
```

### 2. Freundlich → Formell

**Input:**

```json
{
  "text": "Hallo! Deine Anfrage ist bei uns eingegangen. Wir melden uns gleich bei dir! 😊",
  "tone": "formal"
}
```

**Output:**

```json
{
  "rewritten": "Ihre Anfrage wurde erhalten. Wir werden uns zeitnah bei Ihnen melden.",
  "tone": "formal"
}
```

### 3. Neutral → Überzeugend (Persuasive)

**Input:**

```json
{
  "text": "Wir haben hochwertigen Granit im Angebot.",
  "tone": "persuasive"
}
```

**Output:**

```json
{
  "rewritten": "Profitieren Sie von unserem exklusiven Granit-Angebot! Überzeugen Sie sich selbst von der hohen Qualität.",
  "tone": "persuasive"
}
```

### 4. Professionell → Casual

**Input:**

```json
{
  "text": "Vielen Dank für Ihre Anfrage. Wir werden die Unterlagen prüfen und uns anschließend mit Ihnen in Verbindung setzen.",
  "tone": "casual"
}
```

**Output:**

```json
{
  "rewritten": "Hey! Danke für deine Anfrage. Wir schauen uns die Unterlagen an und melden uns dann bei dir! 😉",
  "tone": "casual"
}
```

### 5. Kurz und knapp (Concise)

**Input:**

```json
{
  "text": "Ich möchte Sie bitten, die Anfrage zu prüfen und mir dann eine Rückmeldung zu geben.",
  "tone": "concise"
}
```

**Output:**

```json
{
  "rewritten": "Bitte Anfrage prüfen. Rückmeldung folgt.",
  "tone": "concise"
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/tone_rewriter/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Erweiterbarkeit

### Neue Töne hinzufügen

```python
_TONE_RULES["neuer_ton"] = {
    "formal_level": 0.6,
    "personal_pronouns": True,
    "contractions": True,
    "emoji": False,
    "exclamation_limit": 0,
    "word_style": "custom",
    "example": "Beispieltext im neuen Ton.",
}
```

### Neue Wort-Ersetzungen

```python
_WORD_REPLACEMENTS["de"]["custom"] = {
    "altes_wort": "neues_wort",
    # ...
}
```

### Neue Emojis

```python
_EMOJIS["custom"] = ["🎯", "⭐", "🔥"]
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Schreibe diesen Text in einem freundlichen Ton: 'Ihre Anfrage wurde erhalten. Wir werden uns in Kürze bei Ihnen melden.'"_
>
> **Elisa:** _"Hier ist der Text im freundlichen Ton: 'Hallo! Deine Anfrage ist bei uns eingegangen. Wir melden uns gleich bei dir! 😊'"_

---

## 📚 Siehe auch

- [Text Analyzer Plugin](../text_analyzer)
- [Grammar Checker Plugin](../grammar_checker)
- [Summarizer Plugin](../summarizer)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
