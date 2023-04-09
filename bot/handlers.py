from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

from bot.commands import start, track_menu, track_product, show_products, get_product_actions, remove_product, \
    skip_track
from bot.states import STATES

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# HANDLERS
start_handler = CommandHandler("start", start)

track_product_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r"^Добавить товар для отслеживания$"), track_menu)],
    states={
        STATES["TRACK"]: [
            CommandHandler("skip_track", skip_track),
            MessageHandler(filters.TEXT, track_product)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", start),
    ],
)

edit_product_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r"^Показать отслеживаемые товары$"), show_products)],
    states={
        STATES["SHOW"]: [
            CallbackQueryHandler(get_product_actions, pattern=r"^id=\d+$"),
            CallbackQueryHandler(remove_product, pattern=rf"^\d+\.{STATES['REMOVE']}$"),
        ]
    },
    fallbacks=[CommandHandler("cancel", start)],
)
