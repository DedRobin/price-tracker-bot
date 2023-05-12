from warnings import filterwarnings

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from source.bot.commands import (
    get_product_actions,
    remove_product,
    show_products,
    skip_track,
    start,
    add_user,
    check_admin_key,
    track_menu,
    track_product,
    cancel
)
from source.bot.states import STATES

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

# HANDLERS
start_handler = CommandHandler("start", start)
add_user_handler = ConversationHandler(
    entry_points=[
        CommandHandler("add_user", add_user),
    ],
    states={
        STATES["ADD_USER"]: [
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT, check_admin_key),
        ]
    },
    fallbacks=[
        CommandHandler("cancel", start)
    ],
)

track_product_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Добавить товар для отслеживания$"), track_menu)
    ],
    states={
        STATES["TRACK"]: [
            CommandHandler("skip_track", skip_track),
            MessageHandler(filters.TEXT, track_product),
        ]
    },
    fallbacks=[
        CommandHandler("cancel", start),
    ],
)

edit_product_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Показать отслеживаемые товары$"), show_products)
    ],
    states={
        STATES["PRODUCT_LIST"]: [
            CallbackQueryHandler(get_product_actions, pattern=r"^\d+$"),
            CallbackQueryHandler(remove_product, pattern=rf"^\d+\.{STATES['REMOVE']}$"),
        ]
    },
    fallbacks=[CommandHandler("cancel", start)],
)
