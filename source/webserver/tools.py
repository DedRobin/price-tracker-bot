import time
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from telegram import Update
from telegram.ext import Application
from sqladmin import Admin

from source.database.engine import get_engine
from source.database.admin import UserAdmin, ProductAdmin, AdminAuth


async def create_app(bot_app: Application) -> FastAPI:
    web_app = FastAPI()

    # web_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.2"])

    engine = await get_engine()

    authentication_backend = AdminAuth(secret_key="secret_key")

    admin = Admin(
        app=web_app,
        title="Price Tracker Admin",
        engine=engine,
        authentication_backend=authentication_backend
    )

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
