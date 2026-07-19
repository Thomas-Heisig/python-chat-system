# 📄 Replicate API Plugin

**ID:** `replicate_api`  
**Kategorie:** 🔌 Externe APIs  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Replicate API Plugin ermöglicht die **Nutzung von über 50.000 KI-Modellen** auf der Replicate Cloud-Plattform:

- **Bildgenerierung** – Stable Diffusion, SDXL, Flux, etc.
- **Textgenerierung** – Llama, Mistral, etc.
- **Audio** – Bark, MusicGen, etc.
- **Custom** – Beliebige Modelle aus der Replicate-Bibliothek

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(replicate|sdxl|stable diffusion|bild generieren|image|text-to-image)\b
```

**Beispiele:**

- _"Generiere ein Bild mit Replicate."_
- _"Nutze SDXL für eine Bildgenerierung."_
- _"Replicate API für Textgenerierung."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable            | Beschreibung      | Erforderlich |
| ------------------- | ----------------- | ------------ |
| `REPLICATE_API_KEY` | Replicate API-Key | ✅           |

### Replicate API-Key erhalten

1. Registriere dich auf [replicate.com](https://replicate.com/)
2. Gehe zu **Account** → **API Tokens**
3. Erstelle einen neuen API-Key
4. Setze den Key als `REPLICATE_API_KEY` in der Umgebung.

---

## 📦 Input-Schema

### Bildgenerierung (Standard)

```json
{
  "task": "image",
  "prompt": "A beautiful granite kitchen countertop, photorealistic",
  "model": "stability-ai/sdxl",
  "parameters": {
    "width": 1024,
    "height": 1024,
    "num_outputs": 1,
    "num_inference_steps": 30,
    "guidance_scale": 7.5
  },
  "wait": true,
  "timeout": 120
}
```

### Textgenerierung

```json
{
  "task": "text",
  "prompt": "Explain the difference between granite and marble.",
  "model": "meta/llama-2-70b-chat",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 512
  }
}
```

### Custom-Modell

```json
{
  "task": "custom",
  "model": "owner/model",
  "version": "version-hash",
  "prompt": "Input text"
}
```

---

## 📤 Output-Schema

```json
{
  "success": true,
  "prediction_id": "abc-123-def",
  "model": "stability-ai/sdxl",
  "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
  "status": "succeeded",
  "output": ["https://replicate.delivery/.../image.png"],
  "urls": {
    "get": "https://api.replicate.com/v1/predictions/abc-123-def",
    "cancel": "https://api.replicate.com/v1/predictions/abc-123-def/cancel"
  },
  "message": "Prediction abc-123-def erfolgreich abgeschlossen."
}
```

---

## 🧪 Beispiele

### 1. SDXL-Bildgenerierung

**Input:**

```json
{
  "task": "image",
  "prompt": "A modern kitchen with a black granite island, photorealistic, 8k",
  "parameters": {
    "width": 1024,
    "height": 768,
    "num_outputs": 2
  }
}
```

**Output:** Zwei Bild-URLs

### 2. Llama 2 Textgenerierung

**Input:**

```json
{
  "task": "text",
  "prompt": "What are the advantages of quartzite kitchen countertops?",
  "model": "meta/llama-2-70b-chat",
  "parameters": {
    "temperature": 0.3,
    "max_tokens": 300
  }
}
```

### 3. Nur Prediction-ID (asynchron)

**Input:**

```json
{
  "task": "image",
  "prompt": "A granite fireplace surround",
  "wait": false
}
```

**Output:** Prediction-ID zur späteren Abfrage.

---

## 📁 Datei-Struktur

```text
packages/plugins/replicate_api/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📊 Kosten (Replicate)

| Modell           | Preis (pro Bild/Anfrage)  |
| ---------------- | ------------------------- |
| **SDXL**         | ~$0.0023 pro Bild         |
| **Llama 2 70B**  | ~$0.00095 pro 1000 Tokens |
| **Bark (Audio)** | ~$0.0015 pro Sekunde      |

> **Hinweis:** Die Kosten variieren je nach Modell und Größe. Prüfe die aktuellen Preise auf [replicate.com/pricing](https://replicate.com/pricing).

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültiger API-Key"

**Lösung:** Prüfe `REPLICATE_API_KEY` in der Umgebung. Der Key muss korrekt und aktiv sein.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Replicate hat ein Rate-Limit von etwa 1000 Anfragen pro Tag für den kostenlosen Tier. Warte oder upgrade.

### Fehler: "Modell nicht gefunden"

**Lösung:** Prüfe, ob der Modell-Identifier korrekt ist. Für `stability-ai/sdxl` ist der korrekte Identifier `stability-ai/sdxl`.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Generiere ein Bild für eine Granit-Küchenarbeitsplatte mit Replicate."_
>
> **Elisa:** _"✅ Bild wurde generiert! [Bild-URL]. Kosten: ca. $0.0023."_

> **Nutzer:** _"Erstelle eine detaillierte Analyse von Granit mit Llama 2."_
>
> **Elisa:** _"Granit ist ein magmatisches Tiefengestein..."_

---

## 📚 Siehe auch

- [Replicate API Dokumentation](https://replicate.com/docs/reference/http)
- [Replicate Models](https://replicate.com/explore)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
