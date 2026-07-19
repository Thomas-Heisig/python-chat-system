from __future__ import annotations

import json
import os
import re
from html import unescape
from typing import Any, cast
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import httpx

# ----------------------------------------------------------------------
# Metadaten – dynamische Settings (werden vom Frontend geladen)
# ----------------------------------------------------------------------
PLUGIN_META: dict[str, Any] = {
    "id": "pricefinder",
    "name": "Price Finder",
    "description": "Universelle Preisabfrage für Material, Service und Zubehör (lokal + Internet-Fallback)",
    "category": "🛒 E-Commerce & Preis",
    "apiKeyRequired": False,
    "intentPattern": r"\b(preis|presi|kosten|euro|€|qm|preisliste|angebot|kalkulation|verlegung|einbau|montage)\b",
    "status": "implemented",
    "settingsFields": [
        # ... (wie bereits definiert, bleiben unverändert)
        # Ich kopiere sie aus der vorherigen Version, aber wir können sie vereinfachen
        {
            "key": "mode",
            "label": "Betriebsmodus",
            "type": "select",
            "default": "hybrid",
            "group": "Allgemein",
            "options": [
                {"value": "local-only", "label": "Nur lokale Daten"},
                {"value": "hybrid", "label": "Hybrid (lokal + Internet-Fallback)"},
                {"value": "internet-only", "label": "Nur Internet"},
            ],
        },
        {
            "key": "enable_web_fallback",
            "label": "Internet-Fallback aktiv",
            "type": "boolean",
            "default": True,
            "group": "Internet",
        },
        # ... weitere Settings bleiben gleich (aus Platzgründen nicht wiederholt)
    ],
}

# ----------------------------------------------------------------------
# Lokale Preis-Datenbank (Default-Werte, werden mit JSON-Datei gemerged)
# ----------------------------------------------------------------------
_DEFAULT_PRICE_DB: dict[str, Any] = {
    "granit": {
        "name": "Granit",
        "entity_type": "material",
        "variants": {
            "nero assoluto": {"price_per_qm": 180.0, "currency": "EUR", "min_order": 2},
            "bianco sardo": {"price_per_qm": 210.0, "currency": "EUR", "min_order": 2},
            "giallo venezia": {"price_per_qm": 195.0, "currency": "EUR", "min_order": 2},
            "rosso levanto": {"price_per_qm": 220.0, "currency": "EUR", "min_order": 2},
            "verde marina": {"price_per_qm": 205.0, "currency": "EUR", "min_order": 2},
        },
        "formats": {
            "30x60": {"price_per_qm": 180.0},
            "40x40": {"price_per_qm": 175.0},
            "60x60": {"price_per_qm": 185.0},
            "80x80": {"price_per_qm": 195.0},
        },
        "thickness": {"2cm": 1.0, "3cm": 1.3, "4cm": 1.6},
        "unit": "qm",
    },
    "marmor": {
        "name": "Marmor",
        "entity_type": "material",
        "variants": {
            "carrara": {"price_per_qm": 220.0, "currency": "EUR", "min_order": 2},
            "calacatta": {"price_per_qm": 280.0, "currency": "EUR", "min_order": 2},
            "statuario": {"price_per_qm": 320.0, "currency": "EUR", "min_order": 2},
            "verde guatemala": {"price_per_qm": 240.0, "currency": "EUR", "min_order": 2},
        },
        "formats": {"30x60": {"price_per_qm": 220.0}, "40x40": {"price_per_qm": 215.0}, "60x60": {"price_per_qm": 225.0}},
        "thickness": {"2cm": 1.0, "3cm": 1.4, "4cm": 1.8},
        "unit": "qm",
    },
    "service:verlegung": {
        "name": "Verlegung",
        "entity_type": "service",
        "category": "installation",
        "price": 45.0,
        "currency": "EUR",
        "unit": "qm",
    },
    "service:einbau": {
        "name": "Einbau",
        "entity_type": "service",
        "category": "installation",
        "price": 55.0,
        "currency": "EUR",
        "unit": "qm",
    },
    "service:versiegelung": {
        "name": "Versiegelung",
        "entity_type": "service",
        "category": "care",
        "price": 18.0,
        "currency": "EUR",
        "unit": "qm",
    },
    "accessory:fugenmasse": {
        "name": "Fugenmasse",
        "entity_type": "accessory",
        "price": 14.0,
        "currency": "EUR",
        "unit": "stueck",
    },
    "accessory:kleber": {
        "name": "Kleber",
        "entity_type": "accessory",
        "price": 22.0,
        "currency": "EUR",
        "unit": "stueck",
    },
}


