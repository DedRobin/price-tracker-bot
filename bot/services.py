import os
import re
from telegram import Update
from aiohttp import ClientSession

from bot.settings import get_logger

SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")

logger = get_logger(__name__)


async def get_data_from_update(update: Update) -> dict:
    data = {
        "first_name": update.effective_chat.first_name,
        "last_name": update.effective_chat.last_name,
        "username": update.effective_chat.username,
        "link": update.effective_chat.link,
        "chat_id": update.effective_chat.id
    }

    return data


async def get_chat_ids() -> list:
    async with ClientSession() as session:
        url = f"http://{SERVER_HOST}:8080/api/users/"
        async with session.get(url=url) as resp:
            data: dict = await resp.json()
            chat_ids = [user["chat_id"] for user in data.values()]
    logger.info("Get chat IDs")
    return chat_ids


async def check_link(link: str) -> bool:
    match = re.match(pattern=r"https:\/\/catalog.onliner.by\/.+", string=link)
    logger.info(f"'{link}' is correct")

    return True if match else False


async def check_product_in_db(username: str, link: str) -> bool:
    async with ClientSession() as session:
        url = f"http://{SERVER_HOST}:8080/api/products/"
        params = {
            "username": username,
            "link": link
        }
        async with session.get(url=url, params=params) as resp:
            data = await resp.json()
    return True if data else False


async def add_product(username: str, link: str, name: str, current_price: float) -> int:
    async with ClientSession() as session:
        url = f"http://{SERVER_HOST}:8080/api/products/"
        data = {
            "username": username,
            "link": link,
            "name": name,
            "current_price": current_price,
        }
        async with session.post(url=url, json=data) as resp:
            return resp.status


async def get_user_products(username: str):
    async with ClientSession() as session:
        url = f"http://{SERVER_HOST}:8080/api/products/"
        params = {
            "username": username,
        }
        async with session.get(url=url, params=params) as resp:
            products = await resp.json()
            return products
