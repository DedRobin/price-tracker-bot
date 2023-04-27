import os

from telegram.ext import ApplicationBuilder

from bot.handlers import edit_product_handler, start_handler, track_product_handler, add_user_handler
from bot.settings import get_logger

if __name__ == "__main__":
    logger = get_logger()

    application = ApplicationBuilder().token(os.environ.get("BOT_TOKEN")).build()

    application.add_handler(start_handler)
    application.add_handler(track_product_handler)
    application.add_handler(edit_product_handler)
    application.add_handler(add_user_handler)

    application.run_polling()
