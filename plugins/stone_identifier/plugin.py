# packages/plugins/stone_identifier/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportUnusedImport=false

import json
import os
from typing import Any

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "stone_identifier",
    "name": "Stone Identifier",
    "description": "Identifikation von Natursteinen anhand von Textbeschreibungen oder Bildern",
    "category": "🏢 Spezial (Naturstein)",
    "apiKeyRequired": False,
    "intentPattern": r"\b(stein|granit|marmor|quarzit|schiefer|travertin|erkennen|identifizieren|welcher stein)\b",
    "status": "implemented",
    "settingsFields": [],
}


# --- Lokale Datenbank für Steineigenschaften (für Text-Identifikation) ---
# In einer realen Umgebung könnte diese aus einer Datenbank kommen oder durch ML ergänzt werden.
_STONE_DB: list[dict[str, Any]] = [
    {
        "id": "granit_nero_assoluto",
        "name": "Nero Assoluto",
        "type": "Granit",
        "origin": "Indien",
        "colors": ["schwarz", "dunkelgrau", "anthrazit"],
        "patterns": ["feinkörnig", "gleichmäßig", "glitzernd"],
        "finish": ["poliert", "geschliffen", "gebürstet"],
        "characteristics": ["hart", "säurebeständig", "kratzfest", "wetterfest"],
        "uses": ["Küchenarbeitsplatten", "Böden", "Fassaden", "Grabsteine"],
        "texture": "fein bis mittel",
        "hardness": 7,
    },
    {
        "id": "marmor_carrara",
        "name": "Carrara",
        "type": "Marmor",
        "origin": "Italien",
        "colors": ["weiß", "hellgrau", "creme"],
        "patterns": ["feine Adern", "wolkenartig", "leicht durchscheinend"],
        "finish": ["poliert", "geschliffen", "gehärtet"],
        "characteristics": ["weicher", "säureempfindlich", "porös", "edel"],
        "uses": ["Böden", "Wandverkleidungen", "Badezimmer", "Skulpturen"],
        "texture": "fein",
        "hardness": 3,
    },
    {
        "id": "quarzit_bianco",
        "name": "Bianco",
        "type": "Quarzit",
        "origin": "Brasilien",
        "colors": ["weiß", "creme", "hellgrau", "silber"],
        "patterns": ["glitzernd", "kristallin", "dezent"],
        "finish": ["geschliffen", "poliert"],
        "characteristics": ["sehr hart", "säurebeständig", "kratzfest", "langlebig"],
        "uses": ["Küchenarbeitsplatten", "Böden", "Wandverkleidungen"],
        "texture": "mittel",
        "hardness": 8,
    },
    {
        "id": "schiefer_grau",
        "name": "Grauer Schiefer",
        "type": "Schiefer",
        "origin": "Deutschland",
        "colors": ["grau", "anthrazit", "schwarz", "blaugrau"],
        "patterns": ["geschichtet", "rustikal", "natürlich"],
        "finish": ["gebrochen", "gebürstet", "gehärtet"],
        "characteristics": ["frostbeständig", "rutschfest", "säurebeständig", "wetterfest"],
        "uses": ["Böden", "Fassaden", "Dächer", "Terrassen"],
        "texture": "grob",
        "hardness": 5,
    },
    {
        "id": "travertin_classico",
        "name": "Classico",
        "type": "Travertin",
        "origin": "Italien",
        "colors": ["beige", "creme", "goldbraun"],
        "patterns": ["porös", "löcherig", "natürlich"],
        "finish": ["gefüllt", "geschliffen", "getrommelt"],
        "characteristics": ["porös", "warm", "antik", "pflegeintensiv"],
        "uses": ["Böden", "Wandverkleidungen", "Außenbereich"],
        "texture": "grob",
        "hardness": 4,
    },
]


