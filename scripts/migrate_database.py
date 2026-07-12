import shutil
import sys
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import make_url

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_config
from app.database.base import Base
import app.db_models  # noqa: F401


def to_sync_sqlalchemy_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def resolve_sqlite_db_path(sync_url: str) -> Path | None:
    parsed = make_url(sync_url)
    if parsed.drivername != "sqlite":
        return None
    database_name = parsed.database
    if database_name in (None, "", ":memory:"):
        return None
    db_path = Path(database_name)
    if not db_path.is_absolute():
        db_path = (ROOT / db_path).resolve()
    return db_path


def backup_sqlite_database(db_path: Path) -> Path | None:
    if not db_path.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(f"{db_path.suffix}.{timestamp}.bak")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, backup_path)
    return backup_path


def inspect_schema(sync_url: str) -> tuple[bool, bool, set[str]]:
    engine = create_engine(sync_url)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = set(inspector.get_table_names())
    finally:
        engine.dispose()

    managed_tables = set(Base.metadata.tables.keys())
    has_alembic_version = "alembic_version" in tables
    has_managed_tables = len(tables.intersection(managed_tables)) > 0
    return has_alembic_version, has_managed_tables, tables


def main() -> None:
    alembic_config = Config(str(ROOT / "alembic.ini"))
    runtime_url = get_config().database_url
    sync_url = to_sync_sqlalchemy_url(runtime_url)

    sqlite_path = resolve_sqlite_db_path(sync_url)
    backup_path = backup_sqlite_database(sqlite_path) if sqlite_path is not None else None

    if sqlite_path is not None:
        print(f"[safe-migrate] Datenbank: {sqlite_path}")
    if backup_path is not None:
        print(f"[safe-migrate] Backup erstellt: {backup_path}")

    has_alembic_version, has_managed_tables, tables = inspect_schema(sync_url)
    print(
        "[safe-migrate] Vorabpruefung:",
        f"alembic_version={'ja' if has_alembic_version else 'nein'},",
        f"schema_tabellen={len(tables)}",
    )

    try:
        if has_alembic_version:
            print("[safe-migrate] Versionstabelle vorhanden -> upgrade head")
            command.upgrade(alembic_config, "head")
        elif has_managed_tables:
            print("[safe-migrate] Bestehendes unversioniertes Schema erkannt -> stamp head, dann upgrade head")
            command.stamp(alembic_config, "head")
            command.upgrade(alembic_config, "head")
        else:
            print("[safe-migrate] Leeres Schema erkannt -> upgrade head")
            command.upgrade(alembic_config, "head")
    except Exception as exc:
        if backup_path is not None and sqlite_path is not None and backup_path.exists():
            shutil.copy2(backup_path, sqlite_path)
            print(f"[safe-migrate] Fehler, Backup wiederhergestellt: {backup_path}")
        raise RuntimeError(f"Sichere Migration fehlgeschlagen: {exc}") from exc

    print("[safe-migrate] Migration erfolgreich abgeschlossen.")


if __name__ == "__main__":
    main()
