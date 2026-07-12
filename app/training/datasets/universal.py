from __future__ import annotations

import csv
from html import unescape
from html.parser import HTMLParser
import importlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from app.training.datasets.errors import DatasetValidationError


@dataclass(slots=True)
class CanonicalMessage:
    role: str
    content: str


@dataclass(slots=True)
class CanonicalRecord:
    id: str
    messages: list[CanonicalMessage]
    metadata: dict[str, object]
    evaluation: dict[str, object]


class DatasetParser(Protocol):
    name: str

    def can_parse(self, path: Path, sample_text: str) -> bool: ...

    def parse(self, path: Path) -> list[CanonicalRecord]: ...


SUPPORTED_EXTENSIONS = {
    ".jsonl",
    ".json",
    ".csv",
    ".md",
    ".markdown",
    ".txt",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".htm",
    ".pdf",
    ".docx",
}


def parse_dataset_to_canonical(path: Path) -> list[CanonicalRecord]:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise DatasetValidationError("unsupported_dataset_format")

    sample_text = _read_sample_text(path)
    for parser in _parsers():
        if parser.can_parse(path, sample_text):
            records = parser.parse(path)
            if records:
                return records
    raise DatasetValidationError("dataset_format_not_detected")


def canonical_to_pairs(records: list[CanonicalRecord]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    for item in records:
        user_message = ""
        assistant_message = ""
        for msg in item.messages:
            role = msg.role.strip().lower()
            content = msg.content.strip()
            if role == "user" and not user_message:
                user_message = content
            if role == "assistant" and not assistant_message:
                assistant_message = content
        if user_message and assistant_message:
            pairs.append({"prompt": user_message, "completion": assistant_message})
    if not pairs:
        raise DatasetValidationError("dataset_has_no_trainable_pairs")
    return pairs


def write_canonical_jsonl(records: list[CanonicalRecord], target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as handle:
        for record in records:
            payload: dict[str, object] = {
                "id": record.id,
                "messages": [{"role": m.role, "content": m.content} for m in record.messages],
                "metadata": record.metadata,
                "evaluation": record.evaluation,
            }
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.write("\n")


def _new_record(messages: list[CanonicalMessage], metadata: dict[str, object] | None = None) -> CanonicalRecord:
    return CanonicalRecord(
        id=str(uuid.uuid4()),
        messages=messages,
        metadata=metadata or {},
        evaluation={},
    )


def _parsers() -> list[DatasetParser]:
    return [
        OpenAiMessagesJsonParser(),
        ShareGptJsonParser(),
        AlpacaJsonParser(),
        QaJsonParser(),
        CsvQaParser(),
        MarkdownQaParser(),
        ChatMlTextParser(),
        YamlQaParser(),
        XmlQaParser(),
        HtmlQaParser(),
        PdfTextParser(),
        DocxTextParser(),
    ]


def _read_sample_text(path: Path) -> str:
    if path.suffix.lower() in {".pdf", ".docx"}:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:5000]
    except OSError as exc:
        raise DatasetValidationError("dataset_file_not_readable") from exc


def _normalize_messages(messages: list[dict[str, object]]) -> list[CanonicalMessage]:
    normalized: list[CanonicalMessage] = []
    for item in messages:
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if role not in {"system", "user", "assistant"} or not content:
            continue
        normalized.append(CanonicalMessage(role=role, content=content))
    if not any(msg.role == "user" for msg in normalized) or not any(msg.role == "assistant" for msg in normalized):
        raise DatasetValidationError("messages_missing_user_or_assistant")
    return normalized


def _as_mapping(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    normalized: dict[str, object] = {}
    for key, item in cast(dict[object, object], value).items():
        normalized[str(key)] = item
    return normalized


def _as_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


class OpenAiMessagesJsonParser:
    name = "openai_messages"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        if path.suffix.lower() not in {".json", ".jsonl"}:
            return False
        return "\"messages\"" in sample_text

    def parse(self, path: Path) -> list[CanonicalRecord]:
        records: list[CanonicalRecord] = []
        for payload_raw in _iter_json_rows(path):
            payload = _as_mapping(payload_raw)
            if payload is None:
                continue
            messages = payload.get("messages")
            if not isinstance(messages, list):
                continue
            normalized = _normalize_messages(cast(list[dict[str, object]], messages))
            metadata_raw = payload.get("metadata")
            metadata = cast(dict[str, object], metadata_raw) if isinstance(metadata_raw, dict) else {}
            records.append(_new_record(normalized, metadata=metadata))
        return records


class ShareGptJsonParser:
    name = "sharegpt"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        if path.suffix.lower() not in {".json", ".jsonl"}:
            return False
        return "\"conversations\"" in sample_text and "\"from\"" in sample_text

    def parse(self, path: Path) -> list[CanonicalRecord]:
        records: list[CanonicalRecord] = []
        for payload_raw in _iter_json_rows(path):
            payload = _as_mapping(payload_raw)
            if payload is None:
                continue
            conversations = payload.get("conversations")
            if not isinstance(conversations, list):
                continue
            normalized: list[CanonicalMessage] = []
            for item_raw in cast(list[object], conversations):
                item = _as_mapping(item_raw)
                if item is None:
                    continue
                source = _as_text(item.get("from")).lower()
                value = _as_text(item.get("value"))
                if not value:
                    continue
                if source in {"human", "user"}:
                    normalized.append(CanonicalMessage(role="user", content=value))
                elif source in {"gpt", "assistant"}:
                    normalized.append(CanonicalMessage(role="assistant", content=value))
                elif source == "system":
                    normalized.append(CanonicalMessage(role="system", content=value))
            if normalized:
                records.append(_new_record(normalized))
        return records


class AlpacaJsonParser:
    name = "alpaca"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        if path.suffix.lower() not in {".json", ".jsonl"}:
            return False
        return "\"instruction\"" in sample_text and "\"output\"" in sample_text

    def parse(self, path: Path) -> list[CanonicalRecord]:
        records: list[CanonicalRecord] = []
        for payload_raw in _iter_json_rows(path):
            payload = _as_mapping(payload_raw)
            if payload is None:
                continue
            instruction = _as_text(payload.get("instruction"))
            input_text = _as_text(payload.get("input"))
            output = _as_text(payload.get("output"))
            if not instruction or not output:
                continue
            user_text = instruction if not input_text else f"{instruction}\n\n{input_text}"
            records.append(
                _new_record(
                    [
                        CanonicalMessage(role="user", content=user_text),
                        CanonicalMessage(role="assistant", content=output),
                    ]
                )
            )
        return records


class QaJsonParser:
    name = "qa_json"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        if path.suffix.lower() not in {".json", ".jsonl"}:
            return False
        return "\"question\"" in sample_text and "\"answer\"" in sample_text

    def parse(self, path: Path) -> list[CanonicalRecord]:
        records: list[CanonicalRecord] = []
        for payload_raw in _iter_json_rows(path):
            payload = _as_mapping(payload_raw)
            if payload is None:
                continue
            question = _as_text(payload.get("question") or payload.get("input"))
            answer = _as_text(payload.get("answer") or payload.get("output") or payload.get("target"))
            if not question or not answer:
                continue
            records.append(
                _new_record(
                    [
                        CanonicalMessage(role="user", content=question),
                        CanonicalMessage(role="assistant", content=answer),
                    ]
                )
            )
        return records


class CsvQaParser:
    name = "csv_qa"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        return path.suffix.lower() == ".csv"

    def parse(self, path: Path) -> list[CanonicalRecord]:
        records: list[CanonicalRecord] = []
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                question = str(row.get("question") or row.get("prompt") or row.get("input") or "").strip()
                answer = str(row.get("answer") or row.get("completion") or row.get("output") or "").strip()
                if not question or not answer:
                    continue
                records.append(
                    _new_record(
                        [
                            CanonicalMessage(role="user", content=question),
                            CanonicalMessage(role="assistant", content=answer),
                        ]
                    )
                )
        return records


class MarkdownQaParser:
    name = "markdown_qa"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        return path.suffix.lower() in {".md", ".markdown"}

    def parse(self, path: Path) -> list[CanonicalRecord]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        question_blocks = re.split(r"(?im)^##\s*frage\s*$", text)
        records: list[CanonicalRecord] = []
        if len(question_blocks) <= 1:
            return records
        for block in question_blocks[1:]:
            parts = re.split(r"(?im)^##\s*antwort\s*$", block)
            if len(parts) < 2:
                continue
            question = parts[0].strip()
            answer = parts[1].strip()
            if not question or not answer:
                continue
            records.append(
                _new_record(
                    [
                        CanonicalMessage(role="user", content=question),
                        CanonicalMessage(role="assistant", content=answer),
                    ]
                )
            )
        return records


class ChatMlTextParser:
    name = "chatml"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        if path.suffix.lower() != ".txt":
            return False
        return "<|user|>" in sample_text and "<|assistant|>" in sample_text

    def parse(self, path: Path) -> list[CanonicalRecord]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = re.split(r"(?i)<\|user\|>", text)
        records: list[CanonicalRecord] = []
        for chunk in chunks[1:]:
            user_and_rest = chunk.split("<|assistant|>", 1)
            if len(user_and_rest) != 2:
                continue
            user_text = user_and_rest[0].strip()
            assistant_tail = user_and_rest[1]
            assistant_text = re.split(r"(?i)<\|(user|system|assistant)\|>", assistant_tail)[0].strip()
            if not user_text or not assistant_text:
                continue
            records.append(
                _new_record(
                    [
                        CanonicalMessage(role="user", content=user_text),
                        CanonicalMessage(role="assistant", content=assistant_text),
                    ]
                )
            )
        return records


class YamlQaParser:
    name = "yaml_qa"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        return path.suffix.lower() in {".yaml", ".yml"}

    def parse(self, path: Path) -> list[CanonicalRecord]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        question_match = re.search(r"(?im)^question\s*:\s*(.+)$", text)
        answer_match = re.search(r"(?im)^answer\s*:\s*(.+)$", text)
        if not question_match or not answer_match:
            return []
        return [
            _new_record(
                [
                    CanonicalMessage(role="user", content=question_match.group(1).strip()),
                    CanonicalMessage(role="assistant", content=answer_match.group(1).strip()),
                ]
            )
        ]


class XmlQaParser:
    name = "xml_qa"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        return path.suffix.lower() == ".xml"

    def parse(self, path: Path) -> list[CanonicalRecord]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        question_match = re.search(r"(?is)<question[^>]*>(.*?)</question>", text)
        answer_match = re.search(r"(?is)<answer[^>]*>(.*?)</answer>", text)
        if not question_match or not answer_match:
            return []
        question = re.sub(r"<[^>]+>", "", question_match.group(1)).strip()
        answer = re.sub(r"<[^>]+>", "", answer_match.group(1)).strip()
        if not question or not answer:
            return []
        return [
            _new_record(
                [
                    CanonicalMessage(role="user", content=question),
                    CanonicalMessage(role="assistant", content=answer),
                ]
            )
        ]


class _PlainTextHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data:
            self._parts.append(data)

    def as_text(self) -> str:
        merged = " ".join(self._parts)
        merged = unescape(merged)
        return re.sub(r"\s+", " ", merged).strip()


def _extract_plain_text_from_html(text: str) -> str:
    parser = _PlainTextHtmlParser()
    parser.feed(text)
    parser.close()
    return parser.as_text()


class HtmlQaParser:
    name = "html_qa"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        return path.suffix.lower() in {".html", ".htm"}

    def parse(self, path: Path) -> list[CanonicalRecord]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        plain = _extract_plain_text_from_html(text)
        if not plain:
            return []
        return [
            _new_record(
                [
                    CanonicalMessage(role="user", content="Fasse den folgenden Fachtext strukturiert zusammen."),
                    CanonicalMessage(role="assistant", content=plain),
                ],
                metadata={"document_type": "html"},
            )
        ]


class PdfTextParser:
    name = "pdf_text"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> list[CanonicalRecord]:
        try:
            pypdf_module = importlib.import_module("pypdf")
            pdf_reader_cls = getattr(pypdf_module, "PdfReader", None)
            if pdf_reader_cls is None:
                raise DatasetValidationError("pdf_parser_dependency_missing")
        except Exception as exc:
            raise DatasetValidationError("pdf_parser_dependency_missing") from exc

        reader = pdf_reader_cls(str(path))
        texts: list[str] = []
        pages = getattr(reader, "pages", [])
        for page in pages:
            extract_text = getattr(page, "extract_text", None)
            raw_text = extract_text() if callable(extract_text) else ""
            text = str(raw_text or "").strip()
            if text:
                texts.append(text)
        merged = "\n\n".join(texts).strip()
        if not merged:
            return []
        return [
            _new_record(
                [
                    CanonicalMessage(role="user", content="Fasse den folgenden Fachtext strukturiert zusammen."),
                    CanonicalMessage(role="assistant", content=merged),
                ],
                metadata={"document_type": "pdf"},
            )
        ]


class DocxTextParser:
    name = "docx_text"

    def can_parse(self, path: Path, sample_text: str) -> bool:
        return path.suffix.lower() == ".docx"

    def parse(self, path: Path) -> list[CanonicalRecord]:
        try:
            docx_module = importlib.import_module("docx")
            document_cls = getattr(docx_module, "Document", None)
            if document_cls is None:
                raise DatasetValidationError("docx_parser_dependency_missing")
        except Exception as exc:
            raise DatasetValidationError("docx_parser_dependency_missing") from exc

        document = document_cls(str(path))
        paragraphs = getattr(document, "paragraphs", [])
        lines: list[str] = []
        for paragraph in paragraphs:
            text = _as_text(getattr(paragraph, "text", ""))
            if text:
                lines.append(text)
        merged = "\n".join(lines).strip()
        if not merged:
            return []
        return [
            _new_record(
                [
                    CanonicalMessage(role="user", content="Fasse den folgenden Fachtext strukturiert zusammen."),
                    CanonicalMessage(role="assistant", content=merged),
                ],
                metadata={"document_type": "docx"},
            )
        ]


def _iter_json_rows(path: Path) -> list[object]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows: list[object] = []
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    rows.append(json.loads(stripped))
                except json.JSONDecodeError as exc:
                    raise DatasetValidationError(f"invalid_json_line:{line_number}:{exc.msg}") from exc
        return rows

    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError as exc:
        raise DatasetValidationError("invalid_json") from exc

    if isinstance(payload, list):
        return cast(list[object], payload)
    return [payload]
