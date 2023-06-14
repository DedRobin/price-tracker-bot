from aiohttp import ClientSession
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from source.bot.users.queries import select_users
from source.bot.users.services import get_joined_users
from source.database.engine import create_session
from source.bot.config.tools.decorators import log
from source.bot.config.settings import TIMEOUT_CONVERSATION
from source.bot.products.services import (
    add_product,
    check_link,
    check_product_in_db,
    check_relationship,
    get_user_products,
    untrack_product,
)
from source.bot.products.callback_data import STATES, STOP
from source.parsers import onliner
from source.settings import get_logger

logger = get_logger(__name__)


@log(logger)
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


@log(logger)
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to the startpoint"""

    query = update.callback_query
    await query.answer()
    context.user_data["back"] = True

    # Back to the starting point
    await start(update, context)

    return ConversationHandler.END


@log(logger)
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exit from some menu"""
    text = "Вы вышли из меню"
    await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=text
    )

    context.user_data.clear()
    return ConversationHandler.END


@log(logger)
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


@log(logger)
async def track_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    link = message.text

    product_is_existed = await check_product_in_db(update.effective_chat.username, link=link)
    link_is_correct = await check_link(link=link)
    if product_is_existed or not link_is_correct:
        text = "Ошибка"
        error_emoji = "\U00002757"
        if product_is_existed:
            context.user_data["text"] = f"{error_emoji} Такая ссылка уже отслеживается\n"
        elif not link_is_correct:
            context.user_data["text"] = f"{error_emoji} Ваша ссылка некорректная\n"

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


@log(logger)
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


@log(logger)
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


@log(logger)
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


@log(logger)
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the help text to the chat"""

    text = f"""Чтобы запустить бота введите команду /start.
После этого ваш диалог с ботом будет активен {TIMEOUT_CONVERSATION} секунд.
Если бот перестал реагировать на нажатие кнопок или не отвечает на сообщения,то снова введите команду /start"""
    await update.message.reply_text(text=text)
