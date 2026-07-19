# Business Letter Manual Frontpage

Eigenstaendige manuelle React-/TypeScript-Oberflaeche fuer das Plugin `business_letter`.

## Zielordner

```text
plugins/business_letter/frontend/
  BusinessLetterManualPage.tsx
  BusinessLetterManualPage.css
  README.md
```

## Integration im Projekt

Die Seite ist bereits im bestehenden Plugin-Popup verdrahtet.

Klickpfad:

```text
Plugins -> business_letter -> Frontend
```

Dabei wird in `WorkspacePage.tsx` direkt die Komponente `BusinessLetterManualPage` gerendert.

## Enthalten

- Dokumenttyp-Auswahl
- Angebote, Rechnungen, Lieferscheine, Gutschriften und Mahnungen
- Empfaenger- und Adressdaten
- dynamische Dokumentpositionen
- automatische Netto-, Steuer- und Bruttoberechnung
- Einleitungs- und Abschlusstexte
- Kaeufer- und Zahlungsreferenz
- PDF-, XML-, Validierungs- und Speicheroptionen
- Ausfuehrung ueber `/api/plugins/execute`
- Fehler- und Ergebnisanzeige
- responsive Desktop- und Mobilansicht
- plugin-lokale Entwurfs-Persistenz (Load, Autosave, manuelles Save/Reload)

## Entwurfs-Persistenz

Die Frontpage speichert ihre Eingabedaten plugin-lokal in den Settings.

- Kategorie: `plugins`
- Key: `business_letter_frontpage_draft` (dynamisch aus `pluginId` abgeleitet)
- Scope: benutzerbezogen (`user_id`)

Die gemeinsame Persistenzlogik liegt zentral in `plugins/shared/frontend/usePluginDraft.ts`.

Damit bleibt der Arbeitskontext des Plugins zwischen Aufrufen erhalten und ist nicht nur an den Session-State gebunden.

## Payload-Hinweis

Im Projekt wird der Frontend-Submit an den vorhandenen App-Contract angepasst und als Plugin-Execute-Payload gesendet:

```json
{
  "pluginId": "business_letter",
  "pluginInput": {
    "action": "create_document"
  },
  "pluginSettings": {},
  "userId": 1
}
```

Falls sich die erwarteten Backend-Feldnamen aendern, muss nur `buildPayload()` in `BusinessLetterManualPage.tsx` angepasst werden.
