import logging
import os

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5000))
SEND_DELAY = int(os.environ.get("SEND_EVERY", 3600))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


def get_logger(name: str = "") -> logging.Logger:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger(name or __name__)
    return logger
