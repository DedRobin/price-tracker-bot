from aiohttp import ClientSession
from bs4 import BeautifulSoup


async def parse_onliner(url: str) -> tuple:
    async with ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")
            name = soup.find("h1", class_="catalog-masthead__title js-nav-header")
            name = name.string.strip()
            price = soup.find(
                "a", class_="offers-description__link offers-description__link_nodecor js-description-price-link")
            if not price:
                price = 0.0
            else:
                price = float("".join(n.replace(",", ".") if n.isdigit() or n == "," else "" for n in price.string))
            return name, price
