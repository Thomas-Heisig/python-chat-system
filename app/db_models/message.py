from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    parent_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("model_configs.id"), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
