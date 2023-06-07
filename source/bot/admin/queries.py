from sqlalchemy.ext.asyncio.session import AsyncSession

from source.database.models import User
from source.settings import get_logger

logger = get_logger(__name__)


async def insert_user_as_admin(session: AsyncSession, username: str, chat_id: int) -> bool:
    """Add a new admin"""

    user = User(username=username, chat_id=chat_id, is_admin=True)
    try:
        session.add(user)
    except Exception as ex:
        logger.error(ex)
        return False
    await session.commit()
    return True
