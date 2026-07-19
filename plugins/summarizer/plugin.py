# packages/plugins/summarizer/plugin.py
from __future__ import annotations

import re
from typing import Any, cast


PLUGIN_META: dict[str, Any] = {
    "id": "summarizer",
    "name": "Summarizer",
    "description": "Zusammenfassung langer Texte (extractive oder abstractive)",
    "category": "🧠 NLP & Content",
    "apiKeyRequired": False,
    "intentPattern": r"\b(zusammenfassen|kurzfassung|summary|resümee|text verdichten)\b",
    "status": "implemented",
    "settingsFields": [
        {
            "key": "mode",
            "label": "Standard-Modus",
            "type": "select",
            "default": "auto",
            "group": "Modell",
            "options": [
                {"value": "auto", "label": "Auto"},
                {"value": "extractive", "label": "Extractive"},
                {"value": "abstractive", "label": "Abstractive"},
            ],
        },
        {
            "key": "max_length",
            "label": "Maximale Wortanzahl",
            "type": "number",
            "default": 150,
            "group": "Laufzeit",
        },
        {
            "key": "min_length",
            "label": "Minimale Wortanzahl",
            "type": "number",
            "default": 30,
            "group": "Laufzeit",
        },
        {
            "key": "ratio",
            "label": "Summary-Verhältnis",
            "type": "number",
            "default": 0.3,
            "group": "Laufzeit",
        },
    ],
}


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key_raw, value_raw in cast(dict[object, Any], value).items():
        normalized[str(key_raw)] = value_raw
    return normalized


