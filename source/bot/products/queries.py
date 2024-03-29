from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import Row, RowMapping, delete, exists, select
from sqlalchemy.orm import selectinload

from source.database.engine import create_session
from source.database.models import Product, User
from source.settings import get_logger

logger = get_logger(__name__)


async def exist_product(link: str) -> bool:
    """Check if the product exists"""

    async_session = await create_session()
    async with async_session() as session:
        select_query = select(Product).where(Product.product_link == link)
        is_existed = await session.scalar(exists(select_query).select())
        return True if is_existed else False


async def insert_product(username: str, link: str, name: str, price: float) -> None:
    """Add a new product for tracking if it doesn't exist"""

    async_session = await create_session()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.username == username))
        product = Product(
            product_link=link,
            name=name,
            current_price=price,
            previous_price=price,
            updated_at=datetime.now(),
        )
        product.users.append(user)
        session.add(product)
        await session.commit()


async def select_products(params: dict = None) -> Sequence[Row | RowMapping | Any]:
    """Get products by some filter"""

    logger.info("Receiving products")

    async_session = await create_session()
    async with async_session() as session:
        select_query = select(Product)

        if params:
            username = params.get("username")
            link = params.get("link")
            product_id = params.get("product_id")

            if username:
                user_query = select(User).where(User.username == username)
                user = await session.scalar(user_query)
                select_query = select_query.where(Product.users.contains(user))
            if product_id:
                select_query = select_query.where(Product.id == product_id)
            if link:
                select_query = select_query.where(Product.product_link == link)

        select_query = select_query.options(selectinload(Product.users))
        products = await session.scalars(select_query)
        products = products.all()

        logger.info("Products received")
        return products


async def get_product(product_id: int):
    """Get a special product by it ID"""

    async_session = await create_session()
    async with async_session() as session:
        select_query = select(Product).where(Product.id == product_id)
        product = await session.scalar(select_query)
        product = product.__dict__
        del product["_sa_instance_state"]
        product["updated_at"] = (product["updated_at"].strftime("%d.%m.%Y, %H:%M:%S"),)
        return product


async def update_product(
    product: Product, price: float = None, name: str = None
) -> Product:
    """Update a specific product"""

    async_session = await create_session()
    async with async_session() as session:
        select_query = (
            select(Product)
            .where(Product.id == product.id)
            .options(selectinload(Product.users))
        )
        product = await session.scalar(select_query)
        if name:
            product.name = name
        product.previous_price = product.current_price
        product.current_price = price
        await session.commit()
        return product


async def remove_product(product_id: int) -> None:
    """Delete a special product from the table"""

    async_session = await create_session()
    async with async_session() as session:
        delete_query = delete(Product).where(Product.id == product_id)
        await session.execute(delete_query)
        await session.commit()
