from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class TrainingArtifact(Base, TimestampMixin):
    __tablename__ = "training_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("training_jobs.id"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(40), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="created")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
