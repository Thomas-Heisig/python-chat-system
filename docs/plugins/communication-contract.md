# Communication Plugin Contract

## Ziel

Kommunikations-Plugins verwenden eine gemeinsame aeussere Datenstruktur,
bleiben intern aber provider- und funktionsspezifisch autonom.

Betroffene Plugins:

- `business_letter`
- `email`
- `whatsapp`
- `translator`

## Gemeinsame Eingabebereiche

### delivery

Enthaelt kanal- und zustellbezogene Angaben.

Beispiele:

- `communication_channel`
- `to`
- `cc`
- `bcc`
- `phone_number`
- `subject`
- `reply_to`

### content

Enthaelt den eigentlichen Nachrichteninhalt.

Beispiele:

- `letter_text`
- `email_text`
- `email_html`
- `whatsapp_text`
- `source_text`
- `translated_text`
- `target_lang`

### metadata

Enthaelt technische und fachliche Kontextinformationen.

Beispiele:

- `conversation_id`
- `document_id`
- `request_id`
- `created_by`
- `validate_only`

## Gemeinsames Validation-Objekt

Alle Plugins liefern nach Moeglichkeit:

```json
{
  "validation": {
    "status": "ready",
    "errors": [],
    "warnings": [],
    "missing_information": []
  }
}
```

Erlaubte Statuswerte:

- `ready`
- `draft`
- `needs_review`
- `invalid`
- `skipped`

## Validate-only

Mit `validate_only=true` wird nur normalisiert und validiert.

Es findet keine externe Aktion statt:

- keine E-Mail wird gesendet
- keine WhatsApp-Nachricht wird gesendet
- keine Uebersetzung wird ausgefuehrt
- kein Dokument wird final erzeugt

## Kanalbewusstes Verhalten

Plugins duerfen Anfragen ueberspringen, wenn der Kommunikationskanal
nicht zu ihrer Aufgabe passt.

Beispiele:

- WhatsApp bei `communication_channel=email`
- Email bei `communication_channel=letter`
- Business-Letter bei reinem WhatsApp-Versand

In diesem Fall wird kein Fehler erzeugt, sondern:

```json
{
  "status": "skipped",
  "reason": "unsupported_channel"
}
```

## Autonomie der Plugins

Der gemeinsame Contract betrifft nur die aeussere Schnittstelle.

Nicht vereinheitlicht werden:

- Provider-Clients
- SMTP-Logik
- Twilio-Logik
- Uebersetzungsanbieter
- Retry-Strategien
- provider-spezifische Fehlerbehandlung

## Kompatibilitaetsregel

Plugins sollen sowohl ihre native Eingabe als auch den gemeinsamen Envelope
akzeptieren, solange dies ohne Mehrdeutigkeit moeglich ist.

## Teststandard

Fuer jedes Kommunikations-Plugin sind mindestens folgende Runtime-Tests
erforderlich:

- native Eingabe
- Envelope-Eingabe
- `validate_only`
- ungueltige Pflichtfelder
- nicht unterstuetzter Kanal
- Provider wird bei `validate_only` nicht aufgerufen

## Maschinenlesbare Definition

Die kanonische maschinenlesbare Version liegt unter:

- `app/plugins/contracts/communication.schema.json`

Diese Datei ist fuer spaetere Typen, Validierung, Frontend-Formulare und
Tests wiederverwendbar.
