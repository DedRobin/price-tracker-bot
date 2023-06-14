from sqlalchemy import delete, exists, select

from source.bot.users.queries import select_users
from source.database.engine import create_session
from source.database.models import SessionToken


async def insert_token(token: str, username: str) -> None:
    """Add the token for user"""

    async_session = await create_session()
    async with async_session() as session:
        user = await select_users(username=username, is_admin=True, lazy_load=False)
        user = user[0]
        new_token = SessionToken(token=token, user_id=user.id)
        session.add(new_token)
        await session.commit()


async def remove_token(token: str) -> None:
    """Add the token for user"""

    async_session = await create_session()
    async with async_session() as session:
        query = delete(SessionToken).where(SessionToken.token == token)
        await session.execute(query)
        await session.commit()


async def exist_token(token: str) -> bool:
    async_session = await create_session()
    async with async_session() as session:
        query = select(SessionToken).where(SessionToken.token == token)
        it_exists = await session.scalar(exists(query).select())
        return it_exists
