from warnings import filterwarnings

from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, TypeHandler, filters
from telegram.warnings import PTBUserWarning

from source.bot.admin.callback_data import *
from source.bot.admin.commands import (
    admin_back,
    admin_menu,
    admin_stop,
    admin_stop_silently,
    admin_stop_warning,
    ask_about_download,
    check_admin_key,
    create_admin,
    database_menu,
    download_db,
    end_current_conv,
    remove_user,
    stop_nested,
    upload_db,
    user_actions,
    user_menu,
)
from source.bot.config.settings import TIMEOUT_CONVERSATION

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

create_admin_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[CallbackQueryHandler(create_admin, pattern=rf"^{CREATE_ADMIN}$")],
    states={
        CHECK_ADMIN_KEY: [
            MessageHandler(filters.TEXT, check_admin_key),
        ],
        TIMEOUT: [TypeHandler(filters.Update, end_current_conv)],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
        CommandHandler("stop", stop_nested),
    ],
    map_to_parent={STOP: STOP},
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
        TIMEOUT: [TypeHandler(filters.Update, end_current_conv)],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
        CommandHandler("stop", stop_nested),
    ],
    map_to_parent={
        BACK: ADMIN_ACTIONS,
        STOP: STOP,
    },
)

download_db_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CallbackQueryHandler(ask_about_download, pattern=rf"^{DOWNLOAD_DB}$"),
    ],
    states={
        DOWNLOAD_DB_ACTIONS: [
            CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
            CommandHandler("stop", stop_nested),
            TypeHandler(filters.Update, download_db),
        ],
        TIMEOUT: [TypeHandler(filters.Update, end_current_conv)],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
    ],
    map_to_parent={
        BACK: BACK,
        STOP: STOP,
    },
)

database_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[CallbackQueryHandler(database_menu, pattern=rf"^{DATABASE}$")],
    states={
        DB_ACTIONS: [
            download_db_handler,
            CallbackQueryHandler(upload_db, pattern=rf"^{UPLOAD_DB}$"),
        ],
        TIMEOUT: [TypeHandler(filters.Update, end_current_conv)],
    },
    fallbacks=[
        CallbackQueryHandler(admin_back, pattern=rf"^{BACK}$"),
        CommandHandler("stop", stop_nested),
    ],
    map_to_parent={
        BACK: ADMIN_ACTIONS,
        END: ADMIN_ACTIONS,
        STOP: STOP,
    },
)

admin_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[CommandHandler("admin", admin_menu)],
    states={
        ADMIN_ACTIONS: [
            create_admin_handler,
            users_handler,
            database_handler,
        ],
        TIMEOUT: [TypeHandler(filters.Update, admin_stop_silently)],
        STOP: [CommandHandler("admin", admin_menu)],
    },
    fallbacks=[
        CommandHandler("admin", admin_stop_warning),
        CallbackQueryHandler(admin_stop, pattern=rf"^{STOP}$"),
        CommandHandler("stop", admin_stop),
    ],
)
