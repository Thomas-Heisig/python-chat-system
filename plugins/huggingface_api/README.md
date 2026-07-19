# 📄 Hugging Face API Plugin

**ID:** `huggingface_api`  
**Kategorie:** 🔌 Externe APIs  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Hugging Face API Plugin ermöglicht die **Nutzung von über 100.000 Modellen** auf Hugging Face über die **Inference API**. Es unterstützt:

- **Textgenerierung** (z.B. Llama, Mistral, Phi)
- **Text-zu-Text** (Übersetzung, Zusammenfassung)
- **Embeddings** (Vektordarstellung von Texten)
- **Bildgenerierung** (Stable Diffusion)
- **Verschiedene NLP-Aufgaben**

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(huggingface|hf|inference|embedding|generation)\b
```

**Beispiele:**

- _"Nutze Hugging Face für Textgenerierung."_
- _"Generiere ein Embedding für diesen Text."_
- _"Verwende das Modell 'microsoft/phi-2'."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable              | Beschreibung                        | Erforderlich |
| --------------------- | ----------------------------------- | ------------ |
| `HUGGINGFACE_API_KEY` | Hugging Face API-Key (Access Token) | ✅           |

### Hugging Face API-Key erhalten

1. Registriere dich auf [huggingface.co](https://huggingface.co/join)
2. Gehe zu **Settings** → **Access Tokens**
3. Erstelle einen neuen Token (lesend + schreibend)
4. Setze den Token als `HUGGINGFACE_API_KEY` in der Umgebung

> **Hinweis:** Ohne API-Key ist die öffentliche Inference API auf Anfragen beschränkt.

---

## 📦 Input-Schema

```json
{
  "model": "microsoft/phi-2",
  "prompt": "Erkläre, was Granit ist.",
  "task": "text-generation",
  "parameters": {
    "temperature": 0.7,
    "max_new_tokens": 200,
    "top_p": 0.9
  }
}
```

| Feld          | Typ          | Standard          | Beschreibung                                           |
| ------------- | ------------ | ----------------- | ------------------------------------------------------ |
| `model`       | string       | `microsoft/phi-2` | Hugging Face Modell-ID                                 |
| `prompt`      | string       | –                 | Eingabetext (erforderlich, außer bei bestimmten Tasks) |
| `input`       | string/array | –                 | Alternativer Input (für Embeddings, Similarity)        |
| `task`        | string       | `text-generation` | Aufgabentyp (siehe Liste)                              |
| `parameters`  | object       | –                 | Zusätzliche Parameter (temperatur, max_tokens, etc.)   |
| `source_lang` | string       | `en`              | Quellsprache (für Übersetzung)                         |
| `target_lang` | string       | `de`              | Zielsprache (für Übersetzung)                          |

### Unterstützte Tasks

| Task                   | Beschreibung                                     |
| ---------------------- | ------------------------------------------------ |
| `text-generation`      | Textgenerierung (z.B. Chat, Storytelling)        |
| `text2text-generation` | Text-zu-Text (z.B. Übersetzung, Zusammenfassung) |
| `summarization`        | Zusammenfassung                                  |
| `translation`          | Übersetzung                                      |
| `fill-mask`            | Maskierte Tokens vorhersagen                     |
| `feature-extraction`   | Embeddings erzeugen                              |
| `sentence-similarity`  | Satzähnlichkeit berechnen                        |
| `image-generation`     | Bildgenerierung (Stable Diffusion)               |
| `text-to-image`        | Text-zu-Bild                                     |
| `image-to-text`        | Bild-zu-Text (OCR, Beschreibung)                 |
| `object-detection`     | Objekterkennung in Bildern                       |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "task": "text-generation",
  "model": "microsoft/phi-2",
  "generated_text": "Granit ist ein magmatisches Gestein...",
  "result": [
    {
      "generated_text": "Granit ist ein magmatisches Gestein..."
    }
  ]
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Hugging Face API-Key nicht konfiguriert."
}
```

---

## 🧪 Beispiele

### 1. Textgenerierung (Phi-2)

**Input:**

```json
{
  "model": "microsoft/phi-2",
  "prompt": "Erkläre, was Granit ist.",
  "task": "text-generation",
  "parameters": {
    "temperature": 0.7,
    "max_new_tokens": 200
  }
}
```

**Output:**

```json
{
  "success": true,
  "generated_text": "Granit ist ein magmatisches Tiefengestein, das hauptsächlich aus Quarz, Feldspat und Glimmer besteht..."
}
```

### 2. Embeddings (feature-extraction)

**Input:**

```json
{
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "input": "Granit ist ein magmatisches Gestein.",
  "task": "feature-extraction"
}
```

**Output:**

```json
{
  "success": true,
  "result": [[0.123, 0.456, ...]]  // Vektor-Embedding
}
```

### 3. Übersetzung

**Input:**

```json
{
  "model": "Helsinki-NLP/opus-mt-en-de",
  "prompt": "Granite is a natural stone.",
  "task": "translation",
  "source_lang": "en",
  "target_lang": "de"
}
```

### 4. Zusammenfassung

**Input:**

```json
{
  "model": "facebook/bart-large-cnn",
  "prompt": "Langer Text hier...",
  "task": "summarization",
  "parameters": {
    "max_length": 150,
    "min_length": 30
  }
}
```

### 5. Bildgenerierung (SDXL)

**Input:**

```json
{
  "model": "stabilityai/stable-diffusion-xl-base-1.0",
  "prompt": "A beautiful granite kitchen countertop.",
  "task": "image-generation"
}
```

**Output:** Bild-Daten (Base64-kodiert)

---

## 📁 Datei-Struktur

```
packages/plugins/huggingface_api/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key"

**Lösung:** Prüfe `HUGGINGFACE_API_KEY` in der Umgebung. Stelle sicher, dass der Token gültig und nicht abgelaufen ist.

### Fehler: "Modell wird gerade geladen"

**Lösung:** Hugging Face lädt das Modell bei der ersten Anfrage. Warte einige Sekunden und versuche es erneut.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Die kostenlose Inference API hat ein Limit von etwa 30 Anfragen pro Minute. Warte einen Moment oder upgrade auf einen bezahlten Plan.

### Fehler: "Modell nicht gefunden"

**Lösung:** Prüfe, ob die Modell-ID korrekt ist und das Modell öffentlich zugänglich ist.

---

## 📊 Nutzungslimits (Hugging Face Inference API)

| Tier           | Anfragen/Minute   | Preis       |
| -------------- | ----------------- | ----------- |
| **Kostenlos**  | ~30               | 0 €         |
| **Pro**        | ~500              | $9/Monat    |
| **Enterprise** | Benutzerdefiniert | Individuell |

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Nutze Hugging Face Phi-2 für eine Erklärung von Granit."_
>
> **Elisa:** _"Granit ist ein magmatisches Tiefengestein, das hauptsächlich aus Quarz, Feldspat und Glimmer besteht..."_

> **Nutzer:** _"Generiere ein Embedding für diesen Text: 'Granit ist hart.'"_
>
> **Elisa:** _"Embedding erfolgreich erstellt (384 Dimensionen)."_

---

## 📚 Siehe auch

- [Hugging Face Models](https://huggingface.co/models)
- [Hugging Face Inference API Dokumentation](https://huggingface.co/docs/api-inference/index)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
