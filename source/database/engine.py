from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from source.database.models import Base
from source.database.settings import DB_ECHO, DB_URL
from sqlalchemy.ext.asyncio.engine import AsyncEngine


async def get_engine() -> AsyncEngine:
    engine = create_async_engine(url=DB_URL, echo=DB_ECHO)
    return engine


async def create_session() -> async_sessionmaker:
    engine = await get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return async_session
