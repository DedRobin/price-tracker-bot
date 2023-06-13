from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters, TypeHandler
)

from source.bot.admin.commands import admin_menu, database_menu, ask_about_download, download_db, upload_db, user_menu, \
    user_actions, remove_user, clear_data
from source.bot.admin.callback_data import *
from source.bot.admin.commands import admin_back
from source.bot.settings import TIMEOUT_CONVERSATION
from source.bot.admin.commands import create_admin, check_admin_key
from source.bot.commands import stop

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

create_admin_handler = ConversationHandler(
    # conversation_timeout=TIMEOUT_CONVERSATION,

    entry_points=[
        CallbackQueryHandler(create_admin, pattern=rf"^{CREATE_ADMIN}$")
    ],
    states={
        CHECK_ADMIN_KEY: [
            MessageHandler(filters.TEXT, check_admin_key),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
    ],
    map_to_parent={
        TIMEOUT: TIMEOUT
    }
)

users_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CallbackQueryHandler(user_menu, pattern=rf"^{USERS}$"),
    ],
    states={
        USER_ACTIONS: [
            CallbackQueryHandler(user_actions, pattern=r"^user_id=\d+$"),
            CallbackQueryHandler(remove_user, pattern=rf"^{REMOVE_USER}$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
    ],
    map_to_parent={
        BACK: ADMIN_ACTIONS,
        TIMEOUT: TIMEOUT
    }
)

download_db_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CallbackQueryHandler(ask_about_download, pattern=rf"^{DOWNLOAD_DB}$"),
    ],
    states={
        DOWNLOAD_DB_ACTIONS: [
            CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
            TypeHandler(filters.Update, download_db),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
    ],
    map_to_parent={
        END: BACK,
        TIMEOUT: TIMEOUT,
    }
)

database_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CallbackQueryHandler(database_menu, pattern=rf"^{DATABASE}$")
    ],
    states={
        DB_ACTIONS: [
            download_db_handler,
            CallbackQueryHandler(upload_db, pattern=rf"^{UPLOAD_DB}$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$")
    ],
    map_to_parent={
        BACK: ADMIN_ACTIONS,
        TIMEOUT: TIMEOUT
    }
)

admin_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CommandHandler("admin", admin_menu)
    ],
    states={
        ADMIN_ACTIONS: [
            create_admin_handler,
            users_handler,
            database_handler,
        ],
        TIMEOUT: [TypeHandler(filters.Update, clear_data)],
    },
    fallbacks=[
        CallbackQueryHandler(stop, pattern=rf"^{STOP}$"),
        CommandHandler("stop", stop),
    ],
)
