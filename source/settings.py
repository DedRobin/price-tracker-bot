import os
import logging

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


def get_logger(name: str = "") -> logging.Logger:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger(name or __name__)
    return logger
