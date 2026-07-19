# packages/plugins/care_instructions/plugin.py
from __future__ import annotations

from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "care_instructions",
    "name": "Care Instructions",
    "description": "Pflegeanleitungen für Naturstein (Reinigung, Versiegelung, Schutz)",
    "category": "🏢 Spezial (Naturstein)",
    "apiKeyRequired": False,
    "intentPattern": r"\b(pflege|reinigung|versiegelung|schutz|flecken|naturstein pflegen)\b",
    "status": "implemented",
    "settingsFields": [],
}


# --- Interne Wissensdatenbank für Pflegeanleitungen ---
_CARE_DB: dict[str, dict[str, Any]] = {
    "granit": {
        "name": "Granit",
        "daily_cleaning": "Reinigen Sie mit warmem Wasser und einem milden pH-neutralen Spülmittel. Verwenden Sie ein weiches Tuch oder einen Mopp.",
        "deep_cleaning": "Bei hartnäckigen Flecken: Speziellen Granitreiniger oder eine Mischung aus Wasser und etwas Alkohol verwenden. Keine säurehaltigen Mittel.",
        "sealing": "Versiegelung alle 1–2 Jahre mit einem hochwertigen Granit-Versiegelungsmittel. Vor der Versiegelung gründlich reinigen und trocknen.",
        "protection": "Verwenden Sie Untersetzer für Gläser und heiße Töpfe. Säurehaltige Substanzen (Zitronensaft, Essig) sofort aufwischen.",
        "stain_removal": "Ölflecken: mit Spezialsteinpaste oder Backpulver abdecken, einwirken lassen und abwischen.",
    },
    "marmor": {
        "name": "Marmor",
        "daily_cleaning": "Nur mit weichem, feuchtem Tuch und pH-neutralem Reiniger. Keine Scheuermittel!",
        "deep_cleaning": "Bei Bedarf mit Marmorreiniger (alkalisch) behandeln. Testen Sie immer an einer unauffälligen Stelle.",
        "sealing": "Versiegelung alle 6–12 Monate mit Marmor-Versiegelung. Marmor ist porös, daher wichtig für Fleckenschutz.",
        "protection": "Säurehaltige Getränke (Wein, Zitrus) sofort abwischen. Verwenden Sie Filzgleiter unter Vasen und Deko.",
        "stain_removal": "Flecken mit spezieller Marmor-Paste behandeln. Für hartnäckige Flecken: Poliermittel mit feinem Schleifmittel.",
    },
    "quarzit": {
        "name": "Quarzit",
        "daily_cleaning": "Warmes Wasser mit mildem Reiniger. Abtrocknen mit weichem Tuch.",
        "deep_cleaning": "Spezieller Quarzit-Reiniger (alkalisch). Säurehaltige Mittel vermeiden.",
        "sealing": "Versiegelung alle 2–3 Jahre. Quarzit ist dichter als Marmor, aber dennoch nicht völlig resistent.",
        "protection": "Hitzebeständig, aber dennoch Untersetzer für heiße Töpfe empfehlenswert.",
        "stain_removal": "Flecken mit einer Paste aus Backpulver und Wasser behandeln, einwirken lassen und abwischen.",
    },
    "schiefer": {
        "name": "Schiefer",
        "daily_cleaning": "Feucht wischen mit Wasser und etwas Spülmittel. Keine aggressiven Reiniger.",
        "deep_cleaning": "Spezieller Schieferreiniger. Bei Bedarf mit einer weichen Bürste nacharbeiten.",
        "sealing": "Versiegelung alle 1–2 Jahre mit Schiefer-Öl oder -Wachs.",
        "protection": "Schiefer ist frostbeständig, aber empfindlich gegen Kratzer. Filzgleiter verwenden.",
        "stain_removal": "Ölflecken: mit Spezialsteinpaste behandeln oder mit Talkum bestreuen und einwirken lassen.",
    },
    "travertin": {
        "name": "Travertin",
        "daily_cleaning": "Mildes Reinigungsmittel mit Wasser. Keine Säure!",
        "deep_cleaning": "Bei Verschmutzung: Travertin-Reiniger oder alkalischer Steinreiniger.",
        "sealing": "Versiegelung alle 1–2 Jahre, da Travertin sehr porös ist.",
        "protection": "Empfindlich gegen Säuren und Kratzer. Schutzmatten und Untersetzer nutzen.",
        "stain_removal": "Flecken mit einer Mischung aus Wasser und Backpulver behandeln, einwirken lassen und abwischen.",
    },
    "kalkstein": {
        "name": "Kalkstein",
        "daily_cleaning": "Feucht wischen mit pH-neutralem Reiniger. Trocken nachpolieren.",
        "deep_cleaning": "Kalksteinreiniger (alkalisch) bei Bedarf.",
        "sealing": "Versiegelung alle 1–2 Jahre – sehr wichtig wegen Porosität.",
        "protection": "Keine Säure, keine Scheuermittel. Untersetzer verwenden.",
        "stain_removal": "Flecken mit spezieller Kalkstein-Paste behandeln.",
    },
}


class CareInstructionsPlugin:
    name = "care_instructions"
    description = "Pflegeanleitungen für Naturstein (Reinigung, Versiegelung, Schutz)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "stone": {
                "type": "string",
                "description": "Steinname (z.B. Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein).",
            },
            "category": {
                "type": "string",
                "enum": ["daily_cleaning", "deep_cleaning", "sealing", "protection", "stain_removal"],
                "description": "Optional: spezifische Kategorie der Pflegeanleitung.",
            },
        },
        "required": ["stone"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "stone": {"type": "string"},
            "instructions": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        stone_key = str(input_data.get("stone", "")).strip().lower()
        category = str(input_data.get("category", "")).strip().lower()

        if not stone_key:
            return {"error": "Bitte geben Sie einen Stein an (z.B. Granit, Marmor)."}

        # Finde den passenden Eintrag (auch Teilübereinstimmung)
        stone_data = None
        matched_key = None
        for key in _CARE_DB:
            if stone_key == key:
                stone_data = _CARE_DB[key]
                matched_key = key
                break
        if not stone_data:
            # Teilübereinstimmung
            for key in _CARE_DB:
                if stone_key in key or key in stone_key:
                    stone_data = _CARE_DB[key]
                    matched_key = key
                    break

        if not stone_data:
            return {
                "error": f"Keine Pflegeanleitung für '{input_data.get('stone')}' gefunden. Verfügbare Steine: {', '.join(_CARE_DB.keys())}"
            }

        instructions = stone_data.copy()
        if category:
            if category in instructions:
                instructions = {category: instructions[category]}
            else:
                return {
                    "error": f"Kategorie '{category}' nicht verfügbar. Verfügbare Kategorien: daily_cleaning, deep_cleaning, sealing, protection, stain_removal"
                }

        return {
            "stone": stone_data["name"],
            "instructions": instructions,
        }

