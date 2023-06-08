import logging
import os

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5000))
SEND_DELAY = int(os.environ.get("SEND_EVERY", 3600))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


def get_logger(name: str = "unknown") -> logging.Logger:
    file_log = logging.FileHandler('logs.log')
    console_out = logging.StreamHandler()
    logging.basicConfig(
        handlers=(file_log, console_out),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger(name)
    return logger
