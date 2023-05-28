from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from source.store.database.models import Base
from source.store.database.settings import DB_ECHO, DB_URL


async def get_engine():
    engine = create_async_engine(url=DB_URL, echo=DB_ECHO)
    return engine


async def create_session():
    engine = await get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return async_session
