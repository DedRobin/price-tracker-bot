import inspect
import pathlib
from aiohttp import ClientSession
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
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
            InlineKeyboardButton(text="Добавить товар", callback_data=str(STATES["TRACK_PRODUCT_CONV"])),
            InlineKeyboardButton(text="Список товаров", callback_data=str(STATES["EDIT_TRACK_PRODUCTS_CONV"])),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            reply_markup=reply_markup,
            text="Действия:",
        )
    return STATES["MENU"]


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    await context.bot.send_message(
        chat_id=data["chat_id"],
        text="Введите секретный ключ\n/cancel - отмена",
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
    text = "Вставьте URL-адрес товара для отслеживания\n/cancel - отмена"

    if context.user_data.get("call_again"):
        await update.message.reply_text(text=text)
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=text)
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

    link_is_correct = await check_link(link=link)
    if not link_is_correct:
        text = "Ваша ссылка некорректная"
        await message.reply_text(text=text)
        context.user_data["call_again"] = True
        await track_menu(update, context)
        return STATES["TRACK"]

    product_is_existed = await check_product_in_db(
        username=data["username"], link=link
    )
    if product_is_existed:
        text = "Такая ссылка уже отслеживается"
        await message.reply_text(text=text)
        context.user_data["call_again"] = True
        await track_menu(update, context)
        return STATES["TRACK"]
    else:
        async with ClientSession() as session:
            name, price = await onliner.parse(session=session, url=link)

        is_added = await add_product(
            username=data["username"], link=link, name=name, price=price
        )
        if is_added:
            text = "Товар был добавлен для отслеживается"
        else:
            text = "Не удалось добавить товар"

    # await context.bot.send_message(chat_id=data["chat_id"], text=text)
    await message.reply_text(text=text)

    # Back to the starting point
    await start(update, context)

    context.user_data.clear()

    return ConversationHandler.END


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        products = await get_user_products(username=data["username"])
        context.user_data["products"] = {
            f"id={callback_index}": product for callback_index, product in enumerate(products)
        }
        keyboard = [
            [
                InlineKeyboardButton(
                    text=product.get("name"), callback_data=str(callback_index)
                )
            ]
            for callback_index, product in context.user_data["products"].items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=data["chat_id"],
            reply_markup=reply_markup,
            text="Список отслеживаемых товаров\n/cancel - отмена",
        )
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

    keyboard = [
        [
            InlineKeyboardButton(
                text="Удалить", callback_data=f"id={product_id}|{STATES['REMOVE']}"
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(
        reply_markup=reply_markup,
        text=f"Выбран товар:\n{product['name']}\n/cancel - отмена действия",

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

    product_id = query.data.split("|")[0]  # "id={product_id}|{REMOVE}" -> "id={product_id}"
    product_id = int(product_id[3:])  # "id={product_id}" -> "{product_id}"

    await untrack_product(username=data["username"], product_id=product_id)
    await check_relationship(product_id=product_id)

    await query.edit_message_text(text="Товар удален")

    # Clear user_data
    context.user_data.clear()

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


async def upload_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upload database for administrators"""

    chat_ids = await get_chat_ids(is_admin=True)
    for chat_id in chat_ids:
        await context.bot.send_document(chat_id=chat_id, document="database.db", protect_content=True)


async def ask_about_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
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
        await context.bot.send_message(chat_id=data["chat_id"], text="Загрузите файл формата 'name.db'")

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
    await update.message.reply_text("База данных загружена")

    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )
    await update.message.reply_text("Бот остановлен")

    context.user_data.clear()
    return ConversationHandler.END
