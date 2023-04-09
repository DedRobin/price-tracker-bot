import re
from datetime import datetime
# from sqlalchemy import select, exists, delete
# from sqlalchemy.orm import selectinload
# from db.models import Product, User

from bot.settings import get_logger
# from db.tools import create_session
#
# logger = get_logger()
#
#
# async def write_product(username: str, name: str, link: str, current_price: float):
#     async_session = await create_session()
#     async with async_session() as session:
#         async with session.begin():
#             query = select(User).where(User.username == username)
#             user = await session.scalar(query)
#             product = Product(
#                 product_link=link,
#                 name=name,
#                 current_price=current_price,
#                 previous_price=current_price,
#                 users=[user],
#                 updated_at=datetime.now()
#             )
#             session.add(product)
#
#             logger.info(f"User {user.username} wrote a product '{product.name}'")
#
#             return False
#
#
# async def checking_product_in_db(username: str, link: str) -> bool:
#     async_session = await create_session()
#     async with async_session() as session:
#         async with session.begin():
#             select_query = select(Product).where(Product.product_link == link).where(User.username == username)
#             query = select(exists(select_query))
#             is_existed = await session.scalar(query)
#
#             logger.info(f"User {username} checked a product '{link}'")
#
#             return is_existed
#
#

#
#
# async def get_user_products(username: str) -> tuple:
#     async_session = await create_session()
#     async with async_session() as session:
#         query = select(User).where(User.username == username)
#         user = await session.execute(query)
#         user = user.scalars().first()
#         query = select(Product).where(Product.users.contains(user))
#         products = await session.execute(query)
#         products = products.scalars().all()
#
#         logger.info(f"User {username} is getting products")
#
#         return products
#
#
# async def get_product(product_id: int):
#     async_session = await create_session()
#     async with async_session() as session:
#         query = select(Product).where(Product.id == product_id)
#         product = await session.scalar(query)
#
#         logger.info(f"Getting a product '{product.name}'")
#
#         return product
#
#
# async def untrack_product(username: str, product_id: int) -> None:
#     async_session = await create_session()
#     async with async_session() as session:
#         u_query = select(User).where(User.username == username)
#         user = await session.scalar(u_query)
#         p_query = select(Product).where(Product.id == product_id).options(selectinload(Product.users))
#         product = await session.scalar(p_query)
#         a = product.users
#         product.users.remove(user)
#         b = product.users
#
#         if not product.users:
#             delete_query = delete(Product).where(Product.id == product.id)
#             await session.execute(delete_query)
#
#         await session.commit()
#
#         logger.info(f"User {username} removed a product {product.name} from tracking")
#
#
# async def get_chat_ids() -> list:
#     logger.info("Getting chat IDs")
#
#     async_session = await create_session()
#     async with async_session() as session:
#         query = select(User.chat_id)
#         result = await session.scalars(query)
#         result = result.all()
#         return result
