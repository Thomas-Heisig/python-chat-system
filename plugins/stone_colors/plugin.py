# packages/plugins/stone_colors/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportUnusedVariable=false

import json
import os
from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "stone_colors",
    "name": "Stone Colors",
    "description": "Farbpaletten für Naturstein (Granit, Marmor, etc.)",
    "category": "🏢 Spezial (Naturstein)",
    "apiKeyRequired": False,
    "intentPattern": r"\b(farbe|ton|muster|optik|farbpalette|stein farbe|schwarz|weiß|grau|beige|braun|rot|grün|blau)\b",
    "status": "implemented",
    "settingsFields": [],
}


# --- Interne Farbdatenbank ---
# Datenbank mit Farbinformationen für verschiedene Natursteine
_COLOR_DB: dict[str, dict[str, Any]] = {
    # --- Granit ---
    "nero assoluto": {
        "name": "Nero Assoluto",
        "type": "Granit",
        "color": "Schwarz",
        "hex": "#1a1a1a",
        "description": "Tiefschwarzer Granit mit feiner, gleichmäßiger Körnung. Sehr elegant und zeitlos.",
        "variants": ["Nero Assoluto Zimbabwe", "Nero Assoluto Brazil"],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Fassaden", "Grabsteine"],
        "mood": "edel, modern, zeitlos",
        "rgb": (26, 26, 26),
    },
    "bianco sardo": {
        "name": "Bianco Sardo",
        "type": "Granit",
        "color": "Weiß",
        "hex": "#f5f5f0",
        "description": "Weißer Granit mit feinen, grauen Einschlüssen. Hell und freundlich.",
        "variants": [],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Wandverkleidungen"],
        "mood": "hell, freundlich, modern",
        "rgb": (245, 245, 240),
    },
    "giallo venezia": {
        "name": "Giallo Venezia",
        "type": "Granit",
        "color": "Gelb",
        "hex": "#d4a846",
        "description": "Goldgelber Granit mit warmen, erdigen Tönen. Verleiht Räumen eine einladende Atmosphäre.",
        "variants": ["Giallo Venezia Light"],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Außenbereich"],
        "mood": "warm, einladend, mediterran",
        "rgb": (212, 168, 70),
    },
    "rosso levanto": {
        "name": "Rosso Levanto",
        "type": "Granit",
        "color": "Rot",
        "hex": "#8b1a1a",
        "description": "Dunkelroter Granit mit tiefen, satten Farbtönen. Besonders edel und ausdrucksstark.",
        "variants": [],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Repräsentative Bereiche"],
        "mood": "edel, warm, ausdrucksstark",
        "rgb": (139, 26, 26),
    },
    "verde marina": {
        "name": "Verde Marina",
        "type": "Granit",
        "color": "Grün",
        "hex": "#2d5a27",
        "description": "Satter, dunkler grüner Granit mit natürlicher Maserung. Verbindet Eleganz mit Naturverbundenheit.",
        "variants": [],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Außenbereich"],
        "mood": "natürlich, ruhig, elegant",
        "rgb": (45, 90, 39),
    },
    "blu savoia": {
        "name": "Blu Savoia",
        "type": "Granit",
        "color": "Blau",
        "hex": "#1a2a5a",
        "description": "Dunkelblauer Granit mit feinen, glitzernden Einschlüssen. Ein seltener, exklusiver Stein.",
        "variants": [],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Exklusive Projekte"],
        "mood": "exklusiv, ruhig, stilvoll",
        "rgb": (26, 42, 90),
    },
    # --- Marmor ---
    "carrara": {
        "name": "Carrara",
        "type": "Marmor",
        "color": "Weiß",
        "hex": "#f0ece4",
        "description": "Klassischer weißer Marmor aus Italien. Feine, graue Adern verleihen ihm eine edle Note.",
        "variants": ["Carrara Statuario", "Carrara Venato"],
        "suitable_for": ["Böden", "Wandverkleidungen", "Badezimmer", "Skulpturen"],
        "mood": "edel, klassisch, zeitlos",
        "rgb": (240, 236, 228),
    },
    "calacatta": {
        "name": "Calacatta",
        "type": "Marmor",
        "color": "Weiß",
        "hex": "#f5f0e8",
        "description": "Exklusiver italienischer Marmor mit markanten, dunklen Adern. Luxuriös und unverwechselbar.",
        "variants": ["Calacatta Gold", "Calacatta Borghini"],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Wandverkleidungen", "Luxusprojekte"],
        "mood": "luxuriös, exklusiv, elegant",
        "rgb": (245, 240, 232),
    },
    "statuario": {
        "name": "Statuario",
        "type": "Marmor",
        "color": "Weiß",
        "hex": "#f8f4ec",
        "description": "Hochwertiger weißer Marmor mit subtilen, grauen Adern. Extrem edel und begehrt.",
        "variants": [],
        "suitable_for": ["Skulpturen", "Böden", "Wandverkleidungen", "Luxusprojekte"],
        "mood": "exklusiv, künstlerisch, elegant",
        "rgb": (248, 244, 236),
    },
    "verde guatemala": {
        "name": "Verde Guatemala",
        "type": "Marmor",
        "color": "Grün",
        "hex": "#3a6b35",
        "description": "Grüner Marmor mit natürlichen, hellen Adern. Bringt Lebendigkeit in moderne Räume.",
        "variants": [],
        "suitable_for": ["Böden", "Wandverkleidungen", "Außenbereich"],
        "mood": "natürlich, lebendig, modern",
        "rgb": (58, 107, 53),
    },
    # --- Quarzit ---
    "bianco": {
        "name": "Bianco",
        "type": "Quarzit",
        "color": "Weiß",
        "hex": "#f0ede8",
        "description": "Weißer Quarzit mit feiner, glitzernder Textur. Extrem hart und säurebeständig.",
        "variants": ["Bianco Superiore"],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Wandverkleidungen"],
        "mood": "hell, modern, robust",
        "rgb": (240, 237, 232),
    },
    "grigio": {
        "name": "Grigio",
        "type": "Quartzit",
        "color": "Grau",
        "hex": "#8a8a8a",
        "description": "Grauer Quarzit mit subtilen, silbernen Einschlüssen. Modern und vielseitig.",
        "variants": ["Grigio Avorio"],
        "suitable_for": ["Küchenarbeitsplatten", "Böden"],
        "mood": "modern, neutral, stilvoll",
        "rgb": (138, 138, 138),
    },
    "nero": {
        "name": "Nero",
        "type": "Quarzit",
        "color": "Schwarz",
        "hex": "#2a2a2a",
        "description": "Schwarzer Quarzit mit glitzernden, metallischen Einschlüssen. Sehr edel.",
        "variants": [],
        "suitable_for": ["Küchenarbeitsplatten", "Böden", "Fassaden"],
        "mood": "edel, modern, elegant",
        "rgb": (42, 42, 42),
    },
    # --- Schiefer ---
    "grau": {
        "name": "Grau",
        "type": "Schiefer",
        "color": "Grau",
        "hex": "#6b6b6b",
        "description": "Grauer Schiefer mit natürlicher Schichtung. Rustikal und robust.",
        "variants": ["Grau Antik", "Grau Natur"],
        "suitable_for": ["Böden", "Fassaden", "Dächer", "Terrassen"],
        "mood": "rustikal, natürlich, robust",
        "rgb": (107, 107, 107),
    },
    "schwarz": {
        "name": "Schwarz",
        "type": "Schiefer",
        "color": "Schwarz",
        "hex": "#2d2d2d",
        "description": "Schwarzer Schiefer mit matter Oberfläche. Eleganter als grauer Schiefer.",
        "variants": [],
        "suitable_for": ["Böden", "Fassaden", "Kamine"],
        "mood": "edel, modern, robust",
        "rgb": (45, 45, 45),
    },
    "grün": {
        "name": "Grün",
        "type": "Schiefer",
        "color": "Grün",
        "hex": "#4a6b3a",
        "description": "Grüner Schiefer mit erdigen, natürlichen Tönen.",
        "variants": ["Grün Antik"],
        "suitable_for": ["Böden", "Außenbereich"],
        "mood": "natürlich, ruhig, erdig",
        "rgb": (74, 107, 58),
    },
    # --- Travertin ---
    "classico": {
        "name": "Classico",
        "type": "Travertin",
        "color": "Beige",
        "hex": "#d4c4a8",
        "description": "Klassischer Travertin mit warmen, beigen Tönen und natürlichen, kleinen Löchern.",
        "variants": ["Classico Light", "Classico Dark"],
        "suitable_for": ["Böden", "Wandverkleidungen", "Außenbereich"],
        "mood": "warm, mediterran, antik",
        "rgb": (212, 196, 168),
    },
    "noce": {
        "name": "Noce",
        "type": "Travertin",
        "color": "Braun",
        "hex": "#a88b70",
        "description": "Dunklerer Travertin mit warmen, nussbraunen Tönen.",
        "variants": [],
        "suitable_for": ["Böden", "Wandverkleidungen"],
        "mood": "warm, edel, rustikal",
        "rgb": (168, 139, 112),
    },
    "silver": {
        "name": "Silver",
        "type": "Travertin",
        "color": "Grau",
        "hex": "#b5b5aa",
        "description": "Travertin mit silbergrauen Tönen. Modern und elegant.",
        "variants": ["Silver Light", "Silver Dark"],
        "suitable_for": ["Böden", "Wandverkleidungen", "Moderne Projekte"],
        "mood": "modern, elegant, neutral",
        "rgb": (181, 181, 170),
    },
}


