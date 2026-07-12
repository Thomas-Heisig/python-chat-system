from sqlalchemy import not_, or_, select, true
from datetime import datetime, timezone
from app.database.repositories.base_repository import BaseRepository
from app.db_models.conversation import Conversation


class ConversationRepository(BaseRepository):
    @staticmethod
    def _is_visible_to_user(conversation: Conversation, user_id: int, private_conversation_ids: set[int]) -> bool:
        if conversation.archived_at is not None:
            return False
        if conversation.user_id == user_id:
            return True
        if conversation.id in private_conversation_ids:
            return False
        return True

    async def list_by_user(self, user_id: int, limit: int = 100) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.archived_at.is_(None))
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, conversation_id: int, user_id: int) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id).where(Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_any(self, conversation_id: int) -> Conversation | None:
        result = await self.session.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    async def get_visible_by_id(
        self,
        conversation_id: int,
        user_id: int,
        private_conversation_ids: list[int],
    ) -> Conversation | None:
        conversation = await self.get_by_id_any(conversation_id)
        if conversation is None:
            return None
        if not self._is_visible_to_user(conversation, user_id=user_id, private_conversation_ids=set(private_conversation_ids)):
            return None
        return conversation

    async def list_visible_for_user(self, user_id: int, private_conversation_ids: list[int], limit: int = 100) -> list[Conversation]:
        base_query = select(Conversation).where(Conversation.archived_at.is_(None))
        visibility_filter = Conversation.user_id == user_id
        if private_conversation_ids:
            visibility_filter = or_(
                visibility_filter,
                not_(Conversation.id.in_(private_conversation_ids)),
            )
        else:
            # Default visibility remains "internal" until team-scoped rules are introduced.
            visibility_filter = true()

        base_query = base_query.where(visibility_filter)

        result = await self.session.execute(
            base_query.order_by(Conversation.updated_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, user_id: int, title: str | None = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def update_title(self, conversation: Conversation, title: str) -> Conversation:
        conversation.title = title
        conversation.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return conversation

    async def archive_by_id(self, conversation_id: int, user_id: int) -> bool:
        conversation = await self.get_by_id(conversation_id=conversation_id, user_id=user_id)
        if conversation is None:
            return False
        setattr(conversation, "archived_at", datetime.now(timezone.utc))
        await self.session.flush()
        return True
