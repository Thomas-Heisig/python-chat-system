# packages/plugins/installation_guide/plugin.py
from __future__ import annotations

from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "installation_guide",
    "name": "Installation Guide",
    "description": "Verlegeanleitungen für Naturstein (Küchenarbeitsplatten, Böden, Fassaden, etc.)",
    "category": "🏢 Spezial (Naturstein)",
    "apiKeyRequired": False,
    "intentPattern": r"\b(verlegung|einbau|montage|anleitung|installieren|verlegen)\b",
    "status": "implemented",
    "settingsFields": [],
}


# --- Interne Wissensdatenbank für Verlegeanleitungen ---
_INSTALLATION_DB: dict[str, dict[str, Any]] = {
    "granit": {
        "name": "Granit",
        "applications": {
            "küchenarbeitsplatte": {
                "title": "Granit-Küchenarbeitsplatte verlegen",
                "steps": [
                    "Untergrund prüfen: Sauber, eben, tragfähig (mindestens 2 cm Stärke).",
                    "Ausschnitt für Spüle und Herd vorbereiten (wenn nicht werkseitig).",
                    "Trockenverlegung: Platten auflegen und passgenau ausrichten.",
                    "Kleben mit Spezialkleber (Epoxidharz oder Montagekleber) im Zickzack auftragen.",
                    "Platten auflegen, ausrichten und mit Gummihammer leicht andrücken.",
                    "Fugen mit passendem Fugenmaterial (Epoxid) ausfüllen.",
                    "Überstehenden Kleber entfernen und Oberfläche reinigen.",
                    "Nach Aushärtung (24h) versiegeln (bei Granit empfohlen).",
                ],
                "materials": [
                    "Granitplatte (zugeschnitten)",
                    "Montagekleber (Epoxidharz)",
                    "Fugenmasse (Epoxid)",
                    "Gummihammer",
                    "Wasserwaage",
                    "Fugenglättmittel",
                    "Reinigungstuch",
                ],
                "tips": [
                    "Trage die Platten zu zweit – Granit ist schwer.",
                    "Verwende einen Saugheber für präzises Ausrichten.",
                    "Achte auf eine durchgehende Fugenbreite (ca. 2-3 mm).",
                    "Bei Hohlräumen unter der Platte nachkleben.",
                ],
            },
            "boden": {
                "title": "Granitboden verlegen",
                "steps": [
                    "Estrich prüfen: Sauber, eben, trocken (Restfeuchte < 2 %).",
                    "Grundierung auftragen (Haftbrücke).",
                    "Kleber auftragen (Dünnbettmörtel oder Flexkleber).",
                    "Granitplatten im Verband verlegen (kreuzen).",
                    "Mit Gummihammer und Wasserwaage ausrichten.",
                    "Fugen mit Vergussmasse (Epoxid) füllen.",
                    "Überschüssigen Kleber entfernen.",
                    "Nach 48h begehbar, nach 7 Tagen voll belastbar.",
                ],
                "materials": [
                    "Granitplatten",
                    "Flexkleber",
                    "Fugenvergussmasse",
                    "Gummihammer",
                    "Wasserwaage",
                    "Fugenkreuze",
                    "Grundierung",
                ],
                "tips": [
                    "Lass die Platten 24h im Raum akklimatisieren.",
                    "Verwende Fugenkreuze für gleichmäßige Fugenbreite.",
                    "Bei Fußbodenheizung: Dehnungsfugen einplanen.",
                ],
            },
            "fassade": {
                "title": "Granit-Fassade anbringen",
                "steps": [
                    "Untergrund prüfen: Tragfähig, sauber, eben.",
                    "Befestigungssystem wählen (Klammeranker oder Klebemörtel).",
                    "Ankerpunkte markieren und bohren.",
                    "Platten mit Klebemörtel oder Ankern befestigen.",
                    "Fugen mit wetterfestem Fugenmaterial verfüllen.",
                    "Oberfläche reinigen und imprägnieren.",
                ],
                "materials": ["Granitplatten", "Klebemörtel", "Anker", "Fugenmaterial", "Imprägnierung"],
                "tips": [
                    "Verwende rostfreie Anker für Langlebigkeit.",
                    "Achte auf ausreichende Hinterlüftung (falls erforderlich).",
                ],
            },
        },
    },
    "marmor": {
        "name": "Marmor",
        "applications": {
            "küchenarbeitsplatte": {
                "title": "Marmor-Küchenarbeitsplatte verlegen",
                "steps": [
                    "Marmor ist weicher als Granit: Besonders vorsichtig arbeiten.",
                    "Untergrund prüfen: Sauber, eben, tragfähig.",
                    "Ausschnitt für Spüle und Herd vorbereiten.",
                    "Kleben mit speziellem Marmorkleber (kein Säurehaltiger).",
                    "Platten ausrichten und mit Gummihammer andrücken.",
                    "Fugen mit Marmorfugenmasse verfüllen.",
                    "Nach 24h: Oberfläche polieren und versiegeln.",
                ],
                "materials": [
                    "Marmorplatte",
                    "Marmorkleber",
                    "Fugenmasse",
                    "Gummihammer",
                    "Polierpad",
                    "Versiegelung",
                ],
                "tips": [
                    "Marmor ist säureempfindlich – sofort Flecken entfernen.",
                    "Verwende eine weiche Unterlage beim Transport.",
                ],
            },
            "boden": {
                "title": "Marmorboden verlegen",
                "steps": [
                    "Estrich prüfen: Sauber, eben, trocken.",
                    "Grundierung auftragen.",
                    "Kleber auftragen (Flexkleber für Marmor).",
                    "Marmorplatten im Verband verlegen.",
                    "Fugen mit Marmor-Fugenverguss füllen.",
                    "Nach dem Aushärten: Polieren und versiegeln.",
                ],
                "materials": ["Marmorplatten", "Flexkleber", "Fugenverguss", "Gummihammer", "Wasserwaage"],
                "tips": [
                    "Marmor ist porös – unbedingt versiegeln.",
                    "Nur pH-neutrale Reiniger verwenden.",
                ],
            },
        },
    },
    "quarzit": {
        "name": "Quarzit",
        "applications": {
            "küchenarbeitsplatte": {
                "title": "Quarzit-Küchenarbeitsplatte verlegen",
                "steps": [
                    "Quarzit ist sehr hart – ähnlich wie Granit verlegen.",
                    "Untergrund prüfen und vorbereiten.",
                    "Platten mit Epoxidkleber fixieren.",
                    "Fugen mit passender Epoxidmasse verfüllen.",
                    "Nach Aushärtung polieren (optional).",
                ],
                "materials": ["Quarzitplatten", "Epoxidkleber", "Fugenmasse", "Polierwerkzeug"],
                "tips": ["Quarzit ist säurebeständig – ideal für Küchen."],
            },
        },
    },
    "schiefer": {
        "name": "Schiefer",
        "applications": {
            "boden": {
                "title": "Schieferboden verlegen",
                "steps": [
                    "Schiefer ist rutschfest – ideal für Böden.",
                    "Estrich prüfen: Sauber, eben, trocken.",
                    "Kleber (Flexkleber) auftragen.",
                    "Schieferplatten verlegen (Kreuzverband).",
                    "Fugen mit Epoxidverguss füllen.",
                    "Nach Trocknung: mit Schieferöl behandeln (optional).",
                ],
                "materials": ["Schieferplatten", "Flexkleber", "Fugenverguss", "Schieferöl"],
                "tips": ["Schiefer ist frostbeständig – auch für Außenbereiche geeignet."],
            },
            "fassade": {
                "title": "Schiefer-Fassade verkleiden",
                "steps": [
                    "Untergrund prüfen (tragfähig, sauber).",
                    "Schieferplatten mit Klebemörtel oder Ankern befestigen.",
                    "Fugen mit wetterfestem Material verfüllen.",
                    "Oberfläche imprägnieren (bei Bedarf).",
                ],
                "materials": ["Schieferplatten", "Klebemörtel", "Anker", "Fugenmaterial"],
                "tips": ["Schiefer ist witterungsbeständig – ideal für Außenwände."],
            },
        },
    },
    "travertin": {
        "name": "Travertin",
        "applications": {
            "boden": {
                "title": "Travertinboden verlegen",
                "steps": [
                    "Travertin ist porös – sorgfältig versiegeln.",
                    "Estrich prüfen: Sauber, eben, trocken.",
                    "Kleber (Flexkleber) auftragen.",
                    "Travertinplatten verlegen.",
                    "Fugen mit passendem Fugenmaterial füllen.",
                    "Nach dem Trocknen: Travertin versiegeln.",
                ],
                "materials": ["Travertinplatten", "Flexkleber", "Fugenmaterial", "Versiegelung"],
                "tips": ["Travertin ist empfindlich gegen Säuren – nur pH-neutrale Reiniger."],
            },
        },
    },
    "kalkstein": {
        "name": "Kalkstein",
        "applications": {
            "boden": {
                "title": "Kalksteinboden verlegen",
                "steps": [
                    "Kalkstein ist weich – vorsichtig verlegen.",
                    "Estrich prüfen.",
                    "Kleber (Flexkleber) auftragen.",
                    "Kalksteinplatten verlegen.",
                    "Fugen füllen und nach dem Trocknen versiegeln.",
                ],
                "materials": ["Kalksteinplatten", "Flexkleber", "Fugenmaterial", "Versiegelung"],
                "tips": ["Kalkstein ist säureempfindlich – sofort reinigen."],
            },
        },
    },
}


