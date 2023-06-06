import asyncio

import uvicorn
from telegram.ext import ApplicationBuilder, ContextTypes

from source.bot.custom_entities import CustomContext
from source.bot.handlers import (
    add_user_handler,
    download_db_handler,
    help_handler,
    main_conversation_handler,
    upload_db_handler,
)
from source.bot.jobs import send_notifications
from source.settings import HOST, PORT, SEND_DELAY, TOKEN, WEBHOOK_URL, get_logger
from source.webserver.tools import create_app


async def main():
    get_logger()

    context_types = ContextTypes(context=CustomContext)

    # App
    application = ApplicationBuilder().token(TOKEN).context_types(context_types).build()

    # Handlers
    application.add_handler(main_conversation_handler)
    application.add_handler(help_handler)
    application.add_handler(add_user_handler)
    application.add_handler(upload_db_handler)
    application.add_handler(download_db_handler)

    # Jobs
    job_queue = application.job_queue
    job_queue.run_repeating(send_notifications, interval=SEND_DELAY, first=1)

    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram")

    web_app = await create_app(bot_app=application)

    webserver = uvicorn.Server(
        config=uvicorn.Config(app=web_app, port=PORT, use_colors=False, host=HOST)
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