class StoneIdentifierPlugin:
    name = "stone_identifier"
    description = "Identifikation von Natursteinen anhand von Textbeschreibungen oder Bildern"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Textbeschreibung des Steins (z.B. 'schwarzer Stein mit weißen Punkten').",
            },
            "mode": {
                "type": "string",
                "enum": ["text", "image"],
                "default": "text",
                "description": "Modus: text (Textbeschreibung) oder image (Bild-URL).",
            },
            "image_url": {
                "type": "string",
                "description": "URL des Bildes (nur für mode='image').",
            },
            "api_key": {
                "type": "string",
                "description": "API-Key für externe Bilderkennung (optional).",
            },
        },
        "required": ["query"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "identified_stone": {"type": "object"},
            "matches": {"type": "array"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.storage_path = os.getenv("STONE_DB_PATH", "./stone_db.json")
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(_STONE_DB, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _load_stone_db(self) -> list[dict[str, Any]]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return _STONE_DB

    def _save_stone_db(self, data: list[dict[str, Any]]):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _text_identifier(self, query: str) -> list[dict[str, Any]]:
        """Identifikation basierend auf Textbeschreibung."""
        query_lower = query.lower()
        stone_db = self._load_stone_db()
        results = []

        for stone in stone_db:
            score = 0
            # Suche in Namen
            if query_lower in stone.get("name", "").lower():
                score += 5
            # Suche in Farben
            for color in stone.get("colors", []):
                if color.lower() in query_lower:
                    score += 2
            # Suche in Mustern
            for pattern in stone.get("patterns", []):
                if pattern.lower() in query_lower:
                    score += 2
            # Suche in Eigenschaften
            for characteristic in stone.get("characteristics", []):
                if characteristic.lower() in query_lower:
                    score += 1
            # Suche in Verwendung
            for use in stone.get("uses", []):
                if use.lower() in query_lower:
                    score += 1
            # Suche in Stein-Typ
            if stone.get("type", "").lower() in query_lower:
                score += 3

            if score > 0:
                results.append({**stone, "score": score})

        # Sortieren nach Score (absteigend)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results

    async def _image_identifier(self, image_url: str, api_key: str | None) -> dict[str, Any]:
        """Identifikation basierend auf Bild (über externe API)."""
        if not api_key:
            # Hinweis: Hier könnte eine Integration mit Google Vision, Replicate oder anderen Diensten erfolgen.
            # Für den Prototyp geben wir einen Platzhalter zurück.
            return {"error": "Bilderkennung benötigt eine externe API (z.B. Google Vision). API-Key fehlt."}

        # Platzhalter für echte Implementierung
        # In einer Produktivumgebung würde hier ein Aufruf an Google Vision, Clarifai, etc. erfolgen.
        # Beispiel mit Google Vision:
        # endpoint = "https://vision.googleapis.com/v1/images:annotate?key=" + api_key
        # payload = {
        #     "requests": [{
        #         "image": {"source": {"imageUri": image_url}},
        #         "features": [{"type": "LABEL_DETECTION", "maxResults": 10}]
        #     }]
        # }
        # response = httpx.post(endpoint, json=payload)
        # labels = response.json()["responses"][0]["labelAnnotations"]
        # names = [label["description"].lower() for label in labels]
        # query = " ".join(names)

        return {"error": "Bilderkennung ist in dieser Version nicht implementiert. Verwende Text-Modus."}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        if not query:
            return {"success": False, "error": "query ist erforderlich."}

        mode = str(input_data.get("mode", "text")).lower()
        image_url = str(input_data.get("image_url", "")).strip() or None
        api_key = str(input_data.get("api_key", "")).strip() or None

        if mode == "image":
            if not image_url:
                return {"success": False, "error": "Für Bildidentifikation ist eine image_url erforderlich."}
            if not api_key:
                return {"success": False, "error": "Für Bildidentifikation wird ein API-Key benötigt."}
            result = await self._image_identifier(image_url, api_key)
            if "error" in result:
                return {"success": False, "error": result["error"]}
            # Wenn Bilderkennung erfolgreich wäre, würde hier die extrahierte Beschreibung an _text_identifier weitergegeben.
            # Derzeit Fehler, da nicht implementiert.
            return {"success": False, "error": "Bilderkennung ist in dieser Version nicht implementiert."}

        # Text-Modus
        matches = self._text_identifier(query)
        if not matches:
            return {
                "success": False,
                "error": "Kein passender Stein für die Beschreibung gefunden.",
                "matches": [],
            }

        best_match = matches[0]
        result = {
            "name": best_match.get("name"),
            "type": best_match.get("type"),
            "origin": best_match.get("origin"),
            "colors": best_match.get("colors"),
            "patterns": best_match.get("patterns"),
            "characteristics": best_match.get("characteristics"),
            "uses": best_match.get("uses"),
            "hardness": best_match.get("hardness"),
        }

        # Limit auf Top 3 Matches
        top_matches = matches[:3]

        return {
            "success": True,
            "identified_stone": result,
            "matches": top_matches,
            "message": f"Stein identifiziert: {best_match.get('name')} (Score: {best_match.get('score', 0)})",
        }


