# Calculator Plugin

Der Calculator bietet sichere mathematische Auswertung ueber AST-Parsing und eine eigene Frontend-Oberflaeche im Plugin-Popup.

## Struktur

Der Plugin-Ordner folgt jetzt derselben Modulstruktur wie `business_letter`:

```text
plugins/calculator/
  assets/
    logo.svg
  frontend/
    CalculatorManualPage.tsx
    CalculatorManualPage.css
    README.md
  models/
  renderers/
  services/
    calculation.py
  constants.py
  settings.py
  plugin.py
  README.md
```

## Funktionen

- Grundrechenarten: `+ - * / ** %`
- Funktionen: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `log`, `ln`, `exp`, `abs`, `floor`, `ceil`, `round`, `factorial`, `min`, `max`
- Konstanten: `pi`, `e`, `tau`, sowie `pi`-Eingabe ueber `π`
- Preset-Aktionen fuer typische Rechnungen
- Winkelmodus fuer Trigonometrie: `rad` oder `deg` (auch fuer inverse Trigonometrie: Ausgabe in Radiant oder Grad)
- Rundung ueber `precision` (0 bis 12)
- Zusätzliche Sicherheitsregeln: nur numerische Konstanten, keine booleschen Werte, keine Keyword-Argumente in Funktionsaufrufen

## Contract

`POST /api/plugins/execute`

Beispiel:

```json
{
  "plugin_id": "calculator",
  "plugin_input": {
    "action": "evaluate",
    "expression": "sin(30) + cos(60)",
    "angle_mode": "deg",
    "precision": 6
  },
  "plugin_settings": {
    "angle_mode": "deg",
    "precision": 6
  }
}
```

Antwort (Beispiel):

```json
{
  "result": 1,
  "expression": "sin(30) + cos(60)",
  "action": "evaluate",
  "angle_mode": "deg",
  "precision": 6
}
```

## Frontend

Die plugin-spezifische Oberflaeche liegt unter:

`plugins/calculator/frontend/`

Sie ist im Workspace unter `Plugins -> Calculator -> Frontend` eingebunden.

Das Frontend zeigt jetzt zusaetzlich ein sichtbares Plugin-Logo aus `plugins/calculator/assets/logo.svg` im Header.
