import os

from telegram import Bot

from source.database.engine import create_session
from source.database.queries import select_admins

bot = Bot(token=os.environ.get("BOT_TOKEN"))


async def send_notification_to_admin(ip_address) -> None:
    """Sending a warning notification that someone is trying to log in"""

    text = f"Кто-пытался пытается зайти в панель администратора (IP={ip_address})"
    async_session = await create_session()
    async with async_session() as session:
        admins = await select_admins(session=session)
    if admins:
        for admin in admins:
            await bot.send_message(chat_id=admin.chat_id, text=text)
