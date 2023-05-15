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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    reply_markup = ReplyKeyboardMarkup(
        [
            ["Добавить товар для отслеживания", "Показать отслеживаемые товары"],
            # ["Действие 3 в разработке", "Действие 4 в разработке"],
        ],
        one_time_keyboard=True,
    )
    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            reply_markup=reply_markup,
            text="Выберите действие.",
        )


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

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text="Вставьте URL-адрес товара для отслеживания\n/cancel - отмена",
        )
    return STATES["TRACK"]


async def track_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        link = update.message.text
        link_is_correct = await check_link(link=link)
        if not link_is_correct:
            await context.bot.send_message(
                chat_id=data["chat_id"],
                text="Ваша ссылка некорректная\nВставьте URL-адрес товара для отслеживания\n/skip_track - пропустить",
            )
            return STATES["TRACK"]
        # !!!
        product_is_existed = await check_product_in_db(
            username=data["username"], link=link
        )
        if product_is_existed:
            text = "Такая ссылка уже отслеживается"
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

        await context.bot.send_message(chat_id=data["chat_id"], text=text)
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
            callback_index: product for callback_index, product in enumerate(products)
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
    callback_index = int(query.data)
    product = context.user_data["products"][callback_index]
    product_id = product["id"]

    keyboard = [
        [
            InlineKeyboardButton(
                text="Удалить", callback_data=f"{product_id}.{STATES['REMOVE']}"
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(
        text=f"Выбран товар:\n{product['name']}\n/cancel - отмена действия"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup,
        text="Действия:",
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

    product_id = int(query.data.split(".")[0])

    await untrack_product(username=data["username"], product_id=product_id)
    await check_relationship(product_id=product_id)

    await context.bot.send_message(chat_id=data["chat_id"], text="Товар удален")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    await update.message.reply_text("Отмена")

    return ConversationHandler.END


async def upload_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upload database for administrators"""

    chat_ids = await get_chat_ids(is_admin=True)
    for chat_id in chat_ids:
        await context.bot.send_document(chat_id=chat_id, document="database.db", protect_content=True)


async def download_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download database for administrators"""

    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(
            *data.values(), command
        )
    )

    chat_ids = await get_chat_ids(is_admin=True)
    if data["chat_id"] in chat_ids:
        file = await update.effective_message.document.get_file()
        await file.download_to_drive("database.db")
        await context.bot.send_message(chat_id=data["chat_id"], text="База данных загружена")
