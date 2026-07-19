import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
import hashlib
import json
import logging
import os
import re
import threading
from typing import Any, TypedDict, cast
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.context_builder import ContextBuilder
from app.chat.diagnostics_store import prompt_diagnostics_store
from app.chat.token_counter import TokenCounter
from app.database.repositories.conversation_repository import ConversationRepository
from app.database.repositories.knowledge_repository import KnowledgeRepository
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.user_repository import UserRepository
from app.db_models.model_config import ModelConfig
from app.models.loader import create_backend
from app.models.executor import ModelExecutor
from app.models.manager import model_manager
from app.schemas.chat import ChatRequest, ChatResponse
from app.settings.service import SettingsService
from app.settings.validator import validate_setting
from app.tools import PluginExecutionError, PluginExecutor


logger = logging.getLogger(__name__)

_SPECIALIST_KEYWORDS = {
    "naturstein",
    "marmor",
    "granit",
    "gneis",
    "quarzit",
    "travertin",
    "kalkstein",
    "sandstein",
    "fensterbank",
    "tausalz",
    "imprägnierung",
    "impragnierung",
    "verfugung",
    "frost",
}


_RESPONSE_STYLE_APPENDIX = (
    "Antworte standardmaessig in natuerlichem, zusammenhaengendem Fliesstext auf Deutsch.\n"
    "Verwende keine Markdown-Syntax, keine Emojis und keine kuenstlichen Ueberschriften.\n"
    "Setze Aufzaehlungen oder Nummerierungen nur dann ein, wenn der Nutzer das ausdruecklich verlangt oder der Inhalt ohne Liste unklar waere.\n"
    "Halte Antworten klar, praezise und gut lesbar mit kurzen Absaetzen.\n"
    "Wiederhole die Nutzerfrage nicht unnoetig und antworte bei einfachen Fragen kurz."
)


CONVERSATION_PROJECT_MAP_SETTING_KEY = "conversation_project_map"
WORKSPACE_PROJECT_META_MAP_SETTING_KEY = "project_meta_map"

_PLUGIN_SEARCH_PATTERN = re.compile(
    r"<plugin_search>\s*(?P<payload>\{.*?\})\s*</plugin_search>",
    re.IGNORECASE | re.DOTALL,
)
_PLUGIN_MANIFEST_PATTERN = re.compile(
    r"<plugin_manifest>\s*(?P<plugin_id>[^<]+?)\s*</plugin_manifest>",
    re.IGNORECASE | re.DOTALL,
)
_PLUGIN_FUNCTION_PATTERN = re.compile(
    r"<plugin_function>\s*(?P<payload>\{.*?\})\s*</plugin_function>",
    re.IGNORECASE | re.DOTALL,
)

_DOCUMENT_REQUEST_KEYWORDS = {
    "dokument",
    "dokumentanfrage",
    "geschaeftsbrief",
    "geschäftsbrief",
    "brief",
    "anschreiben",
    "angebot",
    "auftragsbestaetigung",
    "auftragsbestätigung",
    "lieferschein",
    "rechnung",
    "gutschrift",
    "stornorechnung",
    "mahnung",
    "zahlungserinnerung",
    "abnahmeprotokoll",
    "reklamation",
}

_PRICE_RESEARCH_KEYWORDS = {
    "internet",
    "durchschnitt",
    "durchschnittlich",
    "preis",
    "preise",
    "ermittel",
    "recherchiere",
}

_DOCUMENT_TYPE_HINTS: list[tuple[str, str]] = [
    ("auftragsbestaetigung", "auftragsbestaetigung"),
    ("auftragsbestätigung", "auftragsbestaetigung"),
    ("zahlungserinnerung", "zahlungserinnerung"),
    ("stornorechnung", "stornorechnung"),
    ("gutschrift", "gutschrift"),
    ("lieferschein", "lieferschein"),
    ("rechnung", "rechnung"),
    ("mahnung", "mahnung"),
    ("angebot", "angebot"),
    ("reklamation", "reklamation_antwort"),
    ("brief", "allgemein"),
    ("anschreiben", "allgemein"),
]

_UNIT_CODE_MAP = {
    "stueck": "C62",
    "stück": "C62",
    "stk": "C62",
    "qm": "MTK",
    "m2": "MTK",
    "lfm": "MTR",
    "m": "MTR",
}


def clean_model_output_text(text: str) -> str:
    candidate = str(text or "").replace("\r\n", "\n")
    if not candidate:
        return ""

    candidate = re.sub(r"<think>.*?</think>", "", candidate, flags=re.DOTALL | re.IGNORECASE)
    candidate = re.sub(r"^<think>\s*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"(?im)^thinking process:\s*", "", candidate)
    candidate = re.sub(r"(?im)^assistant:\s*", "", candidate)

    lowered = candidate.lower()
    if "analyze the request" in lowered or "determine the core fact" in lowered or "determine the core information" in lowered:
        if "###" not in candidate and not re.search(r"(?im)^(ja|nein|verwende|nutze|marmor|granit|quarzit)\b", candidate):
            return ""

    candidate = re.sub(r"\n{3,}", "\n\n", candidate)
    candidate = re.sub(r"([^\n])\n([*-]\s)", r"\1\n\n\2", candidate)
    candidate = re.sub(r"([^\n])\n(\d+\.\s)", r"\1\n\n\2", candidate)
    candidate = _enforce_plain_text_readability(candidate)
    return candidate.strip()


def _enforce_plain_text_readability(text: str) -> str:
    if not text.strip():
        return ""

    # Keep fenced code blocks intact and normalize prose chunks only.
    parts = re.split(r"(```[\s\S]*?```)", text)
    normalized_parts: list[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            normalized_parts.append(part)
            continue
        normalized_parts.append(_reflow_prose_to_plain_text(part))

    merged = "".join(normalized_parts)
    merged = re.sub(r"\n{3,}", "\n\n", merged)
    return merged.strip()


def _reflow_prose_to_plain_text(text: str) -> str:
    raw = text.replace("\r\n", "\n")
    if not raw.strip():
        return ""

    lines = [line.rstrip() for line in raw.split("\n")]
    cleaned_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue

        # Remove heading markers while keeping content.
        stripped = re.sub(r"^#{1,6}\s+", "", stripped)

        # Convert markdown list markers into plain sentences.
        stripped = re.sub(r"^[-*]\s+", "", stripped)
        stripped = re.sub(r"^\d+\.\s+", "", stripped)

        cleaned_lines.append(stripped)

    paragraphs: list[str] = []
    current: list[str] = []
    for line in cleaned_lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    merged = "\n\n".join(paragraphs)
    merged = re.sub(r"[ \t]+", " ", merged)
    merged = re.sub(r"\n{3,}", "\n\n", merged)
    return merged.strip()


def _enforce_markdown_readability(text: str) -> str:
    if not text.strip():
        return ""

    # Keep fenced code blocks intact and only reflow prose chunks.
    parts = re.split(r"(```[\s\S]*?```)", text)
    normalized_parts: list[str] = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            normalized_parts.append(part)
            continue
        normalized_parts.append(_reflow_prose_to_markdown(part))

    merged = "".join(normalized_parts)
    merged = re.sub(r"\n{3,}", "\n\n", merged)
    merged = _promote_long_intro_to_header(merged)
    merged = _normalize_inline_list_blobs(merged)
    merged = _split_long_list_runs(merged)
    merged = _ensure_spacing_after_headers(merged)
    return merged


def _reflow_prose_to_markdown(text: str) -> str:
    raw = text.replace("\r\n", "\n")
    if not raw.strip():
        return raw

    has_markdown_structure = bool(
        re.search(r"(?m)^\s*(#{1,6}\s|[-*]\s|\d+\.\s|>\s)", raw)
    )

    collapsed = re.sub(r"[ \t]+", " ", raw).strip()
    if not collapsed:
        return ""

    if not has_markdown_structure and "\n" not in collapsed and len(collapsed) > 240:
        sentences = [
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9])", collapsed)
            if item.strip()
        ]
        if len(sentences) >= 3:
            paragraphs: list[str] = []
            chunk: list[str] = []
            for sentence in sentences:
                chunk.append(sentence)
                if len(chunk) >= 2:
                    paragraphs.append(" ".join(chunk))
                    chunk = []
            if chunk:
                paragraphs.append(" ".join(chunk))
            return "\n\n".join(paragraphs)

    # Normalize manually broken lines to paragraph blocks.
    lines = [line.strip() for line in raw.split("\n")]
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if re.match(r"^#{1,6}\s", line) or re.match(r"^[-*]\s", line) or re.match(r"^\d+\.\s", line):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append(line)
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    rebuilt = "\n\n".join(paragraphs)
    rebuilt = re.sub(r"\n{3,}", "\n\n", rebuilt)
    return rebuilt


def _split_long_list_runs(text: str, *, max_items: int = 5) -> str:
    lines = text.split("\n")
    result: list[str] = []
    run: list[str] = []

    def flush_run() -> None:
        nonlocal run
        if not run:
            return
        if len(run) <= max_items:
            result.extend(run)
            run = []
            return

        chunks: list[list[str]] = []
        for idx in range(0, len(run), max_items):
            chunks.append(run[idx : idx + max_items])

        for chunk_index, chunk in enumerate(chunks):
            if chunk_index > 0:
                result.append("")
                result.append("### Weitere Punkte")
                result.append("")
            result.extend(chunk)
        run = []

    for line in lines:
        if re.match(r"^\s*([-*]|\d+\.)\s", line):
            run.append(line)
            continue
        flush_run()
        result.append(line)

    flush_run()
    return "\n".join(result)


def _promote_long_intro_to_header(text: str) -> str:
    lines = text.split("\n")
    if not lines:
        return text
    first_nonempty_idx = -1
    for idx, line in enumerate(lines):
        if line.strip():
            first_nonempty_idx = idx
            break
    if first_nonempty_idx < 0:
        return text

    first_line = lines[first_nonempty_idx].strip()
    has_header = bool(re.match(r"^#{1,6}\s", first_line))
    if has_header:
        return text

    if len(first_line) > 16 and len(first_line) < 110 and not first_line.endswith(":"):
        lines[first_nonempty_idx] = f"## {first_line}"
    return "\n".join(lines)


def _normalize_inline_list_blobs(text: str) -> str:
    # Convert patterns like "...: * A * B * C" into proper bullet lines.
    result_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if "*" in stripped and stripped.count("*") >= 2 and not stripped.startswith("*"):
            parts = [part.strip() for part in stripped.split("*") if part.strip()]
            if len(parts) >= 3:
                head = parts[0]
                result_lines.append(head)
                result_lines.append("")
                for item in parts[1:]:
                    result_lines.append(f"- {item}")
                continue
        result_lines.append(line)
    return "\n".join(result_lines)


