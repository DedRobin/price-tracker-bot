from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select, exists
from source.database.models import User
from source.settings import get_logger
logger = get_logger(__name__)


async def insert_admin_or_update(session: AsyncSession, username: str, chat_id: int) -> bool:
    """Add a new admin or update it"""

    query = select(User).where(User.username == username)
    user = await session.scalar(query)
    if user:
        user.is_admin = True
        await session.commit()
        return True
    else:
        user = User(username=username, chat_id=chat_id, is_admin=True)
    try:
        session.add(user)
        await session.commit()
    except Exception as ex:
        logger.error(ex)
        return False
    return True


async def admin_exists(session: AsyncSession, username: str) -> None:
    """Check if current user is an admin"""

    query = exists(User).where(User.username == username, User.is_admin == True).select()
    result = await session.scalar(query)
    return result
