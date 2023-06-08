from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters, TypeHandler,
)

from source.bot.admin.commands import admin_menu, database_menu, ask_about_download, download_db, upload_db
from source.bot.admin.callback_data import *
from source.bot.admin.commands import admin_back
from source.bot.settings import TIMEOUT_CONVERSATION
from source.bot.admin.commands import create_admin, check_admin_key
from source.bot.commands import stop

create_admin_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(create_admin, pattern=rf"^{CREATE_ADMIN}$")
    ],
    states={
        CHECK_ADMIN_KEY: [
            MessageHandler(filters.TEXT, check_admin_key),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{GO_BACK}$"),
    ]
)

download_db_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(ask_about_download, pattern=rf"^{DOWNLOAD_DB}$"),
    ],
    states={
        DOWNLOAD_DB_ACTIONS: [
            TypeHandler(filters.Update, download_db),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{GO_BACK}$"),
    ],
    map_to_parent={
        GO_BACK: GO_BACK
    }
)

database_handler = ConversationHandler(
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
        CallbackQueryHandler(admin_back, pattern=rf"^{GO_BACK}$")
    ],
    map_to_parent={
        GO_BACK: ADMIN_ACTIONS
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
            database_handler,
        ],
    },
    fallbacks=[
        CallbackQueryHandler(stop, pattern=rf"^{STOP}$"),
        CommandHandler("stop", stop),
    ]
)
