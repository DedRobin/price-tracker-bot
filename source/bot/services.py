import os
import re

from telegram import Update

from source.bot.queries import (
    add_user_for_product,
    exist_product,
    insert_product,
    insert_user,
    remove_product,
    remove_user_from_special_product,
    select_products,
    select_users,
)
from source.settings import enable_logger

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
    if admin_key == os.environ.get("USER_KEY"):
        await insert_user(username=username, chat_id=chat_id)
        return True
    elif admin_key == os.environ.get("ADMIN_KEY"):
        await insert_user(username=username, chat_id=chat_id, is_admin=True)
        return True
    return False


async def get_chat_ids(is_admin: bool = False) -> list:
    """Get all chat IDs by some """

    users = await select_users(
        is_admin=is_admin,
    )

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


async def add_product(username: str, link: str, name: str, price: float) -> int:
    product_exists = await exist_product(link=link)
    if product_exists:
        await add_user_for_product(username=username, link=link)
    else:
        await insert_product(username=username, link=link, name=name, price=price)
    return True


async def get_user_products(username: str) -> list[dict]:
    params = {"username": username}
    products = await select_products(params)
    product_list = []
    for product in products:
        product_list.append(
            {
                "id": product.id,
                "name": product.name,
                "link": product.product_link,
                "current_price": product.current_price,
                "previous_price": product.previous_price,
                "updated_at": product.updated_at.strftime("%d.%m.%Y, %H:%M:%S"),
                "chat_ids": [user.chat_id for user in product.users],
            }
        )

    return product_list


async def untrack_product(username: str, product_id: int):
    """Untrack a special product"""

    await remove_user_from_special_product(username=username, product_id=product_id)
    logger.info("Untrack the product")


async def check_relationship(product_id: int) -> None:
    """Check the relationship of users with products"""

    params = {"product_id": product_id}
    product = await select_products(params)
    product = product[0]
    users = product.users
    if not users:
        await remove_product(product_id)
