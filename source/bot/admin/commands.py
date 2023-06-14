import os

from source.bot.config.tools.decorators import log
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import ContextTypes

from source.bot.admin.callback_data import *
from source.bot.admin.queries import insert_admin_or_update, admin_exists, delete_user
from source.bot.users.queries import select_users
from source.database.engine import create_session
from source.settings import get_logger

logger = get_logger(__name__)


@log(logger)
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run the admin menu"""

    keyboard = []

    async_session = await create_session()
    async with async_session() as session:
        result = await admin_exists(
            session=session,
            username=update.effective_user.username
        )
    if result:  # If admin exists
        context.user_data["is_admin"] = True
        keyboard.extend(
            [
                [InlineKeyboardButton(
                    text="\U0001F466\U0001F467 Пользователи", callback_data=str(USERS)
                )],
                [InlineKeyboardButton(
                    text="\U0001F4D4 База данных", callback_data=str(DATABASE)
                )]
            ]
        )
    else:  # If admin does not exist
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="\U0001F170 Создать администратора", callback_data=str(CREATE_ADMIN)
                ),
            ],
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="\U0000274C Выйти из меню", callback_data=str(STOP)
            ),
        ],
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Меню администартора"

    extra_text = context.user_data.get("extra_text")
    previous_message: Message = context.user_data.get("message")
    if previous_message:
        if extra_text:
            text = extra_text + "\n\n" + text
        if previous_message.text != text:
            if context.user_data.get("db_was_uploaded"):
                # Replace DB's message and the previous message

                await previous_message.delete()
                message = await context.bot.send_message(
                    chat_id=update.effective_message.chat_id,
                    text=text,
                    reply_markup=reply_markup
                )
            else:
                message = await previous_message.edit_text(
                    text=text,
                    reply_markup=reply_markup
                )
            context.user_data["message"] = message
            if extra_text:
                del context.user_data["extra_text"]
    else:
        message = await update.message.reply_text(
            text=text,
            reply_markup=reply_markup
        )
        context.user_data["message"] = message

    return ADMIN_ACTIONS


@log(logger)
async def create_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get("is_admin"):
        text = "Вы уже добавлены как администратор"
        await update.callback_query.answer()

        context.user_data["extra_text"] = text
        await admin_menu(update, context)
        return END

    text = "Введите секретный ключ"
    keyboard = [
        [
            InlineKeyboardButton(
                text="Отмена", callback_data=str(BACK)
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    message = await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
    )

    context.user_data["message"] = message

    return CHECK_ADMIN_KEY


@log(logger)
async def check_admin_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Checking the administrator key received from a text message"""

    admin_key = update.message.text
    await update.message.delete()

    if admin_key == os.environ.get("ADMIN_KEY"):
        async_session = await create_session()
        async with async_session() as session:
            username = update.effective_user.username
            chat_id = update.effective_message.chat_id
            admin_is_created = await insert_admin_or_update(
                session=session, username=username, chat_id=chat_id
            )

        if admin_is_created:
            extra_text = "\U0001F44D Вы добавлены как администратор"
        else:
            extra_text = "\U00002049 Не удалось добавить Вас как администартора"
    else:
        extra_text = "\U0001F44E Неправильный ключ"

    context.user_data["extra_text"] = extra_text

    await admin_menu(update, context)

    return END


@log(logger)
async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel adding yourself as an administrator"""

    await update.callback_query.answer()
    await admin_menu(update, context)
    return BACK


@log(logger)
async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displaying all users"""

    await update.callback_query.answer()

    users = await select_users(is_admin=False)
    if users:
        context.user_data["users"] = {
            f"user_id={callback_index}": user
            for callback_index, user in enumerate(users)
        }
        keyboard = [
            [
                InlineKeyboardButton(
                    text=user.username, callback_data=str(callback_index)
                )
            ]
            for callback_index, user in context.user_data["users"].items()
        ]
        keyboard.append(
            [
                InlineKeyboardButton(text="Назад", callback_data=str(BACK)),
            ]
        )

        text = "\U0001F466\U0001F467 Пользователи"
    else:
        text = "Вы еще не добавили пользователей"
        keyboard = [[
            InlineKeyboardButton(text="Назад", callback_data=str(BACK)),
        ]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    previous_message = context.user_data["message"]
    context.user_data["message"] = await previous_message.edit_text(
        text=text,
        reply_markup=reply_markup
    )
    return USER_ACTIONS


@log(logger)
async def user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displaying actions applied to users"""

    await update.callback_query.answer()
    user_id = update.callback_query.data
    user = context.user_data["users"][user_id]
    context.user_data["user"] = user
    keyboard = [
        [
            InlineKeyboardButton(text="Удалить", callback_data=str(REMOVE_USER))
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=str(BACK)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Действия над пользователем '{user.username}'"
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    return USER_ACTIONS


@log(logger)
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Removing the specific user"""

    await update.callback_query.answer()
    context.user_data["message"] = update.callback_query.message
    user = context.user_data["user"]
    async_session = await create_session()
    async with async_session() as session:
        user_delete = await delete_user(session=session, user=user)
    if user_delete:
        extra_text = f"Пользователь {user.username} удален"
    else:
        extra_text = f"Не удалось удалить пользователя {user.username}"
    context.user_data["extra_text"] = extra_text
    await admin_menu(update, context)
    return END


@log(logger)
async def database_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display DB actions"""

    keyboard = [
        [
            InlineKeyboardButton(
                text="\U00002B06 Загрузить базу данных", callback_data=str(DOWNLOAD_DB)
            ),
        ],
        [
            InlineKeyboardButton(
                text="\U00002B07 Выгрузить базу данных", callback_data=str(UPLOAD_DB)
            ),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=str(BACK)),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Действия с базой данных"
    previous_message = context.user_data["message"]
    context.user_data["message"] = await previous_message.edit_text(
        text=text,
        reply_markup=reply_markup
    )
    return DB_ACTIONS


@log(logger)
async def ask_about_download(
        update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """Ask about DB loading"""

    previous_message = context.user_data["message"]
    keyboard = [
        [
            InlineKeyboardButton(text="Назад", callback_data=str(BACK)),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Загрузите файл формата 'db_name.db'"
    context.user_data["message"] = await previous_message.edit_text(text=text, reply_markup=reply_markup)

    return DOWNLOAD_DB_ACTIONS


@log(logger)
async def download_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Download the database for administrator"""

    file = await update.effective_message.document.get_file()
    await file.download_to_drive("database.db")
    await update.message.delete()

    context.user_data["extra_text"] = "\U0001F44D База данных загружена"

    await admin_menu(update, context)
    return BACK


@log(logger)
async def upload_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Upload database for the administrator"""
    message = context.user_data["message"]
    chat_id = message.chat_id
    await context.bot.send_document(
        chat_id=chat_id, document="database.db", protect_content=True,
    )
    context.user_data["db_was_uploaded"] = True
    await admin_menu(update, context)
    return END


@log(logger)
async def clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clearing all user data before shutting down the function"""

    previous_message: Message = context.user_data["message"]
    await context.bot.send_message(
        chat_id=previous_message.chat_id,
        text="Время ожидания истекло"
    )
    context.user_data.clear()


@log(logger)
async def admin_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exit from the main conversation"""

    text = "Вы вышли из меню"
    await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=text,
    )
    context.user_data.clear()
    return END


@log(logger)
async def exit_from_nested_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exit from the second level"""

    return END
