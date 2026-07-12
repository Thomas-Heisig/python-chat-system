from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from typing import Protocol, cast
from app.core.config import get_config

_engine: AsyncEngine | None = None


class _DbCursor(Protocol):
    def execute(self, sql: str) -> object: ...
    def close(self) -> None: ...


class _DbConnection(Protocol):
    def cursor(self) -> _DbCursor: ...


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        cfg = get_config()
        engine_kwargs: dict[str, object] = {"echo": False, "future": True}
        if str(cfg.database_url).startswith("sqlite"):
            engine_kwargs["connect_args"] = {"timeout": 10}
        _engine = create_async_engine(cfg.database_url, **engine_kwargs)

        if str(cfg.database_url).startswith("sqlite"):
            @event.listens_for(_engine.sync_engine, "connect")
            def _configure_sqlite(dbapi_connection, _connection_record) -> None:  # type: ignore[no-redef]
                connection = cast(_DbConnection, dbapi_connection)
                cursor = connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=10000")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    return _engine
