from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
from telegram import Update
from telegram.ext import Application
from sqladmin import Admin

from source.store.database.tools import get_engine
from source.store.database.admin import UserAdmin, ProductAdmin, AdminAuth


async def create_app(bot_app: Application) -> FastAPI:
    web_app = FastAPI()
    egnine = await get_engine()
    authentication_backend = AdminAuth(secret_key="secret_key")

    admin = Admin(app=web_app, engine=egnine, authentication_backend=authentication_backend)

    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)

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
