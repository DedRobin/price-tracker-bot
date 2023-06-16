from warnings import filterwarnings

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters, TypeHandler,
)
from telegram.warnings import PTBUserWarning

from source.bot.products.commands import (
    back,
    start,
    stop,
    stop_nested,
    stop_silently,
    get_product_actions,
    remove_product,
    show_products,
    track_menu,
    track_product,
    get_help, stop_warning
)
from source.bot.users.handlers import asks_handler

from source.bot.config.settings import TIMEOUT_CONVERSATION
from source.bot.products.callback_data import STATES, STOP, TIMEOUT

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

track_product_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CallbackQueryHandler(track_menu, pattern=rf"^{STATES['TRACK_PRODUCT_CONV']}$")
    ],
    states={
        STATES["TRACK"]: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, track_product),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$"),
        CommandHandler("stop", stop_nested),
    ],
    map_to_parent={
        STOP: STOP
    }
)

edit_product_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CallbackQueryHandler(
            show_products, pattern=rf"^{STATES['EDIT_TRACK_PRODUCTS_CONV']}$"
        )
    ],
    states={
        STATES["PRODUCT_LIST"]: [
            CallbackQueryHandler(get_product_actions, pattern=r"^id=\d+$"),
            CallbackQueryHandler(remove_product, pattern=rf"^id=\d+\|{STATES['REMOVE']}$"),
        ],
    },
    fallbacks=[
        CommandHandler("stop", stop_nested),
        CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$")
    ],
    map_to_parent={
        STOP: STOP
    }
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
        TIMEOUT: [TypeHandler(filters.Update, stop_silently)],
        STOP: [CommandHandler("start", start)]
    },
    fallbacks=[
        CommandHandler("start", stop_warning),
        CommandHandler("stop", stop),
        CallbackQueryHandler(stop, pattern=rf"^{STOP}$"),
    ],
)

help_handler = CommandHandler("help", get_help)
