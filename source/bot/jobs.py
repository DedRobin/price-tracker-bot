from aiohttp import ClientSession
from telegram.ext import ContextTypes

from source.bot.queries import select_products, update_product
from source.parsers import onliner
from source.settings import enable_logger

logger = enable_logger(__name__)


async def send_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Sending notifications about price changes for each product"""

    products = await select_products()

    async with ClientSession() as session:
        for product in products:
            url = product.product_link

            # Received a product price by URL
            _, new_price = await onliner.parse(session, url)

            if new_price != product.current_price:
                updated_product = await update_product(product=product, price=new_price)
                chat_ids = [user.chat_id for user in updated_product.users]

                # Product data
                current_price = updated_product.current_price
                previous_price = updated_product.previous_price
                link = updated_product.product_link
                name = updated_product.name

                # Count a difference
                different = current_price - previous_price
                different = round(different, 2)
                if abs(different) >= 1:
                    word = "снизилась" if different < 0 else "выросла"
                    emoji = "\U0001F601" if different < 0 else "\U0001F621"

                    notification_text = f"""{emoji}{name}
                    
{link}  
    
Цена {word} на {abs(different)} BYN
Предыдущая цена = {previous_price} BYN
Новая цена = {current_price} BYN"""

                    for chat_id in chat_ids:
                        await context.bot.send_message(
                            chat_id=chat_id, text=notification_text
                        )
                else:
                    pass

        logger.info("All notifications have been sent")
