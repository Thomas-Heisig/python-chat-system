# packages/plugins/product_catalog/plugin.py
from __future__ import annotations

import json
import os
from typing import Any, cast


PLUGIN_META: dict[str, Any] = {
    "id": "product_catalog",
    "name": "Product Catalog",
    "description": "Durchsucht den internen Produktkatalog für Natursteinprodukte",
    "category": "🛒 E-Commerce & Preis",
    "apiKeyRequired": False,
    "intentPattern": r"\b(katalog|produkt|fliesen|platte|arbeitsplatte|stein|bestellen|angebot)\b",
    "status": "implemented",
    "settingsFields": [],
}


# --- Interne Produktdatenbank (Beispielkatalog) ---
# In einer realen Umgebung würde diese aus einer Datenbank oder API kommen.
_CATALOG_DB: list[dict[str, Any]] = [
    {
        "id": "P001",
        "name": "Nero Assoluto Granit Fliese 60x60",
        "category": "fliese",
        "material": "granit",
        "variant": "nero assoluto",
        "format": "60x60",
        "thickness": "2cm",
        "finish": "polished",
        "price": 185.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 120,
        "description": "Edle schwarze Granitfliese, poliert, für Böden und Arbeitsplatten.",
        "tags": ["granit", "schwarz", "fliese", "innen"],
        "image_url": "/images/nero-assoluto-60x60.jpg",
    },
    {
        "id": "P002",
        "name": "Bianco Sardo Marmor Fliese 40x40",
        "category": "fliese",
        "material": "marmor",
        "variant": "bianco sardo",
        "format": "40x40",
        "thickness": "2cm",
        "finish": "honed",
        "price": 215.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 85,
        "description": "Weißer Marmor, geschliffen, für Bäder und Wandverkleidungen.",
        "tags": ["marmor", "weiß", "fliese", "bad"],
        "image_url": "/images/bianco-sardo-40x40.jpg",
    },
    {
        "id": "P003",
        "name": "Giallo Venezia Granit Fliese 30x60",
        "category": "fliese",
        "material": "granit",
        "variant": "giallo venezia",
        "format": "30x60",
        "thickness": "2cm",
        "finish": "polished",
        "price": 195.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 200,
        "description": "Gelb-goldene Granitfliese, poliert, für moderne Küchen.",
        "tags": ["granit", "gelb", "fliese", "küche"],
        "image_url": "/images/giallo-venezia-30x60.jpg",
    },
    {
        "id": "P004",
        "name": "Carrara Marmor Platte 300x140cm",
        "category": "platte",
        "material": "marmor",
        "variant": "carrara",
        "format": "300x140",
        "thickness": "3cm",
        "finish": "polished",
        "price": 450.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 15,
        "description": "Großformatige Carrara-Marmorplatte für Arbeitsplatten und Tische.",
        "tags": ["marmor", "weiß", "platte", "arbeitsplatte"],
        "image_url": "/images/carrara-platte.jpg",
    },
    {
        "id": "P005",
        "name": "Quarzit Bianco Platte 250x120cm",
        "category": "platte",
        "material": "quarzit",
        "variant": "bianco",
        "format": "250x120",
        "thickness": "3cm",
        "finish": "honed",
        "price": 380.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 10,
        "description": "Weiße Quarzitplatte, geschliffen, extrem hart und säurebeständig.",
        "tags": ["quarzit", "weiß", "platte", "arbeitsplatte"],
        "image_url": "/images/quarzit-bianco-platte.jpg",
    },
    {
        "id": "P006",
        "name": "Schiefer Grau Fliese 30x60",
        "category": "fliese",
        "material": "schiefer",
        "variant": "grau",
        "format": "30x60",
        "thickness": "2cm",
        "finish": "brushed",
        "price": 120.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 300,
        "description": "Graue Schieferfliese, gebürstet, für Außenbereiche und Terrassen.",
        "tags": ["schiefer", "grau", "fliese", "außen", "terrasse"],
        "image_url": "/images/schiefer-grau-30x60.jpg",
    },
    {
        "id": "P007",
        "name": "Travertin Classico Fliese 40x40",
        "category": "fliese",
        "material": "travertin",
        "variant": "classico",
        "format": "40x40",
        "thickness": "2cm",
        "finish": "tumbled",
        "price": 150.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 180,
        "description": "Klassischer Travertin, getrommelt, für rustikale Böden.",
        "tags": ["travertin", "beige", "fliese", "rustikal"],
        "image_url": "/images/travertin-classico-40x40.jpg",
    },
    {
        "id": "P008",
        "name": "Nero Assoluto Granit Arbeitsplatte 240x60cm",
        "category": "arbeitsplatte",
        "material": "granit",
        "variant": "nero assoluto",
        "format": "240x60",
        "thickness": "3cm",
        "finish": "polished",
        "price": 320.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 8,
        "description": "Fertige Granit-Arbeitsplatte, schwarz poliert, mit abgeschrägter Kante.",
        "tags": ["granit", "schwarz", "arbeitsplatte", "küche"],
        "image_url": "/images/nero-assoluto-arbeitsplatte.jpg",
    },
    {
        "id": "P009",
        "name": "Marmor Statuario Fliese 60x60",
        "category": "fliese",
        "material": "marmor",
        "variant": "statuario",
        "format": "60x60",
        "thickness": "2cm",
        "finish": "polished",
        "price": 320.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 45,
        "description": "Exklusive Statuario-Marmorfliese, poliert, für luxuriöse Projekte.",
        "tags": ["marmor", "weiß", "fliese", "luxus"],
        "image_url": "/images/statuario-60x60.jpg",
    },
    {
        "id": "P010",
        "name": "Quarzit Nero Fliese 60x60",
        "category": "fliese",
        "material": "quarzit",
        "variant": "nero",
        "format": "60x60",
        "thickness": "2cm",
        "finish": "honed",
        "price": 225.0,
        "currency": "EUR",
        "unit": "qm",
        "stock": 60,
        "description": "Schwarze Quarzitfliese, geschliffen, für moderne Böden.",
        "tags": ["quarzit", "schwarz", "fliese", "modern"],
        "image_url": "/images/quarzit-nero-60x60.jpg",
    },
]


