import inspect
import os

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.settings import get_logger
from bot.states import STATES
from bot.services import get_data_from_update, get_chat_ids, check_link, check_product_in_db, add_product, \
    get_user_products, untrack_product
from parsers.services import parse_onliner

# from bot.queries import write_product, checking_product_in_db, get_user_products, get_product, untrack_product, \
#     checking_correctness_link, get_chat_ids


logger = get_logger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    reply_markup = ReplyKeyboardMarkup(
        [
            ["Добавить товар для отслеживания", "Показать отслеживаемые товары"],
            # ["Действие 3 в разработке", "Действие 4 в разработке"],
        ],
        one_time_keyboard=True
    )
    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            reply_markup=reply_markup,
            text="Выберите действие."
        )


async def track_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text="Вставьте URL-адрес товара для отслеживания\n/skip_track - пропустить"
        )
    return STATES["TRACK"]


async def skip_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    await update.message.reply_text(
        "Вы отменили действие"
    )
    return ConversationHandler.END


async def track_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        link = update.message.text
        link_is_correct = await check_link(link=link)
        if not link_is_correct:
            await context.bot.send_message(
                chat_id=data["chat_id"],
                text="Ваша ссылка некорректная\nВставьте URL-адрес товара для отслеживания\n/skip_track - пропустить"
            )
            return STATES["TRACK"]
        # !!!
        product_is_existed = await check_product_in_db(
            username=data["username"],
            link=link
        )
        if product_is_existed:
            text = "Такая ссылка уже отслеживается"
        else:
            name, price = await parse_onliner(url=link)

            status = await add_product(username=data["username"], link=link, name=name, current_price=price)
            if status == 201:
                text = f"Товар '{name}' был добавлен для отслеживается"
            else:
                text = f"Не удалось добавить товар (Ошибка {status})"

        await context.bot.send_message(
            chat_id=data["chat_id"],
            text=text
        )
        return ConversationHandler.END


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    chat_ids = await get_chat_ids()

    if data["chat_id"] in chat_ids:
        products = await get_user_products(username=data["username"])
        context.user_data["products"] = {index: product for index, product in enumerate(products)}
        keyboard = [
            [
                InlineKeyboardButton(
                    text=product.get("name"),
                    callback_data=index)
            ]
            for index, product in context.user_data["products"].items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=data["chat_id"],
            reply_markup=reply_markup,
            text="Список отслеживаемых товаров"
        )
    return STATES["PRODUCT_LIST"]


async def get_product_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    query = update.callback_query
    index = int(query.data)
    product = context.user_data["products"][index]
    product_id = product["id"]

    keyboard = [
        [
            InlineKeyboardButton(text="Удалить", callback_data=f"{product_id}.{STATES['REMOVE']}"),

        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(text=f"Выбран товар:\n{product['name']}\n/cancel - отмена действия")
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
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    query = update.callback_query
    await query.answer()

    product_id = query.data.split(".")[0]
    status = await untrack_product(username=data["username"], product_id=int(product_id))
    if status == 200:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text="Товар удален",
        )
    else:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text=f"Что-то пошло не так (Ошибка {status})",
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = await get_data_from_update(update)
    command = inspect.currentframe().f_code.co_name
    logger.info(
        "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'".format(*data.values(), command))

    await update.message.reply_text(
        "Вы закончили диалог"
    )

    return ConversationHandler.END
