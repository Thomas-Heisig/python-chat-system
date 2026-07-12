from sqlalchemy import select
from app.database.repositories.base_repository import BaseRepository
from app.db_models.conversation import Conversation
from app.db_models.message import Message


class MessageRepository(BaseRepository):
    async def list_by_conversation(self, conversation_id: int, limit: int = 50) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        rows.reverse()
        return rows

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        model_id: int | None = None,
        metadata_json: str | None = None,
    ) -> Message:
        item = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_id=model_id,
            metadata_json=metadata_json,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_latest_by_conversation(self, conversation_id: int) -> Message | None:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def find_idempotent_exchange(
        self,
        user_id: int,
        idempotency_key: str,
        conversation_id: int | None = None,
    ) -> tuple[Message, Message] | None:
        normalized_key = idempotency_key.strip()
        if not normalized_key:
            return None

        marker = f'"idempotency_key":"{normalized_key}"'
        query = (
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Conversation.user_id == user_id)
            .where(Message.role == "user")
            .where(Message.metadata_json.is_not(None))
            .where(Message.metadata_json.like(f"%{marker}%"))
            .order_by(Message.id.desc())
        )
        if conversation_id is not None:
            query = query.where(Message.conversation_id == conversation_id)

        user_message = (await self.session.execute(query.limit(1))).scalar_one_or_none()
        if user_message is None:
            return None

        assistant_message = (
            await self.session.execute(
                select(Message)
                .where(Message.conversation_id == user_message.conversation_id)
                .where(Message.role == "assistant")
                .where(Message.id > user_message.id)
                .order_by(Message.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if assistant_message is None:
            return None

        return user_message, assistant_message
