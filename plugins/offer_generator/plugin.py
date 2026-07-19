# packages/plugins/offer_generator/plugin.py
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "offer_generator",
    "name": "Offer Generator",
    "description": "Generiert Angebote für Natursteinprodukte basierend auf Material, Maßen und Extras",
    "category": "🛒 E-Commerce & Preis",
    "apiKeyRequired": False,
    "intentPattern": r"\b(angebot|preis|kosten|angebotsanfrage|kalkulation|preisliste)\b",
    "status": "implemented",
    "settingsFields": [],
}


# --- Lokale Preis- und Materialdatenbank ---
_PRICE_DB: dict[str, dict[str, Any]] = {
    "granit": {
        "name": "Granit",
        "base_price_per_qm": 180.0,
        "surcharges": {
            "polished": 25.0,
            "honed": 15.0,
            "flamed": 10.0,
            "brushed": 20.0,
        },
        "thickness_multipliers": {
            "2cm": 1.0,
            "3cm": 1.3,
            "4cm": 1.6,
        },
        "edge_profiles": {
            "square": 0.0,
            "beveled": 15.0,
            "bullnose": 25.0,
            "ogee": 35.0,
        },
        "installation_cost_per_qm": 80.0,
        "material_types": ["granit", "granite"],
    },
    "marmor": {
        "name": "Marmor",
        "base_price_per_qm": 220.0,
        "surcharges": {
            "polished": 30.0,
            "honed": 20.0,
            "brushed": 25.0,
        },
        "thickness_multipliers": {
            "2cm": 1.0,
            "3cm": 1.4,
            "4cm": 1.8,
        },
        "edge_profiles": {
            "square": 0.0,
            "beveled": 20.0,
            "bullnose": 30.0,
            "ogee": 40.0,
        },
        "installation_cost_per_qm": 90.0,
        "material_types": ["marmor", "marble"],
    },
    "quarzit": {
        "name": "Quarzit",
        "base_price_per_qm": 200.0,
        "surcharges": {
            "polished": 28.0,
            "honed": 18.0,
        },
        "thickness_multipliers": {
            "2cm": 1.0,
            "3cm": 1.35,
            "4cm": 1.7,
        },
        "edge_profiles": {
            "square": 0.0,
            "beveled": 18.0,
            "bullnose": 28.0,
            "ogee": 38.0,
        },
        "installation_cost_per_qm": 85.0,
        "material_types": ["quarzit", "quartzite"],
    },
    "schiefer": {
        "name": "Schiefer",
        "base_price_per_qm": 120.0,
        "surcharges": {
            "honed": 12.0,
            "brushed": 18.0,
        },
        "thickness_multipliers": {
            "2cm": 1.0,
            "3cm": 1.2,
            "4cm": 1.5,
        },
        "edge_profiles": {
            "square": 0.0,
            "beveled": 10.0,
            "bullnose": 18.0,
        },
        "installation_cost_per_qm": 70.0,
        "material_types": ["schiefer", "slate"],
    },
    "travertin": {
        "name": "Travertin",
        "base_price_per_qm": 150.0,
        "surcharges": {
            "honed": 15.0,
            "brushed": 20.0,
            "tumbled": 12.0,
        },
        "thickness_multipliers": {
            "2cm": 1.0,
            "3cm": 1.25,
            "4cm": 1.6,
        },
        "edge_profiles": {
            "square": 0.0,
            "beveled": 12.0,
            "bullnose": 20.0,
            "ogee": 30.0,
        },
        "installation_cost_per_qm": 75.0,
        "material_types": ["travertin", "travertine"],
    },
    "kalkstein": {
        "name": "Kalkstein",
        "base_price_per_qm": 130.0,
        "surcharges": {
            "honed": 14.0,
            "brushed": 18.0,
        },
        "thickness_multipliers": {
            "2cm": 1.0,
            "3cm": 1.2,
            "4cm": 1.5,
        },
        "edge_profiles": {
            "square": 0.0,
            "beveled": 12.0,
            "bullnose": 20.0,
        },
        "installation_cost_per_qm": 72.0,
        "material_types": ["kalkstein", "limestone"],
    },
}


