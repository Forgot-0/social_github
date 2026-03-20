from datetime import datetime

from pydantic import BaseModel


class ChatDTO(BaseModel):
    id: int
    user_id_1: int
    user_id_2: int
    last_message_at: datetime | None
    created_at: datetime
