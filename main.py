import os
import asyncio
import uvicorn
from telegram.ext import ApplicationBuilder, ContextTypes, Application

from bot.handlers import edit_product_handler, start_handler, track_product_handler, add_user_handler
from bot.settings import enable_logger
from bot.custom_entities import CustomContext
from webserver.tools import create_app


async def main():
    token = os.environ.get("BOT_TOKEN")
    webhook_url = os.environ.get("WEBHOOK_URL")
    admin_chat_id = os.environ.get("ADMIN_CHAT_ID")
    host = os.environ.get("HOST", "127.0.0.1")
    port = os.environ.get("PORT", 5000)

    enable_logger()

    context_types = ContextTypes(context=CustomContext)

    application = Application.builder().token(token).updater(None).context_types(context_types).build()

    application.add_handler(start_handler)
    application.add_handler(track_product_handler)
    application.add_handler(edit_product_handler)
    application.add_handler(add_user_handler)

    await application.bot.set_webhook(url=f"{webhook_url}/telegram")

    web_app = create_app(bot_app=application)

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=web_app,
            port=port,
            use_colors=False,
            host=host,
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
