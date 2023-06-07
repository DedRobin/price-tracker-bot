from warnings import filterwarnings

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    TypeHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from source.bot.commands import (
    ask_about_download,
    back,
    download_db,
    get_help,
    start,
    stop,
    upload_db,
)
from source.bot.products.handlers import edit_product_handler, track_product_handler
from source.bot.settings import TIMEOUT_CONVERSATION
from source.bot.states import STATES
from source.bot.users.handlers import asks_handler

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

help_handler = CommandHandler("help", get_help)

upload_db_handler = CommandHandler("upload_db", upload_db)

download_db_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[CommandHandler("download_db", ask_about_download)],
    states={
        STATES["DOWNLOAD_DB"]: [
            CommandHandler("stop", stop),
            TypeHandler(filters.Update, download_db),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$"),
    ],
)

main_conversation_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CommandHandler("start", start),
    ],
    states={
        STATES["MENU"]: [
            track_product_handler,
            edit_product_handler,
            asks_handler,
        ],
    },
    fallbacks=[
        CommandHandler("stop", stop),
    ],
)

# admin_handler = CommandHandler("admin", admin)


