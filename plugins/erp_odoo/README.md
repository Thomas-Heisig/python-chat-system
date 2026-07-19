# 📋 Odoo ERP Plugin

**ID:** `erp_odoo`  
**Kategorie:** 📊 Business & Analytics  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Odoo ERP Plugin ermöglicht die **Integration Ihres Chat-Systems mit Odoo ERP**. Es unterstützt:

- **Partnerverwaltung** – Erstellen, Suchen und Auflisten von Kunden/Lieferanten
- **Produktverwaltung** – Anzeigen und Suchen von Produkten
- **Auftragsverwaltung** – Erstellen und Anzeigen von Verkaufsaufträgen
- **Lagerbestand** – Abfragen von Lagerbeständen
- **Kategorien** – Anzeigen von Produktkategorien

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(auftrag|rechnung|bestellung|lieferung|odoo|erp|partner|produkt|lager|bestand)\b
```

**Beispiele:**

- _"Erstelle einen neuen Partner für Max Mustermann."_
- _"Zeige mir den Lagerbestand von Produkt XYZ."_
- _"Erstelle einen Verkaufsauftrag für die Granit-Platten."_

---

## ⚙️ Konfiguration

### Umgebungsvariablen

| Variable        | Beschreibung                                   | Erforderlich |
| --------------- | ---------------------------------------------- | ------------ |
| `ODOO_URL`      | Odoo-Instanz-URL (z.B. `https://mein-odoo.de`) | ✅           |
| `ODOO_DB`       | Odoo-Datenbankname                             | ✅           |
| `ODOO_USERNAME` | Odoo-Benutzername                              | ✅           |
| `ODOO_PASSWORD` | Odoo-Passwort / API-Key                        | ✅           |

---

## 📦 Input-Schema

Das Plugin unterstützt verschiedene Aktionen:

### Aktionen im Überblick

| Aktion                  | Beschreibung                   | Erforderliche Felder          |
| ----------------------- | ------------------------------ | ----------------------------- |
| **`list_partners`**     | Listet alle Partner            | `limit` (optional)            |
| **`create_partner`**    | Erstellt einen Partner         | `partner_name`                |
| **`search_partners`**   | Sucht Partner                  | `search_query`                |
| **`list_products`**     | Listet alle Produkte           | `limit` (optional)            |
| **`get_product`**       | Ruft ein Produkt ab            | `product_id`                  |
| **`create_sale_order`** | Erstellt einen Verkaufsauftrag | `partner_name`, `order_lines` |
| **`list_sale_orders`**  | Listet alle Aufträge           | `limit` (optional)            |
| **`get_stock`**         | Ruft Lagerbestand ab           | `product_id`                  |
| **`list_categories`**   | Listet Produktkategorien       | –                             |

---

## 📤 Output-Schema

**Erfolg:**

```json
{
  "success": true,
  "message": "Partner erstellt.",
  "partner": { "id": 123, "name": "Max Mustermann" }
}
```

**Fehler:**

```json
{
  "success": false,
  "error": "Nicht mit Odoo verbunden. Prüfe ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD."
}
```

---

## 🧪 Beispiele

### 1. Partner erstellen

**Input:**

```json
{
  "action": "create_partner",
  "partner_name": "Max Mustermann",
  "partner_email": "max@mustermann.de",
  "partner_phone": "+49 170 1234567"
}
```

**Output:**

```json
{
  "success": true,
  "message": "Partner erstellt.",
  "partner": { "id": 123, "name": "Max Mustermann" }
}
```

### 2. Partner suchen

**Input:**

```json
{
  "action": "search_partners",
  "search_query": "Mustermann"
}
```

**Output:**

```json
{
  "success": true,
  "data": [
    { "id": 123, "name": "Max Mustermann", "email": "max@mustermann.de" }
  ],
  "total": 1
}
```

### 3. Verkaufsauftrag erstellen

**Input:**

```json
{
  "action": "create_sale_order",
  "partner_name": "Max Mustermann",
  "order_lines": [{ "product_id": 456, "quantity": 2, "price_unit": 150.0 }]
}
```

**Output:**

```json
{
  "success": true,
  "message": "Auftrag 789 erstellt.",
  "order": { "id": 789 }
}
```

### 4. Lagerbestand abfragen

**Input:**

```json
{
  "action": "get_stock",
  "product_id": 456,
  "location_id": 1
}
```

**Output:**

```json
{
  "success": true,
  "stock": {
    "product_id": 456,
    "quantity": 25.0,
    "reserved_quantity": 5.0
  },
  "message": "Lagerbestand: 25.0 Stück"
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/erp_odoo/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Nicht mit Odoo verbunden"

**Lösung:** Prüfe die Umgebungsvariablen:

```bash
export ODOO_URL=https://mein-odoo.de
export ODOO_DB=meine-datenbank
export ODOO_USERNAME=admin
export ODOO_PASSWORD=mein-passwort
```

### Fehler: "Partner konnte nicht gefunden oder erstellt werden"

**Lösung:** Prüfe, ob der Partner-Name korrekt ist. Odoo erstellt automatisch einen Partner, wenn er nicht existiert.

### Fehler: "Auftrag konnte nicht erstellt werden"

**Lösung:** Prüfe, ob die `product_id` existiert und die `order_lines` korrekt formatiert sind.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Erstelle einen neuen Kunden 'Max Mustermann' mit E-Mail <max@mustermann.de>."_
>
> **Elisa:** _"✅ Partner 'Max Mustermann' wurde in Odoo erstellt."_

> **Nutzer:** _"Wie viel Lagerbestand haben wir von Produkt 'Granit Platte'?"_
>
> **Elisa:** _"Lagerbestand: 25 Stück. Möchtest du eine Bestellung auslösen?"_

---

## 📚 Siehe auch

- [Odoo API Dokumentation](https://www.odoo.com/documentation/17.0/developer/howtos/rdtraining/03_web_api.html)
- [Odoo XML-RPC](https://www.odoo.com/documentation/17.0/developer/reference/addons/external_api.html)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
