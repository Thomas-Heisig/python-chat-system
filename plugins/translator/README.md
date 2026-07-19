# 📄 Translator Plugin

**ID:** `translator`  
**Kategorie:** 🧠 NLP & Content  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Translator Plugin übersetzt Texte in verschiedene Sprachen. Es unterstützt drei Übersetzungsdienste:

- **LibreTranslate** – Kostenlos, keine API-Key erforderlich (Standard)
- **DeepL** – Höhere Qualität, benötigt API-Key
- **Google Translate** – Breite Sprachunterstützung, benötigt API-Key

Zusaetzlich unterstuetzt das Plugin harmonisierte fachuebergreifende Eingaben (`content`) und einen reinen Vorabcheck via `validate_only=true`.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(übersetze|translate|translation|Übersetzung)\b
```

**Beispiele:**

- _"Übersetze 'Hallo' nach Englisch."_
- _"Translate this text to German."_
- _"Kannst du das auf Französisch übersetzen?"_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable                   | Beschreibung             | Erforderlich        |
| -------------------------- | ------------------------ | ------------------- |
| `DEEPL_API_KEY`            | DeepL API-Key            | ❌ (nur für DeepL)  |
| `GOOGLE_TRANSLATE_API_KEY` | Google Translate API-Key | ❌ (nur für Google) |

---

## 📦 Input-Schema

```json
{
  "text": "Hallo, wie geht es dir?",
  "target_lang": "en",
  "source_lang": "auto",
  "service": "libretranslate",
  "api_key": "optional",
  "preserve_formatting": true,
  "communication_channel": "translator",
  "validate_only": false,
  "content": {
    "email_text": "Hallo, wie geht es dir?",
    "letter_text": "Guten Tag, hiermit bestaetigen wir Ihren Auftrag."
  }
}
```

| Feld                    | Typ     | Beschreibung                                                                                                |
| ----------------------- | ------- | ----------------------------------------------------------------------------------------------------------- |
| `text`                  | string  | Der zu übersetzende Text (erforderlich)                                                                     |
| `target_lang`           | string  | Zielsprache (z.B. `en`, `de`, `fr`, `es`, `it`, `ja`, `zh`, für DeepL auch `EN-US`, `EN-GB`) (erforderlich) |
| `source_lang`           | string  | Quellsprache (Standard: `auto`)                                                                             |
| `service`               | string  | `libretranslate` (Standard), `deepl`, `google`                                                              |
| `api_key`               | string  | API-Key für den Dienst (optional, überschreibt ENV)                                                         |
| `preserve_formatting`   | boolean | HTML-Formatierung beibehalten (nur DeepL)                                                                   |
| `communication_channel` | string  | Optionaler Kontext (`translator`, `letter`, `email`, `both`, `whatsapp`)                                    |
| `validate_only`         | boolean | Nur validieren, keine Uebersetzung ausfuehren                                                               |
| `content`               | object  | Kompatible Textfelder (`message`, `email_text`, `letter_text`, optional `target_lang`)                      |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "translated_text": "Hello, how are you?",
  "detected_source_lang": "de",
  "service_used": "libretranslate",
  "message": "Text erfolgreich von auto nach en uebersetzt (via libretranslate).",
  "validation": {
    "status": "ready",
    "errors": [],
    "warnings": [],
    "missing_information": []
  }
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "DeepL API-Key fehlt.",
  "validation": {
    "status": "needs_review",
    "errors": ["..."],
    "warnings": [],
    "missing_information": ["..."]
  }
}
```

### Validate-only Beispiel

```json
{
  "content": {
    "email_text": "Bitte senden Sie den Termin in Englisch.",
    "target_lang": "en"
  },
  "validate_only": true
}
```

---

## 🧪 Beispiele

### 1. Deutsche → Englisch (LibreTranslate)

**Input:**

```json
{
  "text": "Hallo, wie geht es dir?",
  "target_lang": "en"
}
```

**Output:**

```json
{
  "translated_text": "Hello, how are you?"
}
```

### 2. Englisch → Deutsch (DeepL)

**Input:**

```json
{
  "text": "Hello, how are you?",
  "target_lang": "DE",
  "service": "deepl"
}
```

**Voraussetzung:** `DEEPL_API_KEY` gesetzt.

### 3. Französisch → Englisch (Google)

**Input:**

```json
{
  "text": "Bonjour, comment allez-vous?",
  "target_lang": "en",
  "service": "google"
}
```

**Voraussetzung:** `GOOGLE_TRANSLATE_API_KEY` gesetzt.

---

## 📁 Datei-Struktur

```text
packages/plugins/translator/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Erweiterbarkeit

Weitere Übersetzungsdienste können leicht hinzugefügt werden, indem neue `_translate_*`-Methoden implementiert werden.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Übersetze 'Nero Assoluto ist ein schwarzer Granit' nach Englisch."_
>
> **Elisa:** _"Übersetzung (libretranslate): 'Nero Assoluto is a black granite.'"_

> **Nutzer:** _"DeepL Übersetzung von 'Ich möchte ein Angebot' ins Englische."_
>
> **Elisa:** _"Übersetzung (DeepL): 'I would like a quote.'"_

---

## 📚 Siehe auch

- [DeepL API Dokumentation](https://www.deepl.com/docs-api)
- [Google Translate API](https://cloud.google.com/translate/docs)
- [LibreTranslate](https://libretranslate.com/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
