# packages/plugins/erp_odoo/plugin.py
from __future__ import annotations

import os
import xmlrpc.client
from typing import Any, cast


PLUGIN_META: dict[str, Any] = {
    "id": "erp_odoo",
    "name": "Odoo ERP",
    "description": "Odoo ERP-Integration (Partner, Produkte, Aufträge, Lagerbestand)",
    "category": "📊 Business & Analytics",
    "apiKeyRequired": True,
    "intentPattern": r"\b(auftrag|rechnung|bestellung|lieferung|odoo|erp|partner|produkt|lager|bestand)\b",
    "status": "implemented",
    "settingsFields": [],
}


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key_raw, value_raw in cast(dict[object, Any], value).items():
        normalized[str(key_raw)] = value_raw
    return normalized


class OdooERPPlugin:
    name = "erp_odoo"
    description = "Odoo ERP-Integration (Partner, Produkte, Aufträge, Lagerbestand)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "list_partners",
                    "create_partner",
                    "search_partners",
                    "list_products",
                    "get_product",
                    "create_sale_order",
                    "list_sale_orders",
                    "get_stock",
                    "list_categories",
                ],
                "default": "list_partners",
                "description": "Aktion im Odoo ERP.",
            },
            "partner_name": {"type": "string", "description": "Name des Partners (für create_partner)."},
            "partner_email": {"type": "string", "description": "E-Mail des Partners (für create_partner)."},
            "partner_phone": {"type": "string", "description": "Telefon des Partners (für create_partner)."},
            "partner_id": {"type": "integer", "description": "ID des Partners (für search_partners)."},
            "product_id": {"type": "integer", "description": "ID des Produkts (für get_product)."},
            "product_name": {"type": "string", "description": "Name des Produkts (für Suche)."},
            "product_qty": {"type": "number", "description": "Menge für Auftrag (für create_sale_order)."},
            "order_lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "integer"},
                        "quantity": {"type": "number"},
                        "price_unit": {"type": "number"},
                    },
                },
                "description": "Auftragspositionen (für create_sale_order).",
            },
            "location_id": {
                "type": "integer",
                "description": "Lagerort-ID (für get_stock).",
                "default": 1,
            },
            "limit": {"type": "integer", "default": 20, "description": "Max. Anzahl Ergebnisse."},
            "search_query": {"type": "string", "description": "Suchbegriff (für search_partners, list_products)."},
        },
        "required": ["action"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {"type": "array"},
            "total": {"type": "integer"},
            "partner": {"type": "object"},
            "product": {"type": "object"},
            "order": {"type": "object"},
            "stock": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.url = os.getenv("ODOO_URL", "")
        self.db = os.getenv("ODOO_DB", "")
        self.username = os.getenv("ODOO_USERNAME", "")
        self.password = os.getenv("ODOO_PASSWORD", "")
        self.uid: int | None = None
        self.models: Any = None
        self._connect()

    def _connect(self):
        """Stellt die Verbindung zu Odoo her."""
        if not all([self.url, self.db, self.username, self.password]):
            return

        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            auth_uid = common.authenticate(self.db, self.username, self.password, {})
            if isinstance(auth_uid, int):
                self.uid = auth_uid
            elif isinstance(auth_uid, str) and auth_uid.isdigit():
                self.uid = int(auth_uid)
            else:
                self.uid = None

            if self.uid is not None:
                self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        except Exception:
            self.uid = None
            self.models = None

    def _is_connected(self) -> bool:
        return bool(self.uid and self.models)

    def _search_read(self, model: str, domain: list[Any], fields: list[str] | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Führt eine search_read-Operation auf einem Odoo-Modell durch."""
        if not self._is_connected() or self.models is None or self.uid is None:
            return []
        try:
            raw_result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                "search_read",
                [domain],
                {"fields": fields, "limit": limit} if fields else {"limit": limit},
            )
            if not isinstance(raw_result, list):
                return []

            normalized: list[dict[str, Any]] = []
            for item in cast(list[Any], raw_result):
                normalized_item = _as_dict(item)
                if normalized_item:
                    normalized.append(normalized_item)
            return normalized
        except Exception:
            return []

    def _create(self, model: str, values: dict[str, Any]) -> int | None:
        """Erstellt einen neuen Datensatz in einem Odoo-Modell."""
        if not self._is_connected() or self.models is None or self.uid is None:
            return None
        try:
            raw_result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                "create",
                [values],
            )
            if isinstance(raw_result, int):
                return raw_result
            if isinstance(raw_result, str) and raw_result.isdigit():
                return int(raw_result)
            return None
        except Exception:
            return None

    def _write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        """Aktualisiert Datensätze in einem Odoo-Modell."""
        if not self._is_connected() or self.models is None or self.uid is None:
            return False
        try:
            raw_result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                "write",
                [ids, values],
            )
            return bool(raw_result)
        except Exception:
            return False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = str(input_data.get("action", "list_partners")).lower()

        if not self._is_connected():
            return {
                "success": False,
                "error": "Nicht mit Odoo verbunden. Prüfe ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD.",
            }

        if action == "list_partners":
            return self._list_partners(input_data)
        elif action == "create_partner":
            return self._create_partner(input_data)
        elif action == "search_partners":
            return self._search_partners(input_data)
        elif action == "list_products":
            return self._list_products(input_data)
        elif action == "get_product":
            return self._get_product(input_data)
        elif action == "create_sale_order":
            return self._create_sale_order(input_data)
        elif action == "list_sale_orders":
            return self._list_sale_orders(input_data)
        elif action == "get_stock":
            return self._get_stock(input_data)
        elif action == "list_categories":
            return self._list_categories(input_data)
        else:
            return {"success": False, "error": f"Unbekannte Aktion: {action}"}

    def _list_partners(self, input_data: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(100, int(input_data.get("limit", 20))))
        fields = ["id", "name", "email", "phone", "mobile", "street", "city", "country_id", "company_type"]
        results = self._search_read("res.partner", [("is_company", "=", True)], fields, limit)
        return {
            "success": True,
            "data": results,
            "total": len(results),
            "message": f"{len(results)} Partner gefunden.",
        }

    def _create_partner(self, input_data: dict[str, Any]) -> dict[str, Any]:
        name = str(input_data.get("partner_name", "")).strip()
        if not name:
            return {"success": False, "error": "partner_name ist erforderlich."}

        values: dict[str, Any] = {
            "name": name,
            "is_company": True,
        }
        if input_data.get("partner_email"):
            values["email"] = str(input_data["partner_email"])
        if input_data.get("partner_phone"):
            values["phone"] = str(input_data["partner_phone"])

        partner_id = self._create("res.partner", values)
        if partner_id:
            return {"success": True, "partner": {"id": partner_id, "name": name}, "message": "Partner erstellt."}
        return {"success": False, "error": "Partner konnte nicht erstellt werden."}

    def _search_partners(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("search_query", "")).strip()
        if not query:
            return {"success": False, "error": "search_query ist erforderlich."}
        fields = ["id", "name", "email", "phone"]
        results = self._search_read(
            "res.partner",
            [("name", "ilike", query)],
            fields,
            20,
        )
        return {"success": True, "data": results, "total": len(results)}

    def _list_products(self, input_data: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(100, int(input_data.get("limit", 20))))
        fields = ["id", "name", "default_code", "list_price", "standard_price", "type", "categ_id"]
        results = self._search_read("product.product", [], fields, limit)
        return {"success": True, "data": results, "total": len(results)}

    def _get_product(self, input_data: dict[str, Any]) -> dict[str, Any]:
        product_id = int(input_data.get("product_id", 0))
        if not product_id:
            return {"success": False, "error": "product_id ist erforderlich."}
        fields = ["id", "name", "default_code", "list_price", "standard_price", "type", "categ_id", "description"]
        results = self._search_read("product.product", [("id", "=", product_id)], fields, 1)
        if results:
            return {"success": True, "product": results[0]}
        return {"success": False, "error": "Produkt nicht gefunden."}

    def _list_sale_orders(self, input_data: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(100, int(input_data.get("limit", 20))))
        fields = ["id", "name", "partner_id", "state", "amount_total", "date_order", "user_id"]
        results = self._search_read("sale.order", [], fields, limit)
        return {"success": True, "data": results, "total": len(results)}

    def _create_sale_order(self, input_data: dict[str, Any]) -> dict[str, Any]:
        partner_name = str(input_data.get("partner_name", "")).strip()
        if not partner_name:
            return {"success": False, "error": "partner_name ist erforderlich."}

        # Partner suchen oder erstellen
        partners = self._search_read("res.partner", [("name", "ilike", partner_name)], ["id"], 1)
        if partners:
            partner_id = partners[0]["id"]
        else:
            partner_id = self._create("res.partner", {"name": partner_name, "is_company": True})

        if not partner_id:
            return {"success": False, "error": "Partner konnte nicht gefunden oder erstellt werden."}

        # Order lines
        order_lines = input_data.get("order_lines", [])
        if not order_lines:
            return {"success": False, "error": "order_lines ist erforderlich."}

        order_line_ids: list[tuple[int, int, dict[str, Any]]] = []
        for line in order_lines:
            product_id = line.get("product_id")
            quantity = line.get("quantity", 1)
            price_unit = line.get("price_unit", 0)
            if product_id:
                order_line_ids.append((0, 0, {"product_id": product_id, "product_uom_qty": quantity, "price_unit": price_unit}))

        if not order_line_ids:
            return {"success": False, "error": "Mindestens eine gültige Auftragsposition erforderlich."}

        order_id = self._create("sale.order", {
            "partner_id": partner_id,
            "order_line": order_line_ids,
        })

        if order_id:
            return {"success": True, "order": {"id": order_id}, "message": f"Auftrag {order_id} erstellt."}
        return {"success": False, "error": "Auftrag konnte nicht erstellt werden."}

    def _get_stock(self, input_data: dict[str, Any]) -> dict[str, Any]:
        product_id = int(input_data.get("product_id", 0))
        location_id = int(input_data.get("location_id", 1))
        if not product_id:
            return {"success": False, "error": "product_id ist erforderlich."}

        fields = ["product_id", "location_id", "quantity", "reserved_quantity"]
        results = self._search_read(
            "stock.quant",
            [("product_id", "=", product_id), ("location_id", "=", location_id)],
            fields,
            10,
        )
        if results:
            return {
                "success": True,
                "stock": results[0],
                "message": f"Lagerbestand: {results[0].get('quantity', 0)} Stück",
            }
        return {"success": True, "stock": {"quantity": 0}, "message": "Kein Bestand für dieses Produkt."}

    def _list_categories(self, input_data: dict[str, Any]) -> dict[str, Any]:
        fields = ["id", "name", "parent_id", "complete_name"]
        results = self._search_read("product.category", [], fields, 50)
        return {"success": True, "data": results, "total": len(results)}


