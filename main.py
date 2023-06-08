import asyncio

import uvicorn
from telegram.ext import ApplicationBuilder, ContextTypes

from source.bot.custom_entities import CustomContext
from source.bot.handlers import (
    help_handler,
    main_conversation_handler,
    admin_handler,
)
from source.bot.users.handlers import join_handler
from source.bot.jobs import send_notifications
from source.bot.admin.handlers import create_admin_handler
from source.settings import HOST, PORT, SEND_DELAY, TOKEN, WEBHOOK_URL, get_logger
from source.webserver.app import create_app


async def main():
    get_logger()

    context_types = ContextTypes(context=CustomContext)

    # App
    application = ApplicationBuilder().token(TOKEN).context_types(context_types).build()

    # Handlers
    application.add_handler(main_conversation_handler)
    application.add_handler(help_handler)
    application.add_handler(create_admin_handler)
    application.add_handler(join_handler)
    application.add_handler(admin_handler)

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
