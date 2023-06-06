import inspect

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from source.bot.commands import start
from source.bot.services import get_data_from_update
from source.bot.states import STATES
from source.bot.users.queries import (
    add_joined_user,
    delete_user,
    get_joined_users,
    user_exists,
)
from source.bot.users.services import delete_joined_user, post_admin, post_joined_user
from source.database.engine import create_session
from source.settings import get_logger

logger = get_logger(__name__)


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    user_in_db = await user_exists(username=data["username"])
    if user_in_db:
        text = "Вы уже добавлены как пользователь. Хотите удалить себя?"
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Да", callback_data=str(STATES["DELETE_MYSELF"])
                ),
                InlineKeyboardButton(
                    text="Нет", callback_data=str(STATES["CANCEL_ADD_USER"])
                ),
            ]
        ]
    else:
        text = "Введите секретный ключ"
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Отмена", callback_data=str(STATES["CANCEL_ADD_USER"])
                )
            ]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.send_message(
        chat_id=data["chat_id"],
        text=text,
        reply_markup=reply_markup,
    )

    context.user_data["message_id"] = message.id

    return STATES["ADD_USER"]


async def delete_myself(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    await delete_user(username=data["username"])

    await context.bot.edit_message_text(
        chat_id=data["chat_id"],
        message_id=context.user_data["message_id"],
        text="Вы были удалены",
    )

    return ConversationHandler.END


async def check_admin_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    admin_key = update.message.text
    await update.message.delete()

    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    async_session = await create_session()
    async with async_session() as session:
        user_created = await post_admin(
            session=session,
            admin_key=admin_key,
            username=data["username"],
            chat_id=data["chat_id"],
        )
    if user_created:
        text = "Пользователь добавлен"
    else:
        text = "Не удалось добавить пользователя"

    await context.bot.send_message(chat_id=data["chat_id"], text=text)
    return ConversationHandler.END


async def ask_to_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    user_data = {"username": data["username"], "chat_id": data["chat_id"]}

    async_session = await create_session()
    async with async_session() as session:
        user_added = await add_joined_user(session=session, data=user_data)
    if user_added:
        await update.message.reply_text(
            "Отправлено уведомление администратору, ожидайте"
        )
    else:
        await update.message.reply_text("Не удалось отправить уведомление")


async def show_asks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    query = update.callback_query
    await query.answer()
    joined_users = await get_joined_users()
    context.user_data["joined_users"] = {
        f"ask_id={callback_index}": joined_user
        for callback_index, joined_user in enumerate(joined_users)
    }
    keyboard = [
        [InlineKeyboardButton(text=joined_user.username, callback_data=callback_index)]
        for callback_index, joined_user in context.user_data["joined_users"].items()
    ]
    keyboard.append(
        [InlineKeyboardButton(text="Назад", callback_data=str(STATES["BACK"]))]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Уведомления", reply_markup=reply_markup)
    return STATES["ASK_ACTIONS"]


async def get_joined_user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    keyboard = [
        [
            InlineKeyboardButton(
                text="Добавить", callback_data=f"{STATES['APPLY_ASK']}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Отказать", callback_data=f"{STATES['REFUSE_ASK']}"
            ),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"{STATES['BACK']}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Clear the extra data
    context.user_data["joined_user"] = context.user_data["joined_users"][callback_data]
    del context.user_data["joined_users"]

    user = context.user_data["joined_user"]
    text = f"Выберите действие для пользователя {user.username}"

    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return STATES["ASK_ACTIONS"]


async def apply_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    query = update.callback_query
    await query.answer()
    username = context.user_data["joined_user"].username
    chat_id = context.user_data["joined_user"].chat_id
    async_session = await create_session()
    async with async_session() as session:
        error = await post_joined_user(
            session=session, username=username, chat_id=chat_id
        )

    # Set extra text for next starting menu
    apply_emoji = "\U0001F44D"
    if error:
        context.user_data["text"] = "Ошибка при добавлении пользователя"
        logger.error(error)
    else:
        context.user_data["text"] = f"{apply_emoji} {username} принят"
    context.user_data["back"] = True

    # Delete the user form the JoinedUser table
    joined_user = context.user_data["joined_user"]
    delete_error = await delete_joined_user(session=session, joined_user=joined_user)
    if delete_error:
        context.user_data["text"] = "Ошибка при удалении пользователя"
        logger.error(delete_error)

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


async def refuse_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    query = update.callback_query
    await query.answer()
    joined_user = context.user_data["joined_user"]
    async_session = await create_session()
    async with async_session() as session:
        error = await delete_joined_user(session=session, joined_user=joined_user)

    # Set extra text for next starting menu
    remove_emoji = "\U0001F534"
    if error:
        context.user_data["text"] = "Ошибка при удалении пользователя"
        logger.error(error)
    else:
        context.user_data["text"] = f"{remove_emoji} {joined_user.username} отклонен"
    context.user_data["back"] = True

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END
