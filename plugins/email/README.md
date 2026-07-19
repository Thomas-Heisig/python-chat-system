# 📧 E-Mail Plugin

**ID:** `email`  
**Kategorie:** 📱 Social & Communication  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das E-Mail Plugin ermöglicht das **Senden von E-Mails** über zwei Provider:

- **SMTP** – Universeller E-Mail-Versand (Gmail, Outlook, eigener Server)
- **SendGrid** – Cloud-basierter E-Mail-Versand (mit API-Key)

Es unterstützt:

- HTML-E-Mails
- CC / BCC
- Anhänge (Base64-kodiert)
- Retry-Logik (exponentieller Backoff)
- harmonisierte Nutzdaten aus `business_letter` (`email`, `delivery`, `content`)
- kanalbewusstes Verhalten (`communication_channel=letter` wird bewusst uebersprungen)
- optionalen Vorabcheck ohne Versand (`validate_only=true`)

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(email|mail|schreiben|anfrage|versenden|nachricht)\b
```

**Beispiele:**

- _"Sende eine E-Mail an <max@mustermann.de>."_
- _"Schreibe eine Anfrage an den Vertrieb."_
- _"Versende die Angebots-PDF per E-Mail."_

---

## ⚙️ Konfiguration

### SMTP (empfohlen)

| Variable       | Beschreibung                        | Erforderlich |
| -------------- | ----------------------------------- | ------------ |
| `SMTP_HOST`    | SMTP-Server (z.B. `smtp.gmail.com`) | ✅           |
| `SMTP_PORT`    | SMTP-Port (z.B. `587`)              | ✅           |
| `SMTP_USER`    | SMTP-Benutzername                   | ✅           |
| `SMTP_PASS`    | SMTP-Passwort / App-Passwort        | ✅           |
| `SENDER_EMAIL` | Absender-E-Mail-Adresse             | ✅           |

### SendGrid (alternativ)

| Variable           | Beschreibung            | Erforderlich |
| ------------------ | ----------------------- | ------------ |
| `SENDGRID_API_KEY` | SendGrid API-Key        | ✅           |
| `SENDER_EMAIL`     | Absender-E-Mail-Adresse | ✅           |

### Allgemein

| Variable            | Beschreibung                               | Standard |
| ------------------- | ------------------------------------------ | -------- |
| `EMAIL_MAX_RETRIES` | Maximale Anzahl von Wiederholungsversuchen | `3`      |
| `EMAIL_RETRY_DELAY` | Verzögerung zwischen Versuchen (Sekunden)  | `2`      |

---

## 📦 Input-Schema

```json
{
  "to": ["max@mustermann.de"],
  "subject": "Angebot für Küchenarbeitsplatte",
  "body": "Sehr geehrter Herr Mustermann,\n\nhier ist Ihr Angebot...",
  "html_body": "<h1>Angebot</h1><p>Hier ist Ihr Angebot...</p>",
  "cc": ["vertrieb@heishg-naturstein.de"],
  "bcc": ["admin@heishg-naturstein.de"],
  "reply_to": "info@heishg-naturstein.de",
  "attachments": [
    {
      "filename": "angebot.pdf",
      "content": "base64...",
      "mime_type": "application/pdf"
    }
  ],
  "provider": "smtp",
  "communication_channel": "email",
  "validate_only": false
}
```

| Feld | Typ | Beschreibung |
| --- | --- | --- |
| `to` | string/array | Empfänger-E-Mail-Adresse oder Liste (erforderlich für Versand) |
| `subject` | string | Betreff (erforderlich) |
| `body` | string | Text-Inhalt (erforderlich, falls kein `html_body`) |
| `html_body` | string | HTML-Inhalt (optional) |
| `cc` | string/array | CC-Empfänger (kommagetrennt oder Liste) |
| `bcc` | string/array | BCC-Empfänger (kommagetrennt oder Liste) |
| `reply_to` | string | Reply-To-Adresse (optional) |
| `attachments` | array | Anhänge (Base64-kodiert) |
| `provider` | string | `smtp` (Standard) oder `sendgrid` |
| `communication_channel` | string | `letter`, `email`, `both` |
| `validate_only` | boolean | Nur validieren, nicht senden |
| `email`/`delivery`/`content` | object | Kompatible Eingabestruktur aus `business_letter` |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "message": "E-Mail erfolgreich an max@mustermann.de gesendet.",
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
  "error": "SMTP nicht konfiguriert. Prüfe SMTP_HOST, SMTP_USER, SMTP_PASS, SENDER_EMAIL.",
  "validation": {
    "status": "needs_review",
    "errors": ["..."],
    "warnings": [],
    "missing_information": ["..."]
  }
}
```

