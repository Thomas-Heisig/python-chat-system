from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class TrainingDatasetFile(Base, TimestampMixin):
    __tablename__ = "training_dataset_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("training_datasets.id"), nullable=False, index=True)
    split: Mapped[str] = mapped_column(String(30), nullable=False, default="none")
    file_role: Mapped[str] = mapped_column(String(30), nullable=False, default="source")
    relative_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="imported")
    validation_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
