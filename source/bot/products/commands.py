from aiohttp import ClientSession
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from source.bot.decorators import to_log
from source.bot.commands import start
from source.bot.products.services import (
    add_product,
    check_link,
    check_product_in_db,
    check_relationship,
    get_user_products,
    untrack_product,
)
from source.bot.callback_data import STATES
from source.parsers import onliner
from source.settings import get_logger

logger = get_logger(__name__)


@to_log(logger)
async def track_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    emoji = "\U0001F7E1"
    text = f"{emoji} Вставьте URL-адрес товара для отслеживания"
    keyboard = [[InlineKeyboardButton(text="Назад", callback_data=str(STATES["BACK"]))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if context.user_data.get("call_again"):
        text = context.user_data["text"] + "\n" + text
        await context.bot.edit_message_text(
            text=text,
            message_id=context.user_data["message_id"],
            chat_id=update.effective_chat.id,
            reply_markup=reply_markup,
        )
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    return STATES["TRACK"]


@to_log(logger)
async def track_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    link = message.text

    product_is_existed = await check_product_in_db(update.effective_chat.username, link=link)
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

        if not name and not price:
            logger.error(f"Something is wrong.\nThe product={link}")
        else:
            is_added = await add_product(
                username=update.effective_chat.username,
                link=link,
                name=name,
                price=price
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


@to_log(logger)
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    products = await get_user_products(username=update.effective_chat.username)
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


@to_log(logger)
async def get_product_actions(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    callback_index = query.data
    product = context.user_data["products"][callback_index]
    product_id = product["id"]
    emoji = "\U0001F7E2"

    keyboard = [
        [
            InlineKeyboardButton(text="Ссылка", url=product["link"]),
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


@to_log(logger)
async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # "id={product_id}|{REMOVE}" -> "id={product_id}"
    product_id = query.data.split("|")[0]

    # "id={product_id}" -> "{product_id}"
    product_id = int(product_id[3:])

    await untrack_product(username=update.effective_chat.username, product_id=product_id)

    # If relationship does not exist it is deleted
    await check_relationship(product_id=product_id)

    # Set extra text for next starting menu
    remove_emoji = "\U0001F534"
    context.user_data["text"] = f"{remove_emoji} Товар удален"
    context.user_data["back"] = True

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END
