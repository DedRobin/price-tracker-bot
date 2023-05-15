from warnings import filterwarnings

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from source.bot.commands import (
    add_user,
    cancel,
    check_admin_key,
    get_product_actions,
    remove_product,
    show_products,
    start,
    track_menu,
    track_product,
    upload_db,
    download_db,
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
    fallbacks=[CommandHandler("cancel", cancel)],
)

track_product_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(r"^Добавить товар для отслеживания$"), track_menu)
    ],
    states={
        STATES["TRACK"]: [
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT, track_product),
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
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
    fallbacks=[CommandHandler("cancel", cancel)],
)

upload_db_handler = CommandHandler("upload_db", upload_db)
download_db_handler = TypeHandler(filters.Update, download_db)
