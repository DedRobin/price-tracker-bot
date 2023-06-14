from warnings import filterwarnings
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.warnings import PTBUserWarning

from source.bot.products.commands import back
from source.bot.config.settings import TIMEOUT_CONVERSATION
from source.bot.products.callback_data import STATES
from source.bot.users.commands import (
    apply_ask,
    ask_about_joining,
    get_joined_user_actions,
    refuse_ask,
    show_asks,
)

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

asks_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CallbackQueryHandler(show_asks, pattern=rf"^{STATES['ASKS']}$")
    ],
    states={
        STATES["ASK_ACTIONS"]: [
            CallbackQueryHandler(get_joined_user_actions, pattern=r"^ask_id=\d+$"),
            CallbackQueryHandler(apply_ask, pattern=rf"{STATES['APPLY_ASK']}$"),
            CallbackQueryHandler(refuse_ask, pattern=rf"{STATES['REFUSE_ASK']}$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(back, pattern=rf"^{STATES['BACK']}$")],
)

join_handler = CommandHandler("join", ask_about_joining)
