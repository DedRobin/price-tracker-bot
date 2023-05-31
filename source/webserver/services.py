from source.database.queries import insert_token, exist_token


async def add_token_for_user(token: str, username: str) -> None:
    await insert_token(token, username)


async def check_token_in_db(token: str) -> bool:
    it_exists = await exist_token(token)
    return it_exists
