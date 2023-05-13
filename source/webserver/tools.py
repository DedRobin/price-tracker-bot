from fastapi import FastAPI, Request
from fastapi.responses import Response
from telegram import Update
from telegram.ext import Application


def create_app(bot_app: Application) -> FastAPI:
    web_app = FastAPI()

    @web_app.get("/")
    async def index():
        return {"message": "Bot is running"}

    @web_app.post("/telegram")
    async def telegram(request: Request):
        data = await request.json()
        update = Update.de_json(data=data, bot=bot_app.bot)
        await bot_app.update_queue.put(update)
        return Response()

    return web_app
