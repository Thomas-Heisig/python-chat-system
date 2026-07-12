from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_config
from app.database.base import Base
import app.db_models as db_models


config = context.config

if config.config_file_name is not None:
	fileConfig(config.config_file_name)


target_metadata = Base.metadata
_MODELS_MODULE = db_models


def _to_sync_sqlalchemy_url(url: str) -> str:
	if url.startswith("sqlite+aiosqlite://"):
		return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
	if url.startswith("postgresql+asyncpg://"):
		return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
	return url


def run_migrations_offline() -> None:
	runtime_url = _to_sync_sqlalchemy_url(get_config().database_url)
	context.configure(
		url=runtime_url,
		target_metadata=target_metadata,
		literal_binds=True,
		compare_type=True,
		compare_server_default=True,
		dialect_opts={"paramstyle": "named"},
	)

	with context.begin_transaction():
		context.run_migrations()


def run_migrations_online() -> None:
	configuration = config.get_section(config.config_ini_section, {})
	configuration["sqlalchemy.url"] = _to_sync_sqlalchemy_url(get_config().database_url)

	connectable = engine_from_config(
		configuration,
		prefix="sqlalchemy.",
		poolclass=pool.NullPool,
	)

	with connectable.connect() as connection:
		context.configure(
			connection=connection,
			target_metadata=target_metadata,
			compare_type=True,
			compare_server_default=True,
		)

		with context.begin_transaction():
			context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()
