from __future__ import annotations

import ast
from typing import Any

from plugins.calculator.constants import ACTION_PRESETS, INTENT_PATTERN, UNICODE_PI_PATTERN
from plugins.calculator.services.calculation import CalculatorEvaluator, ExpressionValidationError
from plugins.calculator.settings import resolve_angle_mode, resolve_precision


PLUGIN_META: dict[str, Any] = {
    "id": "calculator",
    "name": "Calculator",
    "description": "Mathematische Berechnungen mit erweiterten Funktionen",
    "category": "🧠 NLP & Content",
    "apiKeyRequired": False,
    "intentPattern": INTENT_PATTERN,
    "status": "implemented",
    "summary": "Fuehrt sichere mathematische Ausdruecke und vordefinierte Presets aus.",
    "capabilities": [
        "math.expression.evaluate",
        "math.preset.percentage",
        "math.preset.geometry.circle_area",
        "math.preset.trigonometry",
    ],
    "usage_rules": [
        "Nur mathematische Ausdruecke und erlaubte Funktionen ausfuehren.",
        "Keine Ausfuehrung von Code, Imports oder Attributzugriff.",
        "Bei dry_run nur validieren, nicht persistieren.",
    ],
    "functions": [
        {
            "name": "evaluate",
            "description": "Berechnet einen mathematischen Ausdruck sicher per AST-Validierung.",
            "read_only": True,
            "side_effect": "none",
            "requires_confirmation": False,
            "required_permissions": ["calculator.execute"],
            "idempotent": True,
            "supports_dry_run": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "evaluate",
                            "preset_percentage",
                            "preset_circle_area",
                            "preset_trig",
                            "preset_log_mix",
                        ],
                    },
                    "expression": {"type": "string"},
                    "angle_mode": {"type": "string", "enum": ["rad", "deg"]},
                    "precision": {"type": "number"},
                },
                "required": [],
            },
        },
        {
            "name": "preset_percentage",
            "description": "Laedt ein Preset fuer Prozentrechnung.",
            "read_only": True,
            "side_effect": "none",
            "requires_confirmation": False,
            "required_permissions": ["calculator.execute"],
            "idempotent": True,
            "supports_dry_run": True,
        },
        {
            "name": "preset_circle_area",
            "description": "Laedt ein Preset fuer Kreisflaechenberechnung.",
            "read_only": True,
            "side_effect": "none",
            "requires_confirmation": False,
            "required_permissions": ["calculator.execute"],
            "idempotent": True,
            "supports_dry_run": True,
        },
        {
            "name": "preset_trig",
            "description": "Laedt ein Preset fuer Trigonometrie.",
            "read_only": True,
            "side_effect": "none",
            "requires_confirmation": False,
            "required_permissions": ["calculator.execute"],
            "idempotent": True,
            "supports_dry_run": True,
        },
        {
            "name": "preset_log_mix",
            "description": "Laedt ein Preset fuer Logarithmen-Mix.",
            "read_only": True,
            "side_effect": "none",
            "requires_confirmation": False,
            "required_permissions": ["calculator.execute"],
            "idempotent": True,
            "supports_dry_run": True,
        },
    ],
    "pluginFrontend": {
        "title": "Calculator Frontend",
        "description": "Schnelleinstiege fuer mathematische, technische und kaufmaennische Berechnungen.",
        "page": {
            "eyebrow": "Numerik-Tool",
            "headline": "Rechnen, pruefen, wiederholen",
            "summary": "Nutze Presets fuer Prozent, Geometrie und Trigonometrie oder gib freie Ausdruecke ein.",
            "highlights": [
                "Sichere AST-Auswertung",
                "Winkelmodus: Radiant oder Grad",
                "Konfigurierbare Genauigkeit",
            ],
            "sections": [
                {
                    "id": "quick-calculations",
                    "title": "Schnelle Berechnungen",
                    "description": "Typische Aufgaben direkt vorbereiten und im Runner ausfuehren.",
                    "cards": [
                        {
                            "id": "card-basic",
                            "title": "Grundrechenarten",
                            "description": "Kombiniere Klammern, Potenzen und Restoperationen.",
                            "bullets": ["Beispiel: (12 + 8) * 1.19", "Operatoren: + - * / ** %"],
                            "ctaLabel": "Preset laden",
                            "openTab": "manual",
                            "pluginInput": {"action": "evaluate", "expression": "(12 + 8) * 1.19"},
                        },
                        {
                            "id": "card-percent",
                            "title": "Prozentrechnung",
                            "description": "Rabatte, Zuschlaege oder Margen schnell pruefen.",
                            "bullets": ["Beispiel: 249 * 0.85", "Differenzen in Echtzeit"],
                            "ctaLabel": "Preset laden",
                            "openTab": "manual",
                            "pluginInput": {"action": "preset_percentage"},
                        },
                        {
                            "id": "card-circle",
                            "title": "Kreisflaeche",
                            "description": "Geometrie mit pi und Potenzfunktion.",
                            "bullets": ["Beispiel: pi * 12**2", "Konstanten: pi, e, tau"],
                            "ctaLabel": "Preset laden",
                            "openTab": "manual",
                            "pluginInput": {"action": "preset_circle_area"},
                        },
                    ],
                }
            ],
        },
        "sections": [
            {
                "id": "scientific",
                "title": "Wissenschaftlich",
                "description": "Trigonometrie und Logarithmen mit passendem Modus.",
                "actions": [
                    {
                        "id": "scientific-trig-deg",
                        "label": "Trigonometrie (Grad)",
                        "description": "sin(30) + cos(60) im Gradmodus vorbereiten.",
                        "openTab": "manual",
                        "pluginInput": {"action": "preset_trig"},
                        "pluginSettings": {"angle_mode": "deg", "precision": 6},
                    },
                    {
                        "id": "scientific-log",
                        "label": "Logarithmen",
                        "description": "log(1000) + ln(e**2) vorbereiten.",
                        "openTab": "manual",
                        "pluginInput": {"action": "preset_log_mix"},
                    },
                ],
            },
            {
                "id": "preferences",
                "title": "Einstellungen",
                "description": "Winkelmodus und Rundungsgenauigkeit steuern.",
                "actions": [
                    {
                        "id": "settings-open",
                        "label": "Calculator-Settings oeffnen",
                        "description": "Oeffnet den Settings-Tab fuer Persistenzwerte.",
                        "openTab": "settings",
                    }
                ],
            },
        ],
    },
    "settingsFields": [
        {
            "key": "angle_mode",
            "label": "Winkelmodus",
            "type": "select",
            "group": "Laufzeit",
            "description": "Standardmodus fuer sin/cos/tan.",
            "default": "rad",
            "options": [
                {"label": "Radiant", "value": "rad"},
                {"label": "Grad", "value": "deg"},
            ],
        },
        {
            "key": "precision",
            "label": "Dezimalstellen",
            "type": "number",
            "group": "Laufzeit",
            "description": "Rundet Resultate auf die gewuenschte Zahl an Stellen.",
            "default": 8,
        },
    ],
}