class InstallationGuidePlugin:
    name = "installation_guide"
    description = "Verlegeanleitungen für Naturstein (Küchenarbeitsplatten, Böden, Fassaden, etc.)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "stone": {
                "type": "string",
                "description": "Steinname (z.B. Granit, Marmor, Quarzit, Schiefer, Travertin, Kalkstein).",
            },
            "application": {
                "type": "string",
                "description": "Anwendungsbereich (z.B. Küchenarbeitsplatte, Boden, Fassade, Treppe, Außenbereich).",
                "default": "küchenarbeitsplatte",
            },
        },
        "required": ["stone"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "stone": {"type": "string"},
            "application": {"type": "string"},
            "title": {"type": "string"},
            "steps": {"type": "array"},
            "materials": {"type": "array"},
            "tips": {"type": "array"},
            "error": {"type": "string"},
        },
    }

    def _find_application(self, stone_key: str, app_key: str) -> dict[str, Any] | None:
        """Findet die Anleitung für eine bestimmte Anwendung."""
        stone_data = _INSTALLATION_DB.get(stone_key)
        if not stone_data:
            return None

        # Exakte Suche
        app_data = stone_data["applications"].get(app_key)
        if app_data:
            return app_data

        # Teilübereinstimmung
        for key, value in stone_data["applications"].items():
            if app_key in key or key in app_key:
                return value
        return None

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        stone_name = str(input_data.get("stone", "")).strip().lower()
        application = str(input_data.get("application", "küchenarbeitsplatte")).strip().lower()

        if not stone_name:
            return {"error": "Bitte geben Sie einen Stein an (z.B. Granit, Marmor)."}

        # Finde den passenden Stein (auch Teilübereinstimmung)
        stone_key = None
        for key in _INSTALLATION_DB:
            if stone_name == key:
                stone_key = key
                break
        if not stone_key:
            for key in _INSTALLATION_DB:
                if stone_name in key or key in stone_name:
                    stone_key = key
                    break

        if not stone_key:
            available = ", ".join(_INSTALLATION_DB.keys())
            return {"error": f"Keine Verlegeanleitung für '{input_data.get('stone')}' gefunden. Verfügbare Steine: {available}"}

        # Anwendung suchen
        app_data = self._find_application(stone_key, application)
        if not app_data:
            available_apps = ", ".join(_INSTALLATION_DB[stone_key]["applications"].keys())
            return {
                "error": f"Keine Anleitung für '{application}' bei {stone_key}. Verfügbare Anwendungen: {available_apps}"
            }

        # Ergebnisformatierung
        return {
            "stone": _INSTALLATION_DB[stone_key]["name"],
            "application": application,
            "title": app_data.get("title", ""),
            "steps": app_data.get("steps", []),
            "materials": app_data.get("materials", []),
            "tips": app_data.get("tips", []),
        }

