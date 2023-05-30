from source.database.queries import insert_token


async def add_token_for_user(token: str, username: str) -> None:
    await insert_token(token, username)
