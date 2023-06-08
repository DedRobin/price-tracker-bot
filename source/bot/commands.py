from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from source.bot.decorators import to_log
from source.bot.settings import TIMEOUT_CONVERSATION
from source.bot.callback_data import STATES
from source.bot.callback_data import STOP
from source.bot.users.queries import select_users
from source.bot.users.services import get_joined_users
from source.settings import get_logger
from source.database.engine import create_session

logger = get_logger(__name__)


@to_log(logger)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The starting point for entering the menu"""

    keyboard = [
        [
            InlineKeyboardButton(
                text="Добавить товар", callback_data=str(STATES["TRACK_PRODUCT_CONV"])
            ),
            InlineKeyboardButton(
                text="Список товаров",
                callback_data=str(STATES["EDIT_TRACK_PRODUCTS_CONV"]),
            ),
        ],
        [
            InlineKeyboardButton(
                text="\U0000274C Выйти из меню", callback_data=str(STOP)
            ),
        ],
    ]

    # Count rows for JoinedUsers
    async_session = await create_session()
    async with async_session() as session:
        joined_users = await get_joined_users(session=session)
        len_joined_users = len(joined_users)

    users = await select_users(
        username=update.effective_user.username
    )
    if users:
        user = users[0]

        # Additional option for the admin
        if user.is_admin:
            text_for_button = "Уведомления"
            if len_joined_users:
                text_for_button += " ({0})".format(len_joined_users)
            keyboard.insert(
                1,
                [
                    InlineKeyboardButton(
                        text=text_for_button,
                        callback_data=str(STATES["ASKS"]),
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Действия:"

        go_back = context.user_data.get("back")
        if go_back:
            extra_text = context.user_data.get("text")
            if extra_text:
                text = extra_text + "\n\n" + text

            message = await context.bot.edit_message_text(
                text=text,
                message_id=context.user_data["message_id"],
                chat_id=update.effective_message.chat_id,
                reply_markup=reply_markup,
            )
            context.user_data.clear()
        else:
            message = await context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                reply_markup=reply_markup,
                text=text,
            )
        context.user_data["message_id"] = message.id

    return STATES["MENU"]


@to_log(logger)
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to the startpoint"""

    query = update.callback_query
    await query.answer()
    context.user_data["back"] = True

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


@to_log(logger)
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exit from some menu"""

    text = "Вы вышли из меню"
    await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=text
    )

    context.user_data.clear()
    return ConversationHandler.END


@to_log(logger)
async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the help text to the chat"""

    text = f"""Чтобы запустить бота введите команду /start.
После этого ваш диалог с ботом будет активен {TIMEOUT_CONVERSATION} секунд.
Если бот перестал реагировать на нажатие кнопок или не отвечает на сообщения,то снова введите команду /start"""
    await update.message.reply_text(text=text)
