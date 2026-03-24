
from datetime import datetime

from pydantic import BaseModel, Field

from app.chats.models.message import MessageType


class MessageDTO(BaseModel):
    id: int
    chat_id: int
    author_id: int
    type: MessageType
    content: str | None = Field(default=None)
    reply_to_id: int | None = Field(default=None)
    media_url: str | None = Field(default=None)
    is_deleted: bool
    is_edited: bool
    created_at: datetime
    updated_at: datetime


class MessageCursorPage(BaseModel):
    items: list[MessageDTO]
    next_cursor: int | None
    has_more: bool
    read_cursors: dict[int, int] = {}


class MessageDeliveryStatusDTO(BaseModel):
    message_id: int
    delivered_to: dict[int, bool]


class MemberReadCursorDTO(BaseModel):
    user_id: int
    last_read_message_id: int


class MessageReadDetailsPageDTO(BaseModel):
    items: list[MemberReadCursorDTO]
    next_cursor: int | None = None
    has_more: bool = False
