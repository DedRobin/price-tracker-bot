#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.
# pylint: disable=import-error,wrong-import-position
"""
Simple example of a bot that uses a custom webhook setup and handles custom updates.
For the custom webhook setup, the libraries `starlette` and `uvicorn` are used. Please install
them as `pip install starlette~=0.20.0 uvicorn~=0.17.0`.
Note that any other `asyncio` based web server framework can be used for a custom webhook setup
just as well.
Usage:
Set bot token, url, admin chat_id and port at the start of the `main` function.
You may also need to change the `listen` value in the uvicorn configuration to match your setup.
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""
import asyncio
import html
import logging
import os
from dataclasses import dataclass
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
import uvicorn
from pydantic import BaseModel

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""

    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """

    @classmethod
    def from_update(
            cls,
            update: object,
            application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


async def start(update: Update, context: CustomContext) -> None:
    """Display a message with instructions on how to use this bot."""
    url = context.bot_data["url"]
    payload_url = html.escape(f"{url}/submitpayload?user_id=<your user id>&payload=<payload>")
    text = (
        f"To check if the bot is still running, call <code>{url}/healthcheck</code>.\n\n"
        f"To post a custom update, call <code>{payload_url}</code>."
    )
    await update.message.reply_html(text=text)


async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Callback that handles the custom updates."""
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    await context.bot.send_message(
        chat_id=context.bot_data["admin_chat_id"], text=text, parse_mode=ParseMode.HTML
    )


async def main() -> None:
    """Set up the application and a custom webserver."""

    token = os.environ.get("BOT_TOKEN")
    url = os.environ.get("URL")
    admin_chat_id = os.environ.get("ADMIN_CHAT_ID")
    host = os.environ.get("HOST", "127.0.0.1")
    port = os.environ.get("PORT", 5000)

    context_types = ContextTypes(context=CustomContext)
    # Here we set updater to None because we want our custom webhook server to handle the updates
    # and hence we don't need an Updater instance
    application = (
        Application.builder().token(token).updater(None).context_types(context_types).build()
    )
    # save the values in `bot_data` such that we may easily access them in the callbacks
    application.bot_data["url"] = url
    application.bot_data["admin_chat_id"] = admin_chat_id

    # register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))

    # Pass webhook settings to telegram
    # await application.bot.set_webhook(url=f"{url}/telegram")
    await application.bot.set_webhook(url=f"{url}/telegram")

    # Set up webserver

    app = FastAPI()

    class BotRequest(BaseModel):
        update_id: int
        message: dict

    @app.get("/")
    async def root():
        return {"message": "Bot is running"}

    @app.post("/telegram")
    async def telegram(request: BotRequest):
        data = request.dict()
        await application.update_queue.put(
            Update.de_json(data=data, bot=application.bot)
        )
        return Response()
        # return

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=app,
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
