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
    ask_about_download,
    back,
    cancel_add_user,
    download_db,
    get_help,
    start,
    stop,
    upload_db,
)
from source.bot.products.commands import (
    get_product_actions,
    remove_product,
    show_products,
    track_menu,
    track_product,
)
from source.bot.settings import TIMEOUT_CONV
from source.bot.states import STATES
from source.bot.users.commands import (
    add_user,
    apply_ask,
    ask_to_join,
    check_admin_key,
    delete_myself,
    get_joined_user_actions,
    refuse_ask,
    show_asks,
)

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

# Handlers
add_user_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONV,
    entry_points=[
        CommandHandler("add_user", add_user),
    ],
    states={
        STATES["ADD_USER"]: [
            MessageHandler(filters.TEXT, check_admin_key),
            CallbackQueryHandler(
                delete_myself, pattern=rf"^{STATES['DELETE_MYSELF']}$"
            ),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_add_user, pattern=rf"^{STATES['CANCEL_ADD_USER']}$")
    ],
)

help_handler = CommandHandler("help", get_help)

upload_db_handler = CommandHandler("upload_db", upload_db)

ask_to_join_handler = CommandHandler("ask_to_join", ask_to_join)

download_db_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONV,
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

notifications_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONV,
    entry_points=[CallbackQueryHandler(show_asks, pattern=rf"^{STATES['ASKS']}$")],
    states={
        STATES["ASK_ACTIONS"]: [
            CallbackQueryHandler(get_joined_user_actions, pattern=r"^ask_id=\d+$"),
            CallbackQueryHandler(apply_ask, pattern=rf"{STATES['APPLY_ASK']}$"),
            CallbackQueryHandler(refuse_ask, pattern=rf"{STATES['REFUSE_ASK']}$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$")],
)

main_conversation_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONV,
    entry_points=[
        CommandHandler("start", start),
    ],
    states={
        STATES["MENU"]: [
            track_product_handler,
            edit_product_handler,
            notifications_handler,
        ],
    },
    fallbacks=[
        CommandHandler("stop", stop),
    ],
)
