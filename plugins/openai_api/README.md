# 📄 OpenAI API Plugin

**ID:** `openai_api`  
**Kategorie:** 🔌 Externe APIs  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das OpenAI API Plugin ermöglicht die **Nutzung der OpenAI Cloud-API** für:

- **Chat** – GPT-4, GPT-3.5, etc.
- **Embeddings** – Text-Embedding-3, Ada-002
- **Bildgenerierung** – DALL-E 3, DALL-E 2
- **Transkription** – Whisper (geplant)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(openai|gpt|chatgpt|gpt-4|gpt-3.5|embedding|whisper|dall-e)\b
```

**Beispiele:**

- _"Nutze GPT-4 für diese Frage."_
- _"Generiere ein Embedding für diesen Text."_
- _"OpenAI Bildgenerierung mit DALL-E."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable         | Beschreibung   | Erforderlich |
| ---------------- | -------------- | ------------ |
| `OPENAI_API_KEY` | OpenAI API-Key | ✅           |

### OpenAI API-Key erhalten

1. Registriere dich auf [platform.openai.com](https://platform.openai.com/)
2. Erstelle einen API-Key unter **API Keys**
3. Setze den Key als `OPENAI_API_KEY` in der Umgebung

---

## 📦 Input-Schema

### Chat (Standard)

```json
{
  "task": "chat",
  "prompt": "Erkläre Granit.",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": true,
  "system_prompt": "Du bist ein Naturstein-Experte."
}
```

### Embedding

```json
{
  "task": "embedding",
  "prompt": "Granit ist ein magmatisches Gestein.",
  "embedding_model": "text-embedding-3-small"
}
```

### Bildgenerierung (DALL-E)

```json
{
  "task": "image",
  "image_prompt": "Eine elegante Granit-Küchenarbeitsplatte.",
  "image_size": "1024x1024",
  "image_quality": "standard"
}
```

---

## 📤 Output-Schema

### Chat

```json
{
  "success": true,
  "content": "Granit ist ein magmatisches Gestein...",
  "model": "gpt-4o-mini",
  "tokens_input": 15,
  "tokens_output": 120,
  "tokens_total": 135,
  "cost": 0.00009
}
```

### Embedding

```json
{
  "success": true,
  "embedding": [0.123, 0.456, ...],
  "model": "text-embedding-3-small",
  "tokens_input": 8,
  "tokens_total": 8,
  "cost": 0.00000016
}
```

### Bildgenerierung

```json
{
  "success": true,
  "image_url": "https://...",
  "model": "dall-e-3",
  "cost": 0.04
}
```

---

## 🧪 Beispiele

### 1. Chat (GPT-4o-mini)

**Input:**

```json
{
  "prompt": "Erkläre den Unterschied zwischen Granit und Marmor.",
  "model": "gpt-4o-mini"
}
```

### 2. Embedding

**Input:**

```json
{
  "task": "embedding",
  "prompt": "Granit ist ein magmatisches Gestein."
}
```

### 3. Bildgenerierung (DALL-E 3)

**Input:**

```json
{
  "task": "image",
  "image_prompt": "Eine elegante Granit-Küchenarbeitsplatte in einer modernen Küche.",
  "image_size": "1792x1024",
  "image_quality": "hd"
}
```

### 4. Mit System-Prompt

**Input:**

```json
{
  "prompt": "Was ist die beste Arbeitsplatte für eine Küche?",
  "system_prompt": "Du bist ein Naturstein-Experte und antwortest auf Deutsch.",
  "temperature": 0.3
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/openai_api/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📊 Kosten (OpenAI)

| Modell                     | Input (pro 1k Tokens) | Output (pro 1k Tokens) |
| -------------------------- | --------------------- | ---------------------- |
| **GPT-4**                  | $0.030                | $0.060                 |
| **GPT-4-turbo**            | $0.010                | $0.030                 |
| **GPT-4o**                 | $0.005                | $0.015                 |
| **GPT-4o-mini**            | $0.00015              | $0.0006                |
| **GPT-3.5-turbo**          | $0.0005               | $0.0015                |
| **text-embedding-3-small** | $0.00002              | –                      |
| **text-embedding-3-large** | $0.00013              | –                      |
| **DALL-E 3 (1024x1024)**   | –                     | $0.04 per Bild         |
| **DALL-E 3 (1792x1024)**   | –                     | $0.08 per Bild         |

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key"

**Lösung:** Prüfe `OPENAI_API_KEY` in der Umgebung. Stelle sicher, dass der Key gültig und nicht abgelaufen ist.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Die kostenlosen/bezahlten Pläne haben Rate-Limits. Warte einige Sekunden oder upgrade deinen Plan.

### Fehler: "Modell nicht gefunden"

**Lösung:** Prüfe, ob das Modell für deinen Account verfügbar ist (z.B. GPT-4 für bestimmte Accounts).

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Nutze GPT-4 für eine Erklärung von Granit."_
>
> **Elisa:** _"Granit ist ein magmatisches Tiefengestein, das hauptsächlich aus Quarz, Feldspat und Glimmer besteht..."_

> **Nutzer:** _"Generiere ein Bild für eine Granit-Küchenarbeitsplatte."_
>
> **Elisa:** _"Bild wurde generiert: [image_url] (Kosten: $0.04)"_

---

## 📚 Siehe auch

- [OpenAI API Dokumentation](https://platform.openai.com/docs)
- [OpenAI Preise](https://openai.com/pricing)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
