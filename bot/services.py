import os
import re

from aiohttp import ClientSession
from telegram import Update
from telegram.ext import ContextTypes

from bot.queries import insert_user, select_users, select_products, exist_product, add_user_for_product, insert_product
from bot.settings import enable_logger

SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")

logger = enable_logger(__name__)


async def get_data_from_update(update: Update) -> dict:
    data = {
        "first_name": update.effective_chat.first_name,
        "last_name": update.effective_chat.last_name,
        "username": update.effective_chat.username,
        "link": update.effective_chat.link,
        "chat_id": update.effective_chat.id,
    }

    return data


async def post_user(admin_key: str, username: str, chat_id: int) -> int:
    if admin_key == os.environ.get("ADMIN_KEY"):
        await insert_user(username=username, chat_id=chat_id)
        return True
    return False


async def get_chat_ids() -> list:
    """Get all chat IDs"""

    users = await select_users()
    logger.info("Get chat IDs")
    chat_ids = [user.chat_id for user in users]
    return chat_ids


async def check_link(link: str) -> bool:
    match = re.match(pattern=r"https:\/\/catalog.onliner.by\/.+", string=link)
    logger.info(f"'{link}' is correct")

    return True if match else False


async def check_product_in_db(username: str, link: str) -> bool:
    params = {"username": username, "link": link}
    products = await select_products(params)
    return True if products else False


async def add_product(username: str, link: str) -> int:
    product_exists = await exist_product(link=link)
    if product_exists:
        await add_user_for_product(
            username=username,
            link=link,
        )
    else:
        await insert_product(
            username=username,
            link=link,
            # name=name,
            # current_price=current_price,
        )
    return True

    # async with ClientSession() as session:
    #     url = f"http://{SERVER_HOST}:8080/api/products/"
    #     data = {
    #         "username": username,
    #         "link": link,
    #     }
    #     async with session.post(url=url, json=data) as resp:
    #         return resp.status


async def get_user_products(username: str) -> list[dict]:
    async with ClientSession() as session:
        url = f"http://{SERVER_HOST}:8080/api/products/"
        params = {
            "username": username,
        }
        async with session.get(url=url, params=params) as resp:
            products = await resp.json()
            return products


async def untrack_product(username: str, product_id: int):
    async with ClientSession() as session:
        url = f"http://{SERVER_HOST}:8080/api/products/{product_id}/"
        data = {
            "action": "remove_user",
            "username": username,
        }
        async with session.put(url=url, json=data) as resp:
            return resp.status
