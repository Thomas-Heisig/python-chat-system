from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PluginIdempotencyRecord(Base, TimestampMixin):
    __tablename__ = "plugin_idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "plugin_id",
            "function_name",
            "user_scope",
            "team_scope",
            "idempotency_key",
            name="uq_plugin_idempotency_scope",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plugin_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    function_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    team_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    user_scope: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    team_scope: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)

    arguments_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="in_progress", index=True)

    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
