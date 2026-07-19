# 📄 Grammar Checker Plugin

**ID:** `grammar_checker`  
**Kategorie:** 🧠 NLP & Content  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Grammar Checker Plugin prüft Texte auf **Rechtschreibung, Grammatik und Stil** über die **LanguageTool API**. Es unterstützt:

- **Rechtschreibprüfung** – Tippfehler, falsche Schreibweisen
- **Grammatikprüfung** – Satzbau, Konjugation, Deklination
- **Stilprüfung** – Redundanz, Wortwahl, Verständlichkeit
- **Automatische Korrektur** – Vorschläge für Verbesserungen
- **Mehrere Sprachen** – Deutsch, Englisch, Französisch, Spanisch, etc.

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(rechtschreibung|grammatik|korrektur|sprache|prüfen|grammar|spell|check)\b
```

**Beispiele:**

- _"Prüfe den Text auf Rechtschreibfehler."_
- _"Ist dieser Satz grammatikalisch korrekt?"_
- _"Korrigiere meinen Text bitte."_

---

## ⚙️ Konfiguration

Das Plugin ist **sofort einsatzbereit** (kostenlose LanguageTool API). Es sind keine Umgebungsvariablen erforderlich.

### Alternative: Self-Hosted LanguageTool

Falls Sie LanguageTool selbst hosten möchten:

```env
LANGUAGETOOL_API_URL=http://localhost:8010/v2/check
```

---

## 📦 Input-Schema

```json
{
  "text": "Das is ein Testtext mit viele Fehlern.",
  "language": "de-DE",
  "mode": "all",
  "suggestions": true,
  "max_matches": 20
}
```

| Feld          | Typ     | Standard | Beschreibung                                                                                     |
| ------------- | ------- | -------- | ------------------------------------------------------------------------------------------------ |
| `text`        | string  | –        | Der zu prüfende Text (erforderlich)                                                              |
| `language`    | string  | `auto`   | `auto`, `de-DE`, `en-US`, `en-GB`, `fr-FR`, `es-ES`, `it-IT`, `pt-PT`, `nl-NL`, `pl-PL`, `ru-RU` |
| `mode`        | string  | `all`    | `all`, `spelling`, `grammar`, `style`                                                            |
| `suggestions` | boolean | `true`   | Korrekturvorschläge anzeigen                                                                     |
| `max_matches` | integer | `20`     | Maximale Anzahl angezeigter Fehler                                                               |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "language": "de-DE",
  "detected_language": "German (Germany)",
  "total_matches": 3,
  "message": "3 Fehler gefunden. Sprachversion: German (Germany)",
  "text": "Das is ein Testtext mit viele Fehlern.",
  "corrected_text": "Das ist ein Testtext mit vielen Fehlern.",
  "matches": [
    {
      "type": "Rechtschreibung",
      "message": "Möglicher Tippfehler: 'is'",
      "short_message": "Tippfehler",
      "category": "Rechtschreibung",
      "offset": 4,
      "length": 2,
      "context": "Das [is] ein Testtext mit viele Fehlern.",
      "replacements": ["ist", "isst"]
    },
    {
      "type": "Grammatik",
      "message": "Die Adjektivendung stimmt nicht.",
      "short_message": "Adjektivendung",
      "category": "Grammatik",
      "offset": 26,
      "length": 4,
      "context": "mit [viele] Fehlern.",
      "replacements": ["vielen"]
    }
  ]
}
```

---

## 🧪 Beispiele

### 1. Einfache Rechtschreibprüfung

**Input:**

```json
{
  "text": "Das is ein Testtext mit viele Fehlern.",
  "language": "de-DE"
}
```

**Output:** (wie oben)

### 2. Nur Grammatik prüfen

**Input:**

```json
{
  "text": "Ich gehe nach Hause und ich schlafe.",
  "language": "de-DE",
  "mode": "grammar"
}
```

**Output:** Gibt nur grammatikalische Fehler zurück.

### 3. Englischer Text

**Input:**

```json
{
  "text": "This is a test text with many errors.",
  "language": "en-US"
}
```

### 4. Stilprüfung

**Input:**

```json
{
  "text": "Very, very important matter.",
  "language": "en-US",
  "mode": "style"
}
```

**Output:** Stilistische Verbesserungen (z.B. "very, very" → "extremely").

---

## 📁 Datei-Struktur

```
packages/plugins/grammar_checker/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Zu viele Anfragen an LanguageTool"

**Lösung:** LanguageTool hat ein Limit von etwa 20 Anfragen pro Minute für die öffentliche API. Warte einen Moment und versuche es erneut.

### Fehler: "Text ist zu kurz"

**Lösung:** LanguageTool benötigt mindestens 3 Zeichen für eine sinnvolle Prüfung.

### Fehler: "Ungültige Sprache"

**Lösung:** Verwende einen der unterstützten Sprachcodes: `de-DE`, `en-US`, `en-GB`, `fr-FR`, `es-ES`, `it-IT`, `pt-PT`, `nl-NL`, `pl-PL`, `ru-RU`.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Prüfe diesen Text: 'Das is ein Testtext mit viele Fehlern.'"_
>
> **Elisa:** _"Ich habe 3 Fehler gefunden:_
>
> 1. _'is' sollte 'ist' sein (Rechtschreibung)._
> 2. _'viele' sollte 'vielen' sein (Grammatik)._
> 3. _..._
>    _Korrigierter Text: 'Das ist ein Testtext mit vielen Fehlern.'"_

---

## 📚 Siehe auch

- [LanguageTool API Dokumentation](https://languagetool.org/http-api/swagger-ui/#/default)
- [LanguageTool Public API](https://dev.languagetool.org/public-http-api)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