class PriceFinderPlugin:
    name = "pricefinder"
    description = "Universelle Preisabfrage mit Internet-Fallback"

    # ------------------------------------------------------------------
    # Konstruktor & Config
    # ------------------------------------------------------------------
    def __init__(self):
        self.storage_path = os.getenv("PRICE_STORAGE_PATH", "./prices.json")
        self.mode = os.getenv("PRICEFINDER_MODE", "hybrid").strip().lower()
        self.enable_web_fallback = os.getenv("PRICEFINDER_ENABLE_WEB_FALLBACK", "true").strip().lower() not in {"0", "false", "no"}
        self.default_currency = os.getenv("PRICEFINDER_DEFAULT_CURRENCY", "EUR").strip().upper() or "EUR"
        self.default_unit = os.getenv("PRICEFINDER_DEFAULT_UNIT", "qm").strip().lower() or "qm"
        self.default_entity_type = os.getenv("PRICEFINDER_DEFAULT_ENTITY_TYPE", "material").strip().lower() or "material"
        self.timeout_seconds = max(3.0, float(os.getenv("PRICEFINDER_HTTP_TIMEOUT_SECONDS", "15") or 15))
        self.price_min = float(os.getenv("PRICEFINDER_PRICE_MIN", "1") or 1)
        self.price_max = float(os.getenv("PRICEFINDER_PRICE_MAX", "10000") or 10000)
        self.auto_derive_material = os.getenv("PRICEFINDER_AUTO_DERIVE_MATERIAL", "true").strip().lower() not in {"0", "false", "no"}
        self.return_raw_search_text = os.getenv("PRICEFINDER_RETURN_RAW_SEARCH_TEXT", "false").strip().lower() in {"1", "true", "yes"}
        self.enable_debug_trace = os.getenv("PRICEFINDER_ENABLE_DEBUG_TRACE", "false").strip().lower() in {"1", "true", "yes"}
        self.search_provider = os.getenv("PRICEFINDER_SEARCH_PROVIDER", "auto").strip().lower() or "auto"
        self.enable_material_details = os.getenv("PRICEFINDER_ENABLE_MATERIAL_DETAILS", "true").strip().lower() not in {"0", "false", "no"}
        self.enable_google_image_fallback = os.getenv("PRICEFINDER_ENABLE_GOOGLE_IMAGE", "false").strip().lower() not in {"0", "false", "no"}
        self.enable_knowledge_graph = os.getenv("PRICEFINDER_ENABLE_KNOWLEDGE_GRAPH", "true").strip().lower() not in {"0", "false", "no"}

        self._ensure_storage()

    # ------------------------------------------------------------------
    # Lokale Speicherverwaltung
    # ------------------------------------------------------------------
    def _ensure_storage(self) -> None:
        if os.path.exists(self.storage_path):
            return
        try:
            parent = os.path.dirname(self.storage_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(_DEFAULT_PRICE_DB, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_prices(self) -> dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Merge mit Defaults, damit neue Einträge verfügbar sind
                    merged = dict(_DEFAULT_PRICE_DB)
                    merged.update(cast(dict[str, Any], data))
                    return merged
        except Exception:
            pass
        return dict(_DEFAULT_PRICE_DB)

    def _save_prices(self, data: dict[str, Any]) -> None:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------
    def _normalize_entity_type(self, entity_type: str | None) -> str:
        value = (entity_type or "").strip().lower()
        if value in {"material", "service", "accessory"}:
            return value
        return self.default_entity_type

    def _normalize_search_url(self, raw_url: str) -> str:
        url = (raw_url or "").strip()
        if not url:
            return ""

        if url.startswith("//"):
            url = f"https:{url}"
        elif url.startswith("/"):
            url = urljoin("https://duckduckgo.com", url)

        parsed = urlparse(url)
        if parsed.netloc.endswith("duckduckgo.com"):
            query = parse_qs(parsed.query)
            uddg = query.get("uddg", [""])[0]
            if uddg:
                return unquote(uddg)
        return url

    def _source_weight(self, provider: str, url: str) -> float:
        provider_weights = {
            "google": 1.0,
            "bing": 0.95,
            "duckduckgo_html": 0.9,
            "duckduckgo": 0.8,
        }
        base = provider_weights.get(provider.strip().lower(), 0.85)
        lower_url = (url or "").lower()
        if not lower_url:
            return round(base * 0.75, 3)
        if "wikipedia.org" in lower_url:
            return 0.0
        if any(token in lower_url for token in ["idealo", "geizhals", "preis", "shop", "store", "produkt"]):
            return round(base * 1.1, 3)
        return round(base, 3)

    # ------------------------------------------------------------------
    # Externe API-Aufrufe (Wikipedia, Google Image, Knowledge Graph)
    # ------------------------------------------------------------------
    async def _fetch_wikipedia(self, query: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=min(10.0, self.timeout_seconds)) as client:
                search_resp = await client.get(
                    "https://de.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "format": "json",
                        "srlimit": 1,
                    },
                )
                search_resp.raise_for_status()
                search_data = search_resp.json()
                pages = cast(list[Any], cast(dict[str, Any], search_data.get("query", {})).get("search", []))
                if not pages:
                    return {}

                first = cast(dict[str, Any], pages[0])
                page_title = str(first.get("title", "")).strip()
                if not page_title:
                    return {}

                extract_resp = await client.get(
                    "https://de.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "prop": "extracts|pageimages",
                        "exintro": True,
                        "explaintext": True,
                        "titles": page_title,
                        "format": "json",
                        "pithumbsize": 400,
                        "redirects": 1,
                    },
                )
                extract_resp.raise_for_status()
                extract_data = extract_resp.json()
                pages_map = cast(dict[str, Any], cast(dict[str, Any], extract_data.get("query", {})).get("pages", {}))
                for page_data_raw in pages_map.values():
                    page_data = cast(dict[str, Any], page_data_raw)
                    thumb = cast(dict[str, Any], page_data.get("thumbnail", {})) if isinstance(page_data.get("thumbnail"), dict) else {}
                    return {
                        "url": f"https://de.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
                        "extract": str(page_data.get("extract", "")).strip(),
                        "image_url": str(thumb.get("source", "")).strip() or None,
                    }
        except Exception:
            pass
        return {}

    async def _fetch_google_image(self, query: str) -> str | None:
        if not self.enable_google_image_fallback:
            return None
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
        cx = os.getenv("GOOGLE_SEARCH_CX", "").strip()
        if not api_key or not cx:
            return None
        try:
            async with httpx.AsyncClient(timeout=min(10.0, self.timeout_seconds)) as client:
                resp = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": api_key,
                        "cx": cx,
                        "q": query,
                        "searchType": "image",
                        "num": 1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                items = cast(list[Any], cast(dict[str, Any], data).get("items", []))
                if items:
                    first = cast(dict[str, Any], items[0])
                    link = str(first.get("link", "")).strip()
                    return link or None
        except Exception:
            pass
        return None

    async def _fetch_knowledge_graph(self, query: str) -> dict[str, Any]:
        if not self.enable_knowledge_graph:
            return {}
        api_key = os.getenv("GOOGLE_KNOWLEDGE_GRAPH_API_KEY", "").strip()
        if not api_key:
            return {}
        try:
            async with httpx.AsyncClient(timeout=min(10.0, self.timeout_seconds)) as client:
                resp = await client.get(
                    "https://kgsearch.googleapis.com/v1/entities:search",
                    params={
                        "query": query,
                        "key": api_key,
                        "limit": 1,
                        "languages": "de",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                items = cast(list[Any], cast(dict[str, Any], data).get("itemListElement", []))
                if not items:
                    return {}
                result = cast(dict[str, Any], cast(dict[str, Any], items[0]).get("result", {}))
                detailed = cast(dict[str, Any], result.get("detailedDescription", {})) if isinstance(result.get("detailedDescription"), dict) else {}
                return {
                    "name": str(result.get("name", "")).strip(),
                    "description": str(result.get("description", "")).strip(),
                    "detailed_description": str(detailed.get("articleBody", "")).strip(),
                }
        except Exception:
            pass
        return {}

    # ------------------------------------------------------------------
    # Websuche (mehrere Provider)
    # ------------------------------------------------------------------
    async def _search_web_duckduckgo_api(self, query: str) -> dict[str, Any]:
        text_parts: list[str] = []
        hits: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            params: dict[str, Any] = {"q": query, "format": "json", "no_html": 1, "no_redirect": 1, "skip_disambig": 1}
            response = await client.get("https://api.duckduckgo.com/", params=params)
            response.raise_for_status()
            data = response.json()

            abstract_text = str(data.get("AbstractText", "")).strip()
            abstract_url = str(data.get("AbstractURL", "")).strip()
            if abstract_text:
                text_parts.append(abstract_text)
                hits.append(
                    {
                        "title": str(data.get("Heading", "")).strip() or query,
                        "url": abstract_url,
                        "snippet": abstract_text,
                        "provider": "duckduckgo",
                    }
                )

            def _collect_related(items: list[Any]) -> None:
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    item_dict = cast(dict[str, Any], item)
                    txt = str(item_dict.get("Text", "")).strip()
                    if txt:
                        text_parts.append(txt)
                        hits.append(
                            {
                                "title": str(item_dict.get("FirstURL", "")).strip() or query,
                                "url": str(item_dict.get("FirstURL", "")).strip(),
                                "snippet": txt,
                                "provider": "duckduckgo",
                            }
                        )
                    sub = item_dict.get("Topics", [])
                    if isinstance(sub, list) and sub:
                        _collect_related(cast(list[Any], sub))

            related = data.get("RelatedTopics", [])
            if isinstance(related, list) and related:
                _collect_related(cast(list[Any], related))

        return {
            "success": bool(text_parts),
            "text": "\n".join(text_parts),
            "hits": hits,
            "source": "duckduckgo",
            "error": "Keine verwertbaren Suchtexte gefunden." if not text_parts else "",
        }

    async def _search_web_duckduckgo_html(self, query: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            encoded = quote_plus(query)
            response = await client.get(f"https://html.duckduckgo.com/html/?q={encoded}")
            response.raise_for_status()
            html = response.text
            extracted = self._extract_text_from_html(html)

        hits: list[dict[str, Any]] = []
        seen_keys: set[str] = set()

        result_block_pattern = re.compile(r'(?is)<(?:div|article)[^>]*class="[^"]*(?:result|web-result)[^"]*"[^>]*>(?P<block>.*?)</(?:div|article)>')
        title_pattern = re.compile(r'(?is)<a[^>]*class="[^"]*(?:result__a|result-link|result__url|result-link__url)[^"]*"[^>]*href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>')
        snippet_pattern = re.compile(r'(?is)<(?:a|div|span|p)[^>]*class="[^"]*(?:result__snippet|snippet|result-snippet|result__extras__url)[^"]*"[^>]*>(?P<snippet>.*?)</(?:a|div|span|p)>')

        def _add_hit(raw_url: str, raw_title: str, raw_snippet: str) -> None:
            snippet = self._extract_text_from_html(raw_snippet)
            title = self._extract_text_from_html(raw_title)
            url = self._normalize_search_url(raw_url)
            if not snippet:
                return
            dedupe_key = f"{url}|{snippet[:120].lower()}"
            if dedupe_key in seen_keys:
                return
            seen_keys.add(dedupe_key)
            hits.append(
                {
                    "title": title or query,
                    "url": url,
                    "snippet": snippet,
                    "provider": "duckduckgo_html",
                }
            )

        for block_match in result_block_pattern.finditer(html):
            block = block_match.group("block") or ""
            title_match = title_pattern.search(block)
            snippet_match = snippet_pattern.search(block)
            if title_match and snippet_match:
                _add_hit(
                    title_match.group("url") or "",
                    title_match.group("title") or "",
                    snippet_match.group("snippet") or "",
                )

        if not hits:
            generic_link_pattern = re.compile(r'(?is)<a[^>]*href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>')
            for link_match in generic_link_pattern.finditer(html):
                raw_url = link_match.group("url") or ""
                normalized_url = self._normalize_search_url(raw_url)
                if not normalized_url.startswith("http"):
                    continue
                if any(token in normalized_url.lower() for token in ["duckduckgo.com/y.js", "/about", "/html/?q="]):
                    continue
                raw_title = link_match.group("title") or ""
                nearby = html[link_match.end() : link_match.end() + 700]
                nearby_snippet_match = snippet_pattern.search(nearby)
                raw_snippet = nearby_snippet_match.group("snippet") if nearby_snippet_match else ""
                _add_hit(raw_url, raw_title, raw_snippet)

        return {
            "success": bool(extracted),
            "text": extracted,
            "hits": hits,
            "source": "duckduckgo_html",
            "error": "Keine verwertbaren Suchtexte gefunden." if not extracted else "",
        }

    async def _search_web_google(self, query: str) -> dict[str, Any]:
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
        cx = os.getenv("GOOGLE_SEARCH_CX", "").strip()
        if not api_key or not cx:
            return {"success": False, "error": "Google Search API-Key oder CX fehlt."}

        snippets: list[str] = []
        hits: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": api_key, "cx": cx, "q": query, "num": 10},
            )
            response.raise_for_status()
            data = response.json()
            items = cast(list[Any], cast(dict[str, Any], data).get("items", []))
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_dict = cast(dict[str, Any], item)
                snippet = str(item_dict.get("snippet", "")).strip()
                if snippet:
                    snippets.append(snippet)
                    hits.append(
                        {
                            "title": str(item_dict.get("title", "")).strip() or query,
                            "url": str(item_dict.get("link", "")).strip(),
                            "snippet": snippet,
                            "provider": "google",
                        }
                    )

        return {
            "success": bool(snippets),
            "text": "\n".join(snippets),
            "hits": hits,
            "source": "google",
            "error": "Keine verwertbaren Suchtexte gefunden." if not snippets else "",
        }

    async def _search_web_bing(self, query: str) -> dict[str, Any]:
        api_key = os.getenv("BING_SEARCH_API_KEY", "").strip()
        if not api_key:
            return {"success": False, "error": "Bing Search API-Key fehlt."}

        snippets: list[str] = []
        hits: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                "https://api.bing.microsoft.com/v7.0/search",
                params={"q": query, "count": 10, "mkt": "de-DE"},
                headers={"Ocp-Apim-Subscription-Key": api_key},
            )
            response.raise_for_status()
            data = response.json()
            pages_raw = cast(dict[str, Any], data.get("webPages", {})).get("value", [])
            pages = cast(list[Any], pages_raw) if isinstance(pages_raw, list) else []
            for page_raw in pages:
                if not isinstance(page_raw, dict):
                    continue
                page_dict = cast(dict[str, Any], page_raw)
                snippet = str(page_dict.get("snippet", "")).strip()
                if snippet:
                    snippets.append(snippet)
                    hits.append(
                        {
                            "title": str(page_dict.get("name", "")).strip() or query,
                            "url": str(page_dict.get("url", "")).strip(),
                            "snippet": snippet,
                            "provider": "bing",
                        }
                    )

        return {
            "success": bool(snippets),
            "text": "\n".join(snippets),
            "hits": hits,
            "source": "bing",
            "error": "Keine verwertbaren Suchtexte gefunden." if not snippets else "",
        }

    async def _search_web(self, query: str) -> dict[str, Any]:
        provider = (self.search_provider or "auto").strip().lower()
        attempts: list[str]
        if provider == "duckduckgo":
            attempts = ["duckduckgo"]
        elif provider == "duckduckgo_html":
            attempts = ["duckduckgo_html"]
        elif provider == "google":
            attempts = ["google", "duckduckgo", "duckduckgo_html", "bing"]
        elif provider == "bing":
            attempts = ["bing", "duckduckgo", "duckduckgo_html", "google"]
        else:
            attempts = ["duckduckgo", "duckduckgo_html", "google", "bing"]

        errors: list[str] = []
        text_parts: list[str] = []
        collected_hits: list[dict[str, Any]] = []
        used_source = ""

        for source in attempts:
            try:
                if source == "duckduckgo":
                    result = await self._search_web_duckduckgo_api(query)
                elif source == "duckduckgo_html":
                    result = await self._search_web_duckduckgo_html(query)
                elif source == "google":
                    result = await self._search_web_google(query)
                else:
                    result = await self._search_web_bing(query)
            except Exception as exc:
                errors.append(f"{source}: {exc}")
                continue

            if result.get("success") and result.get("text"):
                text_parts.append(str(result.get("text", "")))
                if isinstance(result.get("hits"), list):
                    collected_hits.extend(cast(list[dict[str, Any]], result.get("hits", [])))
                used_source = source
                break

            err = str(result.get("error", "")).strip()
            if err:
                errors.append(f"{source}: {err}")

        if not text_parts:
            return {"success": False, "error": " | ".join(errors) if errors else "Keine verwertbaren Suchtexte gefunden."}
        return {
            "success": True,
            "text": "\n".join(text_parts),
            "hits": collected_hits,
            "source": used_source or "duckduckgo",
        }

    # ------------------------------------------------------------------
    # Text & Preis-Extraktion
    # ------------------------------------------------------------------
    def _extract_text_from_html(self, html: str) -> str:
        if not html:
            return ""
        normalized = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        normalized = re.sub(r"(?is)<[^>]+>", " ", normalized)
        normalized = unescape(normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def _extract_price_candidates(self, hits: list[dict[str, Any]], preferred_unit: str, query: str) -> list[dict[str, Any]]:
        unit_aliases = {
            "qm": ["qm", "m2", "m²"],
            "lfm": ["lfm", "laufmeter", "lm"],
            "stueck": ["stueck", "stück", "stk"],
        }
        unit_key = preferred_unit.strip().lower() or "qm"
        target_units = unit_aliases.get(unit_key, [unit_key])
        unit_pattern = "|".join(re.escape(u) for u in target_units)

        patterns = [
            re.compile(rf"(\d{{1,5}}(?:[\.,]\d{{1,2}})?)\s*(€|eur|euro|pln|z[łl]|usd|\$|chf|gbp)\s*(?:/|pro|je)\s*(?:{unit_pattern})", re.IGNORECASE),
            re.compile(rf"(\d{{1,5}}(?:[\.,]\d{{1,2}})?)\s*(?:{unit_pattern})\s*(€|eur|euro|pln|z[łl]|usd|\$|chf|gbp)", re.IGNORECASE),
            re.compile(r"(\d{1,5}(?:[\.,]\d{1,2})?)\s*(€|eur|euro|pln|z[łl]|usd|\$|chf|gbp)", re.IGNORECASE),
        ]

        candidates: list[dict[str, Any]] = []

        def _normalize_currency(raw: str) -> str:
            token = raw.strip().lower()
            if token in {"€", "eur", "euro"}:
                return "EUR"
            if token in {"pln", "zł", "zl"}:
                return "PLN"
            if token in {"usd", "$"}:
                return "USD"
            if token == "chf":
                return "CHF"
            if token == "gbp":
                return "GBP"
            return "EUR"
        for hit in hits:
            snippet = str(hit.get("snippet", "")).strip()
            provider = str(hit.get("provider", "")).strip().lower()
            url = str(hit.get("url", "")).strip()
            if not snippet:
                continue
            weight = self._source_weight(provider, url)
            if weight <= 0:
                continue
            for pattern in patterns:
                for match in pattern.findall(snippet):
                    if isinstance(match, tuple):
                        tuple_match = cast(tuple[Any, ...], match)
                        parts = [str(part) for part in tuple_match]
                        if not parts:
                            continue
                        raw = parts[0]
                        currency = _normalize_currency(parts[1]) if len(parts) > 1 else "EUR"
                    else:
                        raw = str(match)
                        currency = "EUR"
                    try:
                        value = float(str(raw).replace(",", "."))
                    except ValueError:
                        continue
                    if not (self.price_min <= value <= self.price_max):
                        continue
                    candidates.append(
                        {
                            "price": value,
                            "weight": weight,
                            "url": url,
                            "provider": provider,
                            "title": str(hit.get("title", "")).strip(),
                            "query": query,
                            "currency": currency,
                        }
                    )
        return candidates

    def _aggregate_weighted_prices(self, candidates: list[dict[str, Any]]) -> dict[str, float] | None:
        if not candidates:
            return None
        values = [float(c.get("price", 0.0) or 0.0) for c in candidates]
        weighted_sum = 0.0
        weight_sum = 0.0
        for candidate in candidates:
            price = float(candidate.get("price", 0.0) or 0.0)
            weight = max(0.01, float(candidate.get("weight", 0.0) or 0.0))
            weighted_sum += price * weight
            weight_sum += weight
        weighted_avg = weighted_sum / weight_sum if weight_sum > 0 else (sum(values) / len(values))
        return {
            "min": min(values),
            "max": max(values),
            "avg": weighted_avg,
            "count": float(len(values)),
        }

    def _triangulate_prices(self, all_candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not all_candidates:
            return None

        grouped: dict[str, list[tuple[float, float]]] = {}
        for candidate in all_candidates:
            currency = str(candidate.get("currency", "EUR")).strip().upper() or "EUR"
            price = float(candidate.get("price", 0.0) or 0.0)
            weight = max(0.01, float(candidate.get("weight", 0.0) or 0.0))
            if price <= 0:
                continue
            grouped.setdefault(currency, []).append((price, weight))

        if not grouped:
            return None

        triangulated: dict[str, Any] = {}
        for currency, pairs in grouped.items():
            values = [p for p, _ in pairs]
            weighted_sum = sum(p * w for p, w in pairs)
            weight_sum = sum(w for _, w in pairs)
            weighted_avg = weighted_sum / weight_sum if weight_sum > 0 else sum(values) / len(values)
            triangulated[currency] = {
                "min": min(values),
                "max": max(values),
                "avg": weighted_avg,
                "count": len(values),
            }

        if "PLN" in triangulated and "EUR" not in triangulated:
            rate = 4.3
            pln_data = cast(dict[str, Any], triangulated["PLN"])
            triangulated["EUR"] = {
                "min": float(pln_data["min"]) / rate,
                "max": float(pln_data["max"]) / rate,
                "avg": float(pln_data["avg"]) / rate,
                "count": int(pln_data["count"]),
                "source": "converted_from_PLN",
            }

        return triangulated

    # ------------------------------------------------------------------
    # Hauptmethode execute
    # ------------------------------------------------------------------
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        prices = self._load_prices()

        entity_name = str(input_data.get("entity_name", "")).strip()
        entity_type = self._normalize_entity_type(str(input_data.get("entity_type", self.default_entity_type)))

        material = str(input_data.get("material", "")).strip()
        variant = str(input_data.get("variant", "")).strip().lower()
        if material and not entity_name:
            entity_name = material
        if not entity_name:
            entity_name = variant or material

        if not entity_name:
            return {"success": False, "error": "entity_name ist erforderlich."}

        format_str = str(input_data.get("format", "")).strip()
        thickness = str(input_data.get("thickness", "2cm")).strip()
        surface_finish = str(input_data.get("surface_finish", "")).strip()
        application = str(input_data.get("application", "")).strip()

        area_raw = input_data.get("area", input_data.get("quantity", 1))
        try:
            area = max(0.1, float(area_raw or 1))
        except (TypeError, ValueError):
            area = 1.0

        internet_access_enabled = bool(input_data.get("internet_access_enabled", True))

        unit = str(input_data.get("unit", self.default_unit)).strip().lower() or self.default_unit
        currency = str(input_data.get("currency", self.default_currency)).strip().upper() or self.default_currency

        # ------------------------------------------------------------------
        # 1. Lokale Suche
        # ------------------------------------------------------------------
        material_details = await self._fetch_material_details(entity_name)
        if self.mode != "internet-only":
            local = self._search_local(prices, entity_name, entity_type, variant, format_str, thickness, area, currency)
            if local and local.get("success"):
                local.update(material_details)
                return local

        # ------------------------------------------------------------------
        # 2. Internet-Fallback (wenn aktiviert)
        # ------------------------------------------------------------------
        if (not self.enable_web_fallback) or (not internet_access_enabled):
            return {
                "success": False,
                "entity_name": entity_name,
                "entity_type": entity_type,
                "error": (
                    f"Keine lokalen Preise fuer '{entity_name}' gefunden. "
                    + ("Internetzugriff ist deaktiviert." if not internet_access_enabled else "Internet-Fallback ist deaktiviert.")
                ),
                "internet_access_enabled": internet_access_enabled,
            }

        # ------------------------------------------------------------------
        # 2a. Material-Details (Wikipedia, Bilder, etc.)
        # ------------------------------------------------------------------
        details = await self._fetch_material_details(entity_name)

        # ------------------------------------------------------------------
        # 2b. Preisrecherche im Web
        # ------------------------------------------------------------------
        query_variants = self._build_query_variants(
            entity_name=entity_name,
            entity_type=entity_type,
            unit=unit,
            thickness=thickness,
            surface_finish=surface_finish,
            application=application,
            format_str=format_str,
        )

        query_attempts: list[dict[str, Any]] = []
        all_hits: list[dict[str, Any]] = []
        all_candidates: list[dict[str, Any]] = []

        for query in query_variants:
            web_result = await self._search_web(query)
            attempt: dict[str, Any] = {
                "query": query,
                "success": bool(web_result.get("success")),
                "source": str(web_result.get("source", "")).strip(),
                "error": str(web_result.get("error", "")).strip(),
                "hit_count": len(cast(list[Any], web_result.get("hits", []))) if isinstance(web_result.get("hits"), list) else 0,
            }
            query_attempts.append(attempt)

            if not web_result.get("success"):
                continue

            hits = cast(list[dict[str, Any]], web_result.get("hits", [])) if isinstance(web_result.get("hits"), list) else []
            if hits:
                all_hits.extend(hits)
                candidates = self._extract_price_candidates(hits, unit, query)
                all_candidates.extend(candidates)

            if len(all_candidates) >= 5:
                break

        # ------------------------------------------------------------------
        # 2c. Preise aggregieren
        # ------------------------------------------------------------------
        triangulated = self._triangulate_prices(all_candidates)

        # ------------------------------------------------------------------
        # 2d. Ergebnis zusammenbauen
        # ------------------------------------------------------------------
        if triangulated:
            eur_data = cast(dict[str, Any], triangulated.get("EUR", {})) if isinstance(triangulated.get("EUR"), dict) else {}
            if not eur_data:
                for value in triangulated.values():
                    if isinstance(value, dict):
                        eur_data = cast(dict[str, Any], value)
                        break

            result: dict[str, Any] = {
                "success": True,
                "source": "internet",
                "entity_name": entity_name,
                "entity_type": entity_type,
                "currency": currency,
                "unit": unit,
                "prices": {
                    "min": round(float(eur_data.get("min", 0.0) or 0.0), 2),
                    "avg": round(float(eur_data.get("avg", 0.0) or 0.0), 2),
                    "max": round(float(eur_data.get("max", 0.0) or 0.0), 2),
                    "count": int(eur_data.get("count", 0) or 0),
                },
                "triangulated_prices": triangulated,
                "price_sources": [
                    {
                        "price": round(float(c.get("price", 0.0)), 2),
                        "weight": round(float(c.get("weight", 0.0)), 3),
                        "provider": str(c.get("provider", "")).strip(),
                        "url": str(c.get("url", "")).strip(),
                        "title": str(c.get("title", "")).strip(),
                        "query": str(c.get("query", "")).strip(),
                        "currency": str(c.get("currency", "EUR")).strip(),
                    }
                    for c in all_candidates[:15]
                ],
                "query_attempts": query_attempts,
                "search_query": query_attempts[0]["query"] if query_attempts else entity_name,
                "search_source": query_attempts[-1]["source"] if query_attempts else "",
                "thickness": thickness,
                "surface_finish": surface_finish,
                "application": application,
                "image_url": details.get("image_url"),
                "thumbnail_url": details.get("thumbnail_url"),
                "external_url": details.get("external_url"),
                "additional_info": details.get("additional_info", {}),
                "message": self._format_price_summary_triangulated(
                    entity_name=entity_name,
                    price_data=triangulated,
                    unit=unit,
                    application=application,
                    details=details,
                ),
            }
            if self.return_raw_search_text:
                result["raw_search_text"] = "\n".join([str(h.get("snippet", "")) for h in all_hits])
            return result

        # Keine Preise, aber Details vorhanden → nur Details zurückgeben
        if details.get("image_url") or details.get("additional_info"):
            return {
                "success": True,
                "source": "details-only",
                "entity_name": entity_name,
                "entity_type": entity_type,
                "currency": currency,
                "unit": unit,
                "image_url": details.get("image_url"),
                "thumbnail_url": details.get("thumbnail_url"),
                "external_url": details.get("external_url"),
                "additional_info": details.get("additional_info", {}),
                "message": f"Keine verlässlichen Preise für '{entity_name}' gefunden, aber Zusatzinformationen wurden geladen.",
            }

        return {
            "success": False,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "error": f"Keine Preise für '{entity_name}' gefunden.",
        }

    # ------------------------------------------------------------------
    # Hilfsmethoden für execute
    # ------------------------------------------------------------------
    async def _fetch_material_details(self, entity_name: str) -> dict[str, Any]:
        details: dict[str, Any] = {
            "image_url": None,
            "thumbnail_url": None,
            "external_url": None,
            "additional_info": {},
        }
        if not self.enable_material_details:
            return details

        wiki = await self._fetch_wikipedia(entity_name)
        if wiki:
            details["external_url"] = wiki.get("url")
            extract_text = str(wiki.get("extract", "")).strip()
            if extract_text:
                details["additional_info"]["wikipedia"] = extract_text
            wiki_image = wiki.get("image_url")
            if isinstance(wiki_image, str) and wiki_image.strip():
                details["image_url"] = wiki_image.strip()
                details["thumbnail_url"] = wiki_image.strip()

        if not details.get("image_url"):
            image_url = await self._fetch_google_image(entity_name)
            if image_url:
                details["image_url"] = image_url
                details["thumbnail_url"] = image_url

        kg_data = await self._fetch_knowledge_graph(entity_name)
        if kg_data:
            details["additional_info"]["knowledge_graph"] = kg_data

        return details

    def _search_local(
        self,
        prices: dict[str, Any],
        entity_name: str,
        entity_type: str,
        variant: str,
        format_str: str,
        thickness: str,
        area: float,
        currency: str,
    ) -> dict[str, Any] | None:
        name_lower = entity_name.lower().strip()
        type_lower = entity_type.lower().strip()

        # 1. Direkte Suche (entity_type:name)
        direct_key = f"{type_lower}:{name_lower}"
        if direct_key in prices and isinstance(prices[direct_key], dict):
            row = cast(dict[str, Any], prices[direct_key])
            base_price = row.get("price")
            if base_price is not None:
                return {
                    "success": True,
                    "source": "local",
                    "entity_name": row.get("name", entity_name),
                    "entity_type": type_lower,
                    "price": float(base_price),
                    "currency": str(row.get("currency", self.default_currency)),
                    "unit": str(row.get("unit", self.default_unit)),
                    "total_price": round(float(base_price) * area, 2),
                }

        # 2. Material mit Varianten/Formaten
        if type_lower == "material":
            # Suche nach dem Materialkey
            material_key = name_lower
            if material_key not in prices:
                # Versuche Variante zuzuordnen
                for key, data_raw in prices.items():
                    if not isinstance(data_raw, dict):
                        continue
                    data = cast(dict[str, Any], data_raw)
                    variants = cast(dict[str, Any], data.get("variants", {}))
                    if variants:
                        for vk in variants.keys():
                            if variant and variant in vk.lower():
                                material_key = key
                                break
                        if material_key != name_lower:
                            break

            material_data = prices.get(material_key) if isinstance(prices.get(material_key), dict) else None
            if material_data:
                return self._build_legacy_material_result(
                    material_key=material_key,
                    material_data=material_data,
                    variant=variant,
                    format_str=format_str,
                    thickness=thickness,
                    quantity=area,
                    currency=currency,
                )

        # 3. Teilübereinstimmung
        for key, data_raw in prices.items():
            if not isinstance(data_raw, dict):
                continue
            data = cast(dict[str, Any], data_raw)
            k = str(key).lower()
            if name_lower in k and (k.startswith(f"{type_lower}:") or type_lower == "material"):
                if data.get("price") is not None:
                    return {
                        "success": True,
                        "source": "local",
                        "entity_name": data.get("name", entity_name),
                        "entity_type": type_lower,
                        "price": float(data.get("price", 0.0) or 0.0),
                        "currency": str(data.get("currency", self.default_currency)),
                        "unit": str(data.get("unit", self.default_unit)),
                        "total_price": round(float(data.get("price", 0.0) or 0.0) * area, 2),
                    }
        return None

    def _build_legacy_material_result(
        self,
        material_key: str,
        material_data: dict[str, Any],
        variant: str,
        format_str: str,
        thickness: str,
        quantity: float,
        currency: str,
    ) -> dict[str, Any]:
        variants = cast(dict[str, Any], material_data.get("variants", {}))
        formats = cast(dict[str, Any], material_data.get("formats", {}))

        variant_data: dict[str, Any] | None = None
        chosen_variant = variant.strip().lower()
        if chosen_variant:
            for vk, vd in variants.items():
                vk_lower = str(vk).lower()
                if chosen_variant == vk_lower or chosen_variant in vk_lower or vk_lower in chosen_variant:
                    variant_data = cast(dict[str, Any], vd)
                    chosen_variant = str(vk)
                    break
            if not variant_data:
                return {
                    "success": False,
                    "error": f"Variante '{variant}' nicht gefunden. Verfügbare Varianten: {', '.join(list(variants.keys()))}",
                }
        else:
            if variants:
                first_key = list(variants.keys())[0]
                variant_data = cast(dict[str, Any], variants[first_key])
                chosen_variant = str(first_key)

        format_data: dict[str, Any] | None = None
        chosen_format = format_str.strip()
        if chosen_format:
            for fk, fd in formats.items():
                fk_norm = str(fk).replace("x", "").replace(" ", "")
                q_norm = chosen_format.replace("x", "").replace(" ", "")
                if chosen_format == fk or q_norm == fk_norm:
                    format_data = cast(dict[str, Any], fd)
                    chosen_format = str(fk)
                    break
            if not format_data:
                return {
                    "success": False,
                    "error": f"Format '{format_str}' nicht gefunden. Verfügbare Formate: {', '.join(list(formats.keys()))}",
                }
        else:
            if formats:
                first_key = list(formats.keys())[0]
                format_data = cast(dict[str, Any], formats[first_key])
                chosen_format = str(first_key)

        if variant_data is None:
            return {"success": False, "error": "Keine Preisdaten für die gewählte Variante verfügbar."}

        price_per_qm = float(variant_data.get("price_per_qm", 0.0) or 0.0)
        if format_data and format_data.get("price_per_qm"):
            price_per_qm = float(format_data.get("price_per_qm", price_per_qm) or price_per_qm)

        thickness_factor = float(cast(dict[str, Any], material_data.get("thickness", {})).get(thickness, 1.0) or 1.0)
        adjusted_price = price_per_qm * thickness_factor
        min_order = float(variant_data.get("min_order", 1) or 1)
        total_price = adjusted_price * quantity

        if currency != "EUR":
            conversion_rates = {"USD": 1.09, "CHF": 0.98, "GBP": 0.85}
            if currency in conversion_rates:
                factor = float(conversion_rates[currency])
                total_price *= factor
                adjusted_price *= factor

        material_name = str(material_data.get("name", material_key))
        return {
            "success": True,
            "source": "local",
            "entity_name": chosen_variant or material_name,
            "entity_type": "material",
            "price": round(adjusted_price, 2),
            "currency": currency,
            "unit": "qm",
            "total_price": round(total_price, 2),
            "material": material_name,
            "variant": chosen_variant,
            "format": chosen_format,
            "thickness": thickness,
            "price_per_qm": round(adjusted_price, 2),
            "min_order_qm": min_order,
            "available_formats": list(formats.keys()),
            "available_variants": list(variants.keys()),
        }

    def _build_query_variants(
        self,
        *,
        entity_name: str,
        entity_type: str,
        unit: str,
        thickness: str,
        surface_finish: str,
        application: str,
        format_str: str,
    ) -> list[str]:
        suffix = "Preis" if entity_type != "service" else "Kosten"
        variants: list[str] = []

        variants.append(" ".join(part for part in [entity_name, suffix, unit] if part).strip())
        variants.append(" ".join(part for part in [entity_name, entity_type, surface_finish, suffix, unit] if part).strip())
        if format_str:
            variants.append(" ".join(part for part in [entity_name, application, format_str, surface_finish, suffix, unit] if part).strip())
            for alt in self._generate_alternative_formats(format_str):
                variants.append(" ".join(part for part in [entity_name, application, alt, surface_finish, suffix, unit] if part).strip())

        for country, curr in [("Polen", "PLN"), ("Deutschland", "EUR"), ("Europa", "EUR")]:
            variants.append(" ".join(part for part in [entity_name, country, suffix, unit] if part).strip())
            if format_str:
                variants.append(" ".join(part for part in [entity_name, format_str, country, suffix, unit] if part).strip())
            variants.append(" ".join(part for part in [entity_name, curr, suffix, unit] if part).strip())

        variants.append(" ".join(part for part in ["Naturstein", entity_name, format_str, surface_finish, suffix, unit] if part).strip())

        if entity_type == "material":
            variants.append(" ".join(part for part in [entity_name, "Granit", suffix, unit, application, surface_finish] if part).strip())

        variants.append(" ".join(part for part in [entity_name, suffix] if part).strip())

        if application:
            variants.append(" ".join(part for part in [entity_name, application, format_str, surface_finish, suffix] if part).strip())

        seen: set[str] = set()
        deduped: list[str] = []
        for query in variants:
            normalized = re.sub(r"\s+", " ", query).strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(re.sub(r"\s+", " ", query).strip())
        return deduped

    def _generate_alternative_formats(self, format_str: str) -> list[str]:
        alternatives: list[str] = []
        cleaned = re.sub(r"\s*cm\s*", "", format_str, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s*\*\s*", "x", cleaned)
        cleaned = re.sub(r"\s+", "", cleaned)

        match = re.search(r"(\d+(?:[\.,]\d+)?)\s*[xX]\s*(\d+(?:[\.,]\d+)?)", cleaned)
        if not match:
            return alternatives

        w = float(match.group(1).replace(",", "."))
        h = float(match.group(2).replace(",", "."))

        def _fmt(v: float) -> str:
            if abs(v - int(v)) < 1e-6:
                return str(int(v))
            return f"{v:.1f}".replace(".", ",")

        alternatives.extend(
            [
                f"{_fmt(w + 0.5)}x{_fmt(h + 0.5)}",
                f"{_fmt(w + 0.5)}x{_fmt(h)}",
                f"{_fmt(w)}x{_fmt(h + 0.5)}",
                f"{_fmt(h)}x{_fmt(w)}",
                f"{_fmt(w)}x{_fmt(h)} cm",
            ]
        )

        seen: set[str] = set()
        deduped: list[str] = []
        for item in alternatives:
            normalized = item.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(item)
        return deduped

    def _format_price_summary(self, entity_name: str, prices: dict[str, float], currency: str, unit: str) -> str:
        lines = [
            f"{entity_name} - Preisübersicht (Internet)",
            f"Günstigster: {prices['min']:.2f} {currency}/{unit}",
            f"Durchschnitt: {prices['avg']:.2f} {currency}/{unit}",
            f"Höchster: {prices['max']:.2f} {currency}/{unit}",
            f"Basierend auf {int(prices['count'])} gefundenen Preisen",
            "",
            "Soll ich den Durchschnittspreis als Referenz speichern?",
        ]
        return "\n".join(lines)

    def _format_price_summary_triangulated(
        self,
        entity_name: str,
        price_data: dict[str, Any],
        unit: str,
        application: str,
        details: dict[str, Any],
    ) -> str:
        lines: list[str] = [f"{entity_name} - Preisuebersicht (Triangulation)"]
        if application:
            lines.append(f"Anwendung: {application}")

        for curr in ["EUR", "PLN"]:
            data = cast(dict[str, Any], price_data.get(curr, {})) if isinstance(price_data.get(curr), dict) else {}
            if not data:
                continue
            lines.append(
                f"{curr} Durchschnitt: {float(data.get('avg', 0.0)):.2f} {curr}/{unit} "
                f"(Spanne {float(data.get('min', 0.0)):.2f}-{float(data.get('max', 0.0)):.2f}, aus {int(data.get('count', 0) or 0)} Quellen)"
            )

        image_url = str(details.get("image_url", "")).strip()
        if image_url:
            lines.append(f"Bild: {image_url}")

        add_info = cast(dict[str, Any], details.get("additional_info", {})) if isinstance(details.get("additional_info"), dict) else {}
        wiki = str(add_info.get("wikipedia", "")).strip()
        if wiki:
            lines.append(f"Beschreibung: {wiki[:200]}...")

        external_url = str(details.get("external_url", "")).strip()
        if external_url:
            lines.append(f"Quelle: {external_url}")

        lines.append("")
        lines.append("Soll ich den Durchschnittspreis als Referenz speichern? (Ja/Nein)")
        lines.append("Hinweis: Preise koennen je nach Haendler, Qualitaet und Region variieren.")
        return "\n".join(lines)