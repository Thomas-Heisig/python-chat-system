# packages/plugins/grammar_checker/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false

from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "grammar_checker",
    "name": "Grammar Checker",
    "description": "Rechtschreib- und Grammatikprüfung mit LanguageTool API",
    "category": "🧠 NLP & Content",
    "apiKeyRequired": False,
    "intentPattern": r"\b(rechtschreibung|grammatik|korrektur|sprache|prüfen|grammar|spell|check)\b",
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


def _as_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return cast(list[Any], value)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class GrammarCheckerPlugin:
    name = "grammar_checker"
    description = "Rechtschreib- und Grammatikprüfung mit LanguageTool API"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der zu prüfende Text.",
            },
            "language": {
                "type": "string",
                "enum": ["auto", "de-DE", "en-US", "en-GB", "fr-FR", "es-ES", "it-IT", "pt-PT", "nl-NL", "pl-PL", "ru-RU"],
                "default": "auto",
                "description": "Sprache des Textes (auto = automatische Erkennung).",
            },
            "mode": {
                "type": "string",
                "enum": ["all", "spelling", "grammar", "style"],
                "default": "all",
                "description": "Prüfmodus: all, spelling, grammar, style.",
            },
            "suggestions": {
                "type": "boolean",
                "default": True,
                "description": "Ob Korrekturvorschläge angezeigt werden sollen.",
            },
            "max_matches": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 20,
                "description": "Maximale Anzahl an Fehlern, die angezeigt werden.",
            },
        },
        "required": ["text"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "language": {"type": "string"},
            "detected_language": {"type": "string"},
            "matches": {"type": "array"},
            "total_matches": {"type": "integer"},
            "text": {"type": "string"},
            "corrected_text": {"type": "string"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    LANGUAGE_MAP: dict[str, str] = {
        "de-DE": "German (Germany)",
        "en-US": "English (US)",
        "en-GB": "English (UK)",
        "fr-FR": "French (France)",
        "es-ES": "Spanish (Spain)",
        "it-IT": "Italian (Italy)",
        "pt-PT": "Portuguese (Portugal)",
        "nl-NL": "Dutch (Netherlands)",
        "pl-PL": "Polish (Poland)",
        "ru-RU": "Russian (Russia)",
    }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = str(input_data.get("text", "")).strip()
        if not text:
            return {"error": "Kein Text zum Prüfen angegeben."}

        if len(text) < 3:
            return {"error": "Text ist zu kurz für eine sinnvolle Prüfung (mindestens 3 Zeichen)."}

        language = str(input_data.get("language", "auto")).strip()
        mode = str(input_data.get("mode", "all")).strip()
        include_suggestions = bool(input_data.get("suggestions", True))
        max_matches = max(1, min(50, int(input_data.get("max_matches", 20))))

        # LanguageTool API aufrufen
        result = await self._check_text(text, language, mode, include_suggestions, max_matches)

        if "error" in result:
            return result

        # Formatierte Ausgabe
        return self._format_response(text, result, include_suggestions)

    async def _check_text(
        self,
        text: str,
        language: str,
        mode: str,
        include_suggestions: bool,
        max_matches: int,
    ) -> dict[str, Any]:
        """Ruft die LanguageTool API auf."""
        api_url = "https://api.languagetool.org/v2/check"

        # Spracheinstellungen
        if language == "auto":
            lang_param = "auto"
        else:
            lang_param = language

        # Filter für Modus
        enabled_rules = []
        disabled_rules = []
        if mode == "spelling":
            disabled_rules = ["MORFOLOGIK_RULE_DE", "EN_QUOTES", "COMMA_PARENTHESIS_WHITESPACE"]
            enabled_rules = ["MORFOLOGIK_RULE_DE", "MORFOLOGIK_RULE_EN"]
        elif mode == "grammar":
            enabled_rules = ["GRAMMAR", "SENTENCE_STRUCTURE"]
        elif mode == "style":
            enabled_rules = ["STYLE", "REDUNDANCY", "WORDINESS"]
        # else "all" – alle Regeln aktiv

        params = {
            "text": text,
            "language": lang_param,
            "enabledOnly": "false",
        }

        # Filter für benutzerdefinierte Regeln (nur wenn spezifisch)
        if enabled_rules:
            params["enabledRules"] = ",".join(enabled_rules)
        if disabled_rules:
            params["disabledRules"] = ",".join(disabled_rules)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    api_url,
                    data=params,
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return {"error": "Zu viele Anfragen an LanguageTool. Bitte warten Sie einen Moment."}
            if e.response.status_code == 400:
                return {"error": "Ungültige Anfrage. Prüfen Sie die Spracheinstellungen."}
            return {"error": f"HTTP-Fehler: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Fehler beim Aufruf der LanguageTool-API: {str(e)}"}

        if not isinstance(data, dict):
            return {"error": "Ungültige Antwort von der LanguageTool-API."}

        data_map = _as_dict(data)

        # matches extrahieren
        matches_raw = _as_list(data_map.get("matches", []))
        matches: list[dict[str, Any]] = []
        for match_raw in matches_raw:
            match = _as_dict(match_raw)
            if match:
                matches.append(match)

        # Sprache aus der Antwort
        language_map = _as_dict(data_map.get("language", {}))
        detected_lang = str(language_map.get("name", language))
        if language == "auto" and detected_lang == "auto":
            detected_lang = "Unbekannt"

        return {
            "success": True,
            "language": language,
            "detected_language": detected_lang,
            "matches": matches[:max_matches],
            "total_matches": len(matches),
            "raw_response": data_map,
        }

    def _format_response(self, text: str, result: dict[str, Any], include_suggestions: bool) -> dict[str, Any]:
        """Formatiert die API-Antwort für die Ausgabe."""
        matches_raw = result.get("matches", [])
        matches: list[dict[str, Any]] = []
        if isinstance(matches_raw, list):
            for match_raw in matches_raw:
                match = _as_dict(match_raw)
                if match:
                    matches.append(match)

        total = _to_int(result.get("total_matches", len(matches)), len(matches))

        formatted_matches: list[dict[str, Any]] = []
        for match in matches:
            type_map = _as_dict(match.get("type", {}))
            offset = _to_int(match.get("offset", 0), 0)
            length = _to_int(match.get("length", 0), 0)
            replacements_out: list[str] = []
            formatted_match = {
                "type": str(type_map.get("name", "Unbekannt")),
                "message": str(match.get("message", "")),
                "short_message": str(match.get("shortMessage", "")),
                "offset": offset,
                "length": length,
                "replacements": replacements_out,
            }

            # Korrekturvorschläge
            replacements = _as_list(match.get("replacements", []))
            if include_suggestions:
                for r in replacements:
                    replacement = _as_dict(r)
                    value = str(replacement.get("value", "")).strip()
                    if value:
                        replacements_out.append(value)
                # auf max 5 Vorschläge beschränken
                formatted_match["replacements"] = replacements_out[:5]

            # Fehler im Kontext anzeigen
            if offset >= 0 and length > 0:
                start = max(0, offset - 20)
                end = min(len(text), offset + length + 20)
                context = text[start:end]
                # Markierung des Fehlers
                error_pos = offset - start
                if 0 <= error_pos < len(context):
                    formatted_match["context"] = context[:error_pos] + f"[{context[error_pos:error_pos+length]}]" + context[error_pos+length:]
                else:
                    formatted_match["context"] = context

            # Nach Kategorie gruppieren
            category = str(type_map.get("name", ""))
            if "Spelling" in category or "Rechtschreibung" in category:
                formatted_match["category"] = "Rechtschreibung"
            elif "Grammar" in category or "Grammatik" in category:
                formatted_match["category"] = "Grammatik"
            elif "Style" in category or "Stil" in category:
                formatted_match["category"] = "Stil"
            else:
                formatted_match["category"] = "Sonstiges"

            formatted_matches.append(formatted_match)

        # Korrigierter Text (alle automatischen Korrekturen anwenden – sicherheitshalber)
        corrected_text = text
        if include_suggestions:
            # Einfache Korrektur: erste Vorschläge anwenden
            # (nur für eindeutige Korrekturen, die nicht mehrdeutig sind)
            for match in matches:
                replacements = _as_list(match.get("replacements", []))
                if replacements:
                    suggestion = replacements[0]
                    offset = _to_int(match.get("offset", 0), 0)
                    length = _to_int(match.get("length", 0), 0)
                    if isinstance(suggestion, dict):
                        suggestion = _as_dict(suggestion).get("value", "")
                    else:
                        suggestion = str(suggestion)
                    if suggestion and 0 <= offset < len(corrected_text):
                        corrected_text = corrected_text[:offset] + suggestion + corrected_text[offset + length:]

        return {
            "success": True,
            "language": result.get("language"),
            "detected_language": result.get("detected_language"),
            "matches": formatted_matches,
            "total_matches": total,
            "text": text,
            "corrected_text": corrected_text if include_suggestions else None,
            "message": f"{total} Fehler gefunden. Sprachversion: {result.get('detected_language')}",
        }