class StoneColorsPlugin:
    name = "stone_colors"
    description = "Farbpaletten für Naturstein (Granit, Marmor, etc.)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "stone_name": {
                "type": "string",
                "description": "Name des Steins (z.B. 'Nero Assoluto', 'Carrara', 'Bianco Sardo').",
            },
            "stone_type": {
                "type": "string",
                "enum": ["granit", "marmor", "quarzit", "schiefer", "travertin", "kalkstein"],
                "description": "Steinart (optional, Filter).",
            },
            "color": {
                "type": "string",
                "enum": ["schwarz", "weiß", "grau", "beige", "braun", "rot", "grün", "blau", "gelb", "orange", "violett", "rosa"],
                "description": "Farbe (optional, Filter).",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 10,
                "description": "Maximale Anzahl von Ergebnissen.",
            },
        },
        "required": ["stone_name"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "stone": {"type": "object"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.storage_path = os.getenv("COLOR_STORAGE_PATH", "./stone_colors.json")
        self._ensure_storage()

    def _ensure_storage(self):
        """Stellt sicher, dass die Datenbankdatei existiert."""
        if not os.path.exists(self.storage_path):
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(_COLOR_DB, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _load_colors(self) -> dict[str, dict[str, Any]]:
        """Lädt die Farbdatenbank aus der JSON-Datei."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return _COLOR_DB

    def _save_colors(self, data: dict[str, dict[str, Any]]):
        """Speichert die Farbdatenbank in der JSON-Datei."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _find_stone(self, stone_name: str, stone_type: str | None, color: str | None) -> dict[str, Any] | None:
        """Sucht nach einem Stein in der Datenbank."""
        colors_db = self._load_colors()
        stone_name_lower = stone_name.lower()

        # Exakte Suche
        for key, data in colors_db.items():
            if stone_name_lower == key or stone_name_lower == data.get("name", "").lower():
                if stone_type and stone_type.lower() != data.get("type", "").lower():
                    continue
                if color and color.lower() != data.get("color", "").lower():
                    continue
                return data

        # Teilübereinstimmung
        best_match = None
        best_score = 0
        for key, data in colors_db.items():
            name_lower = data.get("name", "").lower()
            if stone_name_lower in name_lower or name_lower in stone_name_lower:
                # Filter anwenden
                if stone_type and stone_type.lower() != data.get("type", "").lower():
                    continue
                if color and color.lower() != data.get("color", "").lower():
                    continue
                # Bewertung
                score = len(name_lower) if stone_name_lower in name_lower else 0
                if score > best_score:
                    best_score = score
                    best_match = data

        return best_match

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        stone_name = str(input_data.get("stone_name", "")).strip()
        if not stone_name:
            return {"success": False, "error": "stein_name ist erforderlich."}

        stone_type = str(input_data.get("stone_type", "")).strip() or None
        color = str(input_data.get("color", "")).strip() or None
        limit = max(1, min(50, int(input_data.get("limit", 10))))

        stone_data = self._find_stone(stone_name, stone_type, color)

        if not stone_data:
            return {
                "success": False,
                "error": f"Stein '{stone_name}' nicht gefunden. Verfügbare Steine: {', '.join(_COLOR_DB.keys())}",
            }

        # Formatierte Ausgabe
        result = {
            "name": stone_data.get("name"),
            "type": stone_data.get("type"),
            "color": stone_data.get("color"),
            "hex": stone_data.get("hex"),
            "description": stone_data.get("description"),
            "suitable_for": stone_data.get("suitable_for", []),
            "mood": stone_data.get("mood"),
            "rgb": stone_data.get("rgb"),
            "variants": stone_data.get("variants", []),
        }

        return {
            "success": True,
            "stone": result,
            "message": f"Informationen zu {stone_data.get('name')} gefunden.",
        }


