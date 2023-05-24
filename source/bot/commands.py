import inspect

from aiohttp import ClientSession
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from source.bot.services import (
    add_product,
    check_link,
    check_product_in_db,
    check_relationship,
    get_chat_ids,
    get_data_from_update,
    get_user_products,
    post_user,
    untrack_product,
)
from source.bot.states import STATES
from source.parsers import onliner
from source.settings import enable_logger
from source.bot.settings import TIMEOUT_CONV

logger = enable_logger(__name__)

# Callback points
TRACK_PRODUCT_CONV, EDIT_TRACK_PRODUCTS_CONV = range(2)
TRACK_PRODUCT = 2
PRODUCT_LIST, REMOVE_PRODUCT = range(3, 5)
ADD_USER, DOWNLOAD_DB = range(5, 7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
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


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
                text="Отмена", callback_data=str(STATES["CANCEL_ADD_USER"])
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=data["chat_id"],
        text="Введите секретный ключ",
        reply_markup=reply_markup,
    )
    return STATES["ADD_USER"]


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

    user_created = await post_user(
        admin_key=admin_key, username=data["username"], chat_id=data["chat_id"]
    )
    if user_created:
        text = "Пользователь добавлен"
    else:
        text = "Не удалось добавить пользователя"

    await context.bot.send_message(chat_id=data["chat_id"], text=text)
    return ConversationHandler.END


async def track_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    emoji = "\U0001F7E1"
    text = f"{emoji} Вставьте URL-адрес товара для отслеживания"
    keyboard = [[InlineKeyboardButton(text="Назад", callback_data=str(STATES["BACK"]))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get("call_again"):
        text = context.user_data["text"] + "\n" + text
        await context.bot.edit_message_text(
            text=text,
            message_id=context.user_data["message_id"],
            chat_id=data["chat_id"],
            reply_markup=reply_markup,
        )
    else:
        query = update.callback_query
        await query.answer()
        # context.user_data["message_id"] = update.effective_message.id
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    return STATES["TRACK"]


async def track_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    message = update.message
    link = message.text

    product_is_existed = await check_product_in_db(username=data["username"], link=link)
    link_is_correct = await check_link(link=link)
    if product_is_existed or not link_is_correct:
        text = "Ошибка"
        error_emoji = "\U00002757"
        if product_is_existed:
            context.user_data["text"] = f"{error_emoji} Такая ссылка уже отслеживается"
        elif not link_is_correct:
            context.user_data["text"] = f"{error_emoji} Ваша ссылка некорректная"

        context.user_data["call_again"] = True

        await message.delete()
        await track_menu(update, context)

        return STATES["TRACK"]

    else:
        async with ClientSession() as session:
            name, price = await onliner.parse(session=session, url=link)

        is_added = await add_product(
            username=data["username"], link=link, name=name, price=price
        )
        if is_added:
            text = "\U0001F44D Товар был добавлен для отслеживается"
        else:
            text = "\U00002757 Не удалось добавить товар"
        await update.message.delete()

        context.user_data["text"] = text
        context.user_data["back"] = True

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    query = update.callback_query
    await query.answer()

    products = await get_user_products(username=data["username"])
    context.user_data["products"] = {
        f"id={callback_index}": product
        for callback_index, product in enumerate(products)
    }
    keyboard = [
        [
            InlineKeyboardButton(
                text=product.get("name"), callback_data=str(callback_index)
            )
        ]
        for callback_index, product in context.user_data["products"].items()
    ]
    keyboard.append(
        [InlineKeyboardButton(text="Назад", callback_data=str(STATES["BACK"]))]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    list_emoji = "\U0001F4DC"
    text = f"{list_emoji} Список отслеживаемых товаров"

    await query.edit_message_text(text=text, reply_markup=reply_markup)

    return STATES["PRODUCT_LIST"]


async def get_product_actions(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    query = update.callback_query
    callback_index = query.data
    product = context.user_data["products"][callback_index]
    product_id = product["id"]
    emoji = "\U0001F7E2"

    keyboard = [
        [
            InlineKeyboardButton(
                text="Ссылка",
                url=product["link"]
            ),
        ],
        [
            InlineKeyboardButton(
                text="Удалить", callback_data=f"id={product_id}|{STATES['REMOVE']}"
            ),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=f"{STATES['BACK']}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(
        reply_markup=reply_markup,
        text=f"Выбран товар:\n\n{emoji} {product['name']}",
    )

    return STATES["PRODUCT_LIST"]


async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    query = update.callback_query
    await query.answer()

    product_id = query.data.split("|")[
        0
    ]  # "id={product_id}|{REMOVE}" -> "id={product_id}"
    product_id = int(product_id[3:])  # "id={product_id}" -> "{product_id}"

    await untrack_product(username=data["username"], product_id=product_id)

    # If relationship does not exist it is deleted
    await check_relationship(product_id=product_id)

    # Set extra text for next starting menu
    remove_emoji = "\U0001F534"
    context.user_data["text"] = f"{remove_emoji} Товар удален"
    context.user_data["back"] = True

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


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
        message = await context.bot.send_message(
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
