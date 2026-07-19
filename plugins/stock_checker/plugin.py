# packages/plugins/stock_checker/plugin.py
from __future__ import annotations

import json
import os
from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "stock_checker",
    "name": "Stock Checker",
    "description": "Lagerbestandsabfrage für Natursteinprodukte",
    "category": "🛒 E-Commerce & Preis",
    "apiKeyRequired": False,
    "intentPattern": r"\b(lager|bestand|verfügbar|lieferbar|vorrat|stock)\b",
    "status": "implemented",
    "settingsFields": [],
}


# --- Interne Lagerdatenbank (Beispiel) ---
_STOCK_DB: dict[str, dict[str, Any]] = {
    "P001": {
        "name": "Nero Assoluto Granit Fliese 60x60",
        "stock": 120,
        "reserved": 15,
        "location": "Lager A",
        "min_stock": 20,
    },
    "P002": {
        "name": "Bianco Sardo Marmor Fliese 40x40",
        "stock": 85,
        "reserved": 5,
        "location": "Lager A",
        "min_stock": 10,
    },
    "P003": {
        "name": "Giallo Venezia Granit Fliese 30x60",
        "stock": 200,
        "reserved": 30,
        "location": "Lager B",
        "min_stock": 25,
    },
    "P004": {
        "name": "Carrara Marmor Platte 300x140cm",
        "stock": 15,
        "reserved": 2,
        "location": "Lager C",
        "min_stock": 5,
    },
    "P005": {
        "name": "Quarzit Bianco Platte 250x120cm",
        "stock": 10,
        "reserved": 3,
        "location": "Lager C",
        "min_stock": 3,
    },
    "P006": {
        "name": "Schiefer Grau Fliese 30x60",
        "stock": 300,
        "reserved": 20,
        "location": "Lager A",
        "min_stock": 30,
    },
    "P007": {
        "name": "Travertin Classico Fliese 40x40",
        "stock": 180,
        "reserved": 10,
        "location": "Lager B",
        "min_stock": 20,
    },
    "P008": {
        "name": "Nero Assoluto Granit Arbeitsplatte 240x60cm",
        "stock": 8,
        "reserved": 1,
        "location": "Lager C",
        "min_stock": 2,
    },
}


class StockCheckerPlugin:
    name = "stock_checker"
    description = "Lagerbestandsabfrage für Natursteinprodukte"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "Produkt-ID (z.B. P001).",
            },
            "product_name": {
                "type": "string",
                "description": "Name des Produkts (Teilsuche möglich).",
            },
            "location": {
                "type": "string",
                "description": "Optional: Lagerort (z.B. Lager A, Lager B).",
            },
            "all_locations": {
                "type": "boolean",
                "default": False,
                "description": "Bestände aller Standorte anzeigen (nur mit product_id).",
            },
        },
        "required": ["product_id"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "product_id": {"type": "string"},
            "product_name": {"type": "string"},
            "stock": {"type": "integer"},
            "reserved": {"type": "integer"},
            "available": {"type": "integer"},
            "location": {"type": "string"},
            "min_stock": {"type": "integer"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.storage_path = os.getenv("STOCK_STORAGE_PATH", "./stock.json")
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(_STOCK_DB, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _load_stock(self) -> dict[str, dict[str, Any]]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return _STOCK_DB

    def _save_stock(self, data: dict[str, dict[str, Any]]):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        product_id = str(input_data.get("product_id", "")).strip()
        product_name = str(input_data.get("product_name", "")).strip()
        location_filter = str(input_data.get("location", "")).strip() or None

        stock_db = self._load_stock()

        if product_id:
            # Exakte Suche nach Produkt-ID
            if product_id not in stock_db:
                return {"success": False, "error": f"Produkt mit ID '{product_id}' nicht gefunden."}

            product = stock_db[product_id]
            stock = product.get("stock", 0)
            reserved = product.get("reserved", 0)
            available = stock - reserved
            location = product.get("location", "Unbekannt")
            min_stock = product.get("min_stock", 0)

            # Nach Lagerort filtern (wenn angegeben)
            if location_filter and location != location_filter:
                return {
                    "success": False,
                    "error": f"Produkt '{product_id}' ist nicht am Standort '{location_filter}' verfügbar.",
                }

            message = f"{available} verfügbar (Lager: {stock}, reserviert: {reserved})"
            if stock < min_stock:
                message += f" ⚠️ Bestand unter Mindestbestand ({min_stock})!"

            return {
                "success": True,
                "product_id": product_id,
                "product_name": product.get("name", ""),
                "stock": stock,
                "reserved": reserved,
                "available": available,
                "location": location,
                "min_stock": min_stock,
                "message": message,
            }

        elif product_name:
            # Suche nach Produktname (Teilsuche)
            results: list[dict[str, Any]] = []
            for pid, product in stock_db.items():
                if product_name.lower() in product.get("name", "").lower():
                    stock = product.get("stock", 0)
                    reserved = product.get("reserved", 0)
                    results.append({
                        "product_id": pid,
                        "product_name": product.get("name", ""),
                        "stock": stock,
                        "reserved": reserved,
                        "available": stock - reserved,
                        "location": product.get("location", "Unbekannt"),
                    })

            if not results:
                return {"success": False, "error": f"Keine Produkte gefunden für '{product_name}'."}

            return {
                "success": True,
                "results": results,
                "message": f"{len(results)} Produkte gefunden.",
            }

        else:
            return {"success": False, "error": "product_id oder product_name ist erforderlich."}

