import os

DB_URL = "sqlite+aiosqlite:///database.db"
DB_ECHO = os.environ.get("DB_ECHO") == "True"
