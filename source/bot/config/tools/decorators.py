from logging import Logger
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes


def log(logger: Logger) -> Callable[[Any], Callable[[Update, Any], Any]]:
    """Decorator for logging the metadata of the bot command"""

    def decorator_wrapper(function) -> Callable[[Update, Any], Any]:
        def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            data = [
                update.effective_chat.first_name,
                update.effective_chat.last_name,
                update.effective_chat.username,
                update.effective_chat.link,
                update.effective_chat.id,
            ]
            command = function.__name__
            log_message = "{0} {1} - {2} ({3}), chat ID={4} used command '/{5}'"
            logger.info(log_message.format(*data, command))
            return function(update, context)

        return wrapper

    return decorator_wrapper
