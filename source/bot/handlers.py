from warnings import filterwarnings

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
)
from telegram.warnings import PTBUserWarning

from source.bot.commands import (
    get_help,
    start,
    stop,
)
from source.bot.products.handlers import edit_product_handler, track_product_handler
from source.bot.admin.handlers import admin_handler
from source.bot.settings import TIMEOUT_CONVERSATION
from source.bot.callback_data import STATES
from source.bot.callback_data import STOP
from source.bot.users.handlers import asks_handler

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)
admin_handler = admin_handler

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
        CallbackQueryHandler(stop, pattern=rf"^{STOP}$"),
    ],
)

help_handler = CommandHandler("help", get_help)
