import os

from telegram import Update

from source.settings import get_logger

SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")

logger = get_logger(__name__)


async def get_data_from_update(update: Update) -> dict:
    data = {
        "first_name": update.effective_chat.first_name,
        "last_name": update.effective_chat.last_name,
        "username": update.effective_chat.username,
        "link": update.effective_chat.link,
        "chat_id": update.effective_chat.id,
    }

    return data
