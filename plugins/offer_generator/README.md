# 📄 Offer Generator Plugin

**ID:** `offer_generator`  
**Kategorie:** 🛒 E-Commerce & Preis  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Offer Generator Plugin erstellt **Angebote für Natursteinprodukte** basierend auf:

- **Material** (Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein)
- **Maßen** (Fläche oder Länge × Breite)
- **Oberfläche** (poliert, geschliffen, geflammt, gebürstet)
- **Kantenprofil** (gerade, abgeschrägt, abgerundet, Ogee)
- **Extras** (Ausschnitte, Installation, Lieferung)
- **Rabatten und Steuern**

Die Angebote werden in einer lokalen JSON-Datei gespeichert (`./offers.json`).

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(angebot|preis|kosten|angebotsanfrage|kalkulation|preisliste)\b
```

**Beispiele:**

- _"Erstelle ein Angebot für eine Granit-Küchenarbeitsplatte 3m x 0,6m."_
- _"Kalkuliere den Preis für Marmorfliesen 10 qm."_
- _"Was kostet eine Quarzit-Arbeitsplatte mit polierter Oberfläche?"_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable             | Beschreibung                | Standard        |
| -------------------- | --------------------------- | --------------- |
| `OFFER_STORAGE_PATH` | Pfad zur JSON-Speicherdatei | `./offers.json` |

---

## 📦 Input-Schema

```json
{
  "material": "Granit",
  "length": 3.0,
  "width": 0.6,
  "thickness": "3cm",
  "surface": "polished",
  "edge_profile": "bullnose",
  "installation": true,
  "cutouts": 2,
  "sink_cutout": true,
  "cooktop_cutout": false,
  "delivery": true,
  "delivery_distance_km": 25,
  "currency": "EUR",
  "tax_rate": 19,
  "discount": 5,
  "customer_name": "Max Mustermann",
  "project_name": "Küchenrenovierung"
}
```

| Feld                   | Typ     | Beschreibung                                               |
| ---------------------- | ------- | ---------------------------------------------------------- |
| `material`             | string  | Material (erforderlich)                                    |
| `length`               | number  | Länge in Metern                                            |
| `width`                | number  | Breite in Metern                                           |
| `area`                 | number  | Fläche in qm (alternativ zu length/width)                  |
| `thickness`            | string  | `2cm`, `3cm`, `4cm` (Standard: `2cm`)                      |
| `surface`              | string  | Oberfläche (z.B. `polished`, `honed`, `flamed`, `brushed`) |
| `edge_profile`         | string  | `square`, `beveled`, `bullnose`, `ogee`                    |
| `installation`         | boolean | Installation enthalten?                                    |
| `cutouts`              | integer | Anzahl Ausschnitte                                         |
| `sink_cutout`          | boolean | Spülenausschnitt?                                          |
| `cooktop_cutout`       | boolean | Kochfeldausschnitt?                                        |
| `delivery`             | boolean | Lieferung enthalten?                                       |
| `delivery_distance_km` | number  | Lieferentfernung in km                                     |
| `currency`             | string  | `EUR`, `USD`, `CHF`, `GBP`                                 |
| `tax_rate`             | number  | Steuersatz in % (Standard: 19)                             |
| `discount`             | number  | Rabatt in %                                                |
| `customer_name`        | string  | Kundenname                                                 |
| `project_name`         | string  | Projektname                                                |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "offer": {
    "id": "OFF-20260628-ABC123",
    "customer": "Max Mustermann",
    "project": "Küchenrenovierung",
    "material": "Granit",
    "area": 1.8,
    "thickness": "3cm",
    "surface": "polished",
    "edge_profile": "bullnose",
    "installation": true,
    "delivery": true,
    "currency": "EUR",
    "tax_rate": 19,
    "discount": 5,
    "items": [
      {
        "description": "Granit 3cm (polished)",
        "quantity": 1.8,
        "unit": "qm",
        "price_per_unit": 234.0,
        "total": 421.2
      }
    ],
    "subtotal": 1234.56,
    "discount_amount": 61.73,
    "net_total": 1172.83,
    "tax_amount": 222.84,
    "grand_total": 1395.67,
    "created_at": "2026-06-28T10:00:00Z",
    "details": {
      "material_price_per_qm": 234.0,
      "surface_surcharge": 30.0,
      "edge_price": 25.0,
      "cutout_total": 100.0,
      "installation_total": 144.0,
      "delivery_total": 50.0
    }
  }
}
```

**Bei Fehlern:**

```json
{
  "success": false,
  "error": "Material 'Blabla' nicht gefunden. Verfügbare Materialien: Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein"
}
```

---

## 🧪 Beispiele

### 1. Einfache Arbeitsplatte

**Input:**

```json
{
  "material": "Granit",
  "length": 3.0,
  "width": 0.6,
  "surface": "polished"
}
```

### 2. Komplettes Angebot mit Extras

**Input:**

```json
{
  "material": "Marmor",
  "area": 5.0,
  "thickness": "3cm",
  "surface": "honed",
  "edge_profile": "ogee",
  "installation": true,
  "sink_cutout": true,
  "cooktop_cutout": true,
  "delivery": true,
  "delivery_distance_km": 30,
  "discount": 10,
  "customer_name": "Anna Schmidt"
}
```

### 3. Rabatt und Steuer

**Input:**

```json
{
  "material": "Quarzit",
  "area": 2.5,
  "discount": 15,
  "tax_rate": 19
}
```

---

## 📁 Datei-Struktur

```text
packages/plugins/offer_generator/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 📁 Speicherort der Angebote

Standardmäßig werden Angebote in einer JSON-Datei gespeichert:

```text
./offers.json
```

**Format:**

```json
[
  {
    "id": "OFF-20260628-ABC123",
    "customer": "Max Mustermann",
    "project": "Küchenrenovierung",
    "material": "Granit",
    "grand_total": 1395.67,
    "created_at": "2026-06-28T10:00:00Z"
  }
]
```

---

## 🔧 Erweiterbarkeit

Die Preisdatenbank kann einfach um weitere Materialien, Oberflächen und Kantenprofile erweitert werden:

```python
_PRICE_DB["neuer_stein"] = {
    "name": "Neuer Stein",
    "base_price_per_qm": 250.0,
    "surcharges": {"polished": 30.0},
    "thickness_multipliers": {"2cm": 1.0, "3cm": 1.4},
    "edge_profiles": {"square": 0.0, "beveled": 20.0},
    "installation_cost_per_qm": 100.0,
}
```

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Erstelle ein Angebot für eine Granit-Arbeitsplatte 3m x 0,6m mit polierter Oberfläche."_
>
> **Elisa:** _"✅ Angebot erstellt:_
> _Material: Granit (3cm, poliert)_
> _Fläche: 1,8 qm_
> _Gesamtpreis: 1.234,56 € (inkl. 19% MwSt.)_
> _Angebots-ID: OFF-20260628-ABC123"_

---

## 📚 Siehe auch

- [PriceFinder Plugin](../pricefinder)
- [ProductCatalog Plugin](../product_catalog)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
