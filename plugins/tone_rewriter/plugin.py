# packages/plugins/tone_rewriter/plugin.py
from __future__ import annotations

import re
from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "tone_rewriter",
    "name": "Tone Rewriter",
    "description": "Schreibt Texte in verschiedenen Stimmungen/Tönen um (professionell, freundlich, sachlich, etc.)",
    "category": "🧠 NLP & Content",
    "apiKeyRequired": False,
    "intentPattern": r"\b(ton|stil|umschreiben|neu schreiben|freundlich|professionell|sachlich|formell|locker)\b",
    "status": "implemented",
    "settingsFields": [],
}


class ToneRewriterPlugin:
    name = "tone_rewriter"
    description = "Schreibt Texte in verschiedenen Stimmungen/Tönen um"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der zu bearbeitende Text.",
            },
            "tone": {
                "type": "string",
                "enum": [
                    "professional",
                    "friendly",
                    "persuasive",
                    "formal",
                    "casual",
                    "enthusiastic",
                    "empathetic",
                    "concise",
                    "detailed",
                    "humorous",
                    "neutral",
                ],
                "default": "professional",
                "description": "Gewünschter Ton/Stil.",
            },
            "target_audience": {
                "type": "string",
                "enum": ["general", "expert", "customer", "partner", "internal"],
                "default": "general",
                "description": "Zielgruppe für den Text.",
            },
            "preserve_keywords": {
                "type": "boolean",
                "default": True,
                "description": "Fachspezifische Begriffe beibehalten.",
            },
            "language": {
                "type": "string",
                "enum": ["de", "en", "auto"],
                "default": "auto",
                "description": "Sprache des Textes (auto = automatische Erkennung).",
            },
        },
        "required": ["text"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "original": {"type": "string"},
            "rewritten": {"type": "string"},
            "tone": {"type": "string"},
            "target_audience": {"type": "string"},
            "changes": {"type": "array"},
            "message": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    # Ton-Transformationsregeln
    _TONE_RULES: dict[str, dict[str, Any]] = {
        "professional": {
            "formal_level": 0.9,
            "personal_pronouns": False,
            "contractions": False,
            "emoji": False,
            "exclamation_limit": 0,
            "word_style": "formal",
            "example": "Die Anfrage wird geprüft und wir werden uns zeitnah bei Ihnen melden.",
        },
        "friendly": {
            "formal_level": 0.3,
            "personal_pronouns": True,
            "contractions": True,
            "emoji": True,
            "exclamation_limit": 2,
            "word_style": "friendly",
            "example": "Hallo! Wir schauen uns deine Anfrage gerne an und melden uns gleich bei dir! 😊",
        },
        "persuasive": {
            "formal_level": 0.5,
            "personal_pronouns": True,
            "contractions": True,
            "emoji": False,
            "exclamation_limit": 1,
            "word_style": "persuasive",
            "example": "Profitieren Sie jetzt von unserem exklusiven Angebot! Wir freuen uns auf Ihre Anfrage.",
        },
        "formal": {
            "formal_level": 1.0,
            "personal_pronouns": False,
            "contractions": False,
            "emoji": False,
            "exclamation_limit": 0,
            "word_style": "formal",
            "example": "Ihre Anfrage wird mit höchster Priorität behandelt. Sie erhalten in Kürze eine Rückmeldung.",
        },
        "casual": {
            "formal_level": 0.1,
            "personal_pronouns": True,
            "contractions": True,
            "emoji": True,
            "exclamation_limit": 3,
            "word_style": "casual",
            "example": "Hey! Klar, schauen wir uns das mal an. Melde mich gleich bei dir! 🙂",
        },
        "enthusiastic": {
            "formal_level": 0.2,
            "personal_pronouns": True,
            "contractions": True,
            "emoji": True,
            "exclamation_limit": 3,
            "word_style": "enthusiastic",
            "example": "Das ist eine großartige Idee! Wir sind total begeistert und kümmern uns sofort darum! 🚀",
        },
        "empathetic": {
            "formal_level": 0.4,
            "personal_pronouns": True,
            "contractions": True,
            "emoji": True,
            "exclamation_limit": 1,
            "word_style": "empathetic",
            "example": "Ich verstehe deine Situation sehr gut und verspreche dir, dass wir eine gute Lösung finden werden.",
        },
        "concise": {
            "formal_level": 0.5,
            "personal_pronouns": False,
            "contractions": False,
            "emoji": False,
            "exclamation_limit": 0,
            "word_style": "concise",
            "example": "Anfrage eingegangen. Rückmeldung folgt heute.",
        },
        "detailed": {
            "formal_level": 0.7,
            "personal_pronouns": True,
            "contractions": False,
            "emoji": False,
            "exclamation_limit": 0,
            "word_style": "detailed",
            "example": "Vielen Dank für Ihre Anfrage. Wir haben folgende Aspekte geprüft: ...",
        },
        "humorous": {
            "formal_level": 0.1,
            "personal_pronouns": True,
            "contractions": True,
            "emoji": True,
            "exclamation_limit": 3,
            "word_style": "humorous",
            "example": "Haha, ja das kenne ich! Stein auf Stein – wir finden da schon eine Lösung! 😄",
        },
        "neutral": {
            "formal_level": 0.5,
            "personal_pronouns": False,
            "contractions": False,
            "emoji": False,
            "exclamation_limit": 0,
            "word_style": "neutral",
            "example": "Die Anfrage wird geprüft. Eine Rückmeldung folgt.",
        },
    }

    # Wort-Ersetzungen für verschiedene Stile
    _WORD_REPLACEMENTS: dict[str, dict[str, dict[str, str]]] = {
        "de": {
            "friendly": {
                "Sie": "du",
                "Ihnen": "dir",
                "Ihr": "dein",
                "Anfrage": "Anliegen",
                "mitteilen": "sagen",
                "erhalten": "bekommen",
                "zeitnah": "gleich",
                "bald": "ganz bald",
                "prüfen": "anschauen",
                "Bearbeitung": "Sache",
            },
            "formal": {
                "du": "Sie",
                "dir": "Ihnen",
                "dein": "Ihr",
                "Anliegen": "Anfrage",
                "sagen": "mitteilen",
                "bekommen": "erhalten",
                "gleich": "zeitnah",
                "anschauen": "prüfen",
                "Sache": "Bearbeitung",
            },
            "persuasive": {
                "können": "profitieren Sie von",
                "Anfrage": "Angebot",
                "prüfen": "nutzen",
                "melden": "überzeugen",
                "Angebot": "Möglichkeit",
            },
            "empathetic": {
                "verstehen": "ich verstehe vollkommen",
                "prüfen": "mich darum kümmern",
                "melden": "dich auf dem Laufenden halten",
            },
            "enthusiastic": {
                "Anfrage": "tolle Anfrage",
                "prüfen": "uns freuen auf",
                "melden": "begeistert melden",
                "gut": "fantastisch",
                "Angebot": "chance",
            },
            "concise": {
                "Vielen Dank": "Danke",
                "Ich möchte Sie bitten": "Bitte",
                "Wir werden": "Wir",
                "Anfrage eingegangen": "Erhalten",
            },
        },
        "en": {
            "friendly": {
                "you": "you",
                "your": "your",
                "request": "question",
                "inform": "let you know",
                "receive": "get",
                "promptly": "soon",
                "review": "look at",
                "handling": "thing",
            },
            "formal": {
                "you": "you",
                "your": "your",
                "question": "inquiry",
                "let you know": "inform you",
                "get": "receive",
                "soon": "promptly",
                "look at": "review",
            },
        },
    }

    # Emojis pro Ton
    _EMOJIS: dict[str, list[str]] = {
        "friendly": ["😊", "🙂", "🌿", "✨", "💪"],
        "casual": ["😉", "🤗", "🎉", "✨", "👋"],
        "enthusiastic": ["🚀", "💥", "⭐", "🎯", "🔥"],
        "empathetic": ["❤️", "🙏", "🌱", "✨", "💕"],
        "humorous": ["😄", "😂", "🤣", "😉", "🤭"],
    }

    def __init__(self):
        pass

    def _detect_language(self, text: str) -> str:
        de_words = ["der", "die", "das", "und", "für", "mit", "von", "im", "am", "auf"]
        en_words = ["the", "and", "for", "with", "of", "in", "on", "at", "to", "from"]
        text_lower = text.lower()
        de_count = sum(1 for w in de_words if w in text_lower)
        en_count = sum(1 for w in en_words if w in text_lower)
        return "de" if de_count > en_count else "en"

    def _apply_tone_transformation(
        self,
        text: str,
        tone: str,
        target_audience: str,
        language: str,
        preserve_keywords: bool,
    ) -> tuple[str, list[str]]:
        """Wendet die Ton-Transformation auf den Text an."""
        changes: list[str] = []
        result = text

        tone_rules = self._TONE_RULES.get(tone, self._TONE_RULES["neutral"])
        replacements = self._WORD_REPLACEMENTS.get(language, {})

        # 1. Wort-Ersetzungen
        for category, words in replacements.items():
            if category in ["friendly", "formal", "persuasive", "empathetic", "enthusiastic", "concise"]:
                # Nur den passenden Stil anwenden, der zum Ton passt
                # Wir wenden den spezifischen Stil an
                if category == tone or (tone in ["professional", "neutral"] and category == "formal"):
                    for old, new in words.items():
                        if old in result:
                            # Achtung: nur ganze Wörter ersetzen
                            result = re.sub(rf'\b{old}\b', new, result)
                            changes.append(f"'{old}' → '{new}'")
                elif tone == "friendly" and category == "friendly":
                    for old, new in words.items():
                        if old in result:
                            result = re.sub(rf'\b{old}\b', new, result)
                            changes.append(f"'{old}' → '{new}'")

        # 2. Stilistische Anpassungen
        if tone_rules["emoji"] and language == "de":
            emojis = self._EMOJIS.get(tone, [])
            if emojis and not any(emoji in result for emoji in emojis):
                # Emoji am Ende hinzufügen, wenn nicht zu lang
                if len(result) < 500:
                    result += f" {emojis[0]}"
                    changes.append("Emoji hinzugefügt")

        # 3. Ausrufezeichen begrenzen
        if tone_rules["exclamation_limit"] >= 0:
            exclamation_count = result.count("!")
            if exclamation_count > tone_rules["exclamation_limit"]:
                # Überzählige Ausrufezeichen durch Punkt ersetzen
                count = 0
                new_result = ""
                for char in result:
                    if char == "!" and count >= tone_rules["exclamation_limit"]:
                        new_result += "."
                    else:
                        if char == "!":
                            count += 1
                        new_result += char
                result = new_result
                changes.append(f"Ausrufezeichen auf {tone_rules['exclamation_limit']} begrenzt")

        # 4. Anrede anpassen (für "friendly" und "casual")
        if tone in ["friendly", "casual", "enthusiastic", "empathetic", "humorous"]:
            if "Sie" in result and language == "de":
                result = result.replace("Sie", "du")
                result = result.replace("Ihnen", "dir")
                result = result.replace("Ihr", "dein")
                changes.append("Anrede auf 'du' umgestellt")

        # 5. Fachbegriffe beibehalten (wenn gewünscht)
        if preserve_keywords:
            # Wir tun hier nichts Spezielles – Fachbegriffe bleiben erhalten
            pass

        return result, changes

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = str(input_data.get("text", "")).strip()
        if not text:
            return {"success": False, "error": "text ist erforderlich."}

        tone = str(input_data.get("tone", "professional")).lower()
        target_audience = str(input_data.get("target_audience", "general")).lower()
        preserve_keywords = bool(input_data.get("preserve_keywords", True))
        language = str(input_data.get("language", "auto")).lower()

        if language == "auto":
            language = self._detect_language(text)

        # Ton validieren
        if tone not in self._TONE_RULES:
            return {
                "success": False,
                "error": f"Unbekannter Ton: {tone}. Verfügbare Töne: {', '.join(self._TONE_RULES.keys())}",
            }

        # Anwenden der Transformation
        rewritten, changes = self._apply_tone_transformation(
            text, tone, target_audience, language, preserve_keywords
        )

        return {
            "success": True,
            "original": text,
            "rewritten": rewritten,
            "tone": tone,
            "target_audience": target_audience,
            "changes": changes,
            "language": language,
            "message": f"Text erfolgreich in den Ton '{tone}' umgeschrieben. {len(changes)} Änderungen vorgenommen.",
        }


