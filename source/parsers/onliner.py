import os

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from source.settings import get_logger

logger = get_logger(__name__)

SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")


async def parse(session: ClientSession, url: str) -> tuple | None:
    async with session.get(url) as resp:
        text = await resp.text()
        soup = BeautifulSoup(text, "html.parser")
        name = soup.find("h1", class_="catalog-masthead__title js-nav-header")
        if not name:
            return None, None
        name = name.string.strip()
        price = soup.find(
            "a",
            class_="offers-description__link offers-description__link_nodecor js-description-price-link",
        )

        if not price:  # Price = "Нет в наличии или под заказ"
            price = 0.0
        else:
            price = float(
                "".join(
                    n.replace(",", ".") if n.isdigit() or n == "," else ""
                    for n in price.string
                )
            )
        logger.info(f"Product name and price are received('{name}', {url})")
        return name, price