class ProductCatalogPlugin:
    name = "product_catalog"
    description = "Durchsucht den internen Produktkatalog für Natursteinprodukte"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Suchbegriff (Name, Material, Variante, Kategorie, Tags).",
            },
            "material": {
                "type": "string",
                "description": "Material (z.B. Granit, Marmor, Quarzit, Schiefer, Travertin).",
            },
            "category": {
                "type": "string",
                "enum": ["fliese", "platte", "arbeitsplatte", "boden", "fassade", "treppe"],
                "description": "Produktkategorie.",
            },
            "variant": {
                "type": "string",
                "description": "Variante/Name des Steins (z.B. 'nero assoluto', 'carrara').",
            },
            "min_price": {
                "type": "number",
                "description": "Mindestpreis (in der gewählten Währung).",
            },
            "max_price": {
                "type": "number",
                "description": "Maximalpreis (in der gewählten Währung).",
            },
            "in_stock": {
                "type": "boolean",
                "default": True,
                "description": "Nur verfügbare Produkte anzeigen.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 10,
                "description": "Maximale Anzahl von Ergebnissen.",
            },
            "sort_by": {
                "type": "string",
                "enum": ["name", "price", "stock"],
                "default": "name",
                "description": "Sortierkriterium.",
            },
            "sort_order": {
                "type": "string",
                "enum": ["asc", "desc"],
                "default": "asc",
                "description": "Sortierreihenfolge.",
            },
            "currency": {
                "type": "string",
                "enum": ["EUR", "USD", "CHF", "GBP"],
                "default": "EUR",
                "description": "Währung für Preisangaben.",
            },
        },
        "required": ["query"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "total": {"type": "integer"},
            "results": {"type": "array"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.storage_path = os.getenv("CATALOG_STORAGE_PATH", "./catalog.json")
        self._ensure_storage()

    def _ensure_storage(self):
        """Stellt sicher, dass die Katalogdatei existiert."""
        if not os.path.exists(self.storage_path):
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(_CATALOG_DB, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _load_catalog(self) -> list[dict[str, Any]]:
        """Lädt den Katalog aus der JSON-Datei."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return _CATALOG_DB

    def _save_catalog(self, catalog: list[dict[str, Any]]):
        """Speichert den Katalog in der JSON-Datei."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(catalog, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _search_products(
        self,
        query: str,
        material: str | None,
        category: str | None,
        variant: str | None,
        min_price: float | None,
        max_price: float | None,
        in_stock: bool,
        limit: int,
        sort_by: str,
        sort_order: str,
        currency: str,
    ) -> list[dict[str, Any]]:
        """Durchsucht den Katalog nach Produkten."""
        catalog = self._load_catalog()
        results: list[dict[str, Any]] = []

        # Umrechnungsfaktoren für Währungen (Beispielwerte)
        conversion_rates = {"EUR": 1.0, "USD": 1.09, "CHF": 0.98, "GBP": 0.85}

        query_lower = query.lower() if query else ""

        for product in catalog:
            # Verfügbarkeit prüfen
            if in_stock and product.get("stock", 0) <= 0:
                continue

            # Materialfilter
            if material and material.lower() != product.get("material", "").lower():
                continue

            # Kategoriefilter
            if category and category.lower() != product.get("category", "").lower():
                continue

            # Variantenfilter
            if variant and variant.lower() != product.get("variant", "").lower():
                continue

            # Preis (in EUR, dann umrechnen)
            price_eur = float(product.get("price", 0))
            price_target = price_eur * conversion_rates.get(currency, 1.0)

            if min_price is not None and price_target < min_price:
                continue
            if max_price is not None and price_target > max_price:
                continue

            # Textsuche (query)
            if query_lower:
                tags_raw = product.get("tags", [])
                tags: list[str] = []
                if isinstance(tags_raw, list):
                    for tag_raw in cast(list[Any], tags_raw):
                        tags.append(str(tag_raw))
                search_fields: list[str] = [
                    str(product.get("name", "")).lower(),
                    str(product.get("description", "")).lower(),
                    str(product.get("material", "")).lower(),
                    str(product.get("variant", "")).lower(),
                    " ".join(tags).lower(),
                ]
                if not any(query_lower in field for field in search_fields):
                    continue

            # Produkt kopieren und Preis in Zielwährung umrechnen
            product_copy = product.copy()
            product_copy["price_target"] = round(price_target, 2)
            product_copy["currency"] = currency
            results.append(product_copy)

        # Sortieren
        reverse = (sort_order == "desc")
        if sort_by == "price":
            results.sort(key=lambda item: float(item.get("price_target", 0)), reverse=reverse)
        elif sort_by == "stock":
            results.sort(key=lambda item: int(item.get("stock", 0)), reverse=reverse)
        else:  # name
            results.sort(key=lambda item: str(item.get("name", "")), reverse=reverse)

        # Limit anwenden
        return results[:limit]

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"success": False, "error": "Suchbegriff (query) ist erforderlich."}

        material = str(input_data.get("material", "")).strip() or None
        category = str(input_data.get("category", "")).strip() or None
        variant = str(input_data.get("variant", "")).strip() or None
        min_price = input_data.get("min_price")
        max_price = input_data.get("max_price")
        if min_price is not None:
            min_price = float(min_price)
        if max_price is not None:
            max_price = float(max_price)
        in_stock = bool(input_data.get("in_stock", True))
        limit = max(1, min(50, int(input_data.get("limit", 10))))
        sort_by = str(input_data.get("sort_by", "name")).strip()
        sort_order = str(input_data.get("sort_order", "asc")).strip()
        currency = str(input_data.get("currency", "EUR")).strip().upper()

        if currency not in ["EUR", "USD", "CHF", "GBP"]:
            currency = "EUR"

        results = self._search_products(
            query=query,
            material=material,
            category=category,
            variant=variant,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            currency=currency,
        )

        # Formatierte Ausgabe
        formatted_results: list[dict[str, Any]] = []
        for product in results:
            formatted_results.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "category": product.get("category"),
                "material": product.get("material"),
                "variant": product.get("variant"),
                "format": product.get("format"),
                "thickness": product.get("thickness"),
                "finish": product.get("finish"),
                "price": product.get("price_target"),
                "currency": product.get("currency"),
                "unit": product.get("unit", "qm"),
                "stock": product.get("stock"),
                "description": product.get("description"),
                "tags": product.get("tags", []),
            })

        return {
            "success": True,
            "total": len(results),
            "results": formatted_results,
            "message": f"{len(results)} Produkte gefunden.",
        }

