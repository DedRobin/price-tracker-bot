from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from source.store.database.models import Base
from source.store.database.settings import DB_ECHO, DB_URL


async def create_session():
    engine = create_async_engine(url=DB_URL, echo=DB_ECHO)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return async_session
