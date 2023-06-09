from typing import Any, Sequence
from sqlalchemy import Row, RowMapping
from sqlalchemy.ext.asyncio.session import AsyncSession

from source.bot.users.queries import (
    insert_joined_user,
    remove_joined_user,
    select_users, select_joined_users,
)
from source.database.models import UnregisteredUser
from source.settings import get_logger

logger = get_logger(__name__)


async def get_chat_ids(is_admin: bool = False) -> list:
    """Get all chat IDs"""

    users = await select_users(
        is_admin=is_admin,
    )

    logger.info("Get chat IDs")
    chat_ids = [user.chat_id for user in users]
    return chat_ids


async def get_joined_users(session: AsyncSession) -> Sequence[Row | RowMapping | Any]:
    """Select the joined user"""

    result = await select_joined_users(session=session)
    return result


async def post_joined_user(
        session: AsyncSession, username: str, chat_id: int
) -> Exception | None:
    """Add the joined user"""

    error = await insert_joined_user(
        session=session, username=username, chat_id=chat_id, is_admin=False
    )
    return error if error else None


async def delete_joined_user(
        session: AsyncSession, joined_user: UnregisteredUser
) -> Exception | None:
    """Delete the joined user"""

    error = await remove_joined_user(session=session, joined_user=joined_user)
    return error if error else None
