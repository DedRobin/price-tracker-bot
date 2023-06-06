from typing import Any, Sequence

from sqlalchemy import Row, RowMapping, delete, exists, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import AsyncSession

from source.database.engine import create_session
from source.database.models import Product, SessionToken, User, JoinedUser


async def delete_user(username: str) -> None:
    """Delete user from DB"""

    async_session = await create_session()
    async with async_session() as session:
        query = delete(User).where(User.username == username)
        await session.execute(query)
        await session.commit()


async def select_users(
        username: str = "", is_admin: bool = False, lazy_load: bool = True
) -> Sequence[Row | RowMapping | Any]:
    """Get all users"""

    async_session = await create_session()
    async with async_session() as session:
        query = select(User)

        if username:
            query = query.where(User.username == username)
        if is_admin:
            query = query.where(User.is_admin == is_admin)
        if not lazy_load:
            query = query.options(selectinload(User.products), selectinload(User.token))

        users = await session.scalars(query)
        users = users.all()
        return users


async def insert_user(session: AsyncSession, username: str, chat_id: int, is_admin: bool = False) -> None:
    """Add a new user"""

    user = User(username=username, chat_id=chat_id, is_admin=is_admin)
    session.add(user)
    await session.commit()


async def user_exists(username: str) -> bool:
    """Check user in DB"""

    async_session = await create_session()
    async with async_session() as session:
        query = select(User).where(User.username == username)
        user_in_db = await session.scalar(exists(query).select())
        return user_in_db


async def insert_joined_user(session: AsyncSession, username: str, chat_id: int,
                             is_admin: bool = False) -> Exception | None:
    """Add a joined user as the user"""

    try:
        user = User(username=username, chat_id=chat_id, is_admin=is_admin)
        session.add(user)
    except Exception as ex:
        return ex

    await session.commit()


async def remove_joined_user(session: AsyncSession, joined_user: JoinedUser) -> Exception | None:
    """Add a specific joined user"""

    try:
        await session.delete(joined_user)
    except Exception as ex:
        return ex
    await session.commit()
