from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
from telegram import Update
from telegram.ext import Application

from source.database.admin_auth import get_admin_panel
from source.database.engine import get_engine


async def create_app(bot_app: Application) -> FastAPI:
    web_app = FastAPI()

    engine = await get_engine()
    get_admin_panel(web_app=web_app, engine=engine)

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
