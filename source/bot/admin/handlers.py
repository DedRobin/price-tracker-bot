from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from source.bot.commands import no_create_admin
from source.bot.settings import TIMEOUT_CONVERSATION
from source.bot.states import STATES
from source.bot.admin.commands import create_admin, check_admin_key

create_admin_handler = ConversationHandler(
    conversation_timeout=TIMEOUT_CONVERSATION,
    entry_points=[
        CommandHandler("create_admin", create_admin),
    ],
    states={
        STATES["CREATE_ADMIN"]: [
            MessageHandler(filters.TEXT, check_admin_key),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(no_create_admin, pattern=rf"^{STATES['NO_CREATE_ADMIN']}$")
    ],
)
