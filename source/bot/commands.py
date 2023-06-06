import inspect

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from source.bot.services import get_data_from_update
from source.bot.settings import TIMEOUT_CONV
from source.bot.states import STATES
from source.bot.users.queries import select_users
from source.bot.users.services import get_chat_ids
from source.settings import get_logger

logger = get_logger(__name__)

# Callback points
TRACK_PRODUCT_CONV, EDIT_TRACK_PRODUCTS_CONV = range(2)
TRACK_PRODUCT = 2
PRODUCT_LIST, REMOVE_PRODUCT = range(3, 5)
ADD_USER, DOWNLOAD_DB = range(5, 7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The starting point for entering the menu"""

    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text="Добавить товар", callback_data=str(STATES["TRACK_PRODUCT_CONV"])
            ),
            InlineKeyboardButton(
                text="Список товаров",
                callback_data=str(STATES["EDIT_TRACK_PRODUCTS_CONV"]),
            ),
        ]
    ]

    users = await select_users(username=data["username"])
    if users:
        user = users[0]

        # Additional option for the admin
        if user.is_admin:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Уведомления",
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
                chat_id=data["chat_id"],
                reply_markup=reply_markup,
            )
            context.user_data.clear()
        else:
            message = await context.bot.send_message(
                chat_id=data["chat_id"],
                reply_markup=reply_markup,
                text=text,
            )
        context.user_data["message_id"] = message.id

    return STATES["MENU"]


async def upload_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upload database for administrators"""

    chat_ids = await get_chat_ids(is_admin=True)
    for chat_id in chat_ids:
        await context.bot.send_document(
            chat_id=chat_id, document="database.db", protect_content=True
        )


async def ask_about_download(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """Ask about DB loading"""

    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    chat_ids = await get_chat_ids(is_admin=True)
    if data["chat_id"] in chat_ids:
        await context.bot.send_message(
            chat_id=data["chat_id"], text="Загрузите файл формата 'db_name.db'"
        )

        return STATES["DOWNLOAD_DB"]


async def download_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Download database for administrators"""

    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    file = await update.effective_message.document.get_file()
    await file.download_to_drive("database.db")
    await update.message.delete()
    await update.message.reply_text("База данных загружена")

    return ConversationHandler.END


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to the startpoint"""
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    query = update.callback_query
    await query.answer()
    context.user_data["back"] = True

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


async def cancel_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel adding yourself as an administrator"""

    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    query = update.callback_query
    await query.answer()
    await query.message.delete()

    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    await update.message.reply_text("Конец диалога")

    context.user_data.clear()
    return ConversationHandler.END


async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    text = f"""Чтобы запустить бота введите команду /start.
После этого ваш диалог с ботом будет активен {TIMEOUT_CONV} секунд.
Если бот перестал реагировать на нажатие кнопок или не отвечает на сообщения,то снова введите команду /start"""
    await update.message.reply_text(text=text)