class OfferGeneratorPlugin:
    name = "offer_generator"
    description = "Generiert Angebote für Natursteinprodukte basierend auf Material, Maßen und Extras"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "material": {
                "type": "string",
                "description": "Material (z.B. Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein).",
            },
            "length": {
                "type": "number",
                "description": "Länge in Metern (für Arbeitsplatten, Fliesen).",
            },
            "width": {
                "type": "number",
                "description": "Breite in Metern (für Arbeitsplatten, Fliesen).",
            },
            "area": {
                "type": "number",
                "description": "Fläche in Quadratmetern (alternativ zu length/width).",
            },
            "thickness": {
                "type": "string",
                "enum": ["2cm", "3cm", "4cm"],
                "default": "2cm",
                "description": "Stärke der Platte.",
            },
            "surface": {
                "type": "string",
                "description": "Oberflächenbearbeitung (z.B. polished, honed, flamed, brushed).",
            },
            "edge_profile": {
                "type": "string",
                "enum": ["square", "beveled", "bullnose", "ogee"],
                "default": "square",
                "description": "Kantenprofil.",
            },
            "installation": {
                "type": "boolean",
                "default": False,
                "description": "Soll die Installation im Angebot enthalten sein?",
            },
            "cutouts": {
                "type": "integer",
                "default": 0,
                "description": "Anzahl der Ausschnitte (z.B. für Spüle, Herd).",
            },
            "sink_cutout": {
                "type": "boolean",
                "default": False,
                "description": "Ausschnitt für Spüle?",
            },
            "cooktop_cutout": {
                "type": "boolean",
                "default": False,
                "description": "Ausschnitt für Kochfeld?",
            },
            "delivery": {
                "type": "boolean",
                "default": False,
                "description": "Soll die Lieferung im Angebot enthalten sein?",
            },
            "delivery_distance_km": {
                "type": "number",
                "default": 0,
                "description": "Lieferentfernung in Kilometern (für Lieferkosten).",
            },
            "currency": {
                "type": "string",
                "enum": ["EUR", "USD", "CHF", "GBP"],
                "default": "EUR",
                "description": "Währung.",
            },
            "tax_rate": {
                "type": "number",
                "minimum": 0,
                "maximum": 30,
                "default": 19,
                "description": "Steuersatz in Prozent.",
            },
            "discount": {
                "type": "number",
                "minimum": 0,
                "maximum": 100,
                "default": 0,
                "description": "Rabatt in Prozent (optional).",
            },
            "customer_name": {
                "type": "string",
                "description": "Name des Kunden (für das Angebot).",
            },
            "project_name": {
                "type": "string",
                "description": "Name des Projekts (optional).",
            },
        },
        "required": ["material"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "offer": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.storage_path = os.getenv("OFFER_STORAGE_PATH", "./offers.json")
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _generate_offer_id(self) -> str:
        import uuid
        return f"OFF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    def _load_offers(self) -> list[dict[str, Any]]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_offer(self, offer: dict[str, Any]):
        offers = self._load_offers()
        offers.append(offer)
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(offers, f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass

    def _find_material(self, material: str) -> dict[str, Any] | None:
        material_lower = material.lower()
        for key, data in _PRICE_DB.items():
            if material_lower == key or material_lower in data.get("material_types", []):
                return data
        return None

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        material = str(input_data.get("material", "")).strip()
        if not material:
            return {"success": False, "error": "Material ist erforderlich."}

        material_data = self._find_material(material)
        if not material_data:
            return {
                "success": False,
                "error": f"Material '{material}' nicht gefunden. Verfügbare Materialien: {', '.join(_PRICE_DB.keys())}",
            }

        length = input_data.get("length")
        width = input_data.get("width")
        area = input_data.get("area")

        if area is None:
            if length is None or width is None:
                return {"success": False, "error": "Gib entweder Fläche (area) oder Länge und Breite an."}
            try:
                area = float(length) * float(width)
            except (TypeError, ValueError):
                return {"success": False, "error": "Länge und Breite müssen Zahlen sein."}
        else:
            try:
                area = float(area)
            except (TypeError, ValueError):
                return {"success": False, "error": "Fläche muss eine Zahl sein."}

        if area <= 0:
            return {"success": False, "error": "Fläche muss größer als 0 sein."}

        thickness = str(input_data.get("thickness", "2cm")).strip()
        surface = str(input_data.get("surface", "")).strip().lower() or "honed"
        edge_profile = str(input_data.get("edge_profile", "square")).strip().lower()
        installation = bool(input_data.get("installation", False))
        cutouts = max(0, int(input_data.get("cutouts", 0)))
        sink_cutout = bool(input_data.get("sink_cutout", False))
        cooktop_cutout = bool(input_data.get("cooktop_cutout", False))
        delivery = bool(input_data.get("delivery", False))
        delivery_distance = max(0, float(input_data.get("delivery_distance_km", 0)))
        currency = str(input_data.get("currency", "EUR")).strip().upper()
        tax_rate = max(0, min(30, float(input_data.get("tax_rate", 19))))
        discount = max(0, min(100, float(input_data.get("discount", 0))))
        customer_name = str(input_data.get("customer_name", "")).strip() or "Kunde"
        project_name = str(input_data.get("project_name", "")).strip() or "Naturstein-Projekt"

        # Preise
        base_price = material_data.get("base_price_per_qm", 0)
        thickness_mult = material_data.get("thickness_multipliers", {}).get(thickness, 1.0)
        surface_surcharge = material_data.get("surcharges", {}).get(surface, 0)
        edge_price = material_data.get("edge_profiles", {}).get(edge_profile, 0)
        install_cost = material_data.get("installation_cost_per_qm", 0)

        # Materialpreis
        material_price = base_price * thickness_mult
        material_total = material_price * area

        # Oberflächenzuschlag
        surface_total = surface_surcharge * area

        # Kantenprofil (pro laufendem Meter – Annahme: Umfang ~ 2*(L+B) für Rechteck)
        if length and width:
            perimeter = 2 * (float(length) + float(width))
        else:
            perimeter = 4 * (area ** 0.5)  # Schätzung für Quadrat
        edge_total = edge_price * perimeter

        # Ausschnitte
        cutout_price = 50.0  # pauschal pro Ausschnitt
        cutout_total = cutouts * cutout_price
        if sink_cutout:
            cutout_total += 80.0
        if cooktop_cutout:
            cutout_total += 80.0

        # Installation
        install_total = install_cost * area if installation else 0

        # Lieferung (pauschal 2€/km)
        delivery_total = delivery_distance * 2.0 if delivery else 0
        if delivery and delivery_distance == 0:
            delivery_total = 30.0  # Pauschale für lokale Lieferung

        # Summe
        subtotal = material_total + surface_total + edge_total + cutout_total + install_total + delivery_total

        # Rabatt
        discount_amount = subtotal * (discount / 100)

        # Steuer
        net_total = subtotal - discount_amount
        tax_amount = net_total * (tax_rate / 100)
        grand_total = net_total + tax_amount

        # Angebot erstellen
        offer: dict[str, Any] = {
            "id": self._generate_offer_id(),
            "customer": customer_name,
            "project": project_name,
            "material": material_data["name"],
            "area": round(area, 2),
            "thickness": thickness,
            "surface": surface,
            "edge_profile": edge_profile,
            "installation": installation,
            "delivery": delivery,
            "currency": currency,
            "tax_rate": tax_rate,
            "discount": discount,
            "items": [
                {"description": f"{material_data['name']} {thickness} ({surface})", "quantity": round(area, 2), "unit": "qm", "price_per_unit": round(material_price, 2), "total": round(material_total, 2)},
            ],
            "subtotal": round(subtotal, 2),
            "discount_amount": round(discount_amount, 2),
            "net_total": round(net_total, 2),
            "tax_amount": round(tax_amount, 2),
            "grand_total": round(grand_total, 2),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "details": {
                "material_price_per_qm": round(material_price, 2),
                "surface_surcharge": round(surface_surcharge, 2),
                "edge_price": round(edge_price, 2),
                "cutout_total": round(cutout_total, 2),
                "installation_total": round(install_total, 2),
                "delivery_total": round(delivery_total, 2),
            },
        }

        self._save_offer(offer)

        return {
            "success": True,
            "offer": offer,
        }

