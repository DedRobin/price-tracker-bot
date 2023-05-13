import asyncio
import os

import uvicorn
from telegram.ext import ApplicationBuilder, ContextTypes

from source.bot.custom_entities import CustomContext
from source.bot.handlers import (
    add_user_handler,
    edit_product_handler,
    start_handler,
    track_product_handler,
)
from source.bot.jobs import send_notifications
from source.settings import enable_logger
from source.webserver.tools import create_app


# def main():
async def main():
    token = os.environ.get("BOT_TOKEN")
    webhook_url = os.environ.get("WEBHOOK_URL")
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))

    enable_logger()

    context_types = ContextTypes(context=CustomContext)

    application = ApplicationBuilder().token(token).context_types(context_types).build()

    application.add_handler(start_handler)
    application.add_handler(track_product_handler)
    application.add_handler(edit_product_handler)
    application.add_handler(add_user_handler)

    job_queue = application.job_queue
    job_queue.run_repeating(send_notifications, interval=1000, first=1)

    await application.bot.set_webhook(url=f"{webhook_url}/telegram")

    web_app = create_app(bot_app=application)

    webserver = uvicorn.Server(
        config=uvicorn.Config(app=web_app, port=port, use_colors=False, host=host)
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
