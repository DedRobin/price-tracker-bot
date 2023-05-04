from fastapi import FastAPI
from fastapi.responses import Response
from telegram import Update
from telegram.ext import Application

from webserver.models import BotRequest


def create_app(bot_app: Application) -> FastAPI:
    web_app = FastAPI()

    @web_app.get("/")
    async def index():
        return {"message": "Bot is running"}

    @web_app.post("/telegram")
    async def telegram(request: BotRequest):
        data = request.dict()
        await bot_app.update_queue.put(
            Update.de_json(data=data, bot=bot_app.bot)
        )
        return Response()

    return web_app