class CalculatorPlugin:
    name = "calculator"
    description = "Mathematische Berechnungen mit erweiterten Funktionen"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self._settings = settings or {}
        self._evaluator = CalculatorEvaluator()

    def set_settings(self, settings: dict[str, Any]) -> None:
        self._settings = settings

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "evaluate",
                    "preset_percentage",
                    "preset_circle_area",
                    "preset_trig",
                    "preset_log_mix",
                ],
                "description": "Optionales Preset fuer typische Berechnungen.",
            },
            "expression": {
                "type": "string",
                "description": "Mathematischer Ausdruck. Unterstützt: + - * / ** % sqrt sin cos tan asin acos atan sinh cosh tanh log ln exp abs floor ceil round factorial min max pi e",
            },
            "angle_mode": {
                "type": "string",
                "enum": ["rad", "deg"],
                "description": "Trigonometrischer Winkelmodus (optional).",
            },
            "precision": {
                "type": "number",
                "description": "Optionales Rundungsziel in Dezimalstellen (0-12).",
            },
        },
        "required": [],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "result": {"type": "number"},
            "expression": {"type": "string"},
            "action": {"type": "string"},
            "angle_mode": {"type": "string"},
            "precision": {"type": "number"},
            "error": {"type": "string"},
        },
    }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = str(input_data.get("action") or "evaluate").strip() or "evaluate"
        expression = str(input_data.get("expression", "")).strip()
        if not expression and action in ACTION_PRESETS:
            expression = ACTION_PRESETS[action]
        expression = UNICODE_PI_PATTERN.sub("pi", expression)
        if not expression:
            return {"error": "Leerer Ausdruck"}

        angle_mode = self._resolve_angle_mode(input_data)
        precision = self._resolve_precision(input_data)

        try:
            # AST parsen
            parsed = ast.parse(expression, mode="eval")
            # Sicherheitsprüfung
            if not self._is_safe_expression(parsed):
                return {"error": "Ungültige oder unsichere Zeichen im Ausdruck"}

            # Auswerten
            result = self._evaluate(parsed, angle_mode=angle_mode)
            rounded_result = round(result, precision)
            return {
                "result": rounded_result,
                "expression": expression,
                "action": action,
                "angle_mode": angle_mode,
                "precision": precision,
            }

        except ZeroDivisionError:
            return {"error": "Division durch Null nicht erlaubt"}
        except ExpressionValidationError as e:
            return {"error": str(e)}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": f"Ungültiger Ausdruck: {str(e)}"}

    def _is_safe_expression(self, node: ast.AST) -> bool:
        return self._evaluator.is_safe_expression(node)

    def _evaluate(self, node: ast.AST, *, angle_mode: str) -> float:
        return self._evaluator.evaluate(node, angle_mode=angle_mode)

    def _resolve_angle_mode(self, input_data: dict[str, Any]) -> str:
        return resolve_angle_mode(input_data, self._settings)

    def _resolve_precision(self, input_data: dict[str, Any]) -> int:
        return resolve_precision(input_data, self._settings)