def _ensure_spacing_after_headers(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    for idx, line in enumerate(lines):
        out.append(line)
        if re.match(r"^#{1,6}\s", line.strip()):
            next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
            if next_line.strip() != "":
                out.append("")
    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _strip_unverified_sources(text: str) -> str:
    if not text.strip():
        return text

    lines = text.split("\n")
    result: list[str] = []
    skip_sources_block = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if re.match(r"^#{1,6}\s+quellen\b", lower) or re.match(r"^quellen\s*:?$", lower):
            skip_sources_block = True
            continue

        if skip_sources_block:
            if stripped == "":
                skip_sources_block = False
                continue
            if stripped.startswith("*") or stripped.startswith("-") or re.match(r"^\d+\.\s", stripped) or "http://" in lower or "https://" in lower:
                continue
            # Continue skipping until a non-source paragraph/header appears.
            if re.match(r"^#{1,6}\s+", stripped):
                skip_sources_block = False
                result.append(line)
                continue
            continue

        if "http://" in lower or "https://" in lower:
            continue

        result.append(line)

    cleaned = "\n".join(result)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class RetrievalSource(TypedDict):
    id: int
    file: str
    position: str
    relevance: str
    status: str
    score: int
    raw_score: int
    normalized_score: float
    keyword_hits: int
    project_id: int | None
    scope_depth: int | None


class RetrievalDiagnostic(TypedDict):
    id: int
    file: str
    position: str
    relevance: str
    status: str
    keyword_hits: int
    raw_score: int
    normalized_score: float
    selected: bool
    discard_reason: str | None
    project_id: int | None
    scope_depth: int | None


class PreparedContextPayload(TypedDict):
    prompt: str
    chat_messages: list[dict[str, str]]
    chat_template_source: str
    system_prompt: str
    temperature: float
    max_new_tokens: int
    top_p: float
    top_k: int
    repetition_penalty: float
    do_sample: bool
    seed: int
    stop_sequences: list[str]
    context_limit: int
    safety_margin: int
    used_context_tokens: int
    used_history_tokens: int
    history_total_messages: int
    history_dropped_messages: int
    external_data_tokens: int
    files_tokens: int
    external_data_integrated: bool
    external_data_sources_count: int
    external_data_selected_count: int
    external_data_dropped_count: int
    external_data_top_k: int
    external_data_selected_sources: list[dict[str, object]]
    retrieval_diagnostics: list[RetrievalDiagnostic]


class ActiveConversationGenerationProfile(TypedDict):
    version_id: str
    params: dict[str, object]


class ImageInputPayload(TypedDict):
    name: str
    mime_type: str
    data_base64: str


def _parse_metadata(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    if isinstance(parsed, dict):
        return cast(dict[str, object], parsed)
    return {}


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.context_builder = ContextBuilder()
        self.executor = ModelExecutor()
        self.plugin_executor = PluginExecutor()
        self.settings_service = SettingsService(session)
        self.conversation_repo = ConversationRepository(session)
        self.message_repo = MessageRepository(session)
        self.knowledge_repo = KnowledgeRepository(session)
        self.user_repo = UserRepository(session)

    def _parse_relevance_percent(self, relevance_raw: object) -> int:
        if isinstance(relevance_raw, (int, float)):
            return max(0, min(100, int(relevance_raw)))
        if isinstance(relevance_raw, str):
            digits = "".join(ch for ch in relevance_raw if ch.isdigit())
            if digits:
                return max(0, min(100, int(digits)))
        return 0

    def _parse_conversation_project_map(self, raw: object) -> dict[int, int]:
        if not isinstance(raw, dict):
            return {}

        parsed: dict[int, int] = {}
        raw_map = cast(dict[object, object], raw)
        for raw_conversation_id, raw_project_id in raw_map.items():
            conversation_id_text = str(raw_conversation_id)
            if not conversation_id_text.isdigit() or not isinstance(raw_project_id, int):
                continue
            parsed[int(conversation_id_text)] = raw_project_id
        return parsed

    def _coerce_project_meta(self, raw: object, project_id: int) -> dict[str, object]:
        base: dict[str, object] = {
            "project_id": project_id,
            "parent_project_id": None,
        }
        if not isinstance(raw, dict):
            return base

        typed_raw = cast(dict[object, object], raw)
        parent_raw = typed_raw.get("parent_project_id")
        if isinstance(parent_raw, int) and parent_raw > 0 and parent_raw != project_id:
            base["parent_project_id"] = parent_raw
        return base

    async def _load_project_meta_map(self, user_id: int) -> dict[int, dict[str, object]]:
        raw = await self.settings_service.get(
            category="workspace",
            key=WORKSPACE_PROJECT_META_MAP_SETTING_KEY,
            user_id=user_id,
        )
        if not isinstance(raw, dict):
            return {}

        out: dict[int, dict[str, object]] = {}
        typed_raw = cast(dict[object, object], raw)
        for raw_project_id, raw_meta in typed_raw.items():
            project_id_text = str(raw_project_id)
            if not project_id_text.isdigit():
                continue
            project_id = int(project_id_text)
            out[project_id] = self._coerce_project_meta(raw_meta, project_id=project_id)
        return out

    def _build_project_ancestry(self, meta_map: dict[int, dict[str, object]], project_id: int) -> list[int]:
        lineage: list[int] = []
        cursor: int | None = project_id
        seen: set[int] = set()

        while isinstance(cursor, int) and cursor > 0 and cursor not in seen:
            lineage.append(cursor)
            seen.add(cursor)
            meta = meta_map.get(cursor)
            if meta is None:
                break
            parent_raw = meta.get("parent_project_id")
            cursor = parent_raw if isinstance(parent_raw, int) and parent_raw > 0 else None

        return list(reversed(lineage))

    async def _resolve_retrieval_scope(
        self,
        *,
        user_id: int,
        conversation_id: int | None,
    ) -> tuple[list[int], bool, dict[int, int]]:
        if conversation_id is None:
            return [], True, {}

        project_map_raw = await self.settings_service.get(
            category="chat",
            key=CONVERSATION_PROJECT_MAP_SETTING_KEY,
            user_id=user_id,
        )
        project_map = self._parse_conversation_project_map(project_map_raw)
        project_id = project_map.get(conversation_id)

        if not isinstance(project_id, int) or project_id <= 0:
            return [], True, {}

        meta_map = await self._load_project_meta_map(user_id=user_id)
        lineage = self._build_project_ancestry(meta_map, project_id=project_id)
        if not lineage:
            lineage = [project_id]

        scope_depth_by_project_id = {lineage_id: idx for idx, lineage_id in enumerate(lineage)}
        return lineage, False, scope_depth_by_project_id

    async def _select_retrieval_sources(
        self,
        user_id: int,
        user_message: str,
        model_id: int | None,
        retrieval_top_k_override: object | None = None,
        conversation_id: int | None = None,
    ) -> tuple[list[RetrievalSource], list[str], int, list[RetrievalDiagnostic]]:
        scope_project_ids, include_unassigned, scope_depth_by_project_id = await self._resolve_retrieval_scope(
            user_id=user_id,
            conversation_id=conversation_id,
        )

        if hasattr(self.knowledge_repo, "list_documents_for_scope"):
            source_items = await self.knowledge_repo.list_documents_for_scope(
                user_id=user_id,
                project_ids=scope_project_ids,
                include_unassigned=include_unassigned,
                limit=200,
            )
        else:
            source_items = await self.knowledge_repo.list_documents(user_id=user_id, limit=200)

        top_k_raw = retrieval_top_k_override
        if top_k_raw is None:
            top_k_raw = await self._get_model_scoped_setting(
                category="knowledge",
                base_key="top_k",
                user_id=user_id,
                model_id=model_id,
            )
        top_k = max(1, min(20, self._to_int(top_k_raw, default=6)))

        min_score_ratio_raw = await self.settings_service.get(
            category="knowledge",
            key="min_score_ratio",
            user_id=user_id,
        )
        min_absolute_score_raw = await self.settings_service.get(
            category="knowledge",
            key="min_absolute_score",
            user_id=user_id,
        )
        min_score_gap_raw = await self.settings_service.get(
            category="knowledge",
            key="min_score_gap",
            user_id=user_id,
        )

        min_score_ratio = min(1.0, max(0.0, self._to_float(min_score_ratio_raw, default=0.5)))
        min_absolute_score = max(0, self._to_int(min_absolute_score_raw, default=1000))
        min_score_gap = max(0, self._to_int(min_score_gap_raw, default=400))

        query_terms = [token.lower() for token in re.findall(r"[A-Za-z0-9]+", user_message) if len(token) >= 4]

        scored: list[RetrievalSource] = []
        for item in source_items:
            file_name = str(item.get("file", ""))
            position = str(item.get("position", "Abschnitt"))
            relevance = str(item.get("relevance", "n/a"))
            status = str(item.get("status", "Bereit"))
            source = str(item.get("source", "Upload"))
            project_id_raw = item.get("project_id")
            project_id = project_id_raw if isinstance(project_id_raw, int) else None
            scope_depth = scope_depth_by_project_id.get(project_id) if isinstance(project_id, int) else None

            source_normalized = source.strip().lower()
            if source_normalized in {"seed_mock", "mock", "placeholder"}:
                continue

            haystack = f"{file_name} {position} {source} {status}".lower()
            haystack_terms = set(re.findall(r"[A-Za-z0-9]+", haystack))
            keyword_hits = sum(1 for term in query_terms if term in haystack_terms)
            relevance_percent = self._parse_relevance_percent(relevance)
            raw_score = keyword_hits * 1000 + relevance_percent

            scored.append(
                {
                    "id": int(item.get("id", 0)),
                    "file": file_name,
                    "position": position,
                    "relevance": relevance,
                    "status": status,
                    "score": raw_score,
                    "raw_score": raw_score,
                    "normalized_score": 0.0,
                    "keyword_hits": keyword_hits,
                    "project_id": project_id,
                    "scope_depth": scope_depth,
                }
            )

        if query_terms:
            scored.sort(key=lambda entry: (entry["keyword_hits"], entry["score"]), reverse=True)
        else:
            scored.sort(key=lambda entry: entry["score"], reverse=True)

        best_raw_score = scored[0]["raw_score"] if scored else 0
        selected: list[RetrievalSource] = []
        diagnostics: list[RetrievalDiagnostic] = []

        for entry in scored:
            normalized_score = (entry["raw_score"] / best_raw_score) if best_raw_score > 0 else 0.0
            entry["normalized_score"] = normalized_score

            discard_reason: str | None = None
            if entry["raw_score"] < min_absolute_score:
                discard_reason = "below_min_absolute_score"
            elif normalized_score < min_score_ratio:
                discard_reason = "below_min_score_ratio"
            elif (best_raw_score - entry["raw_score"]) > min_score_gap:
                discard_reason = "outside_min_score_gap"

            selected_flag = discard_reason is None and len(selected) < top_k
            if selected_flag:
                selected.append(entry)

            diagnostics.append(
                {
                    "id": int(entry["id"]),
                    "file": str(entry["file"]),
                    "position": str(entry["position"]),
                    "relevance": str(entry["relevance"]),
                    "status": str(entry["status"]),
                    "keyword_hits": int(entry["keyword_hits"]),
                    "raw_score": int(entry["raw_score"]),
                    "normalized_score": float(round(normalized_score, 6)),
                    "selected": selected_flag,
                    "discard_reason": None if selected_flag else discard_reason,
                    "project_id": entry["project_id"],
                    "scope_depth": entry["scope_depth"],
                }
            )

        knowledge_messages = [
            f"Quelle: {str(entry['file'])} | Position: {str(entry['position'])} | Relevanz: {str(entry['relevance'])} | Status: {str(entry['status'])}"
            for entry in selected
        ]

        if not selected:
            knowledge_messages = ["Keine relevanten externen Quellen gefunden."]

        return selected, knowledge_messages, top_k, diagnostics

    async def _prepare_context_payload(
        self,
        *,
        user_id: int,
        conversation_id: int | None,
        user_message: str,
        request_model_id: int | None = None,
        request_temperature: float | None = None,
        request_max_new_tokens: int | None = None,
    ) -> PreparedContextPayload:
        normalized_message = user_message.strip()
        resolved_model_id = request_model_id if request_model_id is not None else model_manager.active_model_id
        conversation_profile = await self._get_active_conversation_generation_profile(
            user_id=user_id,
            conversation_id=conversation_id,
        )

        history_messages: list[str] = []
        history_chat_messages: list[dict[str, str]] = []
        if conversation_id is not None:
            private_ids = await self._load_private_conversation_ids()
            conversation = await self.conversation_repo.get_visible_by_id(
                conversation_id=conversation_id,
                user_id=user_id,
                private_conversation_ids=private_ids,
            )
            if conversation is None:
                raise ValueError("conversation_not_found")

            history = await self.message_repo.list_by_conversation(conversation_id=conversation_id, limit=30)
            history_chat_messages = [
                {
                    "role": str(m.role).lower(),
                    "content": str(m.content),
                }
                for m in history
            ]
            history_messages = [f"{msg['role']}: {msg['content']}" for msg in history_chat_messages]

        profile_params = conversation_profile["params"] if conversation_profile is not None else {}

        system_prompt_raw = profile_params.get("system_prompt")
        if system_prompt_raw is None:
            system_prompt_raw = await self._get_model_scoped_setting(
                category="prompt",
                base_key="system_prompt",
                user_id=user_id,
                model_id=resolved_model_id,
            )

        temperature_raw = request_temperature if request_temperature is not None else profile_params.get("temperature")
        if temperature_raw is None:
            temperature_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="temperature",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        max_new_tokens_raw = request_max_new_tokens if request_max_new_tokens is not None else profile_params.get("max_new_tokens")
        if max_new_tokens_raw is None:
            max_new_tokens_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="max_new_tokens",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        top_p_raw = profile_params.get("top_p")
        if top_p_raw is None:
            top_p_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="top_p",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        top_k_sampling_raw = profile_params.get("top_k")
        if top_k_sampling_raw is None:
            top_k_sampling_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="top_k",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        repetition_penalty_raw = profile_params.get("repetition_penalty")
        if repetition_penalty_raw is None:
            repetition_penalty_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="repetition_penalty",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        do_sample_raw = profile_params.get("do_sample")
        if do_sample_raw is None:
            do_sample_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="do_sample",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        seed_raw = profile_params.get("seed")
        if seed_raw is None:
            seed_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="seed",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        stop_sequences_raw = profile_params.get("stop_sequences")
        if stop_sequences_raw is None:
            stop_sequences_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="stop_sequences",
                user_id=user_id,
                model_id=resolved_model_id,
                include_global_fallback=False,
            )

        resolved_system_prompt = str(system_prompt_raw).strip() if isinstance(system_prompt_raw, str) else ""
        if not resolved_system_prompt:
            resolved_system_prompt = "Du bist ein hilfreicher Assistent."
        resolved_system_prompt = self._build_effective_system_prompt(resolved_system_prompt)
        resolved_system_prompt = await self._append_general_settings_self_knowledge(
            base_prompt=resolved_system_prompt,
            user_id=user_id,
        )

        resolved_temperature = self._to_float(temperature_raw, default=0.3)
        resolved_max_new_tokens = self._to_int(max_new_tokens_raw, default=512)
        resolved_top_p = min(1.0, max(0.01, self._to_float(top_p_raw, default=0.9)))
        resolved_top_k_sampling = max(0, self._to_int(top_k_sampling_raw, default=40))
        resolved_repetition_penalty = min(2.0, max(0.5, self._to_float(repetition_penalty_raw, default=1.1)))
        resolved_do_sample = bool(do_sample_raw) if isinstance(do_sample_raw, bool) else True
        resolved_seed = max(0, self._to_int(seed_raw, default=42))
        resolved_stop_sequences = self._coerce_stop_sequences(stop_sequences_raw)

        context_limit, safety_margin = await self._resolve_context_budget(
            user_id=user_id,
            conversation_id=conversation_id,
        )

        selected_sources, knowledge_messages, top_k, retrieval_diagnostics = await self._select_retrieval_sources(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=normalized_message,
            model_id=resolved_model_id,
            retrieval_top_k_override=profile_params.get("retrieval_top_k"),
        )

        build_result = self.context_builder.build_with_metrics(
            system_prompt=resolved_system_prompt,
            history_messages=history_messages,
            user_message=normalized_message,
            model_context=context_limit,
            output_reserve=resolved_max_new_tokens,
            safety_margin=safety_margin,
            knowledge_messages=knowledge_messages,
        )

        counter = TokenCounter()
        used_selected_sources_count = max(0, len(selected_sources) - build_result.dropped_knowledge_count)
        used_selected_sources = selected_sources[:used_selected_sources_count]
        files_tokens = sum(counter.count_text(str(entry["file"])) for entry in used_selected_sources)

        used_context_tokens = min(
            context_limit,
            build_result.fixed_tokens
            + build_result.used_history_tokens
            + build_result.used_knowledge_tokens
            + resolved_max_new_tokens,
        )

        chat_messages: list[dict[str, str]] = [{"role": "system", "content": resolved_system_prompt}]
        chat_messages.extend(history_chat_messages)
        chat_messages.append({"role": "user", "content": normalized_message})

        chat_template_source = "backend_default"
        if model_manager.active_backend_name == "transformers":
            chat_template_source = "tokenizer_config"
        elif model_manager.active_backend_name == "llama_cpp":
            chat_template_source = "gguf_chat_template"

        return {
            "prompt": build_result.prompt,
            "chat_messages": chat_messages,
            "chat_template_source": chat_template_source,
            "system_prompt": resolved_system_prompt,
            "temperature": resolved_temperature,
            "max_new_tokens": resolved_max_new_tokens,
            "top_p": resolved_top_p,
            "top_k": resolved_top_k_sampling,
            "repetition_penalty": resolved_repetition_penalty,
            "do_sample": resolved_do_sample,
            "seed": resolved_seed,
            "stop_sequences": resolved_stop_sequences,
            "context_limit": context_limit,
            "safety_margin": safety_margin,
            "used_context_tokens": used_context_tokens,
            "used_history_tokens": build_result.used_history_tokens,
            "history_total_messages": len(history_messages),
            "history_dropped_messages": build_result.dropped_history_count,
            "external_data_tokens": build_result.used_knowledge_tokens,
            "files_tokens": files_tokens,
            "external_data_integrated": used_selected_sources_count > 0,
            "external_data_sources_count": len(selected_sources),
            "external_data_selected_count": used_selected_sources_count,
            "external_data_dropped_count": build_result.dropped_knowledge_count,
            "external_data_top_k": top_k,
            "external_data_selected_sources": [
                {
                    "id": int(entry["id"]),
                    "file": str(entry["file"]),
                    "position": str(entry["position"]),
                    "relevance": str(entry["relevance"]),
                    "status": str(entry["status"]),
                    "project_id": entry["project_id"],
                    "scope_depth": entry["scope_depth"],
                }
                for entry in used_selected_sources
            ],
            "retrieval_diagnostics": retrieval_diagnostics,
        }

    def _normalize_image_inputs(self, request: ChatRequest) -> list[ImageInputPayload]:
        normalized: list[ImageInputPayload] = []
        for item in request.images:
            data_base64 = str(item.data_base64).strip()
            if not data_base64:
                continue
            normalized.append(
                {
                    "name": str(item.name or "image"),
                    "mime_type": str(item.mime_type or "image/jpeg"),
                    "data_base64": data_base64,
                }
            )
        return normalized

    async def get_context_usage(
        self,
        *,
        user_id: int,
        conversation_id: int | None,
        user_message: str = "",
    ) -> dict[str, Any]:
        payload = await self._prepare_context_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
        )

        context_limit = payload["context_limit"]
        used_context_tokens = payload["used_context_tokens"]
        resolved_max_new_tokens = payload["max_new_tokens"]
        safety_margin = payload["safety_margin"]
        history_dropped_messages = payload["history_dropped_messages"]
        history_total_messages = payload["history_total_messages"]
        external_data_tokens = payload["external_data_tokens"]
        files_tokens = payload["files_tokens"]

        counter = TokenCounter()
        system_prompt_tokens = counter.count_text(f"System: {payload['system_prompt']}")
        user_message_tokens = counter.count_text(f"User: {user_message.strip()}")
        assistant_prefix_tokens = counter.count_text("Assistant:")

        chat_history_tokens = max(
            0,
            used_context_tokens
            - system_prompt_tokens
            - user_message_tokens
            - assistant_prefix_tokens
            - resolved_max_new_tokens
            - external_data_tokens,
        )

        return {
            "context_limit_tokens": context_limit,
            "available_context_tokens": max(0, context_limit - resolved_max_new_tokens - safety_margin),
            "used_context_tokens": used_context_tokens,
            "usage_ratio": (used_context_tokens / context_limit) if context_limit > 0 else 0,
            "breakdown": {
                "system_prompt_tokens": system_prompt_tokens,
                "chat_history_tokens": chat_history_tokens,
                "user_message_tokens": user_message_tokens,
                "assistant_prefix_tokens": assistant_prefix_tokens,
                "external_data_tokens": external_data_tokens,
                "files_tokens": files_tokens,
                "output_reserve_tokens": resolved_max_new_tokens,
                "safety_margin_tokens": safety_margin,
            },
            "history": {
                "total_messages": history_total_messages,
                "dropped_messages": history_dropped_messages,
            },
            "external_data": {
                "integrated": bool(payload["external_data_integrated"]),
                "sources_count": payload["external_data_sources_count"],
                "selected_count": payload["external_data_selected_count"],
                "dropped_count": payload["external_data_dropped_count"],
                "top_k": payload["external_data_top_k"],
                "selected_sources": payload["external_data_selected_sources"],
            },
        }

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        specialist_model = await self._resolve_specialist_model(request.user_id, request.model_id, request.message)
        if model_manager.active_backend is None and specialist_model is None:
            raise RuntimeError("No active model loaded")

        idempotency_key = (request.idempotency_key or "").strip()
        if idempotency_key:
            existing_exchange = await self.message_repo.find_idempotent_exchange(
                user_id=request.user_id,
                idempotency_key=idempotency_key,
                conversation_id=request.conversation_id,
            )
            if existing_exchange is not None:
                _user_message, assistant_message = existing_exchange
                return ChatResponse(
                    conversation_id=assistant_message.conversation_id,
                    message=assistant_message.content,
                    model_id=assistant_message.model_id,
                )

        conversation_id = request.conversation_id
        conversation = None
        if conversation_id is None:
            conversation = await self.conversation_repo.create(
                user_id=request.user_id,
                title=self._build_title_from_message(request.message),
            )
            conversation_id = conversation.id
        else:
            private_ids = await self._load_private_conversation_ids()
            conversation = await self.conversation_repo.get_visible_by_id(
                conversation_id=conversation_id,
                user_id=request.user_id,
                private_conversation_ids=private_ids,
            )
            if conversation is None:
                raise ValueError("conversation_not_found")

        if not conversation.title:
            await self.conversation_repo.update_title(conversation, self._build_title_from_message(request.message))

        prepared_context = await self._prepare_context_payload(
            user_id=request.user_id,
            conversation_id=conversation_id,
            user_message=request.message,
            request_model_id=specialist_model.id if specialist_model is not None else request.model_id,
            request_temperature=request.temperature,
            request_max_new_tokens=request.max_new_tokens,
        )
        image_inputs = self._normalize_image_inputs(request)
        await self._emit_prompt_diagnostics(
            user_id=request.user_id,
            conversation_id=conversation_id,
            request_message=request.message,
            prepared_context=prepared_context,
        )

        specialist_backend = None
        selected_backend = model_manager.active_backend
        selected_model_id = model_manager.active_model_id
        if specialist_model is not None:
            try:
                specialist_backend = self._load_specialist_backend(specialist_model)
                selected_backend = specialist_backend
                selected_model_id = specialist_model.id
            except Exception:
                specialist_backend = None

        direct_document_response = await self._try_direct_document_request_response(
            user_id=request.user_id,
            user_message=request.message,
            idempotency_key=idempotency_key,
            team_id=request.team_id,
            document_scope=request.document_scope,
        )
        if direct_document_response is not None:
            response_text = direct_document_response
            author = await self.user_repo.get_by_id(request.user_id)
            author_username = author.username if author is not None else f"user-{request.user_id}"
            user_metadata: dict[str, Any] = {
                "author_user_id": request.user_id,
                "author_username": author_username,
            }
            if idempotency_key:
                user_metadata["idempotency_key"] = idempotency_key

            await self.message_repo.add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                metadata_json=json.dumps(user_metadata, ensure_ascii=True, separators=(",", ":")),
            )

            await self.message_repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_text,
                model_id=selected_model_id,
            )
            await self.session.commit()

            return ChatResponse(
                conversation_id=conversation_id,
                message=response_text,
                model_id=selected_model_id,
            )

        try:
            generation_config = {
                "chat_messages": prepared_context["chat_messages"],
                "temperature": prepared_context["temperature"],
                "max_new_tokens": prepared_context["max_new_tokens"],
                "top_p": prepared_context["top_p"],
                "top_k": prepared_context["top_k"],
                "repetition_penalty": prepared_context["repetition_penalty"],
                "do_sample": prepared_context["do_sample"],
                "seed": prepared_context["seed"],
                "stop": prepared_context["stop_sequences"],
                "image_inputs": image_inputs,
            }
            try:
                response_text = await self._generate_with_optional_plugin_orchestration(
                    user_id=request.user_id,
                    backend=selected_backend,
                    prompt=str(prepared_context["prompt"]),
                    config=generation_config,
                    user_message=request.message,
                )
            except Exception:
                if specialist_backend is None or model_manager.active_backend is None:
                    raise
                selected_backend = model_manager.active_backend
                selected_model_id = model_manager.active_model_id
                response_text = await self._generate_with_optional_plugin_orchestration(
                    user_id=request.user_id,
                    backend=selected_backend,
                    prompt=str(prepared_context["prompt"]),
                    config=generation_config,
                    user_message=request.message,
                )
        finally:
            if specialist_backend is not None:
                specialist_backend.unload()

        response_text = self._postprocess_model_output(response_text)
        if int(prepared_context["external_data_selected_count"]) <= 0:
            response_text = _strip_unverified_sources(response_text)

        author = await self.user_repo.get_by_id(request.user_id)
        author_username = author.username if author is not None else f"user-{request.user_id}"
        user_metadata: dict[str, Any] = {
            "author_user_id": request.user_id,
            "author_username": author_username,
        }
        if idempotency_key:
            user_metadata["idempotency_key"] = idempotency_key

        await self.message_repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            metadata_json=json.dumps(user_metadata, ensure_ascii=True, separators=(",", ":")),
        )

        await self.message_repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            model_id=selected_model_id,
        )
        await self.session.commit()

        return ChatResponse(
            conversation_id=conversation_id,
            message=response_text,
            model_id=selected_model_id,
        )

    async def stream_response(
        self,
        request: ChatRequest,
        cancel_event: threading.Event | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        specialist_model = await self._resolve_specialist_model(request.user_id, request.model_id, request.message)
        if model_manager.active_backend is None and specialist_model is None:
            raise RuntimeError("No active model loaded")

        idempotency_key = (request.idempotency_key or "").strip()
        if idempotency_key:
            existing_exchange = await self.message_repo.find_idempotent_exchange(
                user_id=request.user_id,
                idempotency_key=idempotency_key,
                conversation_id=request.conversation_id,
            )
            if existing_exchange is not None:
                user_message, assistant_message = existing_exchange
                yield {
                    "event": "conversation",
                    "data": {
                        "conversation_id": assistant_message.conversation_id,
                    },
                }
                yield {
                    "event": "user_message",
                    "data": {
                        "conversation_id": user_message.conversation_id,
                        "message_id": user_message.id,
                    },
                }
                yield {
                    "event": "done",
                    "data": {
                        "conversation_id": assistant_message.conversation_id,
                        "assistant_message_id": assistant_message.id,
                        "model_id": assistant_message.model_id,
                        "message": assistant_message.content,
                        "aborted": False,
                        "deduplicated": True,
                    },
                }
                return

        conversation_id = request.conversation_id
        conversation = None
        if conversation_id is None:
            conversation = await self.conversation_repo.create(
                user_id=request.user_id,
                title=self._build_title_from_message(request.message),
            )
            conversation_id = conversation.id
        else:
            private_ids = await self._load_private_conversation_ids()
            conversation = await self.conversation_repo.get_visible_by_id(
                conversation_id=conversation_id,
                user_id=request.user_id,
                private_conversation_ids=private_ids,
            )
            if conversation is None:
                raise ValueError("conversation_not_found")

        if not conversation.title:
            await self.conversation_repo.update_title(conversation, self._build_title_from_message(request.message))

        yield {
            "event": "conversation",
            "data": {
                "conversation_id": conversation_id,
            },
        }

        prepared_context = await self._prepare_context_payload(
            user_id=request.user_id,
            conversation_id=conversation_id,
            user_message=request.message,
            request_model_id=specialist_model.id if specialist_model is not None else request.model_id,
            request_temperature=request.temperature,
            request_max_new_tokens=request.max_new_tokens,
        )
        image_inputs = self._normalize_image_inputs(request)
        await self._emit_prompt_diagnostics(
            user_id=request.user_id,
            conversation_id=conversation_id,
            request_message=request.message,
            prepared_context=prepared_context,
        )
        prompt = str(prepared_context["prompt"])

        author = await self.user_repo.get_by_id(request.user_id)
        author_username = author.username if author is not None else f"user-{request.user_id}"
        user_metadata: dict[str, Any] = {
            "author_user_id": request.user_id,
            "author_username": author_username,
        }
        if idempotency_key:
            user_metadata["idempotency_key"] = idempotency_key

        user_message = await self.message_repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            metadata_json=json.dumps(user_metadata, ensure_ascii=True, separators=(",", ":")),
        )
        await self.session.commit()

        yield {
            "event": "user_message",
            "data": {
                "conversation_id": conversation_id,
                "message_id": user_message.id,
            },
        }

        chunks: list[str] = []
        aborted = False

        specialist_backend = None
        selected_backend = model_manager.active_backend
        selected_model_id = model_manager.active_model_id
        if specialist_model is not None:
            try:
                specialist_backend = self._load_specialist_backend(specialist_model)
                selected_backend = specialist_backend
                selected_model_id = specialist_model.id
            except Exception:
                specialist_backend = None

        direct_document_response = await self._try_direct_document_request_response(
            user_id=request.user_id,
            user_message=request.message,
            idempotency_key=idempotency_key,
            team_id=request.team_id,
            document_scope=request.document_scope,
        )
        if direct_document_response is not None:
            output = self._postprocess_model_output(direct_document_response)
            if int(prepared_context["external_data_selected_count"]) <= 0:
                output = _strip_unverified_sources(output)

            assistant_message = await self.message_repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=output,
                model_id=selected_model_id,
            )
            await self.session.commit()

            yield {
                "event": "token",
                "data": {"token": output},
            }
            yield {
                "event": "done",
                "data": {
                    "conversation_id": conversation_id,
                    "assistant_message_id": assistant_message.id,
                    "model_id": selected_model_id,
                    "message": output,
                    "aborted": False,
                },
            }
            return

        stream_config = {
            "chat_messages": prepared_context["chat_messages"],
            "temperature": prepared_context["temperature"],
            "max_new_tokens": prepared_context["max_new_tokens"],
            "top_p": prepared_context["top_p"],
            "top_k": prepared_context["top_k"],
            "repetition_penalty": prepared_context["repetition_penalty"],
            "do_sample": prepared_context["do_sample"],
            "seed": prepared_context["seed"],
            "stop": prepared_context["stop_sequences"],
            "image_inputs": image_inputs,
            "cancel_event": cancel_event,
        }

        if await self._plugin_orchestration_enabled(request.user_id):
            try:
                output = await self._generate_with_optional_plugin_orchestration(
                    user_id=request.user_id,
                    backend=selected_backend,
                    prompt=prompt,
                    config=stream_config,
                    user_message=request.message,
                )
            except Exception:
                await self.session.rollback()
                yield {
                    "event": "error",
                    "data": {
                        "detail": "stream_generation_failed",
                    },
                }
                return

            if cancel_event is not None and cancel_event.is_set():
                aborted = True

            output = self._postprocess_model_output(output)
            if int(prepared_context["external_data_selected_count"]) <= 0:
                output = _strip_unverified_sources(output)

            assistant_message_id: int | None = None
            if output:
                assistant_metadata = json.dumps({"aborted": True}, ensure_ascii=True) if aborted else None
                assistant_message = await self.message_repo.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=output,
                    model_id=selected_model_id,
                    metadata_json=assistant_metadata,
                )
                assistant_message_id = assistant_message.id

            if specialist_backend is not None:
                specialist_backend.unload()

            await self.session.commit()

            if output:
                yield {
                    "event": "token",
                    "data": {"token": output},
                }

            yield {
                "event": "done",
                "data": {
                    "conversation_id": conversation_id,
                    "assistant_message_id": assistant_message_id,
                    "model_id": selected_model_id,
                    "message": output,
                    "aborted": aborted,
                },
            }
            return

        async def _yield_stream(backend) -> AsyncIterator[str]:
            async for chunk in backend.stream(prompt, stream_config):
                yield chunk

        try:
            try:
                stream_iter = _yield_stream(selected_backend)
                async for chunk in stream_iter:
                    if cancel_event is not None and cancel_event.is_set():
                        aborted = True
                        break
                    chunks.append(chunk)
                    yield {
                        "event": "token",
                        "data": {"token": chunk},
                    }
            except Exception:
                if specialist_backend is None or model_manager.active_backend is None:
                    raise
                selected_backend = model_manager.active_backend
                selected_model_id = model_manager.active_model_id
                chunks = []
                async for chunk in _yield_stream(selected_backend):
                    if cancel_event is not None and cancel_event.is_set():
                        aborted = True
                        break
                    chunks.append(chunk)
                    yield {
                        "event": "token",
                        "data": {"token": chunk},
                    }
        except Exception as exc:
            await self.session.rollback()
            yield {
                "event": "error",
                "data": {
                    "detail": "stream_generation_failed",
                },
            }
            return

        if cancel_event is not None and cancel_event.is_set():
            aborted = True

        output = "".join(chunks).strip()
        output = self._postprocess_model_output(output)
        if int(prepared_context["external_data_selected_count"]) <= 0:
            output = _strip_unverified_sources(output)
        assistant_message_id: int | None = None

        if output:
            assistant_metadata = json.dumps({"aborted": True}, ensure_ascii=True) if aborted else None
            assistant_message = await self.message_repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=output,
                model_id=selected_model_id,
                metadata_json=assistant_metadata,
            )
            assistant_message_id = assistant_message.id

        if specialist_backend is not None:
            specialist_backend.unload()

        await self.session.commit()

        yield {
            "event": "done",
            "data": {
                "conversation_id": conversation_id,
                "assistant_message_id": assistant_message_id,
                "model_id": selected_model_id,
                "message": output,
                "aborted": aborted,
            },
        }

    async def _resolve_specialist_model(
        self,
        user_id: int,
        request_model_id: int | None,
        user_message: str,
    ) -> ModelConfig | None:
        if request_model_id is not None:
            return None
        auto_specialist_enabled = await self.settings_service.get(category="chat", key="auto_specialist_enabled", user_id=user_id)
        if not bool(auto_specialist_enabled):
            return None
        if not self._is_specialist_query(user_message):
            return None

        if model_manager.active_model_id is not None:
            active_model = (
                await self.session.execute(select(ModelConfig).where(ModelConfig.id == model_manager.active_model_id).limit(1))
            ).scalar_one_or_none()
            if active_model is not None and active_model.backend == "transformers_peft":
                active_metadata = _parse_metadata(active_model.metadata_json)
                active_dataset_name = str(active_metadata.get("dataset_name") or active_model.name).lower()
                if "naturstein" in active_dataset_name:
                    return None

        rows = (await self.session.execute(select(ModelConfig).where(ModelConfig.backend == "transformers_peft"))).scalars().all()
        for row in rows:
            metadata = _parse_metadata(row.metadata_json)
            dataset_name = str(metadata.get("dataset_name") or row.name).lower()
            if "naturstein" in dataset_name:
                return row
        return None

    def _is_specialist_query(self, user_message: str) -> bool:
        tokens = {token.lower() for token in re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", user_message)}
        return any(token in _SPECIALIST_KEYWORDS for token in tokens)

    def _load_specialist_backend(self, model: ModelConfig):
        metadata = _parse_metadata(model.metadata_json)
        backend = create_backend(model.backend)
        backend.load(model.model_path, {"metadata": metadata, "prefer_gpu": True})
        return backend

    async def _load_private_conversation_ids(self) -> list[int]:
        visibility_raw = await self.settings_service.get(category="chat", key="conversation_visibility_map")
        private_ids: list[int] = []
        if isinstance(visibility_raw, dict):
            visibility_map = cast(dict[object, object], visibility_raw)
            for conversation_id_raw, visibility in visibility_map.items():
                parsed_id = (
                    int(conversation_id_raw)
                    if isinstance(conversation_id_raw, (str, int)) and str(conversation_id_raw).isdigit()
                    else None
                )
                if parsed_id is not None and isinstance(visibility, str) and visibility == "private":
                    private_ids.append(parsed_id)
        return private_ids

    def _to_int(self, value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _to_float(self, value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _coerce_stop_sequences(self, value: object) -> list[str]:
        if isinstance(value, list):
            normalized = [
                item.strip()
                for item in cast(list[object], value)
                if isinstance(item, str) and item.strip()
            ]
            if normalized:
                return normalized
        return ["<end_of_turn>", "<eos>"]

    def _build_effective_system_prompt(self, base_prompt: str) -> str:
        normalized_base = base_prompt.strip()
        if not normalized_base:
            normalized_base = "Du bist ein hilfreicher Assistent."

        legacy_style_fragments = (
            "Strukturiere laengere Antworten klar und gut lesbar in Markdown.",
            "Nutze bei Bedarf kurze Ueberschriften (##, ###), kurze Absaetze und Aufzaehlungen.",
            "Vermeide lange ununterbrochene Fliesstexte.",
            "Bei technischen Antworten nutze nach Moeglichkeit: ## Ursache, ## Loesung, ## Verifikation.",
        )
        for fragment in legacy_style_fragments:
            normalized_base = normalized_base.replace(fragment, " ")
        normalized_base = re.sub(r"[ \t]{2,}", " ", normalized_base).strip()

        if _RESPONSE_STYLE_APPENDIX.split("\n", 1)[0] in normalized_base:
            return normalized_base
        return f"{normalized_base}\n\n{_RESPONSE_STYLE_APPENDIX}".strip()

    async def _append_general_settings_self_knowledge(self, *, base_prompt: str, user_id: int) -> str:
        try:
            language_raw, theme_raw, timezone_raw = await asyncio.gather(
                self.settings_service.get(category="system", key="language", user_id=user_id),
                self.settings_service.get(category="system", key="theme", user_id=user_id),
                self.settings_service.get(category="system", key="timezone", user_id=user_id),
            )
        except Exception:
            language_raw, theme_raw, timezone_raw = "de", "system", "Europe/Berlin"

        language = str(language_raw).strip().lower() if isinstance(language_raw, str) else "de"
        if language not in {"de", "en"}:
            language = "de"

        theme = str(theme_raw).strip().lower() if isinstance(theme_raw, str) else "system"
        if theme not in {"system", "light", "dark"}:
            theme = "system"

        timezone_name = str(timezone_raw).strip() if isinstance(timezone_raw, str) else "Europe/Berlin"
        if not timezone_name:
            timezone_name = "Europe/Berlin"

        try:
            timezone = ZoneInfo(timezone_name)
            local_now = datetime.now(timezone)
            local_now_text = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            timezone_name = "Europe/Berlin"
            timezone = ZoneInfo(timezone_name)
            local_now = datetime.now(timezone)
            local_now_text = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")

        settings_appendix = (
            "Selbstwissen (Benutzer-Einstellungen):\n"
            f"- Sprache: {language}\n"
            f"- Theme: {theme}\n"
            f"- Zeitzone: {timezone_name}\n"
            f"- Lokale Zeit: {local_now_text}\n"
            "Beruecksichtige diese Einstellungen bei Sprache, Stil und zeitbezogenen Antworten."
        )

        if "Selbstwissen (Benutzer-Einstellungen):" in base_prompt:
            return base_prompt
        return f"{base_prompt}\n\n{settings_appendix}".strip()

    def _postprocess_model_output(self, text: str) -> str:
        return clean_model_output_text(text)

    async def _get_model_scoped_setting(
        self,
        *,
        category: str,
        base_key: str,
        user_id: int,
        model_id: int | None,
        request_value: object | None = None,
        include_global_fallback: bool = True,
    ) -> object:
        if request_value is not None:
            return await self.settings_service.get(
                category=category,
                key=base_key,
                user_id=user_id,
                request_value=request_value,
            )

        if model_id is not None:
            model_key = f"model_{model_id}_{base_key}"
            model_item = await self.settings_service.repo.get_setting(
                category=category,
                key=model_key,
                user_id=user_id,
                team_id=None,
            )
            if model_item is not None:
                model_value = json.loads(model_item.value_json)
                return validate_setting(category, model_key, model_value)

        if include_global_fallback:
            return await self.settings_service.get(
                category=category,
                key=base_key,
                user_id=user_id,
            )

        return None

    async def _get_active_conversation_generation_profile(
        self,
        *,
        user_id: int,
        conversation_id: int | None,
    ) -> ActiveConversationGenerationProfile | None:
        if conversation_id is None:
            return None

        profiles_raw = await self.settings_service.get(
            category="chat",
            key="conversation_generation_profiles_map",
            user_id=user_id,
        )
        if not isinstance(profiles_raw, dict):
            return None

        conversation_entry_raw = profiles_raw.get(str(conversation_id))
        if not isinstance(conversation_entry_raw, dict):
            return None

        active_version_id = conversation_entry_raw.get("active_version_id")
        versions_raw = conversation_entry_raw.get("versions")
        if not isinstance(active_version_id, str) or not isinstance(versions_raw, list):
            return None

        for item in versions_raw:
            if not isinstance(item, dict):
                continue
            if str(item.get("id", "")) != active_version_id:
                continue
            params_raw = item.get("params")
            if not isinstance(params_raw, dict):
                continue
            return {
                "version_id": active_version_id,
                "params": dict(params_raw),
            }

        return None

    async def _resolve_context_budget(self, user_id: int, conversation_id: int | None) -> tuple[int, int]:
        context_limit_raw = await self.settings_service.get(
            category="chat",
            key="context_limit_tokens",
            user_id=user_id,
        )
        safety_margin_raw = await self.settings_service.get(
            category="chat",
            key="context_safety_margin_tokens",
            user_id=user_id,
        )

        context_limit = self._to_int(context_limit_raw, default=8192)
        safety_margin = self._to_int(safety_margin_raw, default=128)

        if conversation_id is not None:
            map_raw = await self.settings_service.get(
                category="chat",
                key="conversation_context_limit_map",
                user_id=user_id,
            )
            if isinstance(map_raw, dict):
                map_value = cast(dict[str, object], map_raw)
                override_raw = map_value.get(str(conversation_id))
                if isinstance(override_raw, int):
                    context_limit = max(512, override_raw)

        return max(512, context_limit), max(0, safety_margin)

    async def _plugin_orchestration_enabled(self, user_id: int) -> bool:
        enabled_raw = await self.settings_service.get(
            category="chat",
            key="plugin_orchestration_enabled",
            user_id=user_id,
        )
        return bool(enabled_raw)

    def _extract_chat_messages(self, chat_messages: object) -> list[dict[str, str]]:
        normalized_messages: list[dict[str, str]] = []
        if not isinstance(chat_messages, list):
            return normalized_messages

        for item in cast(list[object], chat_messages):
            if not isinstance(item, dict):
                continue
            item_map = cast(dict[str, object], item)
            role = str(item_map.get("role", "")).strip().lower()
            content = str(item_map.get("content", ""))
            if role not in {"system", "user", "assistant"}:
                continue
            normalized_messages.append({"role": role, "content": content})
        return normalized_messages

    def _plugin_response_markup(self, plugin_response: dict[str, Any]) -> str:
        payload = json.dumps(plugin_response, ensure_ascii=False, separators=(",", ":"))
        return f"<plugin_response>{payload}</plugin_response>"

    async def _load_integration_keys(self, *, user_id: int, keys: list[str]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key in keys:
            value = await self.settings_service.get(
                category="integrations",
                key=key,
                user_id=user_id,
            )
            if isinstance(value, (str, bool, int, float, dict)):
                payload[key] = value
        return payload

    async def _load_plugin_settings(self, *, plugin_id: str, user_id: int) -> dict[str, Any]:
        raw = await self.settings_service.get(
            category="plugins",
            key=f"{plugin_id}_profile",
            user_id=user_id,
        )
        plugin_settings = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}

        plugin_integration_map: dict[str, list[str]] = {
            "weather": [
                "openweather_api_key",
                "weatherapi_api_key",
                "tomorrowio_api_key",
            ],
            "websearch": [
                "exa_api_key",
                "brave_search_api_key",
                "bing_search_api_key",
            ],
            "bing_search": [
                "bing_search_api_key",
            ],
        }

        integration_keys = plugin_integration_map.get(plugin_id, [])
        if integration_keys:
            plugin_settings = {
                **plugin_settings,
                "integrations": await self._load_integration_keys(user_id=user_id, keys=integration_keys),
            }

        return plugin_settings

    def _build_plugin_orchestration_discovery_prompt(self) -> str:
        list_capabilities = getattr(self.plugin_executor, "list_capabilities", None)
        capability_index = list_capabilities() if callable(list_capabilities) else []
        compact_items: list[dict[str, str]] = []
        for item in capability_index[:40]:
            capability = str(item.get("capability", "")).strip()
            plugin_id = str(item.get("plugin_id", "")).strip()
            summary = str(item.get("summary", "")).strip()
            if not capability or not plugin_id:
                continue
            compact_items.append(
                {
                    "capability": capability,
                    "plugin_id": plugin_id,
                    "summary": summary,
                }
            )

        capability_json = json.dumps(compact_items, ensure_ascii=False, separators=(",", ":"))
        return (
            "Plugin orchestration protocol:\n"
            "1) If plugin choice is unclear, request candidates via <plugin_search>{\"query\":\"...\",\"limit\":3}</plugin_search>.\n"
            "2) Load only one plugin manifest via <plugin_manifest>plugin_id</plugin_manifest>.\n"
            "3) Optionally inspect one function schema via <plugin_function>{\"plugin_id\":\"...\",\"function_name\":\"...\"}</plugin_function>.\n"
            "4) Execute only with <plugin_call>plugin_id</plugin_call><plugin_input>{...}</plugin_input>.\n"
            "5) Never invent financial values or missing business data. Ask user for missing required inputs.\n"
            f"Capability index: {capability_json}"
        )

    def _extract_plugin_search_request(self, text: str) -> dict[str, Any] | None:
        match = _PLUGIN_SEARCH_PATTERN.search(text)
        if match is None:
            return None
        payload_raw = match.group("payload").strip()
        try:
            payload = json.loads(payload_raw)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        return cast(dict[str, Any], payload)

    def _extract_plugin_manifest_request(self, text: str) -> str | None:
        match = _PLUGIN_MANIFEST_PATTERN.search(text)
        if match is None:
            return None
        plugin_id = match.group("plugin_id").strip()
        return plugin_id or None

    def _extract_plugin_function_request(self, text: str) -> dict[str, Any] | None:
        match = _PLUGIN_FUNCTION_PATTERN.search(text)
        if match is None:
            return None
        payload_raw = match.group("payload").strip()
        try:
            payload = json.loads(payload_raw)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        return cast(dict[str, Any], payload)

    async def _generate_with_optional_plugin_orchestration(
        self,
        *,
        user_id: int,
        backend,
        prompt: str,
        config: dict[str, Any],
        user_message: str,
    ) -> str:
        current_config = dict(config)
        current_messages = self._extract_chat_messages(current_config.get("chat_messages"))
        orchestration_enabled = await self._plugin_orchestration_enabled(user_id)
        auto_discovery_injected = False
        direct_document_execution_attempted = False

        if orchestration_enabled:
            current_messages = [
                *current_messages,
                {"role": "system", "content": self._build_plugin_orchestration_discovery_prompt()},
            ]

        for _ in range(6):
            current_config["chat_messages"] = current_messages
            text = self._postprocess_model_output(
                await self.executor.generate(backend=backend, prompt=prompt, config=current_config)
            )
            if not orchestration_enabled:
                return text

            search_request = self._extract_plugin_search_request(text)
            if search_request is not None:
                query = str(search_request.get("query", "")).strip()
                limit = self._to_int(search_request.get("limit"), default=3)
                if query:
                    candidates = self.plugin_executor.search_plugins(query, limit=max(1, min(8, limit)))
                else:
                    candidates = self.plugin_executor.search_plugins(prompt, limit=max(1, min(8, limit)))
                response_payload = {
                    "query": query or prompt,
                    "candidate_plugins": candidates,
                }
                response_markup = (
                    f"<plugin_search_response>{json.dumps(response_payload, ensure_ascii=False)}</plugin_search_response>"
                )
                current_messages = [
                    *current_messages,
                    {"role": "assistant", "content": text},
                    {"role": "assistant", "content": response_markup},
                ]
                continue

            manifest_plugin_id = self._extract_plugin_manifest_request(text)
            if manifest_plugin_id is not None:
                manifest = self.plugin_executor.describe_plugin(manifest_plugin_id)
                response_payload = (
                    manifest
                    if manifest is not None
                    else {"code": "plugin_not_found", "plugin_id": manifest_plugin_id}
                )
                response_markup = (
                    f"<plugin_manifest_response>{json.dumps(response_payload, ensure_ascii=False)}</plugin_manifest_response>"
                )
                current_messages = [
                    *current_messages,
                    {"role": "assistant", "content": text},
                    {"role": "assistant", "content": response_markup},
                ]
                continue

            function_request = self._extract_plugin_function_request(text)
            if function_request is not None:
                plugin_id = str(function_request.get("plugin_id", "")).strip()
                function_name = str(function_request.get("function_name", "")).strip()
                if plugin_id and function_name:
                    function_schema = self.plugin_executor.describe_function(plugin_id, function_name)
                else:
                    function_schema = None
                response_payload = (
                    function_schema
                    if function_schema is not None
                    else {
                        "code": "plugin_function_not_found",
                        "plugin_id": plugin_id,
                        "function_name": function_name,
                    }
                )
                response_markup = (
                    f"<plugin_function_response>{json.dumps(response_payload, ensure_ascii=False)}</plugin_function_response>"
                )
                current_messages = [
                    *current_messages,
                    {"role": "assistant", "content": text},
                    {"role": "assistant", "content": response_markup},
                ]
                continue

            try:
                plugin_id, plugin_input = self.plugin_executor.parse_markup(text)
            except PluginExecutionError:
                if (
                    orchestration_enabled
                    and not auto_discovery_injected
                    and self._looks_like_document_request(user_message)
                ):
                    candidates = self.plugin_executor.search_plugins(user_message, limit=3)
                    if candidates:
                        response_payload = {
                            "query": user_message,
                            "candidate_plugins": candidates,
                            "auto_discovery": True,
                        }
                        response_markup = (
                            f"<plugin_search_response>{json.dumps(response_payload, ensure_ascii=False)}</plugin_search_response>"
                        )
                        current_messages = [
                            *current_messages,
                            {"role": "assistant", "content": text},
                            {"role": "assistant", "content": response_markup},
                        ]
                        auto_discovery_injected = True
                        continue
                if (
                    orchestration_enabled
                    and auto_discovery_injected
                    and not direct_document_execution_attempted
                ):
                    direct_document_payload = self._build_direct_document_request_payload(user_message)
                    if direct_document_payload is not None:
                        try:
                            plugin_settings = await self._load_plugin_settings(plugin_id="business_letter", user_id=user_id)
                            plugin_response = await self.plugin_executor.execute(
                                "business_letter",
                                direct_document_payload,
                                plugin_settings,
                            )
                        except PluginExecutionError as exc:
                            plugin_response = {"code": exc.code, "error": exc.message}
                        direct_document_execution_attempted = True
                        return self._render_direct_document_result(plugin_response)
                return text

            try:
                plugin_settings = await self._load_plugin_settings(plugin_id=plugin_id, user_id=user_id)
                plugin_response = await self.plugin_executor.execute(plugin_id, plugin_input, plugin_settings)
            except PluginExecutionError as exc:
                plugin_response = {"code": exc.code, "error": exc.message}

            current_messages = [
                *current_messages,
                {"role": "assistant", "content": text},
                {"role": "assistant", "content": self._plugin_response_markup(plugin_response)},
            ]

        return text

    def _looks_like_document_request(self, text: str) -> bool:
        tokens = {
            token.lower()
            for token in re.findall(r"[A-Za-zÄÖÜäöüß0-9_]+", str(text or ""))
            if token
        }
        return any(token in _DOCUMENT_REQUEST_KEYWORDS for token in tokens)

    async def _try_direct_document_request_response(
        self,
        *,
        user_id: int,
        user_message: str,
        idempotency_key: str = "",
        team_id: int | None = None,
        document_scope: str = "user",
    ) -> str | None:
        enabled = await self._plugin_orchestration_enabled(user_id)
        if not enabled:
            return None
        payload = self._build_direct_document_request_payload(user_message)
        if payload is None:
            return None
        payload["tenant_id"] = self._direct_document_tenant_id(user_id=user_id, team_id=team_id, document_scope=document_scope)
        payload = await self._enrich_direct_document_payload_with_pricefinder(
            user_id=user_id,
            user_message=user_message,
            payload=payload,
        )
        resolved_idempotency_key = self._resolve_direct_document_idempotency_key(
            user_id=user_id,
            user_message=user_message,
            idempotency_key=idempotency_key,
        )
        execution_context = {
            "user_id": user_id,
            "team_id": team_id,
            "idempotency_key": resolved_idempotency_key,
            "request_id": resolved_idempotency_key,
        }
        try:
            plugin_settings = await self._load_plugin_settings(plugin_id="business_letter", user_id=user_id)
            plugin_response = await self.plugin_executor.execute(
                "business_letter",
                payload,
                plugin_settings,
                execution_context=execution_context,
            )
        except PluginExecutionError as exc:
            plugin_response = {"code": exc.code, "error": exc.message}
        return self._render_direct_document_result(plugin_response)

    def _resolve_direct_document_idempotency_key(
        self,
        *,
        user_id: int,
        user_message: str,
        idempotency_key: str,
    ) -> str:
        explicit_key = str(idempotency_key or "").strip()
        if explicit_key:
            return explicit_key
        digest = hashlib.sha1(f"{user_id}:{user_message.strip()}".encode("utf-8")).hexdigest()[:24]
        return f"chat-doc-{user_id}-{digest}"

    def _direct_document_tenant_id(self, *, user_id: int, team_id: int | None, document_scope: str) -> str:
        normalized_scope = str(document_scope or "user").strip().lower()
        if normalized_scope == "shared":
            return "shared"
        if normalized_scope == "team" and isinstance(team_id, int):
            return f"team:{team_id}"
        return f"user:{user_id}"

    def _build_direct_document_request_payload(self, text: str) -> dict[str, Any] | None:
        raw = str(text or "").strip()
        if not raw or not self._looks_like_document_request(raw):
            return None

        document_kind = self._detect_document_kind(raw)
        if document_kind is None:
            return None

        customer_name = self._extract_field(raw, [r"kunde\s*(?:ist|:)\s*([^,\n]+)"])
        customer_company = self._extract_field(raw, [r"firma\s*:?\s*([^,\n]+)"])
        project_reference = self._extract_field(raw, [r"projekt\s*:?\s*([^,\n]+)"])
        payment_terms = self._extract_field(raw, [r"zahlungsziel\s*:?\s*([^,\n]+)"])
        delivery_date = self._extract_field(raw, [r"lieferzeit\s*:?\s*([^,\n]+)", r"liefertermin\s*:?\s*([^,\n]+)"])
        positions = self._extract_document_positions(raw)
        freeform_customer_name, street, postal_code, city, recipient_email = self._extract_freeform_recipient_details(raw)
        if not customer_name and freeform_customer_name:
            customer_name = freeform_customer_name

        payload: dict[str, Any] = {
            "action": "create_document",
            "letter_type": document_kind,
            "document_kind": document_kind,
            "subject": self._default_document_subject(document_kind, project_reference),
            "persist_to_database": True,
            "output_formats": ["document_html"],
        }
        if customer_name:
            payload["customer_name"] = customer_name
        if customer_company:
            payload["customer_company"] = customer_company
        if street:
            payload["customer_street"] = street
        if postal_code:
            payload["customer_zip"] = postal_code
        if city:
            payload["customer_city"] = city
        if recipient_email:
            payload["recipient_email"] = recipient_email
        if project_reference:
            payload["project_reference"] = project_reference
        if payment_terms:
            payload["payment_terms"] = payment_terms
        if delivery_date:
            payload["delivery_date"] = delivery_date
        if positions:
            payload["positions"] = positions
        return payload

    async def _enrich_direct_document_payload_with_pricefinder(
        self,
        *,
        user_id: int,
        user_message: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not self._requires_price_research(user_message):
            return payload
        if isinstance(payload.get("positions"), list) and payload.get("positions"):
            return payload

        item_spec = self._extract_freeform_item_spec(user_message)
        if item_spec is None:
            return payload

        try:
            plugin_settings = await self._load_plugin_settings(plugin_id="pricefinder", user_id=user_id)
            result = await self.plugin_executor.execute(
                "pricefinder",
                item_spec["pricefinder_input"],
                plugin_settings,
                execution_context={"user_id": user_id, "request_id": f"pricefinder:{user_id}"},
            )
        except PluginExecutionError:
            return payload

        prices = result.get("prices") if isinstance(result.get("prices"), dict) else {}
        avg_price = prices.get("avg") if isinstance(prices, dict) else None
        if avg_price in (None, ""):
            avg_price = result.get("price_per_qm") or result.get("price")
        try:
            avg_price_value = float(avg_price)
        except (TypeError, ValueError):
            return payload

        payload["positions"] = [
            {
                "line_id": "1",
                "name": item_spec["display_name"],
                "quantity": item_spec["quantity"],
                "unit_code": item_spec["unit_code"],
                "price_net": round(avg_price_value, 2),
                "vat_category": "S",
                "vat_rate": 19,
            }
        ]
        return payload

    def _detect_document_kind(self, text: str) -> str | None:
        lowered = text.lower()
        for needle, document_kind in _DOCUMENT_TYPE_HINTS:
            if needle in lowered:
                return document_kind
        return None

    def _extract_field(self, text: str, patterns: list[str]) -> str:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match is None:
                continue
            value = match.group(1).strip(" .,:;\n\t")
            if value:
                return value
        return ""

    def _extract_document_positions(self, text: str) -> list[dict[str, Any]]:
        positions_block = self._extract_field(text, [r"position(?:en)?\s*:?\s*(.+)$"])
        if not positions_block:
            return []

        explicit_positions = self._extract_explicit_positions(positions_block)
        if explicit_positions:
            return explicit_positions

        quantity_position = self._extract_quantity_position(positions_block, line_id="1")
        if quantity_position is not None:
            return [quantity_position]
        return []

    def _extract_freeform_recipient_details(self, text: str) -> tuple[str, str, str, str, str]:
        lines = [line.strip(" ,") for line in str(text or "").splitlines() if line.strip()]
        recipient_email = ""
        customer_name = ""
        street = ""
        postal_code = ""
        city = ""

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if email_match is not None:
            recipient_email = email_match.group(0).strip()

        for line in lines:
            normalized_line = line
            if recipient_email:
                normalized_line = normalized_line.replace(recipient_email, " ").strip(" ,")
            if not customer_name:
                name_match = re.search(r"\bf[üu]r\s+([^,\n]+)$", normalized_line, flags=re.IGNORECASE)
                if name_match is not None:
                    customer_name = name_match.group(1).strip(" ,")
                    continue
            if not street or not postal_code or not city:
                address_match = re.search(r"^(?P<street>.+?)\s+(?P<zip>\d{5})\s+(?P<city>[A-Za-zÄÖÜäöüß .-]+)$", normalized_line)
                if address_match is not None:
                    street = address_match.group("street").strip(" ,")
                    postal_code = address_match.group("zip").strip()
                    city = address_match.group("city").strip(" ,")
        return customer_name, street, postal_code, city, recipient_email

    def _extract_freeform_item_spec(self, text: str) -> dict[str, Any] | None:
        lines = [line.strip(" ,") for line in str(text or "").splitlines() if line.strip()]
        for line in lines:
            if not re.search(r"\d+(?:[.,]\d+)?\s*m\s*[x\*]\s*\d+(?:[.,]\d+)?\s*m", line, flags=re.IGNORECASE):
                continue
            dims_match = re.search(r"(?P<width>\d+(?:[.,]\d+)?)\s*m\s*[x\*]\s*(?P<height>\d+(?:[.,]\d+)?)\s*m", line, flags=re.IGNORECASE)
            if dims_match is None:
                continue
            width_m = self._parse_number(dims_match.group("width"), default=0.0)
            height_m = self._parse_number(dims_match.group("height"), default=0.0)
            if width_m <= 0.0 or height_m <= 0.0:
                continue
            area = round(width_m * height_m, 4)
            thickness_match = re.search(r"(?P<thickness>\d+(?:[.,]\d+)?)\s*cm", line, flags=re.IGNORECASE)
            thickness = f"{str(thickness_match.group('thickness')).replace(',', '.')}cm" if thickness_match else "2cm"
            surface_finish = "poliert" if re.search(r"\bpol(?:\.|iert)?\b", line, flags=re.IGNORECASE) else ""
            lowered = line.lower()
            if "nero assoluto" in lowered:
                entity_name = "Nero Assoluto"
            else:
                entity_name = re.sub(r"\d+(?:[.,]\d+)?\s*cm", "", line, flags=re.IGNORECASE)
                entity_name = re.sub(r"\d+(?:[.,]\d+)?\s*m\s*[x\*]\s*\d+(?:[.,]\d+)?\s*m", "", entity_name, flags=re.IGNORECASE)
                entity_name = re.sub(r"\bpol(?:\.|iert)?\b", "", entity_name, flags=re.IGNORECASE)
                entity_name = re.sub(r"\s+", " ", entity_name).strip(" ,")
            application = "Fensterbank" if "fensterbank" in lowered else ""
            return {
                "display_name": line,
                "quantity": area,
                "unit_code": "MTK",
                "pricefinder_input": {
                    "entity_name": entity_name or line,
                    "entity_type": "material",
                    "quantity": area,
                    "area": area,
                    "unit": "qm",
                    "currency": "EUR",
                    "thickness": thickness,
                    "surface_finish": surface_finish,
                    "application": application,
                    "internet_access_enabled": True,
                },
            }
        return None

    def _requires_price_research(self, text: str) -> bool:
        lowered = str(text or "").lower()
        return any(keyword in lowered for keyword in _PRICE_RESEARCH_KEYWORDS)

    def _extract_explicit_positions(self, text: str) -> list[dict[str, Any]]:
        pattern = re.compile(
            r"(?P<name>[A-Za-zÄÖÜäöüß0-9\- /]+?)\s+(?P<quantity>\d+(?:[.,]\d+)?)\s*(?P<unit>stück|stk|qm|m2|lfm|m)\s*(?:à|a)\s*(?P<price>\d+(?:[.,]\d+)?)\s*euro",
            re.IGNORECASE,
        )
        positions: list[dict[str, Any]] = []
        for index, match in enumerate(pattern.finditer(text), start=1):
            name = match.group("name").strip(" ,")
            if not name:
                continue
            positions.append(
                {
                    "line_id": str(index),
                    "name": name,
                    "quantity": self._parse_number(match.group("quantity"), default=1.0),
                    "unit_code": self._map_unit_code(match.group("unit")),
                    "price_net": self._parse_number(match.group("price"), default=0.0),
                    "vat_category": "S",
                    "vat_rate": 19,
                }
            )
        return positions

    def _extract_quantity_position(self, text: str, *, line_id: str) -> dict[str, Any] | None:
        quantity_match = re.search(
            r"(?P<quantity>\d+(?:[.,]\d+)?)\s*(?P<unit>stück|stk|qm|m2|lfm|m)\s+(?P<name>.+?)(?:,\s*preis\s*(?P<price>\d+(?:[.,]\d+)?)\s*euro(?:\s*netto)?)?(?:,|$)",
            text,
            flags=re.IGNORECASE,
        )
        if quantity_match is None:
            return None

        name = quantity_match.group("name").strip(" ,")
        if not name:
            return None
        return {
            "line_id": line_id,
            "name": name,
            "quantity": self._parse_number(quantity_match.group("quantity"), default=1.0),
            "unit_code": self._map_unit_code(quantity_match.group("unit")),
            "price_net": self._parse_number(quantity_match.group("price"), default=0.0),
            "vat_category": "S",
            "vat_rate": 19,
        }

    def _parse_number(self, value: str | None, *, default: float) -> float:
        if not value:
            return default
        normalized = value.replace(".", "").replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return default

    def _map_unit_code(self, value: str) -> str:
        normalized = str(value or "").strip().lower()
        return _UNIT_CODE_MAP.get(normalized, "C62")

    def _default_document_subject(self, document_kind: str, project_reference: str) -> str:
        labels = {
            "angebot": "Angebot",
            "rechnung": "Rechnung",
            "lieferschein": "Lieferschein",
            "mahnung": "Mahnung",
            "zahlungserinnerung": "Zahlungserinnerung",
            "auftragsbestaetigung": "Auftragsbestaetigung",
            "gutschrift": "Gutschrift",
            "stornorechnung": "Stornorechnung",
            "reklamation_antwort": "Antwort auf Reklamation",
            "allgemein": "Geschaeftsschreiben",
        }
        label = labels.get(document_kind, "Geschaeftsdokument")
        if project_reference:
            return f"{label} fuer {project_reference}"
        return label

    def _render_direct_document_result(self, plugin_response: dict[str, Any]) -> str:
        error = str(plugin_response.get("error") or "").strip()
        if error:
            return f"Die Dokumentanfrage wurde erkannt, aber das Dokument konnte nicht erzeugt werden: {error}"

        document_type = str(plugin_response.get("document_type") or plugin_response.get("document", {}).get("document_type") or "Dokument")
        status = str(plugin_response.get("status") or plugin_response.get("document", {}).get("status") or "")
        artifacts = plugin_response.get("artifacts")
        pdf_name = ""
        if isinstance(artifacts, list):
            for item in artifacts:
                if not isinstance(item, dict):
                    continue
                file_name = str(item.get("file_name") or item.get("name") or "").strip()
                if file_name.lower().endswith(".pdf"):
                    pdf_name = file_name
                    break

        validation = plugin_response.get("validation")
        missing_information: list[str] = []
        if isinstance(validation, dict):
            raw_missing = validation.get("missing_information")
            if isinstance(raw_missing, list):
                missing_information = [str(item).strip() for item in raw_missing if str(item).strip()]

        document_id = str(plugin_response.get("document_id") or "").strip()
        tenant_id = self._extract_direct_document_tenant_id(plugin_response)
        artifact_actions = self._collect_direct_document_artifact_actions(
            plugin_response,
            document_id=document_id,
            tenant_id=tenant_id,
        )
        result_marker = self._build_direct_document_result_marker(
            document_id=document_id,
            document_type=document_type,
            status=status,
            tenant_id=tenant_id,
            actions=artifact_actions,
        )

        parts = [f"Die Dokumentanfrage wurde direkt ueber business_letter verarbeitet: {document_type} erstellt"]
        if status:
            parts.append(f"Status: {status}.")
        else:
            parts[-1] = f"{parts[-1]}."
        if pdf_name:
            parts.append(f"PDF-Artefakt: {pdf_name}.")
        if missing_information:
            parts.append(f"Offene Angaben: {', '.join(missing_information[:5])}.")
        text = " ".join(parts)
        if result_marker:
            return f"{text}\n\n{result_marker}"
        return text

    def _collect_direct_document_artifact_actions(
        self,
        plugin_response: dict[str, Any],
        *,
        document_id: str,
        tenant_id: str,
    ) -> list[dict[str, str]]:
        if not document_id:
            return []

        database = plugin_response.get("database")
        database_map = database if isinstance(database, dict) else {}
        persisted = database_map.get("persisted") if isinstance(database_map.get("persisted"), dict) else {}
        plugin_storage = persisted.get("plugin_storage") if isinstance(persisted.get("plugin_storage"), dict) else {}
        persisted_artifacts = (
            plugin_storage.get("artifacts") if isinstance(plugin_storage.get("artifacts"), list) else []
        )
        if not persisted_artifacts and isinstance(persisted.get("artifacts"), list):
            persisted_artifacts = persisted.get("artifacts")

        actions: list[dict[str, str]] = []
        for item in persisted_artifacts:
            if not isinstance(item, dict):
                continue
            artifact_kind = str(item.get("artifact_kind") or "").strip().lower()
            if artifact_kind not in {"pdf", "html", "json", "email_html", "xrechnung_xml", "zugferd_xml", "cii_xml"}:
                continue
            label_map = {
                "pdf": "PDF",
                "html": "HTML",
                "json": "JSON",
                "email_html": "E-Mail-HTML",
                "xrechnung_xml": "XRechnung-XML",
                "zugferd_xml": "ZUGFeRD-XML",
                "cii_xml": "CII-XML",
            }
            label = label_map.get(artifact_kind, artifact_kind.upper())
            file_name = str(item.get("storage_key") or "").strip().split("/")[-1]
            actions.append(
                {
                    "kind": artifact_kind,
                    "label": label,
                    "file_name": file_name,
                    "document_id": document_id,
                    "tenant_id": tenant_id,
                }
            )

        return actions

    def _extract_direct_document_tenant_id(self, plugin_response: dict[str, Any]) -> str:
        database = plugin_response.get("database")
        if not isinstance(database, dict):
            return ""
        persisted = database.get("persisted")
        if not isinstance(persisted, dict):
            return ""
        tenant_id = str(persisted.get("tenant_id") or "").strip()
        return tenant_id

    def _build_direct_document_result_marker(
        self,
        *,
        document_id: str,
        document_type: str,
        status: str,
        tenant_id: str,
        actions: list[dict[str, str]],
    ) -> str:
        if not document_id or not actions:
            return ""
        payload = {
            "plugin": "business_letter",
            "documentId": document_id,
            "documentType": document_type,
            "status": status,
            "tenantId": tenant_id,
            "actions": actions,
        }
        return f"[[business_letter_result:{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}]]"

    def _diagnostics_enabled(self) -> bool:
        flag = os.getenv("LOCAL_PROMPT_DIAGNOSTICS", "").strip().lower()
        return flag in {"1", "true", "yes", "on"}

    def _diagnostics_include_prompt(self) -> bool:
        flag = os.getenv("LOCAL_PROMPT_DIAGNOSTICS_INCLUDE_PROMPT", "").strip().lower()
        return flag in {"1", "true", "yes", "on"}

    async def _emit_prompt_diagnostics(
        self,
        *,
        user_id: int,
        conversation_id: int | None,
        request_message: str,
        prepared_context: PreparedContextPayload,
    ) -> None:
        if not self._diagnostics_enabled():
            return

        active_model_id = model_manager.active_model_id
        model_name: str | None = None
        if active_model_id is not None:
            row = (
                await self.session.execute(select(ModelConfig).where(ModelConfig.id == active_model_id))
            ).scalar_one_or_none()
            if row is not None:
                model_name = row.name

        counter = TokenCounter()
        input_tokens = counter.count_text(str(prepared_context["prompt"]))

        diagnostics_payload: dict[str, Any] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "model_id": active_model_id,
            "model_name": model_name,
            "backend": model_manager.active_backend_name,
            "chat_template_source": prepared_context["chat_template_source"],
            "roles": [msg.get("role", "") for msg in prepared_context["chat_messages"]],
            "message_count": len(prepared_context["chat_messages"]),
            "system_prompt": prepared_context["system_prompt"],
            "request_message_chars": len(request_message),
            "input_tokens": input_tokens,
            "history_tokens": prepared_context["used_history_tokens"],
            "knowledge_tokens": prepared_context["external_data_tokens"],
            "retrieval_sources": [
                {
                    "id": item["id"],
                    "file": item["file"],
                    "position": item["position"],
                    "relevance": item["relevance"],
                    "status": item["status"],
                }
                for item in prepared_context["external_data_selected_sources"]
            ],
            "retrieval_scores": prepared_context["retrieval_diagnostics"],
        }

        if self._diagnostics_include_prompt():
            diagnostics_payload["final_prompt"] = prepared_context["prompt"]

        prompt_diagnostics_store.add(diagnostics_payload)
        logger.info("prompt_diagnostics=%s", json.dumps(diagnostics_payload, ensure_ascii=True))

    def _build_title_from_message(self, message: str) -> str:
        compact = " ".join(message.strip().split())
        if not compact:
            return "Neue Konversation"
        if len(compact) <= 60:
            return compact
        return f"{compact[:57].rstrip()}..."
