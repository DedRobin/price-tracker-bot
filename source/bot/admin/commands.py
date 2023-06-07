import os

from source.bot.decorators import to_log
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import ContextTypes, ConversationHandler

from source.bot.admin.queries import insert_user_as_admin
from source.bot.states import STATES
from source.bot.users.queries import user_exists
from source.database.engine import create_session
from source.settings import get_logger

logger = get_logger(__name__)


@to_log(logger)
async def create_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_in_db = await user_exists(username=update.effective_user.username)

    if admin_in_db:
        text = "Вы уже добавлены как администартор"
        await update.message.reply_text(text=text)
        return ConversationHandler.END

    else:
        text = "Введите секретный ключ"
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Отмена", callback_data=str(STATES["NO_CREATE_ADMIN"])
                )
            ]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
    )

    context.user_data["message"] = message

    return STATES["CREATE_ADMIN"]


@to_log(logger)
async def check_admin_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Checking the administrator key received from a text message"""

    previous_message: Message = context.user_data["message"]
    admin_key = update.message.text
    await update.message.delete()

    async_session = await create_session()
    async with async_session() as session:
        if admin_key == os.environ.get("ADMIN_KEY"):
            username = update.effective_user.username
            chat_id = update.effective_message.chat_id
            admin_is_created = await insert_user_as_admin(
                session=session, username=username, chat_id=chat_id
            )

    if admin_is_created:
        text = "Вы добавлены как администратор"
    else:
        text = "Не удалось добавить Вас как администартора"

    await previous_message.edit_text(text=text)

    return ConversationHandler.END


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
