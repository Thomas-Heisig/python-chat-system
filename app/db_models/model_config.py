from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin


class ModelConfig(Base, TimestampMixin):
    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    backend: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_ram_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_vram_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    load_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_loaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
