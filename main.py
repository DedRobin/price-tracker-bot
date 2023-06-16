import asyncio

import uvicorn
from telegram.ext import ApplicationBuilder, ContextTypes

from source.bot.all_handlers import handlers
from source.bot.config.tools.custom_entities import CustomContext
from source.bot.config.tools.jobs import send_notifications
from source.settings import HOST, PORT, SEND_DELAY, TOKEN, WEBHOOK_URL, get_logger
from source.webserver.app import create_app


async def main():
    get_logger()

    context_types = ContextTypes(context=CustomContext)

    # App
    application = ApplicationBuilder().token(TOKEN).context_types(context_types).build()

    # Handlers
    application.add_handlers(handlers)

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
