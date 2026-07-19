# packages/plugins/text_analyzer/plugin.py
from __future__ import annotations

import re
from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "text_analyzer",
    "name": "Text Analyzer",
    "description": "Analysiert Texte (Stimmung, Themen, Schlüsselwörter, Sprache, etc.)",
    "category": "🧠 NLP & Content",
    "apiKeyRequired": False,
    "intentPattern": r"\b(analysiere|bewerte|text|stimmung|sentiment|schlüsselwort|thema|sprache)\b",
    "status": "implemented",
    "settingsFields": [],
}


class TextAnalyzerPlugin:
    name = "text_analyzer"
    description = "Analysiert Texte (Stimmung, Themen, Schlüsselwörter, Sprache, etc.)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der zu analysierende Text.",
            },
            "analysis_type": {
                "type": "string",
                "enum": ["all", "sentiment", "keywords", "language", "summary"],
                "default": "all",
                "description": "Art der Analyse: all, sentiment, keywords, language, summary.",
            },
            "max_keywords": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "Maximale Anzahl an Schlüsselwörtern.",
            },
            "language": {
                "type": "string",
                "enum": ["de", "en", "fr", "es", "it", "auto"],
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
            "text_length": {"type": "integer"},
            "word_count": {"type": "integer"},
            "language": {"type": "string"},
            "sentiment": {"type": "object"},
            "keywords": {"type": "array"},
            "topics": {"type": "array"},
            "summary": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    # Einfache Sentiment-Wortlisten (erweiterbar)
    _POSITIVE_WORDS = {
        "de": [
            "gut", "schön", "toll", "super", "fantastisch", "perfekt", "klasse",
            "positiv", "hervorragend", "ausgezeichnet", "genial", "wunderbar",
            "großartig", "spitze", "prima", "angenehm", "zufrieden", "glücklich",
            "praktisch", "empfehlenswert", "elegant", "edel", "hochwertig",
        ],
        "en": [
            "good", "great", "excellent", "perfect", "wonderful", "fantastic",
            "amazing", "awesome", "brilliant", "outstanding", "superb", "positive",
            "happy", "satisfied", "recommend", "elegant", "high", "quality",
        ],
    }
    _NEGATIVE_WORDS = {
        "de": [
            "schlecht", "schlimm", "furchtbar", "katastrophal", "miserabel",
            "negativ", "enttäuschend", "unzufrieden", "ärgerlich", "schrecklich",
            "teuer", "billig", "unbrauchbar", "mangelhaft", "unzureichend",
            "problematisch", "unzufriedenstellend", "nervig", "peinlich",
        ],
        "en": [
            "bad", "terrible", "horrible", "awful", "poor", "negative",
            "disappointing", "unsatisfied", "annoying", "horrendous", "lousy",
            "cheap", "useless", "defective", "insufficient", "problematic",
            "unacceptable", "frustrating", "embarrassing",
        ],
    }

    def __init__(self):
        self._load_extensions()

    def _load_extensions(self):
        """Erweitert die Wortlisten (optional)."""
        # Hier könnte man externe Listen laden oder ML-Modelle initialisieren
        pass

    def _detect_language(self, text: str) -> str:
        """Einfache Spracherkennung."""
        if not text:
            return "unknown"
        # Deutsche typische Wörter
        de_words = ["der", "die", "das", "und", "für", "mit", "von", "im", "am", "auf", "ein", "einer"]
        en_words = ["the", "and", "for", "with", "of", "in", "on", "at", "to", "from", "by", "an", "a"]
        text_lower = text.lower()
        de_count = sum(1 for w in de_words if w in text_lower)
        en_count = sum(1 for w in en_words if w in text_lower)
        if de_count > en_count:
            return "de"
        elif en_count > de_count:
            return "en"
        return "en"  # Standardfall

    def _sentiment_analysis(self, text: str, language: str) -> dict[str, Any]:
        """Führt eine einfache Sentiment-Analyse durch."""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        positive_words = self._POSITIVE_WORDS.get(language, [])
        negative_words = self._NEGATIVE_WORDS.get(language, [])

        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        neutral_count = len(words) - pos_count - neg_count

        total = max(1, len(words))
        score = (pos_count - neg_count) / total

        if score > 0.1:
            polarity = "positiv"
            emoji = "😊"
        elif score < -0.1:
            polarity = "negativ"
            emoji = "😞"
        else:
            polarity = "neutral"
            emoji = "😐"

        return {
            "score": round(score, 3),
            "polarity": polarity,
            "emoji": emoji,
            "positive_words": pos_count,
            "negative_words": neg_count,
            "neutral_words": neutral_count,
            "sentiment_breakdown": {
                "positive": round(pos_count / total * 100, 1),
                "neutral": round(neutral_count / total * 100, 1),
                "negative": round(neg_count / total * 100, 1),
            },
        }

    def _extract_keywords(self, text: str, language: str, max_keywords: int) -> list[dict[str, Any]]:
        """Extrahiert Schlüsselwörter aus dem Text."""
        # Stoppwörter
        stopwords = {
            "de": ["der", "die", "das", "und", "für", "mit", "von", "im", "am", "auf", "ein", "einer",
                   "dem", "den", "des", "dass", "oder", "aber", "wenn", "weil", "auch", "nur", "sehr",
                   "nicht", "sich", "haben", "werden", "können", "möchten", "wollen"],
            "en": ["the", "and", "for", "with", "of", "in", "on", "at", "to", "from", "by", "an", "a",
                   "that", "or", "but", "if", "because", "also", "only", "very", "not", "have", "will",
                   "can", "would", "should"],
        }
        stopwords_lang = stopwords.get(language, stopwords["en"])

        # Bereinigen
        words = re.findall(r'\b\w{3,}\b', text.lower())
        words = [w for w in words if w not in stopwords_lang and len(w) > 2]

        # Frequenz zählen
        freq: dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1

        # Sortieren
        sorted_words: list[tuple[str, int]] = sorted(freq.items(), key=lambda item: item[1], reverse=True)

        results: list[dict[str, Any]] = []
        for word, count in sorted_words[:max_keywords]:
            # Kontext-Satz finden
            context = ""
            sentences = re.split(r'[.!?]\s+', text)
            for sent in sentences:
                if word in sent.lower():
                    context = sent.strip()
                    break
            results.append({
                "word": word,
                "count": count,
                "relevance": round(count / max(1, len(words)) * 100, 1),
                "context": context[:100] + "..." if len(context) > 100 else context,
            })

        return results

    def _extract_topics(self, text: str, language: str) -> list[dict[str, Any]]:
        """Extrahiert Themen basierend auf Keyword-Clustern."""
        # Beispielhafte Themen (für Naturstein-Domäne)
        topic_keywords = {
            "Stein/Material": ["granit", "marmor", "quarzit", "schiefer", "travertin", "kalkstein", "stein"],
            "Farbe": ["schwarz", "weiß", "grau", "beige", "braun", "rot", "grün", "blau"],
            "Verarbeitung": ["poliert", "geschliffen", "gebürstet", "geflammt", "getrommelt"],
            "Verwendung": ["küche", "boden", "fassade", "bad", "terrasse", "arbeitsplatte", "wand"],
            "Eigenschaften": ["hart", "säurebeständig", "kratzfest", "wetterfest", "porös", "weich"],
            "Service": ["angebot", "beratung", "muster", "termin", "lieferung", "installation"],
        }

        topic_scores: dict[str, int] = {}
        for topic, kws in topic_keywords.items():
            score = 0
            for kw in kws:
                if kw in text.lower():
                    score += 1
            if score > 0:
                topic_scores[topic] = score

        sorted_topics: list[tuple[str, int]] = sorted(topic_scores.items(), key=lambda item: item[1], reverse=True)
        return [{"topic": t, "score": s} for t, s in sorted_topics[:5]]

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = str(input_data.get("text", "")).strip()
        if not text:
            return {"success": False, "error": "text ist erforderlich."}

        analysis_type = str(input_data.get("analysis_type", "all")).lower()
        max_keywords = max(1, min(20, int(input_data.get("max_keywords", 5))))
        language = str(input_data.get("language", "auto")).lower()

        if language == "auto":
            language = self._detect_language(text)

        result: dict[str, Any] = {
            "success": True,
            "text_length": len(text),
            "word_count": len(text.split()),
            "language": language,
        }

        if analysis_type in ["all", "sentiment"]:
            result["sentiment"] = self._sentiment_analysis(text, language)

        if analysis_type in ["all", "keywords"]:
            result["keywords"] = self._extract_keywords(text, language, max_keywords)

        if analysis_type in ["all", "topics"]:
            result["topics"] = self._extract_topics(text, language)

        if analysis_type in ["all", "summary"]:
            result["summary"] = self._generate_summary(text, language, 3)

        return result

    def _generate_summary(self, text: str, language: str, num_sentences: int) -> str:
        """Erstellt eine kurze Zusammenfassung (extractiv)."""
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

        if not sentences:
            return text[:200] + "..." if len(text) > 200 else text

        # Wähle die ersten Sätze (einfach) oder nach Wichtigkeit
        # Hier: erste 3 Sätze
        selected = sentences[:num_sentences]
        summary = ". ".join(selected)
        if summary and not summary.endswith("."):
            summary += "."
        return summary


