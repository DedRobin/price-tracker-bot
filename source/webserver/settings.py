import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    openapi_url: str = os.environ.get("OPENAPI_URL")
