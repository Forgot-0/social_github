
from datetime import datetime

from pydantic import BaseModel


class MessageDTO(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    text: str
    created_at: datetime
    is_deleted: bool


class MessageCursorPage(BaseModel):
    items: list[MessageDTO]
    next_cursor: int | None
    has_more: bool
    read_cursors: dict[int, int] = {}
