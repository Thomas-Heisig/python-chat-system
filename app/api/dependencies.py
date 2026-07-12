from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.chat.service import ChatService


async def db_session_dependency(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session


async def chat_service_dependency(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    return ChatService(session)