class SummarizerPlugin:
    name = "summarizer"
    description = "Zusammenfassung langer Texte (extractive oder abstractive)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der zu zusammenfassende Text.",
            },
            "mode": {
                "type": "string",
                "enum": ["extractive", "abstractive", "auto"],
                "default": "auto",
                "description": "Modus: extractive (Sätze extrahieren), abstractive (neu generieren), auto (automatisch).",
            },
            "max_length": {
                "type": "integer",
                "minimum": 10,
                "maximum": 500,
                "default": 150,
                "description": "Maximale Länge der Zusammenfassung (in Wörtern).",
            },
            "min_length": {
                "type": "integer",
                "minimum": 5,
                "maximum": 100,
                "default": 30,
                "description": "Minimale Länge der Zusammenfassung (in Wörtern).",
            },
            "ratio": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 0.9,
                "default": 0.3,
                "description": "Verhältnis der Zusammenfassung zur Originaltextlänge (für extractive).",
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
            "summary": {"type": "string"},
            "method": {"type": "string"},
            "original_length": {"type": "integer"},
            "summary_length": {"type": "integer"},
            "reduction_percent": {"type": "number"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.model_loaded = False
        self.summarizer_pipeline: Any = None
        self._load_model()

    def _load_model(self):
        """Lädt ein Modell für abstractive Summarization (falls verfügbar)."""
        try:
            # Versuche, transformers zu importieren
            from transformers import pipeline  # type: ignore[reportUnknownVariableType]
            # Prüfe, ob ein Modell verfügbar ist (kleines Modell für schnelle Ergebnisse)
            model_name = "google/pegasus-xsum"  # Für Englisch
            # Für Deutsch: "google/pegasus-multi_news" oder "t5-small"
            self.summarizer_pipeline = pipeline(
                "summarization",
                model=model_name,
                device=-1,  # CPU
            )
            self.model_loaded = True
        except ImportError:
            self.model_loaded = False
        except Exception:
            self.model_loaded = False

    def _extractive_summary(self, text: str, ratio: float, max_length: int, min_length: int) -> str:
        """Extractive Summarization: Wählt die wichtigsten Sätze aus."""
        if not text or len(text.strip()) < 10:
            return text

        # Text in Sätze zerlegen
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return text

        # Einfache Score-Berechnung: Wichtigkeit basierend auf Wortfrequenz
        words = ' '.join(sentences).lower().split()
        word_freq: dict[str, int] = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Satz-Scores berechnen
        sentence_scores: list[tuple[str, float]] = []
        for sent in sentences:
            score = 0.0
            sent_words = sent.lower().split()
            for word in sent_words:
                if word in word_freq:
                    score += float(word_freq[word])
            # Längere Sätze haben mehr Wörter, normalisieren
            score = score / max(1, len(sent_words))
            sentence_scores.append((sent, score))

        # Nach Score sortieren
        sentence_scores.sort(key=lambda item: item[1], reverse=True)

        # Anzahl der Sätze für die Zusammenfassung
        # Begrenzen auf max_length (in Wörtern)
        selected: list[str] = []
        word_count = 0
        for sent, _ in sentence_scores:
            sent_word_count = len(sent.split())
            if word_count + sent_word_count <= max_length:
                selected.append(sent)
                word_count += sent_word_count
            if word_count >= max_length:
                break

        # Originalreihenfolge wiederherstellen
        selected_set = set(selected)
        ordered = [s for s in sentences if s in selected_set]

        summary = '. '.join(ordered)
        if summary and not summary.endswith('.'):
            summary += '.'

        return summary

    def _abstractive_summary(self, text: str, max_length: int, min_length: int) -> str:
        """Abstractive Summarization: Generiert eine neue Zusammenfassung."""
        if not self.model_loaded:
            # Fallback: extractive
            return self._extractive_summary(text, 0.3, max_length, min_length)

        try:
            # Text auf max_length für das Modell begrenzen (512 Tokens)
            # Einfache Begrenzung auf ca. 1000 Zeichen
            if len(text) > 2000:
                text = text[:2000]

            pipeline_fn = self.summarizer_pipeline
            if not callable(pipeline_fn):
                return self._extractive_summary(text, 0.3, max_length, min_length)

            result_raw = pipeline_fn(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
            )
            if isinstance(result_raw, list) and result_raw:
                first = _as_dict(result_raw[0])
                if first:
                    return str(first.get("summary_text", ""))
            return ''
        except Exception:
            # Fallback auf extractive bei Fehlern
            return self._extractive_summary(text, 0.3, max_length, min_length)

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = str(input_data.get("text", "")).strip()
        if not text:
            return {"success": False, "error": "text ist erforderlich."}

        if len(text) < 30:
            return {
                "success": True,
                "summary": text,
                "method": "none",
                "original_length": len(text.split()),
                "summary_length": len(text.split()),
                "reduction_percent": 0.0,
                "message": "Text ist bereits kurz (weniger als 30 Zeichen).",
            }

        mode = str(input_data.get("mode", "auto")).lower()
        max_length = max(10, min(500, int(input_data.get("max_length", 150))))
        min_length = max(5, min(100, int(input_data.get("min_length", 30))))
        ratio = max(0.1, min(0.9, float(input_data.get("ratio", 0.3))))

        original_word_count = len(text.split())

        # Modus-Auswahl
        if mode == "extractive":
            summary = self._extractive_summary(text, ratio, max_length, min_length)
            method = "extractive"
        elif mode == "abstractive":
            summary = self._abstractive_summary(text, max_length, min_length)
            method = "abstractive"
        else:  # auto
            # Wenn der Text kurz ist, verwende extractive
            if len(text) < 500:
                summary = self._extractive_summary(text, ratio, max_length, min_length)
                method = "extractive"
            else:
                # Versuche abstractive, fallback auf extractive
                summary = self._abstractive_summary(text, max_length, min_length)
                method = "abstractive" if summary else "extractive"
                if not summary:
                    summary = self._extractive_summary(text, ratio, max_length, min_length)

        # Falls keine Zusammenfassung erzeugt wurde
        if not summary:
            summary = self._extractive_summary(text, ratio, max_length, min_length)
            method = "extractive (fallback)"

        summary_word_count = len(summary.split())
        reduction = ((original_word_count - summary_word_count) / original_word_count) * 100 if original_word_count > 0 else 0

        return {
            "success": True,
            "summary": summary,
            "method": method,
            "original_length": original_word_count,
            "summary_length": summary_word_count,
            "reduction_percent": round(reduction, 1),
            "message": f"Zusammenfassung erstellt ({method}). Reduziert von {original_word_count} auf {summary_word_count} Wörter ({round(reduction, 1)}%).",
        }