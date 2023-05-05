from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from store.database.models import Base, Product, User
from store.database.settings import DB_URL, DB_ECHO


async def create_session():
    engine = create_async_engine(url=DB_URL, echo=DB_ECHO)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return async_session


async def add_user(username, chat_id):
    async_session = await create_session()
    async with async_session() as session:
        insert_query = insert(User).values({"username": username, "chat_id": chat_id})
        await session.execute(insert_query)
        await session.commit()


async def updated_product():
    # For command
    async_session = await create_session()
    async with async_session() as session:
        select_query = select(Product).limit(1)
        product = await session.execute(select_query)
        product = product.scalars().one()
        product.current_price = 0
        await session.commit()
