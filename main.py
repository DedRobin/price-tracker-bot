import asyncio
import os

import uvicorn
from telegram.ext import ApplicationBuilder, ContextTypes

from source.bot.custom_entities import CustomContext
from source.bot.handlers import add_user_handler, download_db_handler, upload_db_handler, main_conversation_handler, help_handler
from source.bot.jobs import send_notifications
from source.settings import enable_logger
from source.webserver.tools import create_app


async def main():
    token = os.environ.get("BOT_TOKEN")
    webhook_url = os.environ.get("WEBHOOK_URL")
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    send_delay = int(os.environ.get("SEND_EVERY", 3600))

    enable_logger()

    context_types = ContextTypes(context=CustomContext)

    # App
    application = ApplicationBuilder().token(token).context_types(context_types).build()

    # Handlers
    application.add_handler(main_conversation_handler)
    application.add_handler(help_handler)
    application.add_handler(add_user_handler)
    application.add_handler(upload_db_handler)
    application.add_handler(download_db_handler)

    # Jobs
    job_queue = application.job_queue
    job_queue.run_repeating(send_notifications, interval=send_delay, first=1)

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
