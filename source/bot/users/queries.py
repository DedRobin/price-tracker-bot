from typing import Any, Sequence
from sqlalchemy import Row, RowMapping, delete, exists, select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from source.database.engine import create_session
from source.database.models import JoinedUser, Product, User


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


async def user_exists(username: str) -> bool:
    """Check user in DB"""

    async_session = await create_session()
    async with async_session() as session:
        query = select(User).where(User.username == username)
        user_in_db = await session.scalar(exists(query).select())
        return user_in_db


async def add_user_for_product(username: str, link: str) -> None:
    """Add user for product tracking"""

    async_session = await create_session()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.username == username))
        product = await session.scalar(
            select(Product)
            .where(Product.product_link == link)
            .options(selectinload(Product.users))
        )
        product.users.append(user)
        await session.commit()


async def remove_user_from_special_product(username: str, product_id: int) -> None:
    """Delete a special user from product tracking"""

    async_session = await create_session()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.username == username))
        product = await session.scalar(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.users))
        )
        product.users.remove(user)
        await session.commit()


async def insert_joined_user(
        session: AsyncSession, username: str, chat_id: int, is_admin: bool = False
) -> Exception | None:
    """Add a joined user as the user"""

    try:
        user = User(username=username, chat_id=chat_id, is_admin=is_admin)
        session.add(user)
    except Exception as ex:
        return ex

    await session.commit()


async def remove_joined_user(
        session: AsyncSession, joined_user: JoinedUser
) -> Exception | None:
    """Add a specific joined user"""

    try:
        await session.delete(joined_user)
    except Exception as ex:
        return ex
    await session.commit()


async def add_joined_user(session: AsyncSession, data: dict) -> bool:
    join_user = JoinedUser(username=data["username"], chat_id=data["chat_id"])
    session.add(join_user)
    await session.commit()
    return True


async def select_joined_users(session: AsyncSession) -> Sequence[Row | RowMapping | Any]:
    query = select(JoinedUser)
    result = await session.scalars(query)
    result = result.all()
    return result
