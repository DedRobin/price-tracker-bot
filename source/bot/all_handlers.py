from source.bot.admin.handlers import admin_handler
from source.bot.products.handlers import help_handler, main_conversation_handler
from source.bot.users.handlers import join_handler

# All handlers
handlers = [
    main_conversation_handler,
    admin_handler,
    join_handler,
    help_handler,
]
