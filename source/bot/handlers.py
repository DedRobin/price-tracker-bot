from warnings import filterwarnings

from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, TypeHandler, filters
from telegram.warnings import PTBUserWarning

from source.bot.commands import (
    add_user,
    ask_about_download,
    back,
    cancel_add_user,
    check_admin_key,
    download_db,
    get_product_actions,
    remove_product,
    show_products,
    start,
    stop,
    track_menu,
    track_product,
    upload_db,
)
from source.bot.states import STATES

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

# Handlers
# start_handler = CommandHandler("start", start)
add_user_handler = ConversationHandler(  # !!!
    entry_points=[
        CommandHandler("add_user", add_user),
    ],
    states={
        STATES["ADD_USER"]: [
            CommandHandler("back", back),
            MessageHandler(filters.TEXT, check_admin_key),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(cancel_add_user, pattern=rf"^{STATES['CANCEL_ADD_USER']}$")
    ],
)

track_product_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(track_menu, pattern=rf"^{STATES['TRACK_PRODUCT_CONV']}$")
    ],
    states={
        STATES["TRACK"]: [
            MessageHandler(filters.TEXT, track_product),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$"),
    ],
)

edit_product_handler = ConversationHandler(
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
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$"),
    ],
)

upload_db_handler = CommandHandler("upload_db", upload_db)
download_db_handler = ConversationHandler(
    entry_points=[CommandHandler("download_db", ask_about_download)],
    states={
        STATES["DOWNLOAD_DB"]: [
            TypeHandler(filters.Update, download_db),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$"),
    ],
)

main_conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
    ],
    states={
        STATES["MENU"]: [
            track_product_handler,
            edit_product_handler,
        ],
    },
    fallbacks=[CommandHandler("stop", stop)],
)
