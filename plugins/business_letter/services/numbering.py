from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Iterator

_DB_LOCK = Lock()
_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "database" / "business_letter.sqlite3"


class NumberSequenceStore:
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

    @staticmethod
    def _display_year(year: int | None) -> int:
        return year or datetime.now().year

    @classmethod
    def _storage_year(cls, year: int | None, *, year_reset: bool) -> int:
        display_year = cls._display_year(year)
        return display_year if year_reset else 0

    @staticmethod
    def _render_number(
        *,
        prefix: str,
        sequence_kind: str,
        tenant_id: str,
        display_year: int,
        next_value: int,
        width: int,
        pattern: str | None,
    ) -> str:
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

    def has_sequence_entries(self, *, tenant_id: str = "default", sequence_kind: str) -> bool:
        with _DB_LOCK:
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT 1
                    FROM number_sequences
                    WHERE tenant_id = ? AND sequence_kind = ?
                    LIMIT 1
                    """,
                    (tenant_id, sequence_kind),
                ).fetchone()
        return row is not None

    def peek_next_number(
        self,
        *,
        prefix: str,
        sequence_kind: str,
        tenant_id: str = "default",
        year: int | None = None,
        width: int = 5,
        pattern: str | None = None,
        start_value: int = 1,
        year_reset: bool = True,
    ) -> dict[str, Any]:
        display_year = self._display_year(year)
        sequence_year = self._storage_year(year, year_reset=year_reset)
        normalized_start_value = max(1, start_value)
        with _DB_LOCK:
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT current_value
                    FROM number_sequences
                    WHERE tenant_id = ? AND sequence_kind = ? AND sequence_year = ?
                    """,
                    (tenant_id, sequence_kind, sequence_year),
                ).fetchone()
        current_value = int(row["current_value"] if row else normalized_start_value - 1)
        next_value = current_value + 1
        return {
            "preview": self._render_number(
                prefix=prefix,
                sequence_kind=sequence_kind,
                tenant_id=tenant_id,
                display_year=display_year,
                next_value=next_value,
                width=width,
                pattern=pattern,
            ),
            "next_value": next_value,
            "current_value": current_value,
            "display_year": display_year,
            "storage_year": sequence_year,
        }

    def next_number(
        self,
        *,
        prefix: str,
        sequence_kind: str,
        tenant_id: str = "default",
        year: int | None = None,
        width: int = 5,
        pattern: str | None = None,
        start_value: int = 1,
        year_reset: bool = True,
    ) -> str:
        display_year = self._display_year(year)
        sequence_year = self._storage_year(year, year_reset=year_reset)
        normalized_start_value = max(1, start_value)
        with _DB_LOCK:
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT current_value
                    FROM number_sequences
                    WHERE tenant_id = ? AND sequence_kind = ? AND sequence_year = ?
                    """,
                    (tenant_id, sequence_kind, sequence_year),
                ).fetchone()
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
        return self._render_number(
            prefix=prefix,
            sequence_kind=sequence_kind,
            tenant_id=tenant_id,
            display_year=display_year,
            next_value=next_value,
            width=width,
            pattern=pattern,
        )
