# 📄 WhatsApp Plugin

**ID:** `whatsapp`  
**Kategorie:** 📱 Social & Communication  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das WhatsApp Plugin ermöglicht das **Senden von WhatsApp-Nachrichten** über die **Twilio WhatsApp Business API**. Es unterstützt:

- Textnachrichten
- Medienanhänge (Bilder, Dokumente, Videos) über URL
- Status-Tracking der Nachrichten
- harmonisierte Eingaben aus fachuebergreifenden Payloads (`delivery`, `content`)
- kanalbewusstes Verhalten (`communication_channel=letter|email` wird sauber uebersprungen)
- optionalen Vorabcheck ohne Versand (`validate_only=true`)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(whatsapp|wa|nachricht|sms|message|send|benachrichtigung)\b
```

**Beispiele:**

- _"Sende eine WhatsApp-Nachricht an +491701234567."_
- _"Schicke ein Angebot per WhatsApp."_
- _"Benachrichtige den Kunden via WhatsApp."_

---

## ⚙️ Konfiguration

### Twilio WhatsApp Business API einrichten

1. Registriere dich bei [Twilio](https://www.twilio.com/)
2. Aktiviere die **WhatsApp Business API** in der Twilio Console
3. Erhalte eine **WhatsApp-fähige Telefonnummer** (oder nutze die Testnummer)
4. Erstelle eine neue **Messaging Service** oder nutze die Standard-Konfiguration

### Umgebungsvariablen

| Variable               | Beschreibung                                                   | Erforderlich |
| ---------------------- | -------------------------------------------------------------- | ------------ |
| `TWILIO_ACCOUNT_SID`   | Twilio Account SID                                             | ✅           |
| `TWILIO_AUTH_TOKEN`    | Twilio Auth Token                                              | ✅           |
| `TWILIO_WHATSAPP_FROM` | WhatsApp-fähige Absender-Nummer (z.B. `+14155238886` für Test) | ✅           |

---

## 📦 Input-Schema

```json
{
  "to": "+491701234567",
  "message": "Ihr Angebot für die Granit-Arbeitsplatte ist fertig. Hier ist der Link: ...",
  "media_url": "https://example.com/angebot.pdf",
  "from": "+14155238886",
  "communication_channel": "whatsapp",
  "validate_only": false
}
```

| Feld                      | Typ     | Beschreibung                                                     |
| ------------------------- | ------  | ---------------------------------------------------------------- |
| `to`                      | string  | Empfänger-Telefonnummer im internationalen Format (erforderlich) |
| `message`                 | string  | Nachrichtentext (max. 1600 Zeichen, erforderlich)                |
| `media_url`               | string  | URL zu einem Bild, Dokument oder Video (optional)                |
| `from`                    | string  | Absender-Nummer (überschreibt ENV, optional)                     |
| `communication_channel`   | string  | `whatsapp`, `both`, `letter`, `email`                            |
| `validate_only`           | boolean | Nur validieren, nicht senden                                     |
| `delivery`/`content`      | object  | Kompatible Eingabestruktur aus anderen Kommunikations-Plugins    |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "message_sid": "SM1234567890abcdef"
  "status": "sent",
  "to": "+491701234567",
  "message": "WhatsApp-Nachricht an +491701234567 gesendet. Status: sent",
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
  "error": "Twilio nicht konfiguriert. Setze TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN und TWILIO_WHATSAPP_FROM in der Umgebung.",
  "validation": {
    "status": "needs_review",
    "errors": ["..."],
    "warnings": [],
    "missing_information": ["..."]
  }
}
```

### Harmonisiertes Envelope-Beispiel

```json
{
  "delivery": {
    "channel": "both",
    "recipient": "+491701234567"
  },
  "content": {
    "email_text": "Guten Tag, Ihr Auftrag ist jetzt versandbereit."
  },
  "validate_only": true
}
```

---

## 🧪 Beispiele

### 1. Textnachricht senden

**Input:**

```json
{
  "to": "+491701234567",
  "message": "Hallo! Hier ist Elisa von Heishg Naturstein. Ihr Angebot ist fertig."
}
```

**Output:**

```json
{
  "success": true,
  "message_sid": "SM1234567890abcdef",
  "status": "sent",
  "to": "+491701234567",
  "message": "WhatsApp-Nachricht an +491701234567 gesendet. Status: sent"
}
```

### 2. Mit Medienanhang

**Input:**

```json
{
  "to": "+491701234567",
  "message": "Ihr Musterpaket:",
  "media_url": "https://example.com/musterkatalog.pdf"
}
```

### 3. Mit eigenem Absender

**Input:**

```json
{
  "to": "+491701234567",
  "message": "Testnachricht",
  "from": "+14155238886"
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/whatsapp/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Ungültige Twilio-Zugangsdaten"

**Lösung:** Prüfe `TWILIO_ACCOUNT_SID` und `TWILIO_AUTH_TOKEN` in der Umgebung. Diese findest du in der Twilio Console.

### Fehler: "Absender-Nummer nicht gefunden"

**Lösung:** Prüfe `TWILIO_WHATSAPP_FROM`. Die Nummer muss WhatsApp-fähig sein und in der Twilio Console aktiviert sein.

### Fehler: "Rate-Limit überschritten"

**Lösung:** Twilio hat ein Rate-Limit von 1 Nachricht pro Sekunde. Warte etwas und versuche es erneut.

---

## 💰 Preise (Twilio WhatsApp Business API)

| Nachrichtentyp             | Preis (USD)     |
| -------------------------- | --------------- |
| **Text** (pro Nachricht)   | $0.0050         |
| **Media** (pro MB)         | $0.0050         |
| **Conversation** (pro 24h) | $0.0025–$0.0150 |

> **Hinweis:** WhatsApp Business API verwendet ein Conversation-basiertes Preismodell. Prüfe die aktuellen Preise auf der [Twilio Pricing Seite](https://www.twilio.com/whatsapp/pricing).

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Sende eine WhatsApp-Nachricht an +491701234567 mit dem Angebot."_
>
> **Elisa:** _"✅ WhatsApp-Nachricht an +491701234567 gesendet. Status: sent. Nachrichten-ID: SM1234567890abcdef."_

> **Nutzer:** _"Schicke das Angebot-PDF per WhatsApp."_
>
> **Elisa:** _"✅ WhatsApp-Nachricht mit Anhang wurde gesendet."_

---

## 📚 Siehe auch

- [Twilio WhatsApp API Dokumentation](https://www.twilio.com/docs/whatsapp)
- [Twilio Console](https://console.twilio.com/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
