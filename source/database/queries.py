from typing import Any, Sequence

from sqlalchemy import Row, RowMapping, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from source.database.models import User


async def select_admins(session: AsyncSession) -> Sequence[Row | RowMapping | Any]:
    """Get admins"""

    query = select(User).where(User.is_admin == True)
    result = await session.scalars(query)
    admins = result.all()
    return admins
