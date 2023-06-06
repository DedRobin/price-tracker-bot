from source.bot.session_tokens.queries import exist_token, insert_token, remove_token


async def add_token_for_user(token: str, username: str) -> None:
    await insert_token(token, username)


async def remove_token_for_user(token: str) -> None:
    await remove_token(token)


async def check_token_in_db(token: str) -> bool:
    it_exists = await exist_token(token)
    return it_exists
