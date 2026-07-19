# Calculator Manual Frontpage

Eigenstaendige React-/TypeScript-Oberflaeche fuer das Plugin calculator.

## Zielordner

```text
plugins/calculator/frontend/
  CalculatorManualPage.tsx
  CalculatorManualPage.css
  README.md
```

## Integration

Die Komponente wird im Plugin-Popup gerendert:

- Navigation: Plugins -> Calculator -> Frontend
- Datei: frontend/src/components/content/WorkspacePage.tsx

## Funktionen

- Header mit sichtbarem Plugin-Logo (`plugins/calculator/assets/logo.svg`)
- Ausdruckseditor mit Presets
- Rechner-Keypad fuer schnelle Eingabe
- Winkelmodus (Radiant/Grad)
- Rundungspraezision (0-12)
- Ergebnisansicht mit Laufzeitmetadaten
- Lokaler Verlauf mit Wiederaufnahme
- Ausfuehrung ueber den bestehenden Plugin-Execute-Contract
- plugin-lokale Entwurfs-Persistenz (Load, Autosave, manuelles Save/Reload)

## Entwurfs-Persistenz

Die Frontpage speichert ihre Eingabedaten plugin-lokal in den Settings.

- Kategorie: `plugins`
- Key: `calculator_frontpage_draft` (dynamisch aus `pluginId` abgeleitet)
- Scope: benutzerbezogen (`user_id`)

Die gemeinsame Persistenzlogik liegt zentral in `plugins/shared/frontend/usePluginDraft.ts`.

## Contract

Die Seite sendet denselben App-Contract wie andere plugin-spezifische Frontpages:

```json
{
  "pluginId": "calculator",
  "pluginInput": {
    "action": "evaluate",
    "expression": "(1250 * 0.19) + sqrt(81)",
    "angle_mode": "rad",
    "precision": 6
  },
  "pluginSettings": {
    "angle_mode": "rad",
    "precision": 6
  },
  "userId": 1
}
```
