import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
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
    "Strukturiere laengere Antworten klar und gut lesbar in Markdown.\n"
    "Verwende bei Bedarf kurze Ueberschriften (##, ###), kurze Absaetze und Aufzaehlungen.\n"
    "Vermeide lange ununterbrochene Fliesstexte; ein Absatz soll in der Regel 3 bis 5 Saetze enthalten.\n"
    "Nutze nummerierte Listen fuer Ablaufschritte.\n"
    "Bei technischen Analysen nutze nach Moeglichkeit die Struktur: ## Ursache, ## Loesung, ## Verifikation.\n"
    "Wiederhole die Nutzerfrage nicht unnoetig und antworte bei einfachen Fragen kurz."
)


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
    candidate = _enforce_markdown_readability(candidate)
    return candidate.strip()


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
    external_data_selected_sources: list[dict[str, int | str]]
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

    async def _select_retrieval_sources(
        self,
        user_id: int,
        user_message: str,
        model_id: int | None,
        retrieval_top_k_override: object | None = None,
    ) -> tuple[list[RetrievalSource], list[str], int, list[RetrievalDiagnostic]]:
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
            )

        max_new_tokens_raw = request_max_new_tokens if request_max_new_tokens is not None else profile_params.get("max_new_tokens")
        if max_new_tokens_raw is None:
            max_new_tokens_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="max_new_tokens",
                user_id=user_id,
                model_id=resolved_model_id,
            )

        top_p_raw = profile_params.get("top_p")
        if top_p_raw is None:
            top_p_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="top_p",
                user_id=user_id,
                model_id=resolved_model_id,
            )

        top_k_sampling_raw = profile_params.get("top_k")
        if top_k_sampling_raw is None:
            top_k_sampling_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="top_k",
                user_id=user_id,
                model_id=resolved_model_id,
            )

        repetition_penalty_raw = profile_params.get("repetition_penalty")
        if repetition_penalty_raw is None:
            repetition_penalty_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="repetition_penalty",
                user_id=user_id,
                model_id=resolved_model_id,
            )

        do_sample_raw = profile_params.get("do_sample")
        if do_sample_raw is None:
            do_sample_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="do_sample",
                user_id=user_id,
                model_id=resolved_model_id,
            )

        seed_raw = profile_params.get("seed")
        if seed_raw is None:
            seed_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="seed",
                user_id=user_id,
                model_id=resolved_model_id,
            )

        stop_sequences_raw = profile_params.get("stop_sequences")
        if stop_sequences_raw is None:
            stop_sequences_raw = await self._get_model_scoped_setting(
                category="chat",
                base_key="stop_sequences",
                user_id=user_id,
                model_id=resolved_model_id,
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
                response_text = await self.executor.generate(
                    backend=selected_backend,
                    prompt=str(prepared_context["prompt"]),
                    config=generation_config,
                )
            except Exception:
                if specialist_backend is None or model_manager.active_backend is None:
                    raise
                selected_backend = model_manager.active_backend
                selected_model_id = model_manager.active_model_id
                response_text = await self.executor.generate(
                    backend=selected_backend,
                    prompt=str(prepared_context["prompt"]),
                    config=generation_config,
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

        if "Strukturiere laengere Antworten" in normalized_base:
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

        return await self.settings_service.get(
            category=category,
            key=base_key,
            user_id=user_id,
        )

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
