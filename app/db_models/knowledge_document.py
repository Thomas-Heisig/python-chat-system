from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class KnowledgeDocument(Base, TimestampMixin):
	__tablename__ = "knowledge_documents"

	id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
	file_name: Mapped[str] = mapped_column(String(300), nullable=False)
	source: Mapped[str | None] = mapped_column(String(200), nullable=True)
	status: Mapped[str] = mapped_column(String(40), nullable=False, default="Bereit")
	index_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
	metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
