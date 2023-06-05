from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
from telegram import Update
from telegram.ext import Application

from source.settings import get_logger
from source.database.admin_auth import get_admin_panel
from source.database.engine import get_engine
from source.webserver.settings import Settings


async def create_app(bot_app: Application) -> FastAPI:
    logger = get_logger(__name__)
    settings = Settings()
    web_app = FastAPI(openapi_url=settings.openapi_url)

    engine = await get_engine()
    get_admin_panel(web_app=web_app, engine=engine)

    @web_app.get("/")
    async def index():
        return {"message": "Bot is running"}

    @web_app.post("/telegram")
    async def telegram(request: Request):
        try:
            data = await request.json()
        except Exception as ex:
            logger.error(ex)
            return Response(status_code=400)
        else:
            update = Update.de_json(data=data, bot=bot_app.bot)
            await bot_app.update_queue.put(update)
            return Response(status_code=200)

    return web_app
