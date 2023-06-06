from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from source.bot.commands import cancel_add_user
from source.bot.handlers import back
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
asks_handler = ConversationHandler(
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
ask_to_join_handler = CommandHandler("ask_to_join", ask_to_join)
