from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Iterator, cast


_DB_LOCK = Lock()
_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "database" / "business_letter.sqlite3"


@dataclass(slots=True)
class PersistedArtifact:
    artifact_id: str
    storage_key: str
    mime_type: str
    sha256: str
    size_bytes: int


class BusinessLetterPersistence:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or _DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        with _DB_LOCK:
            with self._connection() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS document_templates (
                        template_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        document_number TEXT NOT NULL,
                        template_profile TEXT,
                        status TEXT NOT NULL,
                        data_snapshot TEXT NOT NULL,
                        content_hash TEXT NOT NULL,
                        created_by TEXT,
                        approved_by TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS commercial_documents (
                        document_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        document_number TEXT NOT NULL,
                        document_kind TEXT NOT NULL,
                        status TEXT NOT NULL,
                        revision_number INTEGER NOT NULL,
                        snapshot_json TEXT NOT NULL,
                        content_hash TEXT NOT NULL,
                        created_by TEXT,
                        approved_by TEXT,
                        created_at TEXT NOT NULL,
                        sent_at TEXT,
                        reference_document_id TEXT,
                        storage_key TEXT,
                        mime_type TEXT,
                        size_bytes INTEGER,
                        retention_until TEXT,
                        is_immutable INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS document_versions (
                        version_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        document_number TEXT NOT NULL,
                        revision_number INTEGER NOT NULL,
                        snapshot_json TEXT NOT NULL,
                        content_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        created_by TEXT,
                        reason TEXT,
                        is_current INTEGER NOT NULL DEFAULT 1
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS document_artifacts (
                        artifact_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        document_number TEXT NOT NULL,
                        artifact_kind TEXT NOT NULL,
                        storage_key TEXT NOT NULL,
                        mime_type TEXT NOT NULL,
                        sha256 TEXT NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        hash_verified INTEGER NOT NULL DEFAULT 0,
                        retention_until TEXT,
                        archive_group TEXT,
                        payload_text TEXT,
                        created_at TEXT NOT NULL,
                        created_by TEXT,
                        metadata_json TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS document_events (
                        event_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        document_number TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_payload TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        created_by TEXT
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS number_sequences (
                        tenant_id TEXT NOT NULL,
                        sequence_kind TEXT NOT NULL,
                        sequence_year INTEGER NOT NULL,
                        current_value INTEGER NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (tenant_id, sequence_kind, sequence_year)
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dispatch_queue (
                        dispatch_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        document_number TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL UNIQUE,
                        channel TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        to_json TEXT NOT NULL,
                        cc_json TEXT NOT NULL,
                        bcc_json TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        attempt_count INTEGER NOT NULL DEFAULT 0,
                        max_attempts INTEGER NOT NULL DEFAULT 3,
                        next_retry_at TEXT,
                        last_attempt_at TEXT,
                        sent_at TEXT,
                        external_message_id TEXT,
                        last_error TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dispatch_history (
                        history_id TEXT PRIMARY KEY,
                        dispatch_id TEXT NOT NULL,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        attempt INTEGER NOT NULL,
                        details_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                self._ensure_column(connection, "commercial_documents", "retention_until", "TEXT")
                self._ensure_column(connection, "commercial_documents", "is_immutable", "INTEGER NOT NULL DEFAULT 0")
                self._ensure_column(connection, "document_artifacts", "hash_verified", "INTEGER NOT NULL DEFAULT 0")
                self._ensure_column(connection, "document_artifacts", "retention_until", "TEXT")
                self._ensure_column(connection, "document_artifacts", "archive_group", "TEXT")
                self._ensure_column(connection, "document_artifacts", "payload_text", "TEXT")

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        columns = {
            str(row[1])
            for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
            if len(row) > 1
        }
        if column_name in columns:
            return
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _retention_until(days: int | None) -> str | None:
        if days is None or days <= 0:
            return None
        return (datetime.now() + timedelta(days=days)).isoformat()

    @staticmethod
    def _dispatch_backoff_seconds(attempt_count: int) -> int:
        # Exponential backoff with a sane upper limit.
        return min(3600, 60 * (2 ** max(0, attempt_count - 1)))

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {str(key): row[key] for key in row.keys()}

    @staticmethod
    def _as_mapping(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        raw = cast(dict[object, Any], value)
        return {str(key): item for key, item in raw.items()}

    @staticmethod
    def _insert_document_event(
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        event_type: str,
        event_payload: dict[str, Any],
        created_at: str,
        created_by: str,
    ) -> str:
        event_id = f"evt_{hashlib.sha1((document_id + event_type + created_at + created_by).encode('utf-8')).hexdigest()[:16]}"
        connection.execute(
            """
            INSERT INTO document_events (
                event_id, tenant_id, document_id, document_number, event_type,
                event_payload, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                tenant_id,
                document_id,
                document_number,
                event_type,
                json.dumps(event_payload, ensure_ascii=False, sort_keys=True, default=str),
                created_at,
                created_by,
            ),
        )
        return event_id

    def record_document_event(
        self,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        event_type: str,
        event_payload: dict[str, Any],
        created_by: str,
    ) -> dict[str, Any]:
        now = datetime.now().isoformat()
        with _DB_LOCK:
            with self._connection() as connection:
                event_id = self._insert_document_event(
                    connection,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    document_number=document_number,
                    event_type=event_type,
                    event_payload=event_payload,
                    created_at=now,
                    created_by=created_by,
                )
        return {
            "event_id": event_id,
            "tenant_id": tenant_id,
            "document_id": document_id,
            "document_number": document_number,
            "event_type": event_type,
            "created_at": now,
            "created_by": created_by,
        }

    def enqueue_dispatch(
        self,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        idempotency_key: str,
        channel: str,
        provider: str,
        to_values: list[str],
        cc_values: list[str],
        bcc_values: list[str],
        subject: str,
        payload: dict[str, Any],
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        now = datetime.now().isoformat()
        attempt_limit = max(1, int(max_attempts))
        dispatch_id = f"dsp_{hashlib.sha1((tenant_id + document_id + idempotency_key).encode('utf-8')).hexdigest()[:20]}"

        with _DB_LOCK:
            with self._connection() as connection:
                existing = connection.execute(
                    """
                    SELECT *
                    FROM dispatch_queue
                    WHERE idempotency_key = ?
                    LIMIT 1
                    """,
                    (idempotency_key,),
                ).fetchone()
                if existing is not None:
                    existing_item = self._row_to_dict(existing) or {}
                    existing_item["created"] = False
                    return existing_item

                connection.execute(
                    """
                    INSERT INTO dispatch_queue (
                        dispatch_id, tenant_id, document_id, document_number, idempotency_key,
                        channel, provider, to_json, cc_json, bcc_json, subject, payload_json,
                        status, attempt_count, max_attempts, next_retry_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    """,
                    (
                        dispatch_id,
                        tenant_id,
                        document_id,
                        document_number,
                        idempotency_key,
                        channel,
                        provider,
                        json.dumps(to_values, ensure_ascii=False),
                        json.dumps(cc_values, ensure_ascii=False),
                        json.dumps(bcc_values, ensure_ascii=False),
                        subject,
                        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
                        "queued",
                        attempt_limit,
                        now,
                        now,
                        now,
                    ),
                )
                self._insert_dispatch_history(
                    connection,
                    dispatch_id=dispatch_id,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    event_type="enqueued",
                    attempt=0,
                    details={"channel": channel, "provider": provider, "subject": subject},
                    created_at=now,
                )

                created = connection.execute(
                    "SELECT * FROM dispatch_queue WHERE dispatch_id = ? LIMIT 1",
                    (dispatch_id,),
                ).fetchone()
                created_item = self._row_to_dict(created) or {}
                created_item["created"] = True
                return created_item

    def record_dispatch_attempt(
        self,
        *,
        dispatch_id: str,
        success: bool,
        provider_result: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.now().isoformat()
        with _DB_LOCK:
            with self._connection() as connection:
                row = connection.execute(
                    "SELECT * FROM dispatch_queue WHERE dispatch_id = ? LIMIT 1",
                    (dispatch_id,),
                ).fetchone()
                if row is None:
                    raise RuntimeError(f"Dispatch item not found: {dispatch_id}")

                current = self._row_to_dict(row) or {}
                tenant_id = str(current.get("tenant_id") or "")
                document_id = str(current.get("document_id") or "")
                attempt_count = int(current.get("attempt_count") or 0) + 1
                max_attempts = max(1, int(current.get("max_attempts") or 3))

                if success:
                    new_status = "sent"
                    next_retry_at = None
                    sent_at = now
                    last_error = ""
                else:
                    has_retries_left = attempt_count < max_attempts
                    new_status = "queued" if has_retries_left else "failed"
                    delay_seconds = self._dispatch_backoff_seconds(attempt_count)
                    next_retry_at = (datetime.now() + timedelta(seconds=delay_seconds)).isoformat() if has_retries_left else None
                    sent_at = None
                    last_error = str(provider_result.get("error") or "unknown_dispatch_error")

                connection.execute(
                    """
                    UPDATE dispatch_queue
                    SET status = ?,
                        attempt_count = ?,
                        next_retry_at = ?,
                        last_attempt_at = ?,
                        sent_at = COALESCE(?, sent_at),
                        external_message_id = COALESCE(?, external_message_id),
                        last_error = ?,
                        updated_at = ?
                    WHERE dispatch_id = ?
                    """,
                    (
                        new_status,
                        attempt_count,
                        next_retry_at,
                        now,
                        sent_at,
                        str(provider_result.get("message_id") or provider_result.get("id") or "").strip() or None,
                        last_error,
                        now,
                        dispatch_id,
                    ),
                )

                self._insert_dispatch_history(
                    connection,
                    dispatch_id=dispatch_id,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    event_type="sent" if success else ("retry_scheduled" if new_status == "queued" else "failed"),
                    attempt=attempt_count,
                    details={"result": provider_result, "status": new_status},
                    created_at=now,
                )

                updated = connection.execute(
                    "SELECT * FROM dispatch_queue WHERE dispatch_id = ? LIMIT 1",
                    (dispatch_id,),
                ).fetchone()
                return self._row_to_dict(updated) or {}

    @staticmethod
    def _insert_dispatch_history(
        connection: sqlite3.Connection,
        *,
        dispatch_id: str,
        tenant_id: str,
        document_id: str,
        event_type: str,
        attempt: int,
        details: dict[str, Any],
        created_at: str,
    ) -> None:
        history_id = f"dhe_{hashlib.sha1((dispatch_id + event_type + created_at + str(attempt)).encode('utf-8')).hexdigest()[:20]}"
        connection.execute(
            """
            INSERT INTO dispatch_history (
                history_id, dispatch_id, tenant_id, document_id, event_type, attempt, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                dispatch_id,
                tenant_id,
                document_id,
                event_type,
                max(0, int(attempt)),
                json.dumps(details, ensure_ascii=False, sort_keys=True, default=str),
                created_at,
            ),
        )

    def save_template(
        self,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        template_profile: str,
        status: str,
        data_snapshot: dict[str, Any],
        created_by: str = "plugin:business_letter",
        approved_by: str = "",
    ) -> dict[str, Any]:
        template_id = f"tpl_{hashlib.sha1((document_id + document_number).encode('utf-8')).hexdigest()[:16]}"
        snapshot_text = json.dumps(data_snapshot, ensure_ascii=False, sort_keys=True, default=str)
        now = datetime.now().isoformat()
        payload = {
            "template_id": template_id,
            "tenant_id": tenant_id,
            "document_id": document_id,
            "document_number": document_number,
            "template_profile": template_profile,
            "status": status,
            "data_snapshot": snapshot_text,
            "content_hash": self._sha256(snapshot_text),
            "created_by": created_by,
            "approved_by": approved_by,
            "created_at": now,
            "updated_at": now,
        }
        with _DB_LOCK:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO document_templates (
                        template_id, tenant_id, document_id, document_number, template_profile, status,
                        data_snapshot, content_hash, created_by, approved_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(template_id)
                    DO UPDATE SET
                        status = excluded.status,
                        data_snapshot = excluded.data_snapshot,
                        content_hash = excluded.content_hash,
                        approved_by = excluded.approved_by,
                        updated_at = excluded.updated_at
                    """,
                    tuple(payload[field] for field in [
                        "template_id", "tenant_id", "document_id", "document_number", "template_profile", "status",
                        "data_snapshot", "content_hash", "created_by", "approved_by", "created_at", "updated_at",
                    ]),
                )
        return payload

    def save_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        document_kind: str,
        status: str,
        snapshot_json: dict[str, Any],
        created_by: str = "plugin:business_letter",
        approved_by: str = "",
        sent_at: str | None = None,
        reference_document_id: str | None = None,
        storage_key: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
        revision_number: int = 1,
        reason: str = "initial",
    ) -> dict[str, Any]:
        snapshot_text = json.dumps(snapshot_json, ensure_ascii=False, sort_keys=True, default=str)
        now = datetime.now().isoformat()
        content_hash = self._sha256(snapshot_text)
        version_id = f"ver_{hashlib.sha1((document_id + str(revision_number)).encode('utf-8')).hexdigest()[:16]}"
        event_id = f"evt_{hashlib.sha1((document_id + now).encode('utf-8')).hexdigest()[:16]}"
        with _DB_LOCK:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO commercial_documents (
                        document_id, tenant_id, document_number, document_kind, status, revision_number,
                        snapshot_json, content_hash, created_by, approved_by, created_at, sent_at,
                        reference_document_id, storage_key, mime_type, size_bytes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(document_id)
                    DO UPDATE SET
                        status = excluded.status,
                        revision_number = excluded.revision_number,
                        snapshot_json = excluded.snapshot_json,
                        content_hash = excluded.content_hash,
                        approved_by = excluded.approved_by,
                        sent_at = excluded.sent_at,
                        reference_document_id = excluded.reference_document_id,
                        storage_key = excluded.storage_key,
                        mime_type = excluded.mime_type,
                        size_bytes = excluded.size_bytes
                    """,
                    (
                        document_id,
                        tenant_id,
                        document_number,
                        document_kind,
                        status,
                        revision_number,
                        snapshot_text,
                        content_hash,
                        created_by,
                        approved_by,
                        now,
                        sent_at,
                        reference_document_id,
                        storage_key,
                        mime_type,
                        size_bytes,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO document_versions (
                        version_id, tenant_id, document_id, document_number, revision_number,
                        snapshot_json, content_hash, created_at, created_by, reason, is_current
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        version_id,
                        tenant_id,
                        document_id,
                        document_number,
                        revision_number,
                        snapshot_text,
                        content_hash,
                        now,
                        created_by,
                        reason,
                    ),
                )
                connection.execute(
                    """
                    UPDATE document_versions
                    SET is_current = 0
                    WHERE document_id = ? AND version_id != ?
                    """,
                    (document_id, version_id),
                )
                self._insert_document_event(
                    connection,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    document_number=document_number,
                    event_type="document_saved",
                    event_payload={"revision_number": revision_number, "status": status, "reason": reason},
                    created_at=now,
                    created_by=created_by,
                )
        return {
            "document_id": document_id,
            "document_number": document_number,
            "revision_number": revision_number,
            "content_hash": content_hash,
            "version_id": version_id,
            "event_id": event_id,
        }

    def save_artifact(
        self,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        artifact_kind: str,
        storage_key: str,
        mime_type: str,
        payload_text: str,
        created_by: str = "plugin:business_letter",
        metadata: dict[str, Any] | None = None,
    ) -> PersistedArtifact:
        artifact_id = f"art_{hashlib.sha1((document_id + artifact_kind + storage_key).encode('utf-8')).hexdigest()[:16]}"
        digest = self._sha256(payload_text)
        size_bytes = len(payload_text.encode("utf-8"))
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True, default=str)
        with _DB_LOCK:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO document_artifacts (
                        artifact_id, tenant_id, document_id, document_number, artifact_kind,
                        storage_key, mime_type, sha256, size_bytes, created_at, created_by, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(artifact_id)
                    DO UPDATE SET
                        storage_key = excluded.storage_key,
                        mime_type = excluded.mime_type,
                        sha256 = excluded.sha256,
                        size_bytes = excluded.size_bytes,
                        metadata_json = excluded.metadata_json
                    """,
                    (
                        artifact_id,
                        tenant_id,
                        document_id,
                        document_number,
                        artifact_kind,
                        storage_key,
                        mime_type,
                        digest,
                        size_bytes,
                        now,
                        created_by,
                        metadata_json,
                    ),
                )
        return PersistedArtifact(
            artifact_id=artifact_id,
            storage_key=storage_key,
            mime_type=mime_type,
            sha256=digest,
            size_bytes=size_bytes,
        )

    def _reserve_next_number(
        self,
        connection: sqlite3.Connection,
        *,
        tenant_id: str,
        sequence_kind: str,
        sequence_year: int,
        display_year: int,
        prefix: str,
        width: int,
        pattern: str | None = None,
        start_value: int = 1,
    ) -> str:
        row = connection.execute(
            """
            SELECT current_value
            FROM number_sequences
            WHERE tenant_id = ? AND sequence_kind = ? AND sequence_year = ?
            """,
            (tenant_id, sequence_kind, sequence_year),
        ).fetchone()
        normalized_start_value = max(1, start_value)
        current_value = int(row["current_value"] if row else normalized_start_value - 1)
        next_value = current_value + 1
        connection.execute(
            """
            INSERT INTO number_sequences (tenant_id, sequence_kind, sequence_year, current_value, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(tenant_id, sequence_kind, sequence_year)
            DO UPDATE SET current_value = excluded.current_value, updated_at = excluded.updated_at
            """,
            (tenant_id, sequence_kind, sequence_year, next_value, datetime.now().isoformat()),
        )
        sequence_text = f"{next_value:0{width}d}"
        if pattern:
            try:
                return pattern.format(
                    prefix=prefix,
                    year=display_year,
                    month=f"{datetime.now().month:02d}",
                    day=f"{datetime.now().day:02d}",
                    sequence=next_value,
                    sequence_text=sequence_text,
                    width=width,
                    tenant_id=tenant_id,
                    sequence_kind=sequence_kind,
                )
            except Exception:
                pass
        return f"{prefix}-{display_year}-{sequence_text}"

    def persist_bundle_transactional(
        self,
        *,
        tenant_id: str,
        document_id: str,
        document_number: str,
        numbering: dict[str, Any] | None,
        template_profile: str,
        status: str,
        data_snapshot: dict[str, Any],
        document_kind: str,
        snapshot_json: dict[str, Any],
        created_by: str = "plugin:business_letter",
        approved_by: str = "",
        sent_at: str | None = None,
        revision_number: int = 1,
        reason: str = "initial",
        reference_document_id: str | None = None,
        storage_key: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        retention_days: int | None = None,
        immutable_after_release: bool = False,
        verify_hashes: bool = True,
    ) -> dict[str, Any]:
        now = datetime.now().isoformat()
        resolved_document_number = document_number.strip()
        retention_until = self._retention_until(retention_days)
        with _DB_LOCK:
            with self._connection() as connection:
                if not resolved_document_number:
                    cfg = numbering or {}
                    prefix = str(cfg.get("prefix") or "DOC").strip().upper() or "DOC"
                    sequence_kind = str(cfg.get("sequence_kind") or f"business_letter:{prefix}").strip() or f"business_letter:{prefix}"
                    display_year = int(cfg.get("year") or datetime.now().year)
                    sequence_year = display_year if bool(cfg.get("year_reset", True)) else 0
                    width = max(1, min(12, int(cfg.get("width") or 5)))
                    start_value = max(1, int(cfg.get("start_value") or 1))
                    pattern = str(cfg.get("pattern") or "").strip() or None
                    resolved_document_number = self._reserve_next_number(
                        connection,
                        tenant_id=tenant_id,
                        sequence_kind=sequence_kind,
                        sequence_year=sequence_year,
                        display_year=display_year,
                        prefix=prefix,
                        width=width,
                        pattern=pattern,
                        start_value=start_value,
                    )

                template_id = f"tpl_{hashlib.sha1((document_id + resolved_document_number).encode('utf-8')).hexdigest()[:16]}"
                template_snapshot_text = json.dumps(data_snapshot, ensure_ascii=False, sort_keys=True, default=str)
                template_hash = self._sha256(template_snapshot_text)

                connection.execute(
                    """
                    INSERT INTO document_templates (
                        template_id, tenant_id, document_id, document_number, template_profile, status,
                        data_snapshot, content_hash, created_by, approved_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(template_id)
                    DO UPDATE SET
                        status = excluded.status,
                        data_snapshot = excluded.data_snapshot,
                        content_hash = excluded.content_hash,
                        approved_by = excluded.approved_by,
                        updated_at = excluded.updated_at
                    """,
                    (
                        template_id,
                        tenant_id,
                        document_id,
                        resolved_document_number,
                        template_profile,
                        status,
                        template_snapshot_text,
                        template_hash,
                        created_by,
                        approved_by,
                        now,
                        now,
                    ),
                )

                document_snapshot_text = json.dumps(snapshot_json, ensure_ascii=False, sort_keys=True, default=str)
                document_hash = self._sha256(document_snapshot_text)
                version_id = f"ver_{hashlib.sha1((document_id + str(revision_number)).encode('utf-8')).hexdigest()[:16]}"
                event_id = f"evt_{hashlib.sha1((document_id + now).encode('utf-8')).hexdigest()[:16]}"
                existing_document = connection.execute(
                    """
                    SELECT content_hash, status, is_immutable
                    FROM commercial_documents
                    WHERE document_id = ?
                    LIMIT 1
                    """,
                    (document_id,),
                ).fetchone()
                if existing_document is not None and int(existing_document["is_immutable"] or 0) == 1 and str(existing_document["content_hash"] or "") != document_hash:
                    raise RuntimeError("Document is immutable and cannot be modified after release.")

                released_statuses = {"approved", "ready", "queued", "sent", "delivered", "archived"}
                is_immutable = 1 if immutable_after_release and status.lower() in released_statuses else 0

                connection.execute(
                    """
                    INSERT INTO commercial_documents (
                        document_id, tenant_id, document_number, document_kind, status, revision_number,
                        snapshot_json, content_hash, created_by, approved_by, created_at, sent_at,
                        reference_document_id, storage_key, mime_type, size_bytes, retention_until, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(document_id)
                    DO UPDATE SET
                        document_number = excluded.document_number,
                        status = excluded.status,
                        revision_number = excluded.revision_number,
                        snapshot_json = excluded.snapshot_json,
                        content_hash = excluded.content_hash,
                        approved_by = excluded.approved_by,
                        sent_at = excluded.sent_at,
                        reference_document_id = excluded.reference_document_id,
                        storage_key = excluded.storage_key,
                        mime_type = excluded.mime_type,
                        size_bytes = excluded.size_bytes,
                        retention_until = excluded.retention_until,
                        is_immutable = CASE
                            WHEN commercial_documents.is_immutable = 1 THEN 1
                            ELSE excluded.is_immutable
                        END
                    """,
                    (
                        document_id,
                        tenant_id,
                        resolved_document_number,
                        document_kind,
                        status,
                        revision_number,
                        document_snapshot_text,
                        document_hash,
                        created_by,
                        approved_by,
                        now,
                        sent_at,
                        reference_document_id,
                        storage_key,
                        mime_type,
                        size_bytes,
                        retention_until,
                        is_immutable,
                    ),
                )

                connection.execute(
                    """
                    INSERT INTO document_versions (
                        version_id, tenant_id, document_id, document_number, revision_number,
                        snapshot_json, content_hash, created_at, created_by, reason, is_current
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        version_id,
                        tenant_id,
                        document_id,
                        resolved_document_number,
                        revision_number,
                        document_snapshot_text,
                        document_hash,
                        now,
                        created_by,
                        reason,
                    ),
                )
                connection.execute(
                    """
                    UPDATE document_versions
                    SET is_current = 0
                    WHERE document_id = ? AND version_id != ?
                    """,
                    (document_id, version_id),
                )
                self._insert_document_event(
                    connection,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    document_number=resolved_document_number,
                    event_type="document_saved",
                    event_payload={"revision_number": revision_number, "status": status, "reason": reason},
                    created_at=now,
                    created_by=created_by,
                )

                persisted_artifacts: list[dict[str, Any]] = []
                for artifact in artifacts or []:
                    artifact_kind = str(artifact.get("artifact_kind") or "json").strip() or "json"
                    artifact_storage_key = str(artifact.get("storage_key") or f"business_letter/{resolved_document_number}.{artifact_kind}").strip()
                    artifact_mime = str(artifact.get("mime_type") or "application/octet-stream").strip() or "application/octet-stream"
                    payload_text = str(artifact.get("payload_text") or "")
                    metadata_json = json.dumps(artifact.get("metadata") or {}, ensure_ascii=False, sort_keys=True, default=str)
                    digest = self._sha256(payload_text)
                    payload_size = len(payload_text.encode("utf-8"))
                    artifact_id = f"art_{hashlib.sha1((document_id + artifact_kind + artifact_storage_key).encode('utf-8')).hexdigest()[:16]}"
                    artifact_retention_until = str(artifact.get("retention_until") or retention_until or "").strip() or None
                    archive_group = str(artifact.get("archive_group") or "").strip() or None
                    hash_verified = 1

                    connection.execute(
                        """
                        INSERT INTO document_artifacts (
                            artifact_id, tenant_id, document_id, document_number, artifact_kind,
                            storage_key, mime_type, sha256, size_bytes, hash_verified, retention_until, archive_group, payload_text, created_at, created_by, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(artifact_id)
                        DO UPDATE SET
                            storage_key = excluded.storage_key,
                            mime_type = excluded.mime_type,
                            sha256 = excluded.sha256,
                            size_bytes = excluded.size_bytes,
                            hash_verified = excluded.hash_verified,
                            retention_until = excluded.retention_until,
                            archive_group = excluded.archive_group,
                            payload_text = excluded.payload_text,
                            metadata_json = excluded.metadata_json
                        """,
                        (
                            artifact_id,
                            tenant_id,
                            document_id,
                            resolved_document_number,
                            artifact_kind,
                            artifact_storage_key,
                            artifact_mime,
                            digest,
                            payload_size,
                            hash_verified,
                            artifact_retention_until,
                            archive_group,
                            payload_text,
                            now,
                            created_by,
                            metadata_json,
                        ),
                    )
                    if verify_hashes:
                        stored = connection.execute(
                            "SELECT sha256 FROM document_artifacts WHERE artifact_id = ? LIMIT 1",
                            (artifact_id,),
                        ).fetchone()
                        if stored is None or str(stored["sha256"] or "") != digest:
                            raise RuntimeError(f"Artifact hash verification failed for {artifact_kind}.")
                    persisted_artifacts.append(
                        {
                            "artifact_id": artifact_id,
                            "artifact_kind": artifact_kind,
                            "storage_key": artifact_storage_key,
                            "mime_type": artifact_mime,
                            "sha256": digest,
                            "size_bytes": payload_size,
                            "hash_verified": bool(hash_verified),
                            "retention_until": artifact_retention_until,
                            "archive_group": archive_group or "",
                        }
                    )

        return {
            "document_id": document_id,
            "document_number": resolved_document_number,
            "template": {
                "template_id": template_id,
                "content_hash": template_hash,
            },
            "document": {
                "revision_number": revision_number,
                "content_hash": document_hash,
                "version_id": version_id,
                "event_id": event_id,
                "retention_until": retention_until or "",
                "is_immutable": bool(is_immutable),
            },
            "artifacts": persisted_artifacts,
        }

    def mirror_to_guest_database(
        self,
        *,
        guest_db_path: str,
        document_id: str,
        document_number: str,
        payload: dict[str, Any],
        artifacts: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        target_path = Path(guest_db_path).expanduser().resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        created_at = datetime.now().isoformat()

        connection = sqlite3.connect(target_path)
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS guest_business_letter_documents (
                    document_id TEXT PRIMARY KEY,
                    document_number TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS guest_business_letter_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    artifact_kind TEXT NOT NULL,
                    storage_key TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    payload_text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS guest_business_letter_dispatch_queue (
                    dispatch_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    document_number TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    next_retry_at TEXT,
                    last_error TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO guest_business_letter_documents (document_id, document_number, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(document_id)
                DO UPDATE SET
                    document_number = excluded.document_number,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (document_id, document_number, payload_text, created_at, created_at),
            )

            for artifact in artifacts or []:
                artifact_kind = str(artifact.get("artifact_kind") or "json").strip() or "json"
                storage_key = str(artifact.get("storage_key") or f"business_letter/{document_number}.{artifact_kind}").strip()
                mime_type = str(artifact.get("mime_type") or "application/octet-stream").strip() or "application/octet-stream"
                artifact_payload = str(artifact.get("payload_text") or "")
                artifact_id = f"guest_art_{hashlib.sha1((document_id + artifact_kind + storage_key).encode('utf-8')).hexdigest()[:20]}"
                connection.execute(
                    """
                    INSERT INTO guest_business_letter_artifacts (
                        artifact_id, document_id, artifact_kind, storage_key, mime_type, payload_text, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(artifact_id)
                    DO UPDATE SET
                        artifact_kind = excluded.artifact_kind,
                        storage_key = excluded.storage_key,
                        mime_type = excluded.mime_type,
                        payload_text = excluded.payload_text
                    """,
                    (artifact_id, document_id, artifact_kind, storage_key, mime_type, artifact_payload, created_at),
                )

            dispatch_snapshot = payload.get("dispatch_queue_item") if isinstance(payload.get("dispatch_queue_item"), dict) else None
            if dispatch_snapshot:
                dispatch_id = str(dispatch_snapshot.get("dispatch_id") or "").strip()
                if dispatch_id:
                    connection.execute(
                        """
                        INSERT INTO guest_business_letter_dispatch_queue (
                            dispatch_id, document_id, document_number, idempotency_key, status,
                            attempt_count, max_attempts, next_retry_at, last_error, payload_json, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(dispatch_id)
                        DO UPDATE SET
                            status = excluded.status,
                            attempt_count = excluded.attempt_count,
                            max_attempts = excluded.max_attempts,
                            next_retry_at = excluded.next_retry_at,
                            last_error = excluded.last_error,
                            payload_json = excluded.payload_json,
                            updated_at = excluded.updated_at
                        """,
                        (
                            dispatch_id,
                            document_id,
                            document_number,
                            str(dispatch_snapshot.get("idempotency_key") or ""),
                            str(dispatch_snapshot.get("status") or "queued"),
                            int(dispatch_snapshot.get("attempt_count") or 0),
                            int(dispatch_snapshot.get("max_attempts") or 3),
                            str(dispatch_snapshot.get("next_retry_at") or "") or None,
                            str(dispatch_snapshot.get("last_error") or ""),
                            json.dumps(dispatch_snapshot, ensure_ascii=False, sort_keys=True, default=str),
                            created_at,
                            created_at,
                        ),
                    )

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return {
            "path": str(target_path),
            "document_id": document_id,
            "document_number": document_number,
            "artifacts": len(artifacts or []),
        }

    @staticmethod
    def _parse_snapshot_json(raw: Any) -> dict[str, Any]:
        text = str(raw or "").strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except Exception:
            return {}
        if not isinstance(parsed, dict):
            return {}
        raw_mapping = cast(dict[object, Any], parsed)
        return {str(key): value for key, value in raw_mapping.items()}

    def list_documents_for_tenant(self, *, tenant_id: str, limit: int = 500) -> list[dict[str, Any]]:
        resolved_limit = max(1, min(int(limit), 5000))
        rows: list[dict[str, Any]] = []
        with _DB_LOCK:
            with self._connection() as connection:
                result = connection.execute(
                    """
                    SELECT
                        document_id,
                        tenant_id,
                        document_number,
                        document_kind,
                        status,
                        revision_number,
                        snapshot_json,
                        created_at,
                        sent_at,
                        reference_document_id
                    FROM commercial_documents
                    WHERE tenant_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (tenant_id, resolved_limit),
                ).fetchall()

        for row in result:
            item = self._row_to_dict(row) or {}
            snapshot = self._parse_snapshot_json(item.get("snapshot_json"))
            item["snapshot"] = snapshot
            rows.append(item)
        return rows

    def get_document_by_id_or_number(
        self,
        *,
        tenant_id: str,
        document_id: str = "",
        document_number: str = "",
    ) -> dict[str, Any] | None:
        target_id = document_id.strip()
        target_number = document_number.strip()
        if not target_id and not target_number:
            return None

        with _DB_LOCK:
            with self._connection() as connection:
                row = None
                if target_id:
                    row = connection.execute(
                        """
                        SELECT
                            document_id,
                            tenant_id,
                            document_number,
                            document_kind,
                            status,
                            revision_number,
                            snapshot_json,
                            created_at,
                            sent_at,
                            reference_document_id
                        FROM commercial_documents
                        WHERE tenant_id = ? AND document_id = ?
                        LIMIT 1
                        """,
                        (tenant_id, target_id),
                    ).fetchone()
                if row is None and target_number:
                    row = connection.execute(
                        """
                        SELECT
                            document_id,
                            tenant_id,
                            document_number,
                            document_kind,
                            status,
                            revision_number,
                            snapshot_json,
                            created_at,
                            sent_at,
                            reference_document_id
                        FROM commercial_documents
                        WHERE tenant_id = ? AND document_number = ?
                        LIMIT 1
                        """,
                        (tenant_id, target_number),
                    ).fetchone()

        item = self._row_to_dict(row)
        if item is None:
            return None
        item["snapshot"] = self._parse_snapshot_json(item.get("snapshot_json"))
        return item

    def get_artifact_by_document_and_kind(
        self,
        *,
        tenant_id: str,
        document_id: str,
        artifact_kind: str,
    ) -> dict[str, Any] | None:
        target_document_id = document_id.strip()
        target_kind = artifact_kind.strip().lower()
        if not target_document_id or not target_kind:
            return None

        with _DB_LOCK:
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT
                        artifact_id,
                        tenant_id,
                        document_id,
                        document_number,
                        artifact_kind,
                        storage_key,
                        mime_type,
                        sha256,
                        size_bytes,
                        hash_verified,
                        retention_until,
                        archive_group,
                        payload_text,
                        created_at,
                        created_by,
                        metadata_json
                    FROM document_artifacts
                    WHERE tenant_id = ? AND document_id = ? AND LOWER(artifact_kind) = ?
                    LIMIT 1
                    """,
                    (tenant_id, target_document_id, target_kind),
                ).fetchone()

        item = self._row_to_dict(row)
        if item is None:
            return None
        metadata_json = str(item.get("metadata_json") or "").strip()
        try:
            parsed_metadata_raw: Any = json.loads(metadata_json) if metadata_json else {}
        except Exception:
            parsed_metadata_raw = {}
        item["metadata"] = cast(dict[str, Any], parsed_metadata_raw) if isinstance(parsed_metadata_raw, dict) else {}
        return item

    def list_follow_up_documents(
        self,
        *,
        tenant_id: str,
        source_document_id: str = "",
        source_document_number: str = "",
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        target_id = source_document_id.strip()
        target_number = source_document_number.strip()
        if not target_id and not target_number:
            return []

        all_documents = self.list_documents_for_tenant(tenant_id=tenant_id, limit=limit)
        matches: list[dict[str, Any]] = []
        for item in all_documents:
            snapshot = self._as_mapping(item.get("snapshot"))
            document = self._as_mapping(snapshot.get("document"))
            relationships = self._as_mapping(document.get("relationships"))
            rel_source_id = str(relationships.get("source_document_id") or "").strip()
            rel_source_number = str(relationships.get("source_document_number") or "").strip()
            if target_id and rel_source_id == target_id:
                matches.append(item)
                continue
            if target_number and rel_source_number == target_number:
                matches.append(item)

        return matches

    def list_project_documents(
        self,
        *,
        tenant_id: str,
        project_id: str = "",
        customer_id: str = "",
        limit: int = 800,
    ) -> list[dict[str, Any]]:
        target_project_id = project_id.strip()
        target_customer_id = customer_id.strip()
        if not target_project_id and not target_customer_id:
            return []

        all_documents = self.list_documents_for_tenant(tenant_id=tenant_id, limit=limit)
        matches: list[dict[str, Any]] = []
        for item in all_documents:
            snapshot = self._as_mapping(item.get("snapshot"))
            document = self._as_mapping(snapshot.get("document"))
            relationships = self._as_mapping(document.get("relationships"))
            rel_project_id = str(relationships.get("project_id") or "").strip()
            rel_customer_id = str(relationships.get("customer_id") or "").strip()

            if target_project_id and rel_project_id == target_project_id:
                matches.append(item)
                continue
            if not target_project_id and target_customer_id and rel_customer_id == target_customer_id:
                matches.append(item)

        return matches

    def list_document_events_for_document(
        self,
        *,
        tenant_id: str,
        document_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        resolved_limit = max(1, min(int(limit), 1000))
        with _DB_LOCK:
            with self._connection() as connection:
                rows = connection.execute(
                    """
                    SELECT event_id, tenant_id, document_id, document_number, event_type, event_payload, created_at, created_by
                    FROM document_events
                    WHERE tenant_id = ? AND document_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (tenant_id, document_id, resolved_limit),
                ).fetchall()

        items: list[dict[str, Any]] = []
        for row in rows:
            item = self._row_to_dict(row) or {}
            payload_text = str(item.get("event_payload") or "").strip()
            try:
                parsed_payload: Any = json.loads(payload_text) if payload_text else {}
            except Exception:
                parsed_payload = {}
            item["event_payload"] = cast(dict[str, Any], parsed_payload) if isinstance(parsed_payload, dict) else {}
            items.append(item)
        return items
