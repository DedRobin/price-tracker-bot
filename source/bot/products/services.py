import os
import re

from source.bot.products.queries import (
    exist_product,
    insert_product,
    remove_product,
    select_products,
)
from source.bot.users.queries import (
    add_user_for_product,
    remove_user_from_special_product,
)
from source.settings import get_logger

SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")

logger = get_logger(__name__)


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