### Harmonisiertes Beispiel aus `business_letter`

```json
{
  "email": {
    "to": ["kunde@example.de"],
    "cc": [],
    "bcc": ["archiv@example.de"],
    "reply_to": "info@steinmetz-muster.de",
    "subject": "Angebot 2026-0078 - Fensterbank",
    "body_text": "Guten Tag,\n...",
    "body_html": "<p>Guten Tag,</p>..."
  },
  "delivery": {
    "channel": "both",
    "recipient": "kunde@example.de",
    "subject": "Angebot 2026-0078 - Fensterbank",
    "reply_to": "info@steinmetz-muster.de"
  },
  "content": {
    "email_text": "Guten Tag,\n...",
    "email_html": "<p>Guten Tag,</p>..."
  },
  "provider": "smtp",
  "validate_only": true
}
```

---

## 🧪 Beispiele

### 1. Einfache E-Mail (SMTP)

**Input:**

```json
{
  "to": "max@mustermann.de",
  "subject": "Angebot für Küchenarbeitsplatte",
  "body": "Sehr geehrter Herr Mustermann,\n\nhier ist Ihr Angebot für die Granit-Arbeitsplatte.\n\nMit freundlichen Grüßen\nIhr Heishg Naturstein-Team"
}
```

**Output:**

```json
{
  "success": true,
  "message": "E-Mail erfolgreich an max@mustermann.de gesendet."
}
```

### 2. HTML-E-Mail mit CC

**Input:**

```json
{
  "to": "kunde@example.com",
  "cc": "vertrieb@heishg-naturstein.de",
  "subject": "Ihr Naturstein-Angebot",
  "body": "Text-Version...",
  "html_body": "<h1>Ihr Angebot</h1><p>Text-Version...</p>"
}
```

### 3. Mit Anhang (über SendGrid)

**Input:**

```json
{
  "to": "kunde@example.com",
  "subject": "Ihr Musterpaket",
  "body": "Ihr Musterpaket wurde versendet.",
  "attachments": [
    {
      "filename": "katalog.pdf",
      "content": "base64_encoded_content",
      "mime_type": "application/pdf"
    }
  ],
  "provider": "sendgrid"
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/email/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── plugin copy.py     # Backup (optional)
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "SMTP nicht konfiguriert"

**Lösung:** Setze die Umgebungsvariablen:

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=deine-email@gmail.com
export SMTP_PASS=dein-app-passwort
export SENDER_EMAIL=deine-email@gmail.com
```

### Fehler: "Authentication failed" (SMTP)

**Lösung:**

1. Für Gmail: Verwende ein **App-Passwort** (2FA aktivieren)
2. Prüfe, ob der SMTP-Server korrekt ist
3. Prüfe, ob der Port korrekt ist (587 für TLS, 465 für SSL)

### Fehler: "SendGrid-Fehler: 401"

**Lösung:** Prüfe, ob der SendGrid API-Key korrekt und aktiv ist.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Sende eine E-Mail an <max@mustermann.de> mit dem Betreff 'Angebot' und dem Text 'Hier ist Ihr Angebot...'"_
>
> **Elisa:** _"✅ E-Mail erfolgreich an <max@mustermann.de> gesendet."_

> **Nutzer:** _"Schicke das Angebot-PDF an den Kunden."_
>
> **Elisa:** _"✅ E-Mail mit Anhang wurde versendet."_

---

## 📚 Siehe auch

- [SMTP Setup Guide](https://support.google.com/a/answer/176600)
- [SendGrid API Dokumentation](https://docs.sendgrid.com/api-reference)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
