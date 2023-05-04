from pydantic import BaseModel


class BotRequest(BaseModel):
    update_id: int
    message: dict
