from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transactional(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
