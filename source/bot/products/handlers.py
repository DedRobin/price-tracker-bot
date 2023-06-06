from warnings import filterwarnings

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from source.bot.commands import back, start
from source.bot.products.commands import (
    get_product_actions,
    remove_product,
    show_products,
    track_menu,
    track_product,
)
from source.bot.settings import TIMEOUT_CONV
from source.bot.states import STATES

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

track_product_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONV,
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
        CommandHandler("start", start),
    ],
)

edit_product_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONV,
    entry_points=[
        CallbackQueryHandler(
            show_products, pattern=rf"^{STATES['EDIT_TRACK_PRODUCTS_CONV']}$"
        )
    ],
    states={
        STATES["PRODUCT_LIST"]: [
            CallbackQueryHandler(get_product_actions, pattern=r"^id=\d+$"),
            CallbackQueryHandler(
                remove_product, pattern=rf"^id=\d+\|{STATES['REMOVE']}$"
            ),
        ],
    },
    fallbacks=[CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$")],
)
