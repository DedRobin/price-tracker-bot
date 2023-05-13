from aiohttp import ClientSession
from telegram.ext import ContextTypes

from source.settings import enable_logger
from source.parsers import onliner
from source.bot.queries import select_products, update_product

logger = enable_logger(__name__)


async def send_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Sending notifications about price changes for each product"""

    products = await select_products()

    async with ClientSession() as session:
        for product in products:
            url = product.product_link

            # Received a product price by URL
            _, price = await onliner.parse(session, url)

            if price != product.current_price:
                updated_product = await update_product(product=product, price=price)
                chat_ids = [user.chat_id for user in updated_product.users]

                current_price = updated_product.current_price
                previous_price = updated_product.previous_price
                link = updated_product.product_link
                name = updated_product.name

                different = current_price - previous_price
                word = "снизилась" if different < 0 else "выросла" ""
                emoji = "\U0001F601" if different < 0 else "\U0001F621"

                notification_text = f"""{link}
    
{emoji}{name}
    
Цена {word} на {abs(different)} BYN
Предыдущая цена = {previous_price} BYN
Новая цена = {current_price} BYN"""

                for chat_id in chat_ids:
                    await context.bot.send_message(chat_id=chat_id, text=notification_text)

        logger.info("All notifications have been sent")
