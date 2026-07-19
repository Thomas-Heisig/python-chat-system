from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PluginConfirmation(Base, TimestampMixin):
    __tablename__ = "plugin_confirmations"

    id: Mapped[int] = mapped_column(primary_key=True)
    confirmation_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    team_id: Mapped[int | None] = mapped_column(nullable=True, index=True)

    plugin_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    function_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    route_kind: Mapped[str] = mapped_column(String(40), nullable=False)

    arguments_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    arguments_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    plugin_settings_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    execution_context_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    idempotency_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